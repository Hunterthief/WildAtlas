// ============================================
// WildAtlas - Comparison helpers
// Best-effort numeric extraction from free-form stat
// strings (e.g. "56 km/h", "12-15 years") so the
// compare view can highlight the "winner" of a metric.
//
// Unit-aware: normalizes cm->m, g->kg, etc. so that a
// "50-76 cm" fish is correctly compared against a
// "1.2-1.5 m" turtle (both resolved to meters).
// ============================================

import type { Animal } from "./types";
import { hasValue } from "./animals";

export interface MetricRow {
  id: string;
  label: string;
  icon?: string;
  /** Returns the display string for a given animal. */
  value: (a: Animal) => string | undefined;
  /** Returns a comparable number (in the metric's canonical unit, higher = "better") or null. */
  numeric?: (a: Animal) => number | null;
  /** When true, the lowest number wins instead of the highest. */
  lowerIsBetter?: boolean;
  /** The canonical unit this metric is normalized to (for documentation). */
  unit?: string;
}

// ---------- Numeric parsers ----------

/** Extract the first number from a string (handles decimals). */
export function parseFirstNumber(value: string | undefined): number | null {
  if (!value) return null;
  const match = value.replace(/,/g, "").match(/-?\d+(\.\d+)?/);
  return match ? Number(match[0]) : null;
}

/** Parse a range like "12-15" or "0.8–1.1" → average (13.5). Single numbers pass through. */
export function parseRangeAverage(value: string | undefined): number | null {
  if (!value) return null;
  const cleaned = value.replace(/[–—]/g, "-").replace(/,/g, "");
  const rangeMatch = cleaned.match(/(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)/);
  if (rangeMatch) {
    return (Number(rangeMatch[1]) + Number(rangeMatch[2])) / 2;
  }
  return parseFirstNumber(value);
}

/** Detect the unit suffix present in a stat string. */
type LengthUnit = "m" | "cm" | "mm" | "in" | "ft";
type WeightUnit = "kg" | "g" | "mg" | "lb" | "oz" | "t";

function detectLengthUnit(value: string): LengthUnit | null {
  const v = value.toLowerCase();
  if (v.includes("mm")) return "mm";
  if (v.includes("cm")) return "cm";
  if (v.includes("in") && !v.includes("inc")) return "in";
  if (v.includes("ft")) return "ft";
  if (v.includes("m")) return "m";
  return null;
}

function detectWeightUnit(value: string): WeightUnit | null {
  const v = value.toLowerCase();
  if (v.includes("mg")) return "mg";
  if (v.includes("kg")) return "kg";
  if (v.includes("lb") || v.includes("pound")) return "lb";
  if (v.includes("oz") || v.includes("ounce")) return "oz";
  // Match ton / tonne / tons / tonnes (avoid matching "g" fallback)
  if (v.includes("tonne")) return "t";
  if (/\btons?\b/.test(v)) return "t";
  if (v.includes("g")) return "g";
  return null;
}

/**
 * Convert a length value to meters, given the source unit.
 * Returns null for unknown units.
 */
function toMeters(num: number, unit: LengthUnit): number {
  switch (unit) {
    case "m":
      return num;
    case "cm":
      return num / 100;
    case "mm":
      return num / 1000;
    case "in":
      return num * 0.0254;
    case "ft":
      return num * 0.3048;
    default:
      return num;
  }
}

/** Convert a weight value to kilograms, given the source unit. */
function toKilograms(num: number, unit: WeightUnit): number {
  switch (unit) {
    case "kg":
      return num;
    case "g":
      return num / 1000;
    case "mg":
      return num / 1_000_000;
    case "lb":
      return num * 0.453592;
    case "oz":
      return num * 0.0283495;
    case "t":
      return num * 1000;
    default:
      return num;
  }
}

/**
 * Parse a length stat string to meters (the canonical unit).
 * Handles ranges, cm/m/mm/in/ft. Strips parenthetical notes
 * like "(wingspan)" before parsing so they don't interfere.
 */
export function parseLengthToMeters(value: string | undefined): number | null {
  if (!value) return null;
  // Strip parenthetical content and trailing labels
  const cleaned = value.replace(/\([^)]*\)/g, "").trim();
  const unit = detectLengthUnit(cleaned);
  if (!unit) return null;
  const avg = parseRangeAverage(cleaned);
  if (avg === null) return null;
  return toMeters(avg, unit);
}

/** Parse a weight stat string to kilograms (canonical unit). */
export function parseWeightToKg(value: string | undefined): number | null {
  if (!value) return null;
  const cleaned = value.replace(/\([^)]*\)/g, "").trim();
  const unit = detectWeightUnit(cleaned);
  if (!unit) return null;
  const avg = parseRangeAverage(cleaned);
  if (avg === null) return null;
  return toKilograms(avg, unit);
}

/** Parse a speed value to km/h (most data is already km/h). */
export function parseSpeed(value: string | undefined): number | null {
  if (!value) return null;
  const cleaned = value.replace(/\([^)]*\)/g, "").trim();
  const avg = parseRangeAverage(cleaned);
  return avg;
}

/** Parse a lifespan: handles "years", "weeks", "days", "months". Returns days. */
export function parseLifespanToDays(value: string | undefined): number | null {
  if (!value) return null;
  const cleaned = value.replace(/\([^)]*\)/g, "").trim().toLowerCase();
  const avg = parseRangeAverage(cleaned);
  if (avg === null) return null;
  if (cleaned.includes("day")) return avg;
  if (cleaned.includes("week")) return avg * 7;
  if (cleaned.includes("month")) return avg * 30;
  if (cleaned.includes("year")) return avg * 365;
  // No unit — assume years (most common in dataset)
  return avg * 365;
}

export const METRIC_ROWS: MetricRow[] = [
  {
    id: "classification",
    label: "Class",
    icon: "📚",
    value: (a) => a.classification?.class,
  },
  {
    id: "order",
    label: "Order",
    value: (a) => a.classification?.order,
  },
  {
    id: "family",
    label: "Family",
    value: (a) => a.classification?.family,
  },
  {
    id: "diet",
    label: "Diet",
    icon: "🍽️",
    value: (a) => a.ecology?.diet,
  },
  {
    id: "length",
    label: "Length",
    icon: "📏",
    value: (a) => a.physical?.length,
    numeric: (a) => parseLengthToMeters(a.physical?.length),
    unit: "m",
  },
  {
    id: "height",
    label: "Height",
    icon: "📐",
    value: (a) => a.physical?.height,
    numeric: (a) => parseLengthToMeters(a.physical?.height),
    unit: "m",
  },
  {
    id: "weight",
    label: "Weight",
    icon: "⚖️",
    value: (a) => a.physical?.weight,
    numeric: (a) => parseWeightToKg(a.physical?.weight),
    unit: "kg",
  },
  {
    id: "speed",
    label: "Top Speed",
    icon: "⚡",
    value: (a) => a.physical?.top_speed,
    numeric: (a) => parseSpeed(a.physical?.top_speed),
    unit: "km/h",
  },
  {
    id: "lifespan",
    label: "Lifespan",
    icon: "⏳",
    value: (a) => a.physical?.lifespan,
    numeric: (a) => parseLifespanToDays(a.physical?.lifespan),
    unit: "days",
  },
  {
    id: "habitat",
    label: "Habitat",
    icon: "🌍",
    value: (a) => a.ecology?.habitat,
  },
  {
    id: "locations",
    label: "Locations",
    icon: "🗺️",
    value: (a) => a.ecology?.locations,
  },
  {
    id: "group_behavior",
    label: "Group Behavior",
    icon: "👥",
    value: (a) => a.ecology?.group_behavior,
  },
  {
    id: "conservation",
    label: "Conservation",
    icon: "🛡️",
    value: (a) => a.ecology?.conservation_status,
  },
  {
    id: "gestation",
    label: "Gestation",
    icon: "🤰",
    value: (a) => a.reproduction?.gestation_period,
  },
  {
    id: "litter",
    label: "Litter / Clutch Size",
    icon: "🐣",
    value: (a) => a.reproduction?.average_litter_size,
  },
  {
    id: "young",
    label: "Young Called",
    icon: "🍼",
    value: (a) => a.reproduction?.name_of_young ?? a.young_name,
  },
  {
    id: "group_name",
    label: "Group Name",
    icon: "🏷️",
    value: (a) => a.group_name,
  },
];

/**
 * For a given metric, returns the set of animal indices that are
 * the "winner" (to be highlighted). Returns empty set when there
 * are no comparable numeric values or fewer than 2 valid entries.
 */
export function getWinners(animals: Animal[], metric: MetricRow): Set<number> {
  if (!metric.numeric) return new Set();
  const values = animals.map((a, i) => ({ i, n: metric.numeric!(a) }));
  const valid = values.filter((v) => v.n !== null && v.n > 0);
  if (valid.length < 2) return new Set();

  const target = metric.lowerIsBetter
    ? Math.min(...valid.map((v) => v.n!))
    : Math.max(...valid.map((v) => v.n!));

  const winners = new Set<number>();
  for (const v of valid) {
    if (v.n === target) winners.add(v.i);
  }
  return winners;
}

/** Whether a metric has at least one value across the given animals. */
export function metricHasData(animals: Animal[], metric: MetricRow): boolean {
  return animals.some((a) => hasValue(metric.value(a)));
}
