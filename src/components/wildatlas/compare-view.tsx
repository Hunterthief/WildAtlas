"use client";

import * as React from "react";
import { Plus, X, ArrowLeft, GitCompare, Trophy, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { AnimalImage } from "./animal-image";
import { ConservationBadge } from "./conservation-badge";
import {
  useAnimals,
  useCompare,
  useWikipediaSearch,
  type CatalogEntry,
} from "@/hooks/use-animals";
import type { AnimalRef } from "./wildatlas-app";
import {
  METRIC_ROWS,
  getWinners,
  metricHasData,
} from "@/lib/compare";
import type { Animal } from "@/lib/types";
import { cn } from "@/lib/utils";

interface CompareViewProps {
  initialRefs: AnimalRef[];
  onRefsChange: (refs: AnimalRef[]) => void;
  onBack: () => void;
  onSelectAnimal: (name: string, wikipediaTitle?: string, type?: string, featured?: boolean) => void;
}

const MAX_COMPARE = 3;

export function CompareView({
  initialRefs,
  onRefsChange,
  onBack,
  onSelectAnimal,
}: CompareViewProps) {
  const { data: animalsData } = useAnimals();
  const [selected, setSelected] = React.useState<AnimalRef[]>(
    initialRefs.length > 0 ? initialRefs.slice(0, MAX_COMPARE) : [],
  );
  const [customSearch, setCustomSearch] = React.useState("");

  const { data, isLoading, isError } = useCompare(selected);

  React.useEffect(() => {
    onRefsChange(selected);
  }, [selected, onRefsChange]);

  // Live Wikipedia search for adding animals not in the catalog
  const wikiSearch = useWikipediaSearch(customSearch);
  const wikiResults = wikiSearch.data?.results ?? [];

  const catalog: CatalogEntry[] = animalsData?.animals ?? [];
  const compared: Animal[] = data?.animals ?? [];

  const selectedKeys = new Set(selected.map((s) => s.name.toLowerCase()));

  const addFromCatalog = (entry: CatalogEntry) => {
    if (selected.length >= MAX_COMPARE || selectedKeys.has(entry.name.toLowerCase())) return;
    setSelected((prev) => [
      ...prev,
      { name: entry.name, wikipediaTitle: entry.wikipediaTitle, type: entry.type, featured: entry.featured },
    ]);
  };

  const addFromSearch = (title: string) => {
    if (selected.length >= MAX_COMPARE || selectedKeys.has(title.toLowerCase())) return;
    setSelected((prev) => [...prev, { name: title, wikipediaTitle: title }]);
    setCustomSearch("");
  };

  const removeAnimal = (name: string) => {
    setSelected((prev) => prev.filter((s) => s.name !== name));
  };

  const availableCatalog = catalog.filter(
    (c) => !selectedKeys.has(c.name.toLowerCase()),
  );

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <button
        type="button"
        onClick={onBack}
        className="mb-6 inline-flex items-center gap-2 rounded-md text-sm text-muted-foreground transition-colors hover:text-primary focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        Back to encyclopedia
      </button>

      <header className="mb-8 flex flex-col gap-2">
        <div className="flex items-center gap-2">
          <GitCompare className="h-6 w-6 text-primary" aria-hidden="true" />
          <h1 className="text-3xl font-bold tracking-tight">Compare Animals</h1>
        </div>
        <p className="text-sm text-muted-foreground">
          Pick up to {MAX_COMPARE} species from the catalog or search Wikipedia for
          any animal. The best value in each measurable category is highlighted.
        </p>
      </header>

      {/* Selected animals */}
      <div className="mb-6 rounded-xl border border-border bg-card/40 p-4 sm:p-5">
        <div className="flex flex-wrap items-center gap-3">
          {selected.map((ref) => (
            <div
              key={ref.name}
              className="inline-flex items-center gap-2 rounded-full border border-primary/40 bg-primary/10 py-1 pl-3 pr-1 text-sm"
            >
              <span className="font-medium">{ref.name}</span>
              <button
                type="button"
                onClick={() => removeAnimal(ref.name)}
                className="rounded-full p-1 text-muted-foreground hover:bg-primary/20 hover:text-foreground focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                aria-label={`Remove ${ref.name} from comparison`}
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}

          {selected.length === 0 && (
            <p className="text-sm text-muted-foreground">
              No animals selected yet. Add some below.
            </p>
          )}
        </div>
      </div>

      {/* Add from catalog + live Wikipedia search */}
      {selected.length < MAX_COMPARE && (
        <div className="mb-8 grid grid-cols-1 gap-4 lg:grid-cols-2">
          {/* Catalog picker */}
          <div className="rounded-xl border border-border bg-card/40 p-4">
            <h2 className="mb-3 text-sm font-semibold">From catalog</h2>
            {availableCatalog.length > 0 ? (
              <Select value="" onValueChange={(v) => {
                const entry = catalog.find((c) => c.name === v);
                if (entry) addFromCatalog(entry);
              }}>
                <SelectTrigger className="w-full" aria-label="Add an animal from the catalog">
                  <SelectValue placeholder="Select an animal…" />
                </SelectTrigger>
                <SelectContent>
                  {availableCatalog.map((c) => (
                    <SelectItem key={c.id} value={c.name}>
                      {c.name} {c.featured ? "★" : ""}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <p className="text-xs text-muted-foreground">Catalog exhausted.</p>
            )}
          </div>

          {/* Live Wikipedia search */}
          <div className="rounded-xl border border-border bg-card/40 p-4">
            <h2 className="mb-3 text-sm font-semibold">Search Wikipedia</h2>
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={customSearch}
                onChange={(e) => setCustomSearch(e.target.value)}
                placeholder="Any animal, e.g. “axolotl”…"
                className="pl-9"
                aria-label="Search Wikipedia for an animal to compare"
              />
            </div>
            {customSearch.trim().length >= 2 && (
              <ul className="mt-2 max-h-48 overflow-y-auto scroll-thin">
                {wikiSearch.isFetching && (
                  <li className="px-2 py-1 text-xs text-muted-foreground">Searching…</li>
                )}
                {wikiResults
                  .filter((r) => !selectedKeys.has(r.title.toLowerCase()))
                  .slice(0, 6)
                  .map((r) => (
                    <li key={r.title}>
                      <button
                        type="button"
                        onClick={() => addFromSearch(r.title)}
                        className="w-full rounded-md px-2 py-1.5 text-left text-sm hover:bg-accent focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      >
                        <span className="font-medium">{r.title}</span>
                        <span className="block truncate text-xs text-muted-foreground">
                          {r.description}
                        </span>
                      </button>
                    </li>
                  ))}
              </ul>
            )}
          </div>
        </div>
      )}

      {/* Loading */}
      {selected.length > 0 && isLoading && (
        <div className="space-y-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-12 animate-pulse rounded-lg bg-muted/40" />
          ))}
        </div>
      )}

      {/* Error */}
      {selected.length > 0 && isError && (
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-6 text-center text-sm text-destructive">
          Couldn&apos;t load comparison data. Please try again.
        </div>
      )}

      {/* Comparison table */}
      {selected.length > 0 && compared.length > 0 && (
        <ComparisonTable
          animals={compared}
          onSelectAnimal={onSelectAnimal}
        />
      )}
    </div>
  );
}

function ComparisonTable({
  animals,
  onSelectAnimal,
}: {
  animals: Animal[];
  onSelectAnimal: (name: string, wikipediaTitle?: string, type?: string, featured?: boolean) => void;
}) {
  const winnersByMetric = React.useMemo(
    () => METRIC_ROWS.map((m) => getWinners(animals, m)),
    [animals],
  );

  const visibleMetrics = METRIC_ROWS.filter((m) => metricHasData(animals, m));

  return (
    <div className="overflow-x-auto scroll-thin">
      <table className="w-full border-collapse text-sm">
        <caption className="sr-only">
          Side-by-side comparison of {animals.map((a) => a.name).join(", ")}
        </caption>
        <thead>
          <tr>
            <th
              scope="col"
              className="sticky left-0 z-10 w-40 bg-background p-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground"
            >
              Attribute
            </th>
            {animals.map((a) => (
              <th key={a.id} scope="col" className="min-w-[180px] p-3 align-top">
                <button
                  type="button"
                  onClick={() => onSelectAnimal(a.name, undefined, undefined)}
                  className="flex w-full flex-col items-center gap-2 text-center focus:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-lg"
                >
                  <AnimalImage
                    src={a.image ?? a.images?.[0]}
                    alt={a.name}
                    fallbackLabel={a.name}
                    className="h-16 w-16 rounded-full border-2 border-border"
                  />
                  <span className="text-sm font-bold text-foreground hover:text-primary">
                    {a.name}
                  </span>
                  <span className="font-serif text-xs italic text-muted-foreground">
                    {a.scientific_name || "—"}
                  </span>
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {visibleMetrics.map((metric, mi) => {
            const winners = winnersByMetric[METRIC_ROWS.indexOf(metric)];
            return (
              <tr
                key={metric.id}
                className="border-t border-border hover:bg-card/30"
              >
                <th
                  scope="row"
                  className="sticky left-0 z-10 bg-background p-3 text-left text-xs font-medium text-muted-foreground"
                >
                  {metric.icon ? (
                    <span className="mr-1.5" aria-hidden="true">
                      {metric.icon}
                    </span>
                  ) : null}
                  {metric.label}
                </th>
                {animals.map((a, ai) => {
                  const raw = metric.value(a);
                  const isWinner = winners.has(ai);
                  return (
                    <td key={a.id} className="p-3 align-top">
                      <CellValue
                        value={raw}
                        isWinner={isWinner}
                        isConservation={metric.id === "conservation"}
                        conservationStatus={a.ecology?.conservation_status}
                      />
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function CellValue({
  value,
  isWinner,
  isConservation,
  conservationStatus,
}: {
  value: string | undefined;
  isWinner: boolean;
  isConservation: boolean;
  conservationStatus?: string;
}) {
  if (isConservation) {
    return conservationStatus ? (
      <ConservationBadge status={conservationStatus} className="text-[0.65rem]" />
    ) : (
      <span className="text-muted-foreground">—</span>
    );
  }

  if (!value || value.trim() === "") {
    return <span className="text-muted-foreground">—</span>;
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-xs",
        isWinner
          ? "bg-primary/15 font-semibold text-primary"
          : "text-foreground",
      )}
    >
      {isWinner && (
        <Trophy className="h-3 w-3 shrink-0" aria-label="Best in category" />
      )}
      {value}
    </span>
  );
}
