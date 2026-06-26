import { NextResponse } from "next/server";
import { ANIMALS, classifyAnimal, findAnimalByName } from "@/lib/animals";
import { getAnimalByName } from "@/lib/wikipedia";

// GET /api/animals/[name]?wikipediaTitle=...&type=...
// Returns the full detail record for a single animal.
//   - Curated dataset: instant
//   - Filesystem-cached Wikipedia fetch: instant
//   - Not yet cached: returns 202 with { pending: true } so the client
//     can show a loading state and poll. The watcher process fetches
//     Wikipedia + enriches with the LLM, writing to the cache.
export async function GET(
  request: Request,
  { params }: { params: Promise<{ name: string }> },
) {
  try {
    const { name } = await params;
    const decoded = decodeURIComponent(name);
    const { searchParams } = new URL(request.url);
    const wikipediaTitle = searchParams.get("wikipediaTitle") ?? undefined;
    const typeParam = searchParams.get("type") as
      | "mammal"
      | "bird"
      | "reptile"
      | "fish"
      | "amphibian"
      | "insect"
      | null;

    // Curated dataset first (fast path, no queue)
    const curated = findAnimalByName(decoded);
    if (curated) {
      return NextResponse.json({
        animal: { ...curated, type: classifyAnimal(curated) },
        source: "curated",
        pending: false,
      });
    }

    // On-demand (cached or queue a fetch)
    const result = await getAnimalByName(decoded, {
      wikipediaTitle,
      type: typeParam ?? undefined,
    });

    if (result.animal) {
      return NextResponse.json({
        animal: result.animal,
        source: result.source,
        pending: false,
      });
    }

    // Pending — the watcher is fetching. Client should poll.
    return NextResponse.json(
      { animal: null, source: "fetching", pending: true, name: decoded },
      { status: 202 },
    );
  } catch (error) {
    console.error("[/api/animals/[name]] failed:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { error: "Failed to load animal detail", detail: message },
      { status: 500 },
    );
  }
}
