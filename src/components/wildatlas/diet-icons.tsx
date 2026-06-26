import { getDietTypes } from "@/lib/animals";
import { cn } from "@/lib/utils";

interface DietIconsProps {
  diet?: string;
  animalType?: string;
  summary?: string;
  className?: string;
}

const DIET_STYLES: Record<string, string> = {
  carnivore: "bg-red-500/20 text-red-300",
  herbivore: "bg-emerald-500/20 text-emerald-300",
  omnivore: "bg-orange-500/20 text-orange-300",
  insectivore: "bg-purple-500/20 text-purple-300",
  piscivore: "bg-sky-500/20 text-sky-300",
  nectarivore: "bg-pink-500/20 text-pink-300",
  scavenger: "bg-amber-700/30 text-amber-300",
  unknown: "bg-muted text-muted-foreground",
};

/**
 * Renders one or more diet badges derived from the diet string,
 * animal type and summary text. Preserves the multi-icon behaviour
 * of the original getDietTypes() while using accessible tooltips.
 */
export function DietIcons({ diet, animalType, summary, className }: DietIconsProps) {
  const types = getDietTypes(diet, animalType, summary);

  return (
    <div className={cn("flex flex-wrap gap-2", className)}>
      {types.map((t) => (
        <span
          key={t.class}
          title={t.title}
          aria-label={t.title}
          className={cn(
            "inline-flex h-9 w-9 items-center justify-center rounded-lg text-lg",
            DIET_STYLES[t.class] ?? DIET_STYLES.unknown,
          )}
        >
          <span aria-hidden="true">{t.icon}</span>
          <span className="sr-only">{t.title}</span>
        </span>
      ))}
    </div>
  );
}
