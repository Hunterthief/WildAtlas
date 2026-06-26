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
const REQUEST_TIMEOUT = 10_000;

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
  return {
    weight: extractStat(text, [
      /weigh(?:s|ing|t)?[^.]{0,40}?(\d[\d,.]*\s*[–-]\s*\d[\d,.]*\s*(?:kg|g|lb|tons?))/i,
      /weigh(?:s|ing|t)?[^.]{0,30}?(\d[\d,.]*\s*(?:kg|g|lb|tons?))/i,
    ]),
    length: extractStat(text, [
      /(?:body length|total length|length of|measuring)[^.]{0,30}?(\d[\d,.]*\s*[–-]\s*\d[\d,.]*\s*(?:m|cm|mm|ft|in))/i,
      /(?:wingspan|wing span)[^.]{0,20}?(\d[\d,.]*\s*[–-]\s*\d[\d,.]*\s*(?:m|cm|mm|ft|in))/i,
      /(?:long|length)[^.]{0,20}?(\d[\d,.]*\s*[–-]\s*\d[\d,.]*\s*(?:m|cm|mm|ft|in))/i,
    ]),
    height: extractStat(text, [
      /(?:shoulder height|height at the shoulder)[^.]{0,30}?(\d[\d,.]*\s*[–-]\s*\d[\d,.]*\s*(?:m|cm|mm|ft|in))/i,
    ]),
    top_speed: extractStat(text, [
      /(?:speeds? of|top speed|reach[^.]{0,15}speeds?)[^.]{0,20}?(\d[\d,.]*\s*[–-]\s*\d[\d,.]*\s*(?:km\/h|mph|kph))/i,
    ]),
    lifespan: extractStat(text, [
      /(?:live[^.]{0,15}(?:for|up to)|lifespan[^.]{0,15})(\d[\d,.]*\s*[–-]\s*\d[\d,.]*\s*(?:years?|months?|days?))/i,
    ]),
  };
}

function deriveDiet(text: string): string {
  const t = text.toLowerCase();
  if (/carnivore|carnivorous|predator|preys on|feeds on.*animals/.test(t)) return "Carnivore";
  if (/herbivore|herbivorous|grazes|browses|feeds on.*plants|foliage/.test(t)) return "Herbivore";
  if (/omnivore|omnivorous|both plants and animals/.test(t)) return "Omnivore";
  if (/piscivore|feeds on fish|eats fish/.test(t)) return "Piscivore";
  if (/insectivore|feeds on insects|eats insects|ants and termites/.test(t)) return "Insectivore";
  if (/nectar|pollinator|pollinates/.test(t)) return "Nectarivore";
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
  };
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

  const summary = summaryResult.status === "fulfilled" ? summaryResult.value : { extract: "", image: undefined, url: "" };
  const sections = sectionsResult.status === "fulfilled" ? sectionsResult.value : [];

  // Fetch up to 3 key sections in parallel
  const picks: { key: string; index: string }[] = [];
  const seenKeys = new Set<string>();
  for (const p of SECTION_PRIORITIES) {
    if (picks.length >= 3) break;
    if (seenKeys.has(p.key)) continue;
    const pick = pickSection(sections, p.keywords);
    if (pick) { picks.push({ key: p.key, index: pick.index }); seenKeys.add(p.key); }
  }

  const article: NonNullable<Animal["article"]> = { overview: summary.extract };
  const sectionResults = await Promise.allSettled(picks.map((p) => getSectionText(wikipediaTitle, p.index)));
  sectionResults.forEach((res, i) => {
    if (res.status === "fulfilled") article[picks[i].key as keyof typeof article] = res.value.slice(0, 3500);
  });

  // Build the animal object
  const blob = [summary.extract, article.description, article.habitat, article.behavior, article.conservation].filter(Boolean).join("\n\n");
  const animalType = type as any || "mammal";
  const animal: Animal = {
    id: `wiki:${name.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`,
    name,
    scientific_name: extractScientificName(summary.extract),
    summary: summary.extract,
    description: summary.extract,
    image: summary.image,
    images: summary.image ? [summary.image] : [],
    wikipedia_url: summary.url,
    classification: {},
    animal_type: animalType,
    physical: extractPhysicalStats(blob),
    ecology: {
      diet: deriveDiet(blob),
      conservation_status: deriveConservationStatus(blob),
    },
    article,
    sources: ["Wikipedia"],
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
