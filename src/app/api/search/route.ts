import { NextResponse } from "next/server";
import { searchWikipedia } from "@/lib/wikipedia";

// GET /api/search?q=...
// Live Wikipedia article search. Returns titles + descriptions so users
// can discover ANY animal on Wikipedia, not just the curated catalog.
// Selecting a result loads its detail page (fetched on-demand + cached).
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const q = searchParams.get("q") ?? "";
    if (!q.trim()) {
      return NextResponse.json({ results: [] });
    }
    const results = await searchWikipedia(q, 12);
    return NextResponse.json({ results });
  } catch (error) {
    console.error("[/api/search] failed:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { error: "Wikipedia search failed", detail: message },
      { status: 500 },
    );
  }
}
