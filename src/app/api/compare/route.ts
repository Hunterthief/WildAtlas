import { NextResponse } from "next/server";
import { ANIMALS, findAnimalByName } from "@/lib/animals";
import { getAnimalByName } from "@/lib/wikipedia";
import type { Animal } from "@/lib/types";

// GET /api/compare?names=Tiger,Cheetah&wikipediaTitles=...,...&types=...,...
// Returns full records for every requested animal. Curated animals load
// instantly; anything not yet cached returns with a `pending` flag so the
// client knows to poll. The watcher fetches & enriches in the background.
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const namesParam = searchParams.get("names") ?? "";
    const titlesParam = searchParams.get("wikipediaTitles") ?? "";
    const typesParam = searchParams.get("types") ?? "";

    const requestedNames = namesParam
      .split(",")
      .map((n) => decodeURIComponent(n.trim()))
      .filter(Boolean);
    const titles = titlesParam
      .split(",")
      .map((t) => decodeURIComponent(t.trim()))
      .filter(Boolean);
    const types = typesParam
      .split(",")
      .map((t) => decodeURIComponent(t.trim()))
      .filter(Boolean) as (
      | "mammal"
      | "bird"
      | "reptile"
      | "fish"
      | "amphibian"
      | "insect"
    )[];

    if (requestedNames.length === 0) {
      return NextResponse.json({
        animals: [],
        pending: [],
        missing: [],
        available: ANIMALS.map((a) => a.name),
      });
    }

    const animals: Animal[] = [];
    const pending: string[] = [];
    const missing: string[] = [];

    for (let i = 0; i < requestedNames.length; i++) {
      const name = requestedNames[i];
      try {
        const result = await getAnimalByName(name, {
          wikipediaTitle: titles[i],
          type: types[i],
        });
        if (result.animal) {
          animals.push(result.animal);
        } else if (result.pending) {
          pending.push(name);
        } else {
          missing.push(name);
        }
      } catch {
        missing.push(name);
      }
    }

    return NextResponse.json({
      animals,
      pending,
      missing,
      available: ANIMALS.map((a) => a.name),
    });
  } catch (error) {
    console.error("[/api/compare] failed:", error);
    return NextResponse.json(
      { error: "Failed to load comparison data" },
      { status: 500 },
    );
  }
}
