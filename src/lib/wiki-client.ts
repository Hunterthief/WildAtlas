"use client";

// ============================================
// WildAtlas - Client-side Wikipedia fetcher
//
// Fetches animal data DIRECTLY from the Wikipedia REST API in the browser.
// Wikipedia APIs support CORS (Access-Control-Allow-Origin: *), so this
// works on any static host including GitHub Pages — no server needed.
//
// Flow:
//   1. Featured animals: data is in the static animals-data.json (instant)
//   2. Non-featured: fetch summary + sections from Wikipedia client-side
//   3. Results are cached in sessionStorage for the session
// ============================================

import type { Animal } from "@/lib/types";
import { classifyAnimal } from "@/lib/animals";

const SESSION_CACHE = new Map<string, Animal>();
const REQUEST_TIMEOUT = 15_000; // 15s — SPARQL can be slow

async function fetchJsonWithTimeout(url: string): Promise<any> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);
  try {
    const res = await fetch(url, {
      headers: { Accept: "application/json" },
      signal: controller.signal,
    });
    if (!res.ok) throw new Error(`Wikipedia API ${res.status}`);
    return await res.json();
  } finally {
    clearTimeout(timer);
  }
}

// ---------- wikitext → plain text ----------
function wikitextToPlain(wt: string): string {
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

// ---------- section selection ----------
const SECTION_PRIORITIES = [
  { key: "behavior" as const, keywords: ["behaviour and ecology", "behavior and ecology", "ecology and behaviour", "behavior", "behaviour", "ecology", "diet", "diet and feeding", "feeding"] },
  { key: "habitat" as const, keywords: ["distribution and habitat", "habitat", "distribution", "range", "geographic range"] },
  { key: "conservation" as const, keywords: ["conservation", "conservation status", "status", "threats"] },
  { key: "description" as const, keywords: ["description", "characteristics", "appearance", "physical characteristics"] },
];

function pickSection(sections: { heading: string; index: string }[], keywords: string[]) {
  for (const kw of keywords) {
    const hit = sections.find((s) => s.heading.toLowerCase().includes(kw));
    if (hit) return hit;
  }
  return undefined;
}

// ---------- stat extraction (regex) ----------
function extractStat(text: string, patterns: RegExp[]): string {
  for (const re of patterns) {
    const m = text.match(re);
    if (m) return m[1].trim();
  }
  return "";
}

function extractPhysicalStats(text: string) {
  // Comprehensive regex patterns for extracting physical measurements from
  // Wikipedia article text. Handles ranges, various units, and common
  // phrasings. Unit-aware: normalizes tonnes→kg, etc.
  return {
    weight: extractWeight(text),
    length: extractLength(text),
    height: extractHeight(text),
    top_speed: extractSpeed(text),
    lifespan: extractLifespan(text),
  };
}

/** Extract weight with unit normalization. Handles kg, g, tonnes(t), lb, pounds.
 *  Requires weight context keywords (weigh, mass, weight) before the number
 *  to avoid false positives from unrelated text. */
function extractWeight(text: string): string {
  // Range separators: –, -, "to", "and"
  const range = /(\d[\d,.]*\s*(?:[–\-]|to|and)\s*\d[\d,.]*)/;
  const units = /(kg|kgs|g|grams?|t|tonnes?|tons?|lb|lbs|pounds?)/i;

  const patterns: RegExp[] = [
    // Range with weight context: "weighing 2,700–4,000 kg", "mass of 4–5 t"
    new RegExp(`(?:weigh(?:s|ing)?|mass of|weight of|weighs? up to|average[^.]{0,15}weight)[^.]{0,25}?${range.source}\\s*${units.source}`, "i"),
    // Range directly followed by unit: "21 and 65 kg", "110–170 tons"
    new RegExp(`${range.source}\\s*${units.source}(?:\\s*(?:in weight|in mass))?`, "i"),
    // Single value with weight context BEFORE: "weighing 190 kg", "mass of 4 t"
    new RegExp(`(?:weigh(?:s|ing)?|mass of|weight of|weighs? up to|average[^.]{0,15}weight)[^.]{0,15}?(\\d[\\d,.]+)\\s*${units.source}`, "i"),
    // "X kg/t/lb" after explicit weight mention in same sentence
    new RegExp(`(?:weigh[^.]{0,30}?)(\\d[\\d,.]+)\\s*${units.source}`, "i"),
    // "average Xt" or "Xt in weight" — unit comes right after number, weight context nearby
    new RegExp(`(?:average|males?|females?|adults?)\\s+(\\d[\\d,.]+)\\s*(t|tonnes?|tons?|kg|kgs|lb|lbs|pounds?)(?:\\s+in weight)?`, "i"),
    // "Xt in weight" — number+unit followed by "in weight"
    new RegExp(`(\\d[\\d,.]+)\\s*(t|tonnes?|tons?|kg|kgs|lb|lbs|pounds?)\\s+in weight`, "i"),
  ];

  for (const re of patterns) {
    const m = text.match(re);
    if (m) {
      const value = m[1].trim();
      const unit = m[2].toLowerCase().trim();
      const result = normalizeWeight(value, unit);
      if (result) return result; // only return non-empty results
      // If normalizeWeight rejected this match (e.g. year-like), try next pattern
    }
  }
  return "";
}

/** Normalize weight to kg. Handles ranges (–, -, "and", "to") and various units.
 *  Rejects year-like values (1900-2099) to avoid false positives from dates. */
function normalizeWeight(value: string, unit: string): string {
  const unitLower = unit.toLowerCase();
  // Determine conversion factor
  let factor = 1; // default kg
  let displayUnit = "kg";
  if (unitLower === "t" || unitLower.startsWith("tonne")) {
    factor = 1000; displayUnit = "kg";
  } else if (unitLower.startsWith("ton") && !unitLower.startsWith("tonne")) {
    factor = 907.185; displayUnit = "kg";
  } else if (unitLower === "lb" || unitLower === "lbs" || unitLower.startsWith("pound")) {
    factor = 0.453592; displayUnit = "kg";
  } else if (unitLower === "g" || unitLower.startsWith("gram")) {
    factor = 0.001; displayUnit = "kg";
  }

  // Reject year-like values (4-digit numbers 1800-2099 that look like years)
  const isYearLike = (n: number) => n >= 1800 && n <= 2099 && Number.isInteger(n);

  // Handle ranges: "2,700–4,000", "21 and 65", "2.7 to 4.0"
  if (/[–\-]|\bto\b|\band\b/.test(value)) {
    const parts = value.split(/[–\-]|\bto\b|\band\b/).map(p => p.trim().replace(/,/g, ""));
    if (parts.length === 2) {
      const lo = parseFloat(parts[0]);
      const hi = parseFloat(parts[1]);
      if (!isNaN(lo) && !isNaN(hi)) {
        // Reject if either value looks like a year
        if (isYearLike(lo) || isYearLike(hi)) return "";
        const loKg = lo * factor;
        const hiKg = hi * factor;
        if (factor === 1000) {
          return `${lo}–${hi} tonnes`;
        }
        return `${Math.round(loKg)}–${Math.round(hiKg)} ${displayUnit}`;
      }
    }
  }

  // Single value
  const num = parseFloat(value.replace(/,/g, ""));
  if (!isNaN(num)) {
    // Reject year-like single values for tonne unit (most likely a false positive)
    if (isYearLike(num) && (factor === 1000 || factor === 907.185)) return "";
    const kg = num * factor;
    if (factor === 1000) return `${num} tonnes`;
    return `${Math.round(kg)} ${displayUnit}`;
  }
  return `${value} ${unit}`;
}

/** Extract length/wingspan with unit normalization. */
function extractLength(text: string): string {
  const patterns: RegExp[] = [
    // Explicit length: "body length of 2.5–3.3 m", "total length 70–102 cm"
    /(?:body length|total length|length of|measuring|long)[^.]{0,30}?(\d[\d,.]*\s*[–\-]\s*\d[\d,.]*)\s*(m|cm|mm|ft|feet|in|inches)/i,
    /(?:body length|total length|length of|measuring|long)[^.]{0,20}?(\d[\d,.]+)\s*(m|cm|mm|ft|feet|in|inches)/i,
    // Wingspan for birds
    /(?:wingspan|wing span)[^.]{0,20}?(\d[\d,.]*\s*[–\-]\s*\d[\d,.]*)\s*(m|cm|mm|ft|feet|in|inches)/i,
    /(?:wingspan|wing span)[^.]{0,15}?(\d[\d,.]+)\s*(m|cm|mm|ft|feet|in|inches)/i,
    // Generic "X m long" / "X cm in length"
    /(\d[\d,.]*\s*[–\-]\s*\d[\d,.]*)\s*(m|cm|mm)\s*(?:long|in length|in total length)/i,
    /(\d[\d,.]+)\s*(m|cm|mm)\s*(?:long|in length|in total length)/i,
  ];

  for (const re of patterns) {
    const m = text.match(re);
    if (m) {
      return `${m[1].trim()} ${m[2].toLowerCase()}`;
    }
  }
  return "";
}

/** Extract height (shoulder height for quadrupeds). */
function extractHeight(text: string): string {
  const patterns: RegExp[] = [
    /(?:shoulder height|height at the shoulder|at the shoulder)[^.]{0,30}?(\d[\d,.]*\s*[–\-]\s*\d[\d,.]*)\s*(m|cm|mm|ft|feet|in|inches)/i,
    /(?:shoulder height|height at the shoulder|at the shoulder)[^.]{0,20}?(\d[\d,.]+)\s*(m|cm|mm|ft|feet|in|inches)/i,
    /(?:stands?[^.]{0,15}(?:tall|high))[^.]{0,15}?(\d[\d,.]*\s*[–\-]\s*\d[\d,.]*)\s*(m|cm|mm|ft|feet|in|inches)/i,
    /(?:stands?[^.]{0,15}(?:tall|high))[^.]{0,15}?(\d[\d,.]+)\s*(m|cm|mm|ft|feet|in|inches)/i,
    /(?:height[^.]{0,10}?)(\d[\d,.]*\s*[–\-]\s*\d[\d,.]*)\s*(m|cm|mm|ft|feet|in|inches)/i,
    /(?:height[^.]{0,10}?)(\d[\d,.]+)\s*(m|cm|mm|ft|feet|in|inches)/i,
  ];

  for (const re of patterns) {
    const m = text.match(re);
    if (m) {
      return `${m[1].trim()} ${m[2].toLowerCase()}`;
    }
  }
  return "";
}

/** Extract top speed. */
function extractSpeed(text: string): string {
  const patterns: RegExp[] = [
    /(?:speeds? of|top speed|reach[^.]{0,15}speeds?|can run|running at)[^.]{0,20}?(\d[\d,.]*\s*[–\-]\s*\d[\d,.]*)\s*(km\/h|kmh|mph|kph|m\/s)/i,
    /(?:speeds? of|top speed|reach[^.]{0,15}speeds?|can run|running at)[^.]{0,15}?(\d[\d,.]+)\s*(km\/h|kmh|mph|kph|m\/s)/i,
  ];

  for (const re of patterns) {
    const m = text.match(re);
    if (m) {
      return `${m[1].trim()} ${m[2].toLowerCase()}`;
    }
  }
  return "";
}

/** Extract lifespan. Requires explicit lifespan context to avoid false positives. */
function extractLifespan(text: string): string {
  const patterns: RegExp[] = [
    // "lifespan of X years", "life expectancy of X years"
    /(?:lifespan|life expectancy)[^.]{0,10}?(\d[\d,.]*\s*(?:[–\-]|to)\s*\d[\d,.]*)\s*(years?|yrs?)/i,
    /(?:lifespan|life expectancy)[^.]{0,10}?(\d[\d,.]+)\s*(years?|yrs?)/i,
    // "live for X years", "live up to X years", "living X years"
    /(?:live[sd]?[^.]{0,10}(?:for|up to)|living[^.]{0,10})\s*(\d[\d,.]*\s*(?:[–\-]|to)\s*\d[\d,.]*)\s*(years?|yrs?)/i,
    /(?:live[sd]?[^.]{0,10}(?:for|up to)|living[^.]{0,10})\s*(\d[\d,.]+)\s*(years?|yrs?)/i,
    // "X years in the wild", "X years in captivity" (but NOT "X years of age")
    /(\d[\d,.]*\s*(?:[–\-]|to)\s*\d[\d,.]*)\s*(years?|yrs?)\s+(?:in the wild|in captivity|old)/i,
    /(\d[\d,.]+)\s*(years?|yrs?)\s+(?:in the wild|in captivity|old)/i,
  ];

  for (const re of patterns) {
    const m = text.match(re);
    if (m) {
      return `${m[1].trim()} ${m[2].toLowerCase()}`;
    }
  }
  return "";
}

function deriveDiet(text: string, type?: string): string {
  const t = text.toLowerCase();
  // Check explicit diet terms first (most reliable)
  if (/\bcarnivore\b|\bcarnivorous\b/.test(t)) return "Carnivore";
  if (/\bherbivore\b|\bherbivorous\b/.test(t)) return "Herbivore";
  if (/\bomnivore\b|\bomnivorous\b/.test(t)) return "Omnivore";
  if (/\bpiscivore\b|\bpiscivorous\b/.test(t)) return "Piscivore";
  if (/\binsectivore\b|\binsectivorous\b/.test(t)) return "Insectivore";
  if (/\bnectarivore\b|\bnectarivorous\b|\bnectar\b.*\bfeed/.test(t)) return "Nectarivore";
  if (/\bscavenger\b/.test(t)) return "Scavenger";
  // Then check behavioral descriptions
  if (/apex predator|predator|preys on|hunts.*prey|feeds on.*animals|hunting/.test(t)) return "Carnivore";
  if (/grazes|browses|feeds on.*plants|foliage|grazing|browsing/.test(t)) return "Herbivore";
  if (/feeds on fish|eats fish|fish.*diet/.test(t)) return "Piscivore";
  if (/feeds on insects|eats insects|ants and termites|insect.*diet/.test(t)) return "Insectivore";
  if (/pollinator|pollinates/.test(t)) return "Nectarivore";
  // Type-based fallback
  if (type === "fish") return "Carnivore";
  if (type === "insect") return "Herbivore";
  if (type === "bird" || type === "reptile" || type === "amphibian") return "Carnivore";
  return "Omnivore";
}

function deriveConservationStatus(text: string): string {
  const m = text.match(/\b(critically endangered|endangered|vulnerable|near threatened|least concern|extinct in the wild|extinct|conservation dependent)\b/i);
  return m ? m[1] : "";
}

function extractScientificName(summary: string): string {
  // "The tiger (Panthera tigris) is a..." → "Panthera tigris"
  const m = summary.match(/\(([A-Z][a-z]+ [a-z]+(?:\s+[a-z]+)?)\)/);
  return m ? m[1] : "";
}

// ---------- main fetch function ----------
async function getSummary(title: string) {
  const url = `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(title)}`;
  const data = await fetchJsonWithTimeout(url);
  return {
    extract: data.extract ?? "",
    image: data.thumbnail?.source ?? data.originalimage?.source,
    url: data.content_urls?.desktop?.page ?? "",
    wikibaseItem: data.wikibase_item ?? "",
    description: data.description ?? "",
  };
}

// ---------- Wikidata taxonomy fetch (client-side, CORS-enabled) ----------
// Optimized: collects the full parent-taxon chain in ONE request using
// SPARQL (which returns all ancestors at once), instead of 12+ sequential
// API calls. Falls back to the sequential approach if SPARQL fails.
async function getWikidataTaxonomy(qid: string): Promise<{
  scientific_name: string;
  classification: Record<string, string>;
  conservation_status: string;
  physical?: { weight?: string; length?: string; height?: string };
}> {
  // Try SPARQL first — it gets the ENTIRE taxonomy chain in one request
  try {
    const sparqlResult = await getTaxonomyViaSparql(qid);
    if (sparqlResult) return sparqlResult;
  } catch {
    // fall through to sequential approach
  }

  // Fallback: sequential wbgetentities calls (slower but reliable)
  const seqResult = await getTaxonomySequential(qid);
  return { ...seqResult, physical: {} };
}

/** Use Wikidata SPARQL to get the full taxonomy chain in ONE request.
 *  This is much faster than walking the parent-taxon chain sequentially. */
async function getTaxonomyViaSparql(qid: string): Promise<{
  scientific_name: string;
  classification: Record<string, string>;
  conservation_status: string;
  physical: { weight?: string; length?: string; height?: string };
} | null> {
  // Single SPARQL query: taxonomy chain + IUCN status + physical measurements
  // Uses psv: (property statement value) to get the actual numeric value + unit
  const sparql = `
SELECT ?item ?itemLabel ?rank ?rankLabel ?taxonName ?iucnLabel
       ?mass ?massUnitLabel ?length ?lengthUnitLabel ?height ?heightUnitLabel
WHERE {
  {
    SELECT ?item ?rank ?taxonName WHERE {
      wd:${qid} wdt:P171* ?item .
      ?item wdt:P105 ?rank .
      OPTIONAL { ?item wdt:P225 ?taxonName }
    }
  }
  OPTIONAL { ?item rdfs:label ?itemLabel FILTER(lang(?itemLabel) = "en") }
  OPTIONAL { ?rank rdfs:label ?rankLabel FILTER(lang(?rankLabel) = "en") }
  OPTIONAL { wd:${qid} wdt:P141 ?iucn . ?iucn rdfs:label ?iucnLabel FILTER(lang(?iucnLabel) = "en") }
  OPTIONAL { wd:${qid} p:P2067 ?massS . ?massS psv:P2067 ?massV . ?massV wikibase:quantityAmount ?mass . ?massV wikibase:quantityUnit ?massUnit . ?massUnit rdfs:label ?massUnitLabel FILTER(lang(?massUnitLabel) = "en") }
  OPTIONAL { wd:${qid} p:P2043 ?lengthS . ?lengthS psv:P2043 ?lengthV . ?lengthV wikibase:quantityAmount ?length . ?lengthV wikibase:quantityUnit ?lengthUnit . ?lengthUnit rdfs:label ?lengthUnitLabel FILTER(lang(?lengthUnitLabel) = "en") }
  OPTIONAL { wd:${qid} p:P2048 ?heightS . ?heightS psv:P2048 ?heightV . ?heightV wikibase:quantityAmount ?height . ?heightV wikibase:quantityUnit ?heightUnit . ?heightUnit rdfs:label ?heightUnitLabel FILTER(lang(?heightUnitLabel) = "en") }
} LIMIT 50`;

  const url = `https://query.wikidata.org/sparql?query=${encodeURIComponent(sparql)}&format=json&origin=*`;
  const data = await fetchJsonWithTimeout(url);

  const results = data?.results?.bindings ?? [];
  if (results.length === 0) return null;

  const rankMap: Record<string, string> = {
    kingdom: "kingdom", phylum: "phylum", class: "class",
    order: "order", family: "family", genus: "genus",
    species: "species", subspecies: "species",
    subgenus: "genus", subfamily: "family", suborder: "order",
    subclass: "class", subphylum: "phylum",
    infraclass: "class", superfamily: "family",
    infraorder: "order", tribe: "family",
    subtribe: "family", superorder: "order",
  };

  const classification: Record<string, string> = {};
  let sciName = "";
  let conservation = "";
  const physical: { weight?: string; length?: string; height?: string } = {};

  for (const row of results) {
    const rankName = (row.rankLabel?.value ?? "").toLowerCase();
    const key = rankMap[rankName];
    if (key && !classification[key]) {
      classification[key] = row.taxonName?.value || row.itemLabel?.value || "";
    }
    if (row.item?.value?.endsWith(`/${qid}`) && row.taxonName?.value) {
      sciName = row.taxonName.value;
    }
    if (row.iucnLabel?.value) {
      const iucnLabel = row.iucnLabel.value.toLowerCase();
      const iucnMap: Record<string, string> = {
        "least concern": "Least Concern",
        "near threatened": "Near Threatened",
        "vulnerable": "Vulnerable",
        "endangered": "Endangered",
        "critically endangered": "Critically Endangered",
        "extinct in the wild": "Extinct in the Wild",
        "extinct": "Extinct",
        "data deficient": "Data Deficient",
      };
      for (const [k, v] of Object.entries(iucnMap)) {
        if (iucnLabel.includes(k)) { conservation = v; break; }
      }
    }

    // Physical measurements from Wikidata quantities
    // P2067 = mass, P2043 = length, P2048 = height
    // The psv: approach gives us the actual value + unit label
    if (row.mass?.value && !physical.weight) {
      const massVal = Number(row.mass.value);
      const unitLabel = (row.massUnitLabel?.value ?? "").toLowerCase();
      // Convert to kg based on unit
      if (unitLabel.includes("kilogram") || unitLabel.includes("kg")) {
        physical.weight = `${Math.round(massVal)} kg`;
      } else if (unitLabel.includes("gram") && !unitLabel.includes("kilo")) {
        physical.weight = `${Math.round(massVal / 1000)} kg`;
      } else if (unitLabel.includes("ton")) {
        physical.weight = `${Math.round(massVal * 1000)} kg`;
      } else if (unitLabel.includes("pound") || unitLabel.includes("lb")) {
        physical.weight = `${Math.round(massVal * 0.453592)} kg`;
      } else {
        physical.weight = `${Math.round(massVal)} ${unitLabel || "kg"}`;
      }
    }
    if (row.length?.value && !physical.length) {
      const lenVal = Number(row.length.value);
      const unitLabel = (row.lengthUnitLabel?.value ?? "").toLowerCase();
      if (unitLabel.includes("metre") || unitLabel.includes("meter") || unitLabel === "m") {
        physical.length = `${lenVal} m`;
      } else if (unitLabel.includes("centimetre") || unitLabel.includes("centimeter") || unitLabel === "cm") {
        physical.length = `${lenVal} cm`;
      } else if (unitLabel.includes("millimetre") || unitLabel.includes("millimeter") || unitLabel === "mm") {
        physical.length = `${lenVal} mm`;
      } else if (unitLabel.includes("foot") || unitLabel.includes("feet") || unitLabel === "ft") {
        physical.length = `${lenVal} ft`;
      } else {
        physical.length = `${lenVal} ${unitLabel || "m"}`;
      }
    }
    if (row.height?.value && !physical.height) {
      const hVal = Number(row.height.value);
      const unitLabel = (row.heightUnitLabel?.value ?? "").toLowerCase();
      if (unitLabel.includes("metre") || unitLabel.includes("meter") || unitLabel === "m") {
        physical.height = `${hVal} m`;
      } else if (unitLabel.includes("centimetre") || unitLabel.includes("centimeter") || unitLabel === "cm") {
        physical.height = `${hVal} cm`;
      } else {
        physical.height = `${hVal} ${unitLabel || "m"}`;
      }
    }
  }

  return { scientific_name: sciName, classification, conservation_status: conservation, physical };
}

/** Sequential fallback: walk the parent taxon chain one API call at a time. */
async function getTaxonomySequential(qid: string): Promise<{
  scientific_name: string;
  classification: Record<string, string>;
  conservation_status: string;
}> {
  const classification: Record<string, string> = {};
  let sciName = "";
  let conservation = "";

  const rankMap: Record<string, string> = {
    kingdom: "kingdom", phylum: "phylum", class: "class",
    order: "order", family: "family", genus: "genus",
    species: "species", subspecies: "species",
    subgenus: "genus", subfamily: "family", suborder: "order",
    subclass: "class", subphylum: "phylum",
    infraclass: "class", superfamily: "family",
    infraorder: "order", tribe: "family",
    subtribe: "family", superorder: "order",
  };

  // Batch-fetch rank labels to avoid N+1 queries
  const rankLabelCache = new Map<string, string>();

  let currentQid = qid;
  const visited = new Set<string>();

  for (let i = 0; i < 12 && currentQid && !visited.has(currentQid); i++) {
    visited.add(currentQid);
    try {
      const url = `https://www.wikidata.org/w/api.php?action=wbgetentities&ids=${currentQid}&props=claims|labels&languages=en&format=json&origin=*`;
      const data = await fetchJsonWithTimeout(url);
      const entity = data?.entities?.[currentQid];
      if (!entity) break;
      const claims = entity.claims ?? {};
      const label = entity.labels?.en?.value ?? "";

      if (currentQid === qid && claims.P225) {
        sciName = claims.P225[0]?.mainsnak?.datavalue?.value ?? "";
      }

      if (claims.P105) {
        const rankId = claims.P105[0]?.mainsnak?.datavalue?.value?.id;
        if (rankId) {
          let rankName = rankLabelCache.get(rankId);
          if (!rankName) {
            rankName = (await getWikidataLabel(rankId)).toLowerCase();
            rankLabelCache.set(rankId, rankName);
          }
          const key = rankMap[rankName];
          if (key && !classification[key]) {
            classification[key] = claims.P225?.[0]?.mainsnak?.datavalue?.value ?? label;
          }
        }
      }

      if (currentQid === qid && claims.P141) {
        const iucnId = claims.P141[0]?.mainsnak?.datavalue?.value?.id;
        if (iucnId) {
          const iucnLabel = (await getWikidataLabel(iucnId)).toLowerCase();
          const iucnMap: Record<string, string> = {
            "least concern": "Least Concern",
            "near threatened": "Near Threatened",
            "vulnerable": "Vulnerable",
            "endangered": "Endangered",
            "critically endangered": "Critically Endangered",
            "extinct in the wild": "Extinct in the Wild",
            "extinct": "Extinct",
            "data deficient": "Data Deficient",
          };
          for (const [k, v] of Object.entries(iucnMap)) {
            if (iucnLabel.includes(k)) { conservation = v; break; }
          }
        }
      }

      if (claims.P171) {
        currentQid = claims.P171[0]?.mainsnak?.datavalue?.value?.id ?? "";
      } else {
        break;
      }
    } catch {
      break;
    }
  }

  return { scientific_name: sciName, classification, conservation_status: conservation };
}

async function getWikidataLabel(qid: string): Promise<string> {
  try {
    const url = `https://www.wikidata.org/w/api.php?action=wbgetentities&ids=${qid}&props=labels&languages=en&format=json&origin=*`;
    const data = await fetchJsonWithTimeout(url);
    return data?.entities?.[qid]?.labels?.en?.value ?? "";
  } catch {
    return "";
  }
}

async function getSections(title: string) {
  const url = `https://en.wikipedia.org/w/api.php?action=parse&page=${encodeURIComponent(title)}&prop=sections&redirects=1&format=json&origin=*`;
  const data = await fetchJsonWithTimeout(url);
  return (data?.parse?.sections ?? []).map((s: any) => ({ heading: s.line, index: String(s.index) }));
}

async function getSectionText(title: string, index: string) {
  const url = `https://en.wikipedia.org/w/api.php?action=parse&page=${encodeURIComponent(title)}&section=${index}&prop=wikitext&redirects=1&format=json&origin=*`;
  const data = await fetchJsonWithTimeout(url);
  return wikitextToPlain(data?.parse?.wikitext?.["*"] ?? "");
}

/** Fetch a full animal record from Wikipedia (client-side, CORS-enabled). */
export async function fetchAnimalFromWikipedia(
  name: string,
  wikipediaTitle: string,
  type?: string,
): Promise<Animal> {
  // Check session cache
  const cacheKey = wikipediaTitle.toLowerCase();
  if (SESSION_CACHE.has(cacheKey)) return SESSION_CACHE.get(cacheKey)!;

  // Fetch summary + section list in parallel
  const [summaryResult, sectionsResult] = await Promise.allSettled([
    getSummary(wikipediaTitle),
    getSections(wikipediaTitle),
  ]);

  const summary = summaryResult.status === "fulfilled"
    ? summaryResult.value
    : { extract: "", image: undefined, url: "", wikibaseItem: "", description: "" };
  const sections = sectionsResult.status === "fulfilled" ? sectionsResult.value : [];

  // Fetch up to 3 key sections + Wikidata taxonomy in parallel
  const picks: { key: string; index: string }[] = [];
  const seenKeys = new Set<string>();
  for (const p of SECTION_PRIORITIES) {
    if (picks.length >= 3) break;
    if (seenKeys.has(p.key)) continue;
    const pick = pickSection(sections, p.keywords);
    if (pick) { picks.push({ key: p.key, index: pick.index }); seenKeys.add(p.key); }
  }

  const article: NonNullable<Animal["article"]> = { overview: summary.extract };

  // Fetch article sections AND Wikidata taxonomy in parallel
  const [sectionResults, taxonomyResult] = await Promise.allSettled([
    Promise.allSettled(picks.map((p) => getSectionText(wikipediaTitle, p.index))),
    summary.wikibaseItem ? getWikidataTaxonomy(summary.wikibaseItem) : Promise.resolve(null),
  ]);

  if (sectionResults.status === "fulfilled") {
    sectionResults.value.forEach((res, i) => {
      if (res.status === "fulfilled") article[picks[i].key as keyof typeof article] = res.value.slice(0, 3500);
    });
  }

  const taxonomy = taxonomyResult.status === "fulfilled" ? taxonomyResult.value : null;

  // Build the animal object — merge regex + Wikidata data
  const blob = [summary.extract, article.description, article.habitat, article.behavior, article.conservation].filter(Boolean).join("\n\n");
  const animalType = type as any || "mammal";

  // Use Wikidata scientific name if available, else regex extraction
  const sciName = taxonomy?.scientific_name || extractScientificName(summary.extract);

  // Merge classification from Wikidata
  const classification = taxonomy?.classification ?? {};

  // Merge conservation status from Wikidata + regex
  const conservationStatus = taxonomy?.conservation_status || deriveConservationStatus(blob);

  // Merge physical stats: text-extracted values take PRIORITY over Wikidata
  // because Wikidata can have incorrect/outlier values (e.g. Asian elephant
  // mass = 95 kg, which is a birth weight, not adult weight). The Wikipedia
  // article text usually has the correct adult weight in a range.
  // We only fall back to Wikidata if the text extraction found nothing.
  const regexStats = extractPhysicalStats(blob);
  const wikiStats = taxonomy?.physical ?? {};
  const physical = {
    weight: regexStats.weight || wikiStats.weight || "",
    length: regexStats.length || wikiStats.length || "",
    height: regexStats.height || wikiStats.height || "",
    top_speed: regexStats.top_speed || "",
    lifespan: regexStats.lifespan || "",
  };

  const animal: Animal = {
    id: `wiki:${name.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`,
    name,
    scientific_name: sciName,
    summary: summary.extract,
    description: summary.extract,
    image: summary.image,
    images: summary.image ? [summary.image] : [],
    wikipedia_url: summary.url,
    classification,
    animal_type: animalType,
    physical,
    ecology: {
      diet: deriveDiet(blob, animalType),
      conservation_status: conservationStatus,
    },
    article,
    sources: ["Wikipedia", "Wikidata"],
    last_updated: new Date().toISOString(),
  };

  SESSION_CACHE.set(cacheKey, animal);

  return animal;
}

/** Live Wikipedia search (CORS-enabled). */
export async function searchWikipediaClient(
  query: string,
  limit = 12,
): Promise<{ title: string; description: string; url: string }[]> {
  if (!query.trim()) return [];
  const url = `https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=${encodeURIComponent(query)}&srnamespace=0&srlimit=${limit}&format=json&origin=*`;
  try {
    const data = await fetchJsonWithTimeout(url);
    const results = data?.query?.search ?? [];
    return results.map((r: any) => ({
      title: r.title,
      description: (r.snippet ?? "").replace(/<[^>]+>/g, ""),
      url: `https://en.wikipedia.org/wiki/${encodeURIComponent(r.title.replace(/ /g, "_"))}`,
    }));
  } catch {
    return [];
  }
}

/** Load the static catalog JSON.
 *  Uses a relative path so it works both in dev (/) and on GitHub Pages
 *  (where the site is served from /WildAtlas/). */
export async function loadStaticCatalog(): Promise<Animal[]> {
  // Determine the base path from the current URL.
  // In dev: basePath is "" → fetch "/animals-data.json"
  // On GitHub Pages: the site is at /WildAtlas/ → fetch "/WildAtlas/animals-data.json"
  // Using a relative path "animals-data.json" works for both since the
  // index.html is at the root of the site.
  const res = await fetch("animals-data.json");
  if (!res.ok) throw new Error("Failed to load catalog");
  const data = await res.json();
  return data.animals as Animal[];
}
