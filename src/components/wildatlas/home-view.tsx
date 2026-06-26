"use client";

import * as React from "react";
import {
  Search,
  LayoutGrid,
  List,
  X,
  ChevronDown,
  Sparkles,
  ExternalLink,
  Loader2,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { AnimalCard } from "./animal-card";
import { AnimalImage } from "./animal-image";
import {
  useAnimals,
  useWikipediaSearch,
  type CatalogEntry,
  type SearchResult,
} from "@/hooks/use-animals";
import { TYPE_SECTIONS } from "@/lib/types";
import type { AnimalType } from "@/lib/types";
import { cn } from "@/lib/utils";

interface HomeViewProps {
  onSelectAnimal: (name: string, wikipediaTitle?: string, type?: string, featured?: boolean) => void;
}

const STORAGE_VIEW = "wildatlas:view-preference";
const STORAGE_SECTION = (type: string) => `wildatlas:section-${type}`;

export function HomeView({ onSelectAnimal }: HomeViewProps) {
  const [query, setQuery] = React.useState("");
  const [view, setView] = React.useState<"grid" | "list">("grid");
  const [collapsed, setCollapsed] = React.useState<Record<AnimalType, boolean>>({
    mammal: false,
    bird: false,
    reptile: false,
    fish: false,
    amphibian: false,
    insect: false,
  });
  const [showWikiResults, setShowWikiResults] = React.useState(false);

  // Catalog query (local search over the curated + starter catalog)
  const catalogQuery = React.useMemo(() => {
    // When the user types 3+ chars and it's not matching the catalog well,
    // we also fire a live Wikipedia search. The catalog query is always live.
    return query;
  }, [query]);

  const { data, isLoading, isError, error } = useAnimals(catalogQuery);

  // Live Wikipedia search (only kicks in for 2+ chars)
  const wikiSearch = useWikipediaSearch(query);
  const wikiResults = wikiSearch.data?.results ?? [];
  const isWikiSearching = wikiSearch.isFetching;

  // Restore view preference + collapsed state from localStorage on mount
  React.useEffect(() => {
    const savedView = localStorage.getItem(STORAGE_VIEW) as "grid" | "list" | null;
    if (savedView) setView(savedView);
    setCollapsed({
      mammal: localStorage.getItem(STORAGE_SECTION("mammal")) === "collapsed",
      bird: localStorage.getItem(STORAGE_SECTION("bird")) === "collapsed",
      reptile: localStorage.getItem(STORAGE_SECTION("reptile")) === "collapsed",
      fish: localStorage.getItem(STORAGE_SECTION("fish")) === "collapsed",
      amphibian: localStorage.getItem(STORAGE_SECTION("amphibian")) === "collapsed",
      insect: localStorage.getItem(STORAGE_SECTION("insect")) === "collapsed",
    });
  }, []);

  const allEntries: CatalogEntry[] = React.useMemo(
    () => data?.animals ?? [],
    [data],
  );

  // Group by type
  const grouped = React.useMemo(() => {
    const g: Record<AnimalType, CatalogEntry[]> = {
      mammal: [],
      bird: [],
      reptile: [],
      fish: [],
      amphibian: [],
      insect: [],
    };
    for (const e of allEntries) g[e.type].push(e);
    return g;
  }, [allEntries]);

  // Live Wikipedia results not already in the catalog
  const catalogNames = React.useMemo(
    () => new Set(allEntries.map((e) => e.name.toLowerCase())),
    [allEntries],
  );
  const extraWikiResults = React.useMemo(
    () =>
      wikiResults.filter(
        (r) => !catalogNames.has(r.title.toLowerCase()) && r.title !== query,
      ),
    [wikiResults, catalogNames, query],
  );

  const toggleView = (next: "grid" | "list") => {
    setView(next);
    localStorage.setItem(STORAGE_VIEW, next);
  };

  const toggleSection = (type: AnimalType) => {
    setCollapsed((prev) => {
      const next = { ...prev, [type]: !prev[type] };
      localStorage.setItem(
        STORAGE_SECTION(type),
        next[type] ? "collapsed" : "expanded",
      );
      return next;
    });
  };

  const handleSelect = (entry: CatalogEntry) => {
    onSelectAnimal(entry.name, entry.wikipediaTitle, entry.type, entry.featured);
  };

  const handleSelectWiki = (result: SearchResult) => {
    onSelectAnimal(result.title, result.title, undefined, false);
  };

  const totalShown = allEntries.length;
  const hasQuery = query.trim().length > 0;

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Hero / search */}
      <header className="mb-8 flex flex-col items-center gap-5 text-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
            WildAtlas
          </h1>
          <p className="mt-1 text-sm text-muted-foreground sm:text-base">
            Discover the living world, one fact at a time.
          </p>
        </div>

        <div className="relative w-full max-w-lg">
          <Search
            className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden="true"
          />
          <Input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search any animal — browses 100+ species, then searches Wikipedia live…"
            className="h-12 rounded-lg pl-11 pr-10 text-base"
            aria-label="Search animals"
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 rounded-sm p-1 text-muted-foreground hover:text-foreground focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              aria-label="Clear search"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        <div className="flex items-center gap-3">
          <div
            role="group"
            aria-label="View layout"
            className="flex gap-1 rounded-md border border-border bg-card p-1"
          >
            <Button
              type="button"
              size="sm"
              variant={view === "grid" ? "secondary" : "ghost"}
              onClick={() => toggleView("grid")}
              aria-pressed={view === "grid"}
              aria-label="Grid view"
              className="h-8 w-8 p-0"
            >
              <LayoutGrid className="h-4 w-4" />
            </Button>
            <Button
              type="button"
              size="sm"
              variant={view === "list" ? "secondary" : "ghost"}
              onClick={() => toggleView("list")}
              aria-pressed={view === "list"}
              aria-label="List view"
              className="h-8 w-8 p-0"
            >
              <List className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      {/* Loading state */}
      {isLoading && <HomeSkeleton />}

      {/* Error state */}
      {isError && (
        <div className="mx-auto max-w-md rounded-lg border border-destructive/40 bg-destructive/10 p-6 text-center">
          <p className="text-sm font-medium text-destructive">
            Couldn&apos;t load the catalog.
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            {error instanceof Error ? error.message : "Please try again later."}
          </p>
        </div>
      )}

      {/* Live Wikipedia search results (shown when query doesn't fully match catalog) */}
      {hasQuery && (
        <section className="mb-6 overflow-hidden rounded-xl border border-primary/30 bg-primary/5">
          <div className="flex items-center gap-2 bg-primary/10 px-5 py-3">
            <Sparkles className="h-4 w-4 text-primary" aria-hidden="true" />
            <span className="flex-1 text-sm font-semibold">
              Wikipedia results
            </span>
            {isWikiSearching && (
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            )}
          </div>
          <div className="p-4">
            {extraWikiResults.length > 0 ? (
              <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {extraWikiResults.slice(0, 6).map((r) => (
                  <li key={r.title}>
                    <button
                      type="button"
                      onClick={() => handleSelectWiki(r)}
                      className="group flex w-full flex-col gap-1 rounded-lg border border-border bg-card/60 p-3 text-left transition-all hover:border-primary/60 hover:bg-card focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    >
                      <span className="flex items-center gap-1.5 text-sm font-semibold">
                        {r.title}
                        <ExternalLink className="h-3 w-3 text-muted-foreground group-hover:text-primary" />
                      </span>
                      <span className="line-clamp-2 text-xs text-muted-foreground">
                        {r.description}
                      </span>
                      <span className="mt-1 text-[0.65rem] uppercase tracking-wide text-primary/80">
                        Live fetch from Wikipedia →
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              !isWikiSearching && (
                <p className="px-1 py-2 text-sm text-muted-foreground">
                  No additional Wikipedia articles for &ldquo;{query}&rdquo;.
                </p>
              )
            )}
          </div>
        </section>
      )}

      {/* Empty search result */}
      {!isLoading && !isError && totalShown === 0 && !hasQuery && (
        <div className="mx-auto max-w-md rounded-lg border border-border bg-card p-8 text-center">
          <p className="text-2xl">🐾</p>
          <p className="mt-2 font-medium">No animals found</p>
        </div>
      )}

      {/* Type sections (catalog) */}
      {!isLoading && !isError && totalShown > 0 && (
        <div className="flex flex-col gap-5">
          {TYPE_SECTIONS.map((section) => {
            const entries = grouped[section.type];
            if (entries.length === 0) return null;
            const isCollapsed = collapsed[section.type];
            return (
              <Collapsible
                key={section.type}
                open={!isCollapsed}
                onOpenChange={() => toggleSection(section.type)}
                className="overflow-hidden rounded-xl border border-border bg-card/40"
              >
                <CollapsibleTrigger asChild>
                  <button
                    type="button"
                    className="flex w-full items-center gap-3 bg-card px-5 py-4 text-left transition-colors hover:bg-card/80 focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring"
                    aria-expanded={!isCollapsed}
                    aria-controls={`section-content-${section.type}`}
                  >
                    <span className="text-xl" aria-hidden="true">
                      {section.icon}
                    </span>
                    <span className="flex-1 text-sm font-semibold uppercase tracking-wide">
                      {section.label}
                    </span>
                    <span className="rounded-md bg-secondary px-2.5 py-1 text-xs font-semibold text-secondary-foreground">
                      {entries.length}
                    </span>
                    <ChevronDown
                      className={cn(
                        "h-4 w-4 text-muted-foreground transition-transform",
                        isCollapsed && "-rotate-90",
                      )}
                      aria-hidden="true"
                    />
                  </button>
                </CollapsibleTrigger>
                <CollapsibleContent id={`section-content-${section.type}`}>
                  <div
                    className={cn(
                      "grid gap-3 p-5",
                      view === "grid"
                        ? "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
                        : "grid-cols-1",
                    )}
                  >
                    {entries.map((entry) => (
                      <AnimalCard
                        key={entry.id}
                        name={entry.name}
                        scientificName={entry.scientific_name}
                        image={entry.image}
                        featured={entry.featured}
                        view={view}
                        onSelect={() => handleSelect(entry)}
                      />
                    ))}
                  </div>
                </CollapsibleContent>
              </Collapsible>
            );
          })}
        </div>
      )}

      {/* Inspiration */}
      <section className="mx-auto mt-12 max-w-3xl rounded-xl border border-border bg-card/40 p-8 text-center">
        <h2 className="text-lg font-semibold">A living encyclopedia</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Browse over 100 curated species above, or search for any animal —
          WildAtlas fetches details live from Wikipedia and caches them for
          instant repeat access. Inspired by{" "}
          <a
            href="https://www.facts.app/"
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-primary hover:underline"
          >
            Facts.app
          </a>
          .
        </p>
      </section>
    </div>
  );
}

function HomeSkeleton() {
  return (
    <div className="flex flex-col gap-5">
      {TYPE_SECTIONS.slice(0, 3).map((s) => (
        <div
          key={s.type}
          className="overflow-hidden rounded-xl border border-border bg-card/40"
        >
          <div className="flex items-center gap-3 bg-card px-5 py-4">
            <div className="h-5 w-5 animate-pulse rounded bg-muted" />
            <div className="h-4 w-24 animate-pulse rounded bg-muted" />
          </div>
          <div className="grid grid-cols-1 gap-3 p-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="h-16 animate-pulse rounded-lg border border-border bg-muted/40"
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
