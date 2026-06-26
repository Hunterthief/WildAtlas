"use client";

import * as React from "react";
import { getLocationDots } from "@/lib/animals";
import { cn } from "@/lib/utils";

interface WorldMapProps {
  locations?: string;
  className?: string;
}

/**
 * World map with pulsing location dots. The map SVG (public/world.svg)
 * is inverted on dark backgrounds. Locations are resolved to percentage
 * coordinates and rendered as accessible, tooltip-enabled markers.
 */
export function WorldMap({ locations, className }: WorldMapProps) {
  const dots = React.useMemo(
    () => (locations ? getLocationDots(locations) : []),
    [locations],
  );
  const [imgOk, setImgOk] = React.useState(true);

  return (
    <div
      className={cn(
        "relative w-full overflow-hidden rounded-lg border border-border bg-background",
        className,
      )}
    >
      {imgOk ? (
        <img
          src="/world.svg"
          alt="World map showing species distribution"
          className="block h-auto w-full opacity-90 [filter:invert(1)] dark:[filter:invert(1)]"
          onError={() => setImgOk(false)}
        />
      ) : (
        <div className="aspect-[2/1] w-full bg-muted" />
      )}

      {/* Location dots overlay */}
      <div className="pointer-events-none absolute inset-0">
        {dots.map((dot, i) => (
          <span
            key={`${dot.label}-${i}`}
            className="animate-location-pulse absolute h-2 w-2 rounded-full border-2 border-background bg-primary"
            style={{ left: `${dot.x}%`, top: `${dot.y}%` }}
            title={dot.label}
            aria-label={`Found in ${dot.label}`}
          />
        ))}
      </div>

      {dots.length === 0 && (
        <p className="absolute inset-0 flex items-center justify-center px-4 text-center text-xs text-muted-foreground">
          No mapped locations available
        </p>
      )}
    </div>
  );
}
