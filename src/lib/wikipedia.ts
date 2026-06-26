// ============================================
// WildAtlas - Animal data access (cache + queue)
//
// The Next.js API routes use this module to read cached animal data.
// ALL network fetching (Wikipedia) and LLM enrichment happen in a
// SEPARATE watcher process (src/lib/enrich-watcher.mjs) because the
// Turbopack dev server crashes when API handlers make outbound HTTPS
// requests.
//
// Flow:
//   1. Curated dataset → instant (13 animals)
//   2. Filesystem cache → instant (after first fetch)
//   3. Not cached → queue a fetch request, return null (client polls)
//   4. Watcher picks up the request, fetches Wikipedia + LLM, writes cache
// ============================================

import { promises as fs } from "fs";
import path from "path";
import type { Animal, AnimalType } from "./types";
import { ANIMALS } from "./animals";

const CACHE_DIR = path.join(process.cwd(), "data", "cache", "wikipedia");
const MEMORY_CACHE = new Map<string, Animal>();

function slugify(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function findCurated(name: string): Animal | undefined {
  const target = name.trim().toLowerCase();
  return ANIMALS.find((a) => a.name.toLowerCase() === target);
}

/**
 * Get an animal by name. Returns:
 *   - The curated animal (instant) if it's in the 13-species dataset
 *   - The cached animal (instant) if already fetched
 *   - null if not cached — and queues a background fetch for next time
 *
 * Also returns a `pending` flag when the animal has been queued but
 * isn't ready yet, so the client can show a loading state and poll.
 */
export async function getAnimalByName(
  name: string,
  opts: { wikipediaTitle?: string; type?: AnimalType } = {},
): Promise<{ animal: Animal | null; pending: boolean; source: string }> {
  // 1. Curated dataset (instant)
  const curated = findCurated(name);
  if (curated) return { animal: curated, pending: false, source: "curated" };

  const slug = slugify(name);

  // 2. In-memory cache
  if (MEMORY_CACHE.has(slug)) {
    return { animal: MEMORY_CACHE.get(slug)!, pending: false, source: "wikipedia" };
  }

  // 3. Filesystem cache
  try {
    const cachedPath = path.join(CACHE_DIR, `${slug}.json`);
    const cachedRaw = await fs.readFile(cachedPath, "utf-8");
    const cached = JSON.parse(cachedRaw) as Animal;
    MEMORY_CACHE.set(slug, cached);
    return { animal: cached, pending: false, source: "wikipedia" };
  } catch {
    // not cached — queue a fetch below
  }

  // 4. Queue a fetch request by writing a small JSON file for the watcher
  //    to pick up. This is just a file write — no HTTP, no subprocess, so
  //    it can't crash the Turbopack dev server.
  await queueFetch(name, slug, opts.wikipediaTitle, opts.type);

  // 5. Return pending — the client should poll in a few seconds
  return { animal: null, pending: true, source: "fetching" };
}

/** Write a small queue request file for the watcher to pick up. */
async function queueFetch(
  name: string,
  slug: string,
  wikipediaTitle?: string,
  type?: AnimalType,
) {
  try {
    const queueDir = path.join(process.cwd(), "data", "cache", "fetch-queue");
    await fs.mkdir(queueDir, { recursive: true });
    const reqFile = path.join(queueDir, `${slug}.json`);
    // Don't re-queue if already pending
    try {
      await fs.access(reqFile);
      return;
    } catch {
      // doesn't exist — write it
    }
    await fs.writeFile(
      reqFile,
      JSON.stringify({
        name,
        wikipediaTitle: wikipediaTitle ?? name,
        type: type ?? "mammal",
        queuedAt: new Date().toISOString(),
      }),
      "utf-8",
    );
  } catch {
    // non-fatal
  }
}

/** Live search of Wikipedia (uses the public search API — reliable, not rate-limited). */
export async function searchWikipedia(
  query: string,
  limit = 12,
): Promise<{ title: string; description: string; url: string }[]> {
  if (!query.trim()) return [];
  const url = `https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=${encodeURIComponent(
    query,
  )}&srnamespace=0&srlimit=${limit}&format=json`;
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 8_000);
    const res = await fetch(url, {
      headers: {
        "User-Agent":
          "WildAtlasBot/1.0 (https://example.org; educational animal encyclopedia project)",
        Accept: "application/json",
      },
      signal: controller.signal,
    });
    clearTimeout(timer);
    if (!res.ok) return [];
    const data = await res.json();
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

/** Clear the in-memory cache (forces re-read from filesystem). */
export function clearMemoryCache(): void {
  MEMORY_CACHE.clear();
}
