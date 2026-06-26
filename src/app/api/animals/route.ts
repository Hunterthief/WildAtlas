import { NextResponse } from "next/server";
import { ANIMALS, classifyAnimal } from "@/lib/animals";
import { CURATED_CATALOG } from "@/lib/curated-catalog";
import type { Animal, AnimalType } from "@/lib/types";

// GET /api/animals
// Returns the browsable catalog: the curated dataset (13 rich animals)
// PLUS the curated starter catalog (~95 well-known species). Each entry
// carries enough info for a card; full detail is fetched on-demand when
// a user opens an animal (see /api/animals/[name]).
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const query = searchParams.get("q")?.toLowerCase().trim() ?? "";
    const typeFilter = searchParams.get("type") as AnimalType | null;

    // Curated dataset → rich summaries
    const featured: (Animal & { type: AnimalType; featured: true })[] = ANIMALS.map(
      (a) => ({
        ...a,
        type: classifyAnimal(a),
        featured: true as const,
      }),
    );

    // Starter catalog → lightweight entries (skip ones already featured)
    const featuredNames = new Set(featured.map((a) => a.name.toLowerCase()));
    const featuredTitles = new Set(
      featured.map((a) => a.name.toLowerCase()),
    );

    type CatalogItem = {
      id: string;
      name: string;
      scientific_name: string;
      image?: string;
      wikipediaTitle: string;
      type: AnimalType;
      featured: false;
    };
    const catalog: CatalogItem[] = CURATED_CATALOG.filter(
      (c) =>
        !featuredNames.has(c.name.toLowerCase()) &&
        !featuredTitles.has(c.wikipediaTitle.toLowerCase()),
    ).map((c) => ({
      id: `cat:${c.wikipediaTitle}`,
      name: c.name,
      scientific_name: "",
      wikipediaTitle: c.wikipediaTitle,
      type: c.type,
      featured: false as const,
    }));

    // Combine
    let all = [
      ...featured.map((a) => ({
        id: a.id,
        name: a.name,
        scientific_name: a.scientific_name,
        image: a.image ?? a.images?.[0],
        wikipediaTitle: a.name,
        type: a.type,
        featured: true,
      })),
      ...catalog,
    ];

    // Filter by type
    if (typeFilter && ["mammal", "bird", "reptile", "fish", "amphibian", "insect"].includes(typeFilter)) {
      all = all.filter((a) => a.type === typeFilter);
    }

    // Filter by search query
    if (query) {
      all = all.filter(
        (a) =>
          a.name.toLowerCase().includes(query) ||
          a.scientific_name.toLowerCase().includes(query),
      );
    }

    return NextResponse.json({
      count: all.length,
      featuredCount: featured.length,
      animals: all,
    });
  } catch (error) {
    console.error("[/api/animals] failed:", error);
    return NextResponse.json(
      { error: "Failed to load catalog" },
      { status: 500 },
    );
  }
}
