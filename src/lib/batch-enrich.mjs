// Batch enrichment script — processes all cached animals that lack LLM data,
// with a 4-second delay between each to avoid API rate limits (429).
//
// Usage: node src/lib/batch-enrich.mjs

import ZAI from "z-ai-web-dev-sdk";
import { readFileSync, writeFileSync, readdirSync, existsSync } from "fs";
import path from "path";
import { setTimeout as sleep } from "timers/promises";

const ROOT = process.cwd();
const CACHE_DIR = path.join(ROOT, "data", "cache", "wikipedia");

const EXTRACTION_PROMPT = `You are a precise wildlife data extractor. Given the Wikipedia article text about an animal, extract structured facts. Only include values actually stated in the text — leave a field empty ("") if not mentioned. Use metric units (m, cm, kg, km/h, years).

Output STRICT JSON (no markdown fences) with this exact shape:
{
  "scientific_name": "Panthera tigris",
  "young_name": "cub",
  "group_name": "pride",
  "physical": { "length": "", "height": "", "weight": "", "top_speed": "", "lifespan": "" },
  "ecology": { "diet": "", "habitat": "", "locations": "", "group_behavior": "", "conservation_status": "", "biggest_threat": "", "distinctive_features": [] },
  "classification": { "kingdom": "", "phylum": "", "class": "", "order": "", "family": "", "genus": "", "species": "" },
  "reproduction": { "gestation_period": "", "average_litter_size": "", "name_of_young": "" },
  "time_period_text": ""
}

Rules:
- diet: one of Carnivore, Herbivore, Omnivore, Piscivore, Insectivore, Nectarivore, Scavenger, Filter feeder
- conservation_status: one of Least Concern, Near Threatened, Vulnerable, Endangered, Critically Endangered, Extinct in the Wild, Extinct, Data Deficient
- Use ranges (en-dash –) when given. Single value otherwise.
- For egg-layers: gestation=incubation, litter=clutch size.
- classification: fill all 7 ranks if mentioned. Blank if not.
- Do NOT invent values. Empty "" is better than a guess.`;

function mergeExtracted(animal, extracted) {
  const merged = { ...animal };
  if (extracted.scientific_name?.trim()) merged.scientific_name = extracted.scientific_name.trim();
  if (extracted.young_name?.trim()) merged.young_name = extracted.young_name.trim();
  if (extracted.group_name?.trim()) merged.group_name = extracted.group_name.trim();
  if (extracted.physical) {
    merged.physical = { ...(animal.physical || {}) };
    for (const [k, v] of Object.entries(extracted.physical)) {
      if (typeof v === "string" && v.trim()) merged.physical[k] = v;
    }
  }
  if (extracted.ecology) {
    merged.ecology = { ...(animal.ecology || {}) };
    for (const [k, v] of Object.entries(extracted.ecology)) {
      if (typeof v === "string" && v.trim()) merged.ecology[k] = v;
      else if (Array.isArray(v) && v.length) merged.ecology[k] = v;
    }
  }
  if (extracted.classification) {
    merged.classification = { ...(animal.classification || {}) };
    for (const [k, v] of Object.entries(extracted.classification)) {
      if (typeof v === "string" && v.trim()) merged.classification[k] = v;
    }
  }
  if (extracted.reproduction) {
    merged.reproduction = { ...(animal.reproduction || {}) };
    for (const [k, v] of Object.entries(extracted.reproduction)) {
      if (typeof v === "string" && v.trim()) merged.reproduction[k] = v;
    }
  }
  if (extracted.time_period_text?.trim()) {
    merged.time_period = { text: extracted.time_period_text.trim(), width: "50%", start: "Ancient", end: "Present" };
  }
  return merged;
}

async function main() {
  const zai = await ZAI.create();
  const files = readdirSync(CACHE_DIR).filter(f => f.endsWith(".json")).sort();

  let processed = 0;
  let skipped = 0;
  let failed = 0;

  for (const file of files) {
    const cacheFile = path.join(CACHE_DIR, file);
    const animal = JSON.parse(readFileSync(cacheFile, "utf-8"));

    // Skip if already has full LLM data
    if (animal.scientific_name?.trim() && (animal.classification?.class || "")?.trim()) {
      skipped++;
      continue;
    }

    // Build the text blob from article sections
    const blob = [
      animal.summary,
      animal.article?.overview,
      animal.article?.description,
      animal.article?.habitat,
      animal.article?.behavior,
      animal.article?.conservation,
    ].filter(Boolean).join("\n\n");

    if (!blob.trim()) {
      console.log(`  ✗ ${animal.name}: no text to extract from`);
      failed++;
      continue;
    }

    try {
      const response = await zai.chat.completions.create({
        messages: [{
          role: "user",
          content: `${EXTRACTION_PROMPT}\n\nAnimal name: ${animal.name}\n\nWikipedia article text:\n${blob.slice(0, 5000)}`,
        }],
        thinking: { type: "disabled" },
      });

      const content = response.choices?.[0]?.message?.content ?? "";
      const cleaned = content.replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/i, "").trim();

      let extracted;
      try {
        extracted = JSON.parse(cleaned);
      } catch {
        const m = cleaned.match(/\{[\s\S]*\}/);
        extracted = m ? JSON.parse(m[0]) : {};
      }

      const enriched = mergeExtracted(animal, extracted);
      writeFileSync(cacheFile, JSON.stringify(enriched, null, 2));
      processed++;
      console.log(`  ✓ [${processed}] ${animal.name}: sci=${enriched.scientific_name || "?"} class=${enriched.classification?.class || "?"}`);
    } catch (err) {
      console.error(`  ✗ ${animal.name}: ${err.message?.slice(0, 80)}`);
      failed++;
      // If rate-limited, wait longer
      if (err.message?.includes("429")) {
        console.log("    Rate limited, waiting 30s...");
        await sleep(30000);
      }
    }

    // 4-second delay between calls to avoid rate limits
    await sleep(4000);
  }

  console.log(`\nDone. Processed: ${processed} | Skipped (already enriched): ${skipped} | Failed: ${failed}`);
}

main().catch(console.error);
