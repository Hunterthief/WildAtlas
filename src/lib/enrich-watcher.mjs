// WildAtlas - Fetch & Enrich watcher (Node, long-running)
//
// Watches data/cache/fetch-queue/ for *.json request files. For each, it:
//   1. Fetches the Wikipedia summary + key sections (parallel, with timeouts)
//   2. Saves the regex-extracted animal to the cache immediately
//   3. Spawns a short-lived node worker to call the LLM for structured extraction
//   4. Merges the LLM data and writes the enriched animal back to the cache
// Then deletes the request file.
//
// ALL network calls (Wikipedia + LLM) happen here, never inside Next.js.
// This is required because the Turbopack dev server crashes when API route
// handlers make outbound HTTPS requests.

import { readFileSync, writeFileSync, unlinkSync, readdirSync, existsSync, mkdirSync } from "fs";
import { spawn } from "child_process";
import path from "path";

const ROOT = process.cwd();
const FETCH_QUEUE_DIR = path.join(ROOT, "data", "cache", "fetch-queue");
const CACHE_DIR = path.join(ROOT, "data", "cache", "wikipedia");
const WORKER = path.join(ROOT, "src", "lib", "llm-extract-worker.mjs");

const WIKI_HEADERS = {
  "User-Agent": "WildAtlasBot/1.0 (https://example.org; educational animal encyclopedia project)",
  Accept: "application/json",
};

const REQUEST_TIMEOUT_MS = 8_000;

function slugify(name) {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

function wikitextToPlain(wt) {
  if (!wt) return "";
  let t = wt;
  t = t.replace(/<!--.*?-->/g, "");
  t = t.replace(/\{\{[^{}]*\}\}/g, "");
  t = t.replace(/<ref[^>]*>.*?<\/ref>/g, "");
  t = t.replace(/<ref[^/]*\/>/g, "");
  t = t.replace(/<[^>]+>/g, "");
  t = t.replace(/\[\[[^\]]*\|([^\]]*)\]\]/g, "$1");
  t = t.replace(/\[\[([^\]]*)\]\]/g, "$1");
  t = t.replace(/\[https?:\/\/\S* ([^\]]*)\]/g, "$1");
  t = t.replace(/\[https?:\/\/\S*\]/g, "");
  t = t.replace(/'{2,}/g, "");
  t = t.replace(/^=+\s*([^=]*)\s*=+$/gm, "$1");
  t = t.replace(/\n{3,}/g, "\n\n");
  t = t.replace(/[ \t]+/g, " ");
  return t.trim();
}

async function fetchJsonWithTimeout(url) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const res = await fetch(url, { headers: WIKI_HEADERS, signal: controller.signal });
    if (!res.ok) throw new Error(`API ${res.status}: ${url.slice(0, 60)}`);
    return await res.json();
  } finally {
    clearTimeout(timer);
  }
}

async function getSummary(title) {
  const data = await fetchJsonWithTimeout(
    `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(title)}`,
  );
  return {
    extract: data.extract ?? "",
    image: data.thumbnail?.source ?? data.originalimage?.source,
    url: data.content_urls?.desktop?.page ?? "",
  };
}

async function getSections(title) {
  const data = await fetchJsonWithTimeout(
    `https://en.wikipedia.org/w/api.php?action=parse&page=${encodeURIComponent(title)}&prop=sections&redirects=1&format=json`,
  );
  return (data?.parse?.sections ?? []).map((s) => ({ heading: s.line, index: String(s.index) }));
}

async function getSectionText(title, index) {
  const data = await fetchJsonWithTimeout(
    `https://en.wikipedia.org/w/api.php?action=parse&page=${encodeURIComponent(title)}&section=${index}&prop=wikitext&redirects=1&format=json`,
  );
  return wikitextToPlain(data?.parse?.wikitext?.["*"] ?? "");
}

const SECTION_PRIORITIES = [
  { key: "behavior", keywords: ["behaviour and ecology", "behavior and ecology", "ecology and behaviour", "behavior", "behaviour", "ecology", "diet", "diet and feeding", "feeding"] },
  { key: "habitat", keywords: ["distribution and habitat", "habitat", "distribution", "range", "geographic range"] },
  { key: "conservation", keywords: ["conservation", "conservation status", "status", "threats"] },
  { key: "description", keywords: ["description", "characteristics", "appearance", "physical characteristics"] },
];

function pickSection(sections, keywords) {
  for (const kw of keywords) {
    const hit = sections.find((s) => s.heading.toLowerCase().includes(kw));
    if (hit) return hit;
  }
  return undefined;
}

function extractStat(text, patterns) {
  for (const re of patterns) {
    const m = text.match(re);
    if (m) return m[1].trim();
  }
  return "";
}

function extractPhysicalStats(text) {
  return {
    weight: extractStat(text, [
      /weigh(?:s|ing|t)?[^.]{0,40}?(\d[\d,.]*\s*[–-]\s*\d[\d,.]*\s*(?:kg|g|lb|tons?))/i,
      /mass[^.]{0,30}?(\d[\d,.]*\s*[–-]\s*\d[\d,.]*\s*(?:kg|g|lb|tons?))/i,
      /weigh(?:s|ing|t)?[^.]{0,30}?(\d[\d,.]*\s*(?:kg|g|lb|tons?))/i,
    ]),
    length: extractStat(text, [
      /(?:body length|total length|length of|measuring)[^.]{0,30}?(\d[\d,.]*\s*[–-]\s*\d[\d,.]*\s*(?:m|cm|mm|ft|in))/i,
      /(?:wingspan|wing span)[^.]{0,20}?(\d[\d,.]*\s*[–-]\s*\d[\d,.]*\s*(?:m|cm|mm|ft|in))/i,
      /(?:long|length)[^.]{0,20}?(\d[\d,.]*\s*[–-]\s*\d[\d,.]*\s*(?:m|cm|mm|ft|in))/i,
    ]),
    height: extractStat(text, [
      /(?:shoulder height|height at the shoulder|standing[^.]{0,15}tall)[^.]{0,30}?(\d[\d,.]*\s*[–-]\s*\d[\d,.]*\s*(?:m|cm|mm|ft|in))/i,
      /(?:height)[^.]{0,20}?(\d[\d,.]*\s*[–-]\s*\d[\d,.]*\s*(?:m|cm|mm|ft|in))/i,
    ]),
    top_speed: extractStat(text, [
      /(?:speeds? of|top speed|reach[^.]{0,15}speeds?)[^.]{0,20}?(\d[\d,.]*\s*[–-]\s*\d[\d,.]*\s*(?:km\/h|mph|kph))/i,
      /(?:speeds? of|top speed|reach[^.]{0,15}speeds?)[^.]{0,20}?(\d[\d,.]*\s*(?:km\/h|mph|kph))/i,
    ]),
    lifespan: extractStat(text, [
      /(?:live[^.]{0,15}(?:for|up to)|lifespan[^.]{0,15}|life expectancy[^.]{0,15})(\d[\d,.]*\s*[–-]\s*\d[\d,.]*\s*(?:years?|months?|days?))/i,
      /(?:live[^.]{0,15}(?:for|up to)|lifespan[^.]{0,15})(\d[\d,.]*\s*(?:years?|months?|days?))/i,
    ]),
  };
}

function deriveDiet(text, type) {
  const t = text.toLowerCase();
  if (/carnivore|carnivorous|predator|preys on|feeds on.*animals/.test(t)) return "Carnivore";
  if (/herbivore|herbivorous|grazes|browses|feeds on.*plants|foliage/.test(t)) return "Herbivore";
  if (/omnivore|omnivorous|both plants and animals/.test(t)) return "Omnivore";
  if (/piscivore|feeds on fish|eats fish/.test(t)) return "Piscivore";
  if (/insectivore|feeds on insects|eats insects|ants and termites/.test(t)) return "Insectivore";
  if (/nectar|pollinator|pollinates/.test(t)) return "Nectarivore";
  if (type === "fish") return "Carnivore";
  if (type === "insect") return "Herbivore";
  if (type === "bird" || type === "reptile" || type === "amphibian") return "Carnivore";
  return "Omnivore";
}

function deriveConservationStatus(text) {
  const m = text.match(/\b(critically endangered|endangered|vulnerable|near threatened|least concern|extinct in the wild|extinct|conservation dependent)\b/i);
  return m ? m[1] : "";
}

function extractLocations(text) {
  const m = text.match(/(?:found|native|distributed|endemic|inhabits|ranges?)\s+(?:in|across|throughout|from)?\s*([A-Z][^.]*(?:Africa|Asia|Europe|America|Australia|India|China|Japan|Russia|Indonesia|Brazil|Argentina|Mexico|Canada|Ocean|Sea|Pacific|Atlantic|Antarctic|Arctic|Caribbean|Mediterranean|Sahara|Himalaya|Amazon|Andes)[^.]*?)(?:\.|;|$)/);
  return m ? m[1].trim().slice(0, 200) : "";
}

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

function buildPrompt(animalName, text) {
  return `You are a precise wildlife data extractor. Given the Wikipedia article text about an animal, extract structured facts. Only include values actually stated in the text — leave a field empty ("") if not mentioned. Use metric units (m, cm, kg, km/h, years).

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
- Do NOT invent values. Empty "" is better than a guess.

Animal name: ${animalName}

Wikipedia article text:
${(text || "").slice(0, 5000)}`;
}

function runWorker(prompt) {
  return new Promise((resolve) => {
    // detached: true + unref() so the worker can NEVER send signals that
    // kill the Next.js dev server (which shares the process session).
    const child = spawn("node", [WORKER], {
      stdio: ["pipe", "pipe", "pipe"],
      timeout: 35_000,
      detached: true,
    });
    child.unref();
    let stdout = "";
    child.stdout.on("data", (d) => { stdout += d.toString(); });
    child.stdin.write(prompt);
    child.stdin.end();
    child.on("error", () => resolve({}));
    child.on("close", () => {
      const trimmed = stdout.trim();
      try { resolve(JSON.parse(trimmed)); } catch {
        const m = trimmed.match(/\{[\s\S]*\}/);
        if (m) { try { resolve(JSON.parse(m[0])); } catch { resolve({}); } }
        else resolve({});
      }
    });
  });
}

async function fetchAndEnrich(req) {
  const { name, wikipediaTitle, type } = req;
  const title = wikipediaTitle || name;
  const slug = slugify(name);

  // 1. Fetch summary + sections in parallel
  const [summaryResult, sectionsResult] = await Promise.allSettled([
    getSummary(title),
    getSections(title),
  ]);
  const summary = summaryResult.status === "fulfilled" ? summaryResult.value : { extract: "", image: undefined, url: "" };
  const sections = sectionsResult.status === "fulfilled" ? sectionsResult.value : [];

  // 2. Fetch up to 3 key sections in parallel
  const picks = [];
  const seenKeys = new Set();
  for (const p of SECTION_PRIORITIES) {
    if (picks.length >= 3) break;
    if (seenKeys.has(p.key)) continue;
    const pick = pickSection(sections, p.keywords);
    if (pick) { picks.push({ key: p.key, index: pick.index }); seenKeys.add(p.key); }
  }
  const article = { overview: summary.extract };
  const sectionResults = await Promise.allSettled(picks.map((p) => getSectionText(title, p.index)));
  sectionResults.forEach((res, i) => {
    if (res.status === "fulfilled") article[picks[i].key] = res.value.slice(0, 3500);
  });

  // 3. Build the animal object with regex-extracted stats
  const blob = [summary.extract, article.description, article.habitat, article.behavior, article.conservation].filter(Boolean).join("\n\n");
  const animalType = type || "mammal";
  const animal = {
    id: `wiki:${slug}`,
    name,
    scientific_name: "",
    summary: summary.extract,
    description: summary.extract,
    image: summary.image,
    images: summary.image ? [summary.image] : [],
    wikipedia_url: summary.url,
    classification: {},
    animal_type: animalType,
    physical: extractPhysicalStats(blob),
    ecology: { diet: deriveDiet(blob, animalType), locations: extractLocations(blob), conservation_status: deriveConservationStatus(blob) },
    article,
    sources: ["Wikipedia"],
    last_updated: new Date().toISOString(),
  };
  // Try scientific name from summary
  const sciMatch = summary.extract.match(/\(([^)]+)\)/);
  if (sciMatch) {
    const twoWord = sciMatch[1].match(/([A-Z][a-z]+ [a-z-]+)/);
    if (twoWord) animal.scientific_name = twoWord[1];
  }

  // 4. Save to cache immediately (partial data available)
  const cacheFile = path.join(CACHE_DIR, `${slug}.json`);
  if (!existsSync(CACHE_DIR)) mkdirSync(CACHE_DIR, { recursive: true });
  writeFileSync(cacheFile, JSON.stringify(animal, null, 2));

  // 5. Spawn LLM worker for structured extraction
  try {
    const extracted = await runWorker(buildPrompt(name, blob));
    const enriched = mergeExtracted(animal, extracted);
    writeFileSync(cacheFile, JSON.stringify(enriched, null, 2));
    console.log(`[watcher] fetched+enriched ${name}`);
  } catch (err) {
    console.error(`[watcher] enrichment failed for ${name}:`, err?.message);
  }
}

async function processRequest(reqFile) {
  let req;
  try {
    req = JSON.parse(readFileSync(reqFile, "utf-8"));
  } catch {
    unlinkSync(reqFile);
    return;
  }
  try {
    await fetchAndEnrich(req);
  } catch (err) {
    console.error(`[watcher] fetch failed for ${req.name}:`, err?.message);
  } finally {
    try { unlinkSync(reqFile); } catch {}
  }
}

async function poll() {
  try {
    if (!existsSync(FETCH_QUEUE_DIR)) { mkdirSync(FETCH_QUEUE_DIR, { recursive: true }); return; }
    const files = readdirSync(FETCH_QUEUE_DIR).filter((f) => f.endsWith(".json")).sort();
    for (const f of files) {
      await processRequest(path.join(FETCH_QUEUE_DIR, f));
    }
  } catch (err) {
    console.error("[watcher] poll error:", err?.message);
  }
}

console.log("🧠 WildAtlas fetch+enrich watcher running. Polling", FETCH_QUEUE_DIR);
setInterval(poll, 3000);
poll();
