"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import type { Animal } from "@/lib/types";
import {
  fetchAnimalFromWikipedia,
  searchWikipediaClient,
  loadStaticCatalog,
} from "@/lib/wiki-client";

// ---------- Catalog (static JSON) ----------

interface CatalogEntry {
  id: string;
  name: string;
  scientific_name: string;
  image?: string;
  wikipediaTitle: string;
  type: "mammal" | "bird" | "reptile" | "fish" | "amphibian" | "insect";
  featured: boolean;
}

/** Load the static catalog from /animals-data.json (works on GitHub Pages). */
export function useAnimals(query?: string, type?: string) {
  return useQuery<{ count: number; animals: CatalogEntry[] }>({
    queryKey: ["catalog"],
    queryFn: () => loadStaticCatalog().then((animals) => ({ count: animals.length, animals })),
    staleTime: Infinity, // static data, never changes
  });
}

// ---------- Animal detail (static for featured, Wikipedia fetch for others) ----------

interface AnimalDetailResponse {
  animal: Animal;
  source: string;
  pending: boolean;
}

/** Full detail for one animal.
 *  - Featured: instant (from static JSON)
 *  - Non-featured: fetched from Wikipedia client-side (CORS), ~2-5s first time */
export function useAnimalDetail(
  name: string | null,
  opts: { wikipediaTitle?: string; type?: string; featured?: boolean } = {},
) {
  return useQuery<AnimalDetailResponse>({
    queryKey: ["animal", name, opts.wikipediaTitle ?? "", opts.type ?? "", opts.featured ?? false],
    queryFn: async () => {
      // Featured animals: fetch from static catalog (instant)
      if (opts.featured) {
        const catalog = await loadStaticCatalog();
        const animal = catalog.find((a) => a.name.toLowerCase() === name!.toLowerCase());
        if (animal) return { animal, source: "curated", pending: false };
      }
      // Non-featured: fetch from Wikipedia client-side
      const animal = await fetchAnimalFromWikipedia(name!, opts.wikipediaTitle ?? name!, opts.type);
      return { animal, source: "wikipedia", pending: false };
    },
    enabled: !!name,
    staleTime: 5 * 60 * 1000, // cache for 5 min
  });
}

// ---------- Compare ----------

interface CompareResponse {
  animals: Animal[];
  pending: string[];
  missing: string[];
}

/** Comparison records for a list of animals. Fetches each from Wikipedia or static catalog. */
export function useCompare(
  entries: { name: string; wikipediaTitle?: string; type?: string; featured?: boolean }[],
) {
  const names = entries.map((e) => e.name).filter(Boolean);
  const key = names.join(",");

  return useQuery<CompareResponse>({
    queryKey: ["compare", key],
    queryFn: async () => {
      const animals: Animal[] = [];
      const missing: string[] = [];
      const catalog = await loadStaticCatalog();

      for (const entry of entries) {
        try {
          if (entry.featured) {
            const animal = catalog.find((a) => a.name.toLowerCase() === entry.name.toLowerCase());
            if (animal) { animals.push(animal); continue; }
          }
          const animal = await fetchAnimalFromWikipedia(entry.name, entry.wikipediaTitle ?? entry.name, entry.type);
          animals.push(animal);
        } catch {
          missing.push(entry.name);
        }
      }
      return { animals, pending: [], missing };
    },
    enabled: names.length > 0,
    staleTime: 5 * 60 * 1000,
  });
}

// ---------- Live Wikipedia search ----------

export interface SearchResult {
  title: string;
  description: string;
  url: string;
}

/** Live Wikipedia search (CORS-enabled, works on GitHub Pages). */
export function useWikipediaSearch(query: string) {
  return useQuery<{ results: SearchResult[] }>({
    queryKey: ["wiki-search", query],
    queryFn: async () => ({ results: await searchWikipediaClient(query, 12) }),
    enabled: query.trim().length >= 2,
    staleTime: 60_000,
  });
}
