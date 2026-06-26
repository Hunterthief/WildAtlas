import { cn } from "@/lib/utils";

interface TimelineBarProps {
  /** Fill width as a CSS percentage string, e.g. "83%". Fuller = more recent origin. */
  fillPercent?: string;
  /** Left label (ancient bound) */
  start?: string;
  /** Right label (recent / present) */
  end?: string;
  className?: string;
}

/**
 * Evolutionary-timeline bar.
 *
 * The bar spans from the oldest lineage in the dataset (left) to the
 * present (right). The fill grows from the left and ENDS at the point
 * where this species first appeared — so a recently-evolved species
 * (origin near the present) has a LONG fill, while an ancient lineage
 * (origin near the left) has a SHORT fill.
 *
 *   [████████████████░░░░░░░░]  ← recent species (long fill)
 *   [██░░░░░░░░░░░░░░░░░░░░░░]  ← ancient species (short fill)
 *   Ancient ──────────── Present
 */
export function TimelineBar({ fillPercent, start, end, className }: TimelineBarProps) {
  const width = fillPercent && fillPercent.trim() !== "" ? fillPercent : "50%";
  return (
    <div className={cn("flex flex-col gap-2", className)}>
      <div
        className="relative h-2 w-full overflow-hidden rounded-full bg-muted"
        role="img"
        aria-label={`Evolved ${fillPercent ?? "50%"} along the timeline from ancient to present`}
      >
        <div
          className="h-full rounded-full bg-gradient-to-r from-primary/60 to-primary"
          style={{ width }}
        />
      </div>
      <div className="flex justify-between text-[0.65rem] uppercase tracking-wide text-muted-foreground">
        <span>{start ?? "Ancient"}</span>
        <span>{end ?? "Present"}</span>
      </div>
    </div>
  );
}
