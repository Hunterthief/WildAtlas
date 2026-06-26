// ============================================
// WildAtlas - Type Definitions
// Typed model for the animal encyclopedia data
// (originally produced by the Python data generator
// from Wikipedia, Wikidata, iNaturalist, IUCN, GBIF, EOL)
// ============================================

export interface CommonName {
  name: string;
  language: string;
}

export interface TimePeriod {
  text: string;
  width: string;
  start: string;
  end?: string;
  millions_years?: number;
  confidence?: number;
  raw_match?: string;
}

export interface Classification {
  kingdom?: string;
  phylum?: string;
  class?: string;
  order?: string;
  family?: string;
  genus?: string;
  species?: string;
}

export interface PhysicalStats {
  weight?: string;
  length?: string;
  height?: string;
  top_speed?: string;
  lifespan?: string;
}

export interface EcologyStats {
  diet?: string;
  habitat?: string;
  locations?: string;
  group_behavior?: string;
  conservation_status?: string;
  biggest_threat?: string;
  distinctive_features?: string[];
  population_trend?: string;
}

export interface ReproductionStats {
  gestation_period?: string;
  average_litter_size?: string;
  name_of_young?: string;
}

export interface AdditionalInfo {
  lifestyle?: string;
  color?: string;
  skin_type?: string;
  prey?: string;
  slogan?: string;
  group?: string;
  number_of_species?: string;
  estimated_population_size?: string;
  most_distinctive_feature?: string;
}

export interface DistributionCoordinates {
  min_lat?: number;
  max_lat?: number;
  min_lon?: number;
  max_lon?: number;
  count?: number;
}

export interface Distribution {
  countries?: string[];
  coordinates?: DistributionCoordinates;
  occurrence_count?: number;
}

/** Rich, Wikipedia-sourced article sections. */
export interface ArticleContent {
  overview?: string;
  description?: string;
  habitat?: string;
  behavior?: string;
  conservation?: string;
}

/** A generated FAQ with a grounded answer. */
export interface FaqEntry {
  id: string;
  question: string;
  answer: string;
}

export interface Animal {
  id: string;
  name: string;
  scientific_name: string;
  common_names?: CommonName[];
  summary?: string;
  description?: string;
  image?: string;
  images?: string[];
  distribution_image?: string;
  time_period?: TimePeriod;
  wikipedia_url?: string;
  wikidata_url?: string;
  eol_url?: string;
  classification?: Classification;
  animal_type?: string;
  young_name?: string;
  group_name?: string;
  physical?: PhysicalStats;
  ecology?: EcologyStats;
  reproduction?: ReproductionStats;
  additional_info?: AdditionalInfo;
  distribution?: Distribution;
  /** Rich, Wikipedia-sourced article sections (overview/description/habitat/behavior/conservation). */
  article?: ArticleContent;
  /** Generated FAQ entries with grounded answers. */
  faqs?: FaqEntry[];
  sources?: string[];
  last_updated?: string;
}

// Lightweight summary used for list/card views & comparison selectors
export interface AnimalSummary {
  id: string;
  name: string;
  scientific_name: string;
  image?: string;
  animal_type?: string;
  classification?: Classification;
  type: AnimalType;
}

// The six top-level groups shown on the encyclopedia home page
export const ANIMAL_TYPES = [
  "mammal",
  "bird",
  "reptile",
  "fish",
  "amphibian",
  "insect",
] as const;

export type AnimalType = (typeof ANIMAL_TYPES)[number];

export interface TypeSectionMeta {
  type: AnimalType;
  label: string;
  icon: string;
}

export const TYPE_SECTIONS: TypeSectionMeta[] = [
  { type: "mammal", label: "Mammals", icon: "🦁" },
  { type: "bird", label: "Birds", icon: "🦅" },
  { type: "reptile", label: "Reptiles", icon: "🐍" },
  { type: "fish", label: "Fish", icon: "🦈" },
  { type: "amphibian", label: "Amphibians", icon: "🐸" },
  { type: "insect", label: "Insects", icon: "🦋" },
];

// Conservation status buckets (IUCN-aligned) used for colour coding
export type ConservationLevel =
  | "least-concern"
  | "near-threatened"
  | "vulnerable"
  | "endangered"
  | "critically-endangered"
  | "extinct"
  | "unknown";

// Diet classification used for the diet icon badges
export interface DietType {
  class: string;
  icon: string;
  title: string;
}
