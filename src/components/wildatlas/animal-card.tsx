"use client";

import { AnimalImage } from "./animal-image";
import { cn } from "@/lib/utils";
import { Star } from "lucide-react";

interface AnimalCardProps {
  name: string;
  scientificName?: string;
  image?: string;
  wikipediaTitle?: string;
  featured?: boolean;
  view: "grid" | "list";
  onSelect: (name: string, wikipediaTitle?: string) => void;
}

/**
 * Animal card for the encyclopedia grid/list views. Works for both
 * featured (curated, rich) and starter-catalog (lightweight) entries.
 * The whole card is a button for keyboard accessibility.
 */
export function AnimalCard({
  name,
  scientificName,
  image,
  featured,
  view,
  onSelect,
}: AnimalCardProps) {
  const isList = view === "list";

  return (
    <button
      type="button"
      onClick={() => onSelect(name)}
      className={cn(
        "group flex w-full items-center gap-3 rounded-lg border border-border bg-card/60 p-3 text-left transition-all hover:border-primary/60 hover:bg-card focus:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        isList ? "p-4" : "",
      )}
      aria-label={`View details for ${name}`}
    >
      <AnimalImage
        src={image}
        alt={name}
        fallbackLabel={name}
        className={cn(
          "shrink-0 rounded-full border-2 border-border",
          isList ? "h-16 w-16" : "h-12 w-12",
        )}
      />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          <span className="truncate text-sm font-semibold uppercase tracking-wide text-foreground">
            {name}
          </span>
          {featured && (
            <Star
              className="h-3 w-3 shrink-0 fill-primary text-primary"
              aria-label="Featured (curated data)"
            />
          )}
        </div>
        <div className="truncate font-serif text-sm italic text-muted-foreground">
          {scientificName || "Tap to load details"}
        </div>
      </div>
    </button>
  );
}
