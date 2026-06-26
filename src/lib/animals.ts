// ============================================
// WildAtlas - Data Access & Helpers
// Central module that loads the animal dataset and
// exposes typed helpers (classification, lookup, search).
// ============================================

import animalData from "@/data/animals.json";
import {
  type Animal,
  type AnimalSummary,
  type AnimalType,
  type ConservationLevel,
  type DietType,
  ANIMAL_TYPES,
} from "./types";

export const ANIMALS: Animal[] = animalData as Animal[];

// ============================================
// Type classification
// (Consolidated from the original duplicated logic
//  in organizeByType() and filterAnimals())
// ============================================
const TYPE_KEYWORDS: Record<AnimalType, string[]> = {
  mammal: [
    "mammal",
    "mammalia",
    "feline",
    "canine",
    "bear",
    "elephant",
    "primate",
    "whale",
    "deer",
    "bovine",
    "equine",
    "rabbit",
    "rodent",
    "bat",
    "giraffe",
    "cheetah",
  ],
  bird: [
    "bird",
    "aves",
    "raptor",
    "owl",
    "penguin",
    "chicken",
    "duck",
    "goose",
    "swan",
    "eagle",
  ],
  reptile: ["reptile", "reptilia", "snake", "lizard", "turtle", "crocodile"],
  fish: ["fish", "shark", "ray", "salmon"],
  amphibian: ["amphibian", "amphibia", "frog", "salamander"],
  insect: ["insect", "insecta", "butterfly", "bee", "ant", "spider", "crab"],
};

/** Classify a single animal into one of the six encyclopedia groups. */
export function classifyAnimal(animal: Animal): AnimalType {
  const animalType = animal.animal_type?.toLowerCase() ?? "";
  const classType = animal.classification?.class?.toLowerCase() ?? "";

  for (const type of ANIMAL_TYPES) {
    if (TYPE_KEYWORDS[type].some((t) => animalType.includes(t) || classType.includes(t))) {
      return type;
    }
  }
  // Default fallback so an animal is never silently dropped
  return "mammal";
}

/** Group all animals by their encyclopedia section. */
export function groupAnimalsByType(animals: Animal[]): Record<AnimalType, Animal[]> {
  const groups: Record<AnimalType, Animal[]> = {
    mammal: [],
    bird: [],
    reptile: [],
    fish: [],
    amphibian: [],
    insect: [],
  };
  for (const animal of animals) {
    groups[classifyAnimal(animal)].push(animal);
  }
  return groups;
}

/** Case-insensitive, accent-tolerant name lookup. */
export function findAnimalByName(name: string): Animal | undefined {
  const target = name.trim().toLowerCase();
  return ANIMALS.find((a) => a.name.toLowerCase() === target);
}

/** Lightweight summary list for cards and selectors. */
export function getAnimalSummaries(): AnimalSummary[] {
  return ANIMALS.map((a) => ({
    id: a.id,
    name: a.name,
    scientific_name: a.scientific_name,
    image: a.image ?? a.images?.[0],
    animal_type: a.animal_type,
    classification: a.classification,
    type: classifyAnimal(a),
  }));
}

/** Full-text search across name, scientific name, type, habitat & locations. */
export function searchAnimals(query: string, animals: Animal[] = ANIMALS): Animal[] {
  const q = query.trim().toLowerCase();
  if (!q) return animals;
  return animals.filter((animal) => {
    return (
      animal.name?.toLowerCase().includes(q) ||
      animal.scientific_name?.toLowerCase().includes(q) ||
      animal.animal_type?.toLowerCase().includes(q) ||
      animal.ecology?.habitat?.toLowerCase().includes(q) ||
      animal.ecology?.locations?.toLowerCase().includes(q)
    );
  });
}

// ============================================
// Conservation status -> colour bucket
// ============================================
export function getConservationLevel(status?: string): ConservationLevel {
  if (!status) return "unknown";
  const s = status.toLowerCase();
  if (s.includes("extinct")) return "extinct";
  if (s.includes("critically")) return "critically-endangered";
  if (s.includes("endangered")) return "endangered";
  if (s.includes("vulnerable")) return "vulnerable";
  if (s.includes("near")) return "near-threatened";
  if (s.includes("least") || s.includes("concern")) return "least-concern";
  return "unknown";
}

// ============================================
// Diet icon derivation
// (Ported & cleaned up from getDietTypes())
// ============================================
export function getDietTypes(
  diet: string | undefined,
  animalType: string | undefined,
  summary: string | undefined,
): DietType[] {
  if (!diet) return [{ class: "unknown", icon: "❓", title: "Unknown diet" }];

  const dietLower = diet.toLowerCase();
  const summaryLower = (summary ?? "").toLowerCase();
  const typeLower = (animalType ?? "").toLowerCase();
  const types: DietType[] = [];

  if (
    dietLower.includes("carnivore") ||
    dietLower.includes("meat") ||
    summaryLower.includes("predator") ||
    summaryLower.includes("preys on") ||
    summaryLower.includes("hunts") ||
    ["feline", "canine", "bear", "shark", "raptor", "snake", "crocodile"].includes(typeLower)
  ) {
    types.push({ class: "carnivore", icon: "🥩", title: "Meat" });
  }

  if (
    dietLower.includes("herbivore") ||
    dietLower.includes("plant") ||
    summaryLower.includes("grazes") ||
    summaryLower.includes("foliage") ||
    summaryLower.includes("vegetation") ||
    ["elephant", "bovine", "deer", "rabbit", "turtle"].includes(typeLower)
  ) {
    types.push({ class: "herbivore", icon: "🌿", title: "Plants" });
  }

  if (
    dietLower.includes("piscivore") ||
    dietLower.includes("fish") ||
    summaryLower.includes("fish") ||
    summaryLower.includes("salmon") ||
    summaryLower.includes("marine") ||
    ["shark", "eagle", "penguin", "bear", "seal", "otter"].includes(typeLower)
  ) {
    types.push({ class: "piscivore", icon: "🐟", title: "Fish" });
  }

  if (
    dietLower.includes("insectivore") ||
    summaryLower.includes("insects") ||
    summaryLower.includes("bugs") ||
    summaryLower.includes("arthropods") ||
    ["frog", "bat", "spider", "lizard", "bird"].includes(typeLower)
  ) {
    types.push({ class: "insectivore", icon: "🐛", title: "Insects" });
  }

  if (
    dietLower.includes("omnivore") ||
    summaryLower.includes("varied diet") ||
    summaryLower.includes("both plants and animals") ||
    ["bear", "pig", "raccoon", "crow"].includes(typeLower)
  ) {
    types.push({ class: "omnivore", icon: "🍽️", title: "Omnivore" });
  }

  if (
    summaryLower.includes("nectar") ||
    summaryLower.includes("pollinator") ||
    ["butterfly", "bee", "hummingbird"].includes(typeLower)
  ) {
    types.push({ class: "nectarivore", icon: "🌸", title: "Nectar" });
  }

  if (
    summaryLower.includes("scavenger") ||
    summaryLower.includes("carrion") ||
    ["vulture", "hyena"].includes(typeLower)
  ) {
    types.push({ class: "scavenger", icon: "🦴", title: "Scavenger" });
  }

  // Fallback so there is always at least one badge
  if (types.length === 0) {
    if (dietLower.includes("carnivore")) {
      types.push({ class: "carnivore", icon: "🥩", title: "Carnivore" });
    } else if (dietLower.includes("herbivore")) {
      types.push({ class: "herbivore", icon: "🌿", title: "Herbivore" });
    } else {
      types.push({ class: "omnivore", icon: "🍽️", title: "Omnivore" });
    }
  }

  // De-duplicate by class while preserving order
  const seen = new Set<string>();
  return types.filter((t) => (seen.has(t.class) ? false : (seen.add(t.class), true)));
}

// ============================================
// Location coordinates for the world map fallback
// (percentage positions on the world.svg)
// ============================================
export const LOCATION_COORDINATES: Record<string, { x: number; y: number }> = {
  asia: { x: 75, y: 40 },
  china: { x: 78, y: 42 },
  india: { x: 72, y: 50 },
  russia: { x: 75, y: 25 },
  indonesia: { x: 80, y: 58 },
  "north america": { x: 25, y: 35 },
  america: { x: 25, y: 35 },
  "united states": { x: 23, y: 38 },
  usa: { x: 23, y: 38 },
  canada: { x: 25, y: 25 },
  alaska: { x: 15, y: 20 },
  "south america": { x: 30, y: 65 },
  africa: { x: 55, y: 55 },
  europe: { x: 55, y: 30 },
  australia: { x: 85, y: 75 },
  mexico: { x: 20, y: 45 },
  japan: { x: 88, y: 38 },
  korea: { x: 83, y: 40 },
  pacific: { x: 45, y: 60 },
  atlantic: { x: 40, y: 45 },
  "indian ocean": { x: 65, y: 60 },
  arctic: { x: 50, y: 10 },
  antarctica: { x: 50, y: 90 },
  brazil: { x: 32, y: 68 },
  argentina: { x: 30, y: 80 },
  egypt: { x: 58, y: 45 },
  "south africa": { x: 58, y: 75 },
  uk: { x: 50, y: 28 },
  france: { x: 52, y: 32 },
  germany: { x: 54, y: 30 },
  italy: { x: 55, y: 35 },
  spain: { x: 48, y: 38 },
  scandinavia: { x: 55, y: 20 },
  norway: { x: 54, y: 20 },
  sweden: { x: 56, y: 22 },
  finland: { x: 58, y: 20 },
  poland: { x: 57, y: 30 },
  turkey: { x: 60, y: 38 },
  iran: { x: 65, y: 40 },
  "saudi arabia": { x: 62, y: 45 },
  thailand: { x: 77, y: 50 },
  vietnam: { x: 79, y: 48 },
  philippines: { x: 83, y: 52 },
  "new zealand": { x: 90, y: 82 },
  "papua new guinea": { x: 87, y: 65 },
  madagascar: { x: 65, y: 70 },
  greenland: { x: 38, y: 15 },
  iceland: { x: 45, y: 18 },
  siberia: { x: 80, y: 25 },
  mongolia: { x: 80, y: 35 },
  tibet: { x: 75, y: 45 },
  alps: { x: 53, y: 33 },
  himalayas: { x: 73, y: 43 },
  andes: { x: 25, y: 70 },
  rockies: { x: 18, y: 35 },
  appalachian: { x: 24, y: 38 },
  nepal: { x: 73, y: 47 },
  bangladesh: { x: 74, y: 48 },
  "russian federation": { x: 75, y: 25 },
};

/** Resolve a single location string to map coordinates (or null). */
export function findLocationCoordinates(location: string): { x: number; y: number } | null {
  const loc = location.toLowerCase().trim();
  if (LOCATION_COORDINATES[loc]) return LOCATION_COORDINATES[loc];

  for (const key in LOCATION_COORDINATES) {
    if (loc.includes(key) || key.includes(loc)) {
      return LOCATION_COORDINATES[key];
    }
  }

  // Broad regional fallbacks
  if (loc.includes("asia") || loc.includes("east")) return LOCATION_COORDINATES["asia"];
  if (loc.includes("america") || loc.includes("usa") || loc.includes("united states")) {
    return LOCATION_COORDINATES["north america"];
  }
  if (loc.includes("europe")) return LOCATION_COORDINATES["europe"];
  if (loc.includes("africa")) return LOCATION_COORDINATES["africa"];
  if (loc.includes("australia") || loc.includes("oceania")) {
    return LOCATION_COORDINATES["australia"];
  }
  if (loc.includes("south") && !loc.includes("korea")) {
    return LOCATION_COORDINATES["south america"];
  }
  if (loc.includes("india")) return LOCATION_COORDINATES["india"];
  if (loc.includes("china")) return LOCATION_COORDINATES["china"];
  if (loc.includes("russia")) return LOCATION_COORDINATES["russia"];
  if (loc.includes("indonesia")) return LOCATION_COORDINATES["indonesia"];

  return null;
}

/** Parse a comma-separated locations string into unique map dots. */
export function getLocationDots(locationsString: string): {
  x: number;
  y: number;
  label: string;
}[] {
  const locations = locationsString.toLowerCase().split(",").map((l) => l.trim());
  const dots: { x: number; y: number; label: string }[] = [];
  const seen = new Set<string>();
  for (const location of locations) {
    const coords = findLocationCoordinates(location);
    if (coords) {
      const key = `${coords.x}-${coords.y}`;
      if (!seen.has(key)) {
        seen.add(key);
        dots.push({ ...coords, label: location });
      }
    }
  }
  return dots;
}

// ============================================
// Misc helpers
// ============================================
export function capitalizeFirst(str?: string): string {
  if (!str) return "";
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/** True when a value is present and meaningful (not empty/dash). */
export function hasValue(value: unknown): value is string {
  return (
    typeof value === "string" && value.trim() !== "" && value.trim() !== "-"
  );
}

/** Safely format a free-form stat string for display. */
export function displayValue(value?: string, fallback = "—"): string {
  return hasValue(value) ? value : fallback;
}

// ============================================
// Time period / evolutionary timeline helpers
//
// The bar visualises WHERE on the Ancient→Present timeline the
// species first appeared. A recently-evolved species (e.g. Tiger,
// ~3.7M years ago) appears near "Present", so its fill is long.
// An ancient lineage (e.g. sharks, ~450M years ago) appears near
// "Ancient", so its fill is short. This is the OPPOSITE of naive
// "older = wider" which incorrectly made ancient species fill more.
//
// Because ages span 1.4M–500M years (a ~350× range), a log scale is
// used so recent species are distinguishable rather than collapsing
// to a near-invisible sliver.
// ============================================

/** Parse the age (in millions of years) from a time_period record or its text. */
export function getAgeInMillionYears(animal: Animal): number | null {
  const tp = animal.time_period;
  if (!tp) return null;
  if (typeof tp.millions_years === "number" && tp.millions_years > 0) {
    return tp.millions_years;
  }
  // Fallback: parse from the text, e.g. "Evolved ~150 million years ago"
  const text = tp.text ?? "";
  const match = text.match(/(\d+(?:\.\d+)?)\s*(?:m|million)/i);
  return match ? Number(match[1]) : null;
}

// Precompute the age range across the whole dataset for normalisation.
const ALL_AGES: number[] = ANIMALS.map(getAgeInMillionYears).filter(
  (a): a is number => a !== null && a > 0,
);
const MAX_AGE = ALL_AGES.length ? Math.max(...ALL_AGES) : 500;
const MIN_AGE = ALL_AGES.length ? Math.min(...ALL_AGES) : 1;
const LOG_SPAN = Math.log(MAX_AGE) - Math.log(MIN_AGE) || 1;

export interface TimelineData {
  /** Display label, e.g. "~3.7 million years ago" */
  text: string;
  /** Fill width as a CSS percentage, e.g. "83%". Recent species → higher. */
  fillPercent: string;
  /** Left label (oldest bound) */
  start: string;
  /** Right label */
  end: string;
  /** Age in millions of years (for sorting / tooltips) */
  ageMillionYears: number | null;
}

/**
 * Compute the timeline display data for an animal.
 * fillPercent uses an inverted log scale: recent → fuller bar.
 */
export function getTimelineData(animal: Animal): TimelineData {
  const tp = animal.time_period;
  const age = getAgeInMillionYears(animal);

  let fillPercent = "50%";
  if (age !== null && age > 0) {
    if (age <= MIN_AGE) {
      fillPercent = "100%";
    } else if (age >= MAX_AGE) {
      fillPercent = "4%"; // small floor so the bar stays visible
    } else {
      // Inverted log scale: closer to Present (small age) → higher fill
      const ratio = (Math.log(MAX_AGE) - Math.log(age)) / LOG_SPAN;
      const pct = Math.max(4, Math.min(100, Math.round(ratio * 100)));
      fillPercent = `${pct}%`;
    }
  } else if (tp?.width) {
    // Last-resort fallback to the extractor's width (only if no age at all)
    fillPercent = tp.width;
  }

  return {
    text: tp?.text ?? "Evolutionary history unknown",
    fillPercent,
    start: `${Math.round(MAX_AGE)}M years ago`,
    end: tp?.end ?? "Present",
    ageMillionYears: age,
  };
}
