import { getConservationLevel } from "@/lib/animals";
import type { ConservationLevel } from "@/lib/types";
import { cn } from "@/lib/utils";

interface ConservationBadgeProps {
  status?: string;
  className?: string;
}

const LEVEL_STYLES: Record<ConservationLevel, string> = {
  "least-concern": "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  "near-threatened": "bg-lime-500/20 text-lime-300 border-lime-500/30",
  vulnerable: "bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
  endangered: "bg-orange-500/20 text-orange-300 border-orange-500/30",
  "critically-endangered": "bg-red-500/20 text-red-300 border-red-500/30",
  extinct: "bg-zinc-500/30 text-zinc-300 border-zinc-500/40",
  unknown: "bg-muted text-muted-foreground border-border",
};

/** Colour-coded conservation status pill (IUCN-aligned buckets). */
export function ConservationBadge({ status, className }: ConservationBadgeProps) {
  const level = getConservationLevel(status);
  const label = status?.trim() || "Unknown";

  return (
    <span
      className={cn(
        "inline-flex w-full items-center justify-center rounded-md border px-3 py-2 text-xs font-semibold uppercase tracking-wide",
        LEVEL_STYLES[level],
        className,
      )}
    >
      {label}
    </span>
  );
}
