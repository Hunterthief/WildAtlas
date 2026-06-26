// ============================================
// WildAtlas - Article & FAQ text generators
// Pure functions that turn structured animal data
// into readable prose for the detail page.
// (Ported & cleaned up from the original script.js,
//  fixing the double-lowercase bug and dead branches.)
// ============================================

import type { Animal } from "./types";
import { displayValue, hasValue } from "./animals";

// ---------- Article section generators ----------

export function generateDescriptionText(animal: Animal): string {
  const phys = animal.physical ?? {};
  const eco = animal.ecology ?? {};
  const summary = animal.summary ?? animal.description ?? "";
  const parts: string[] = [];

  let desc = `${animal.name} is a ${animal.animal_type ?? "animal"}`;
  if (hasValue(eco.diet)) {
    desc += ` and a ${eco.diet!.toLowerCase()}`;
  }
  desc += ".";
  parts.push(desc);

  const sizeParts: string[] = [];
  if (hasValue(phys.length)) sizeParts.push(`length of ${phys.length}`);
  if (hasValue(phys.height)) sizeParts.push(`height of ${phys.height}`);
  if (hasValue(phys.weight)) sizeParts.push(`weight of ${phys.weight}`);
  if (sizeParts.length > 0) {
    parts.push(`It has a ${sizeParts.join(", ")}.`);
  }

  if (eco.distinctive_features && eco.distinctive_features.length > 0) {
    const features = eco.distinctive_features.slice(0, 3).join(", ").toLowerCase();
    parts.push(`The most distinctive features include ${features}.`);
  }

  if (summary) {
    const sentences = summary.split(".").map((s) => s.trim()).filter(Boolean);
    if (sentences.length > 0) {
      parts.push(`${sentences[0]}.`);
    }
  }

  return parts.join(" ");
}

export function generateHabitatText(animal: Animal): string {
  const eco = animal.ecology ?? {};
  const parts: string[] = [];

  if (hasValue(eco.locations)) {
    parts.push(`${animal.name} is found in ${eco.locations!.toLowerCase()}.`);
  }
  if (hasValue(eco.habitat)) {
    parts.push(`It inhabits ${eco.habitat!.toLowerCase()} environments.`);
  }
  if (hasValue(eco.group_behavior)) {
    const behavior = eco.group_behavior!.toLowerCase();
    parts.push(
      behavior === "social"
        ? "This species is social and lives in groups."
        : `This species is typically ${behavior}.`,
    );
  }

  return parts.join(" ") || "Habitat information is not available for this species.";
}

export function generateBehaviorText(animal: Animal): string {
  const eco = animal.ecology ?? {};
  const phys = animal.physical ?? {};
  const summary = animal.summary ?? animal.description ?? "";
  const parts: string[] = [];

  if (hasValue(eco.diet)) {
    const diet = eco.diet!.toLowerCase();
    const lower = animal.name.toLowerCase();
    if (diet === "carnivore") {
      parts.push(`As a carnivore, ${lower} hunts and feeds on other animals.`);
    } else if (diet === "herbivore") {
      parts.push(`As a herbivore, ${lower} feeds primarily on plants and vegetation.`);
    } else if (diet === "omnivore") {
      parts.push(`As an omnivore, ${lower} has a varied diet including both plants and animals.`);
    }
  }

  if (hasValue(phys.top_speed)) {
    parts.push(`It can reach speeds of up to ${phys.top_speed}.`);
  }

  if (hasValue(eco.group_behavior)) {
    const behavior = eco.group_behavior!.toLowerCase();
    if (
      behavior.includes("social") ||
      behavior.includes("herd") ||
      behavior.includes("pack") ||
      behavior.includes("colony") ||
      behavior.includes("flock") ||
      behavior.includes("school")
    ) {
      parts.push("These animals are social and often live in family groups or herds.");
    } else if (behavior.includes("solitary")) {
      parts.push("They are typically solitary animals, coming together only for mating.");
    }
  }

  if (summary) {
    const behaviorKeywords = ["hunt", "feed", "live", "behavior", "social", "group", "solitary"];
    for (const sentence of summary.split(".")) {
      const trimmed = sentence.trim();
      if (trimmed && behaviorKeywords.some((k) => trimmed.toLowerCase().includes(k))) {
        parts.push(`${trimmed}.`);
        break;
      }
    }
  }

  return parts.join(" ") || "Behavioral information is not available for this species.";
}

export function generateConservationText(animal: Animal): string {
  const eco = animal.ecology ?? {};
  const parts: string[] = [];

  if (hasValue(eco.conservation_status)) {
    const status = eco.conservation_status!.toLowerCase();
    parts.push(`${animal.name} is classified as ${status}.`);

    if (status.includes("endangered") || status.includes("critically")) {
      parts.push("This means the species faces a very high risk of extinction in the wild.");
    } else if (status.includes("vulnerable")) {
      parts.push("This means the species faces a high risk of extinction in the wild.");
    } else if (status.includes("least concern")) {
      parts.push("This means the species is widespread and abundant.");
    }
  }

  if (hasValue(eco.biggest_threat)) {
    parts.push(`The biggest threats include ${eco.biggest_threat!.toLowerCase()}.`);
  }

  return parts.join(" ") || "Conservation information is not available for this species.";
}

// ---------- FAQ generators ----------

export function generateDietFAQ(animal: Animal): string {
  const eco = animal.ecology ?? {};
  if (hasValue(eco.diet)) {
    let answer = `${animal.name} is a ${eco.diet!.toLowerCase()}.`;
    if (eco.diet === "Carnivore") answer += " It feeds on other animals.";
    else if (eco.diet === "Herbivore")
      answer += " It feeds primarily on plants and vegetation.";
    else if (eco.diet === "Omnivore")
      answer += " It has a varied diet including both plants and animals.";
    return answer;
  }
  return "Diet information is not available for this species.";
}

export function generateHabitatFAQ(animal: Animal): string {
  const eco = animal.ecology ?? {};
  if (hasValue(eco.locations) || hasValue(eco.habitat)) {
    let answer = "";
    if (hasValue(eco.locations)) {
      answer += `${animal.name} is found in ${eco.locations!.toLowerCase()}. `;
    }
    if (hasValue(eco.habitat)) {
      answer += `It inhabits ${eco.habitat!.toLowerCase()} environments.`;
    }
    return answer.trim();
  }
  return "Habitat information is not available for this species.";
}

export function generateSizeFAQ(animal: Animal): string {
  const phys = animal.physical ?? {};
  const parts: string[] = [];
  if (hasValue(phys.length)) parts.push(`${phys.length} long`);
  if (hasValue(phys.height)) parts.push(`${phys.height} tall`);
  if (hasValue(phys.weight)) parts.push(`weighs ${phys.weight}`);
  if (parts.length > 0) return `${animal.name} is ${parts.join(", ")}.`;
  return "Size information is not available for this species.";
}

export function generateConservationFAQ(animal: Animal): string {
  const eco = animal.ecology ?? {};
  if (hasValue(eco.conservation_status)) {
    let answer = `${animal.name} is classified as ${eco.conservation_status!.toLowerCase()}.`;
    if (hasValue(eco.biggest_threat)) {
      answer += ` The biggest threats include ${eco.biggest_threat!.toLowerCase()}.`;
    }
    return answer;
  }
  return "Conservation status information is not available for this species.";
}

export function generateLifespanFAQ(animal: Animal): string {
  const phys = animal.physical ?? {};
  if (hasValue(phys.lifespan)) {
    return `${animal.name} can live for ${phys.lifespan!.toLowerCase()}.`;
  }
  return "Lifespan information is not available for this species.";
}

export function generateFeaturesFAQ(animal: Animal): string {
  const eco = animal.ecology ?? {};
  if (eco.distinctive_features && eco.distinctive_features.length > 0) {
    const features = eco.distinctive_features.join(", ").toLowerCase();
    return `The most distinctive features of ${animal.name.toLowerCase()} include ${features}.`;
  }
  return "Distinctive feature information is not available for this species.";
}

export function generateDangerFAQ(animal: Animal): string {
  const animalType = animal.animal_type?.toLowerCase() ?? "";
  const dangerousTypes = ["feline", "canine", "bear", "shark", "snake", "crocodile", "raptor"];
  if (dangerousTypes.includes(animalType)) {
    return `${animal.name} can be dangerous to humans if threatened or provoked. It is best to observe from a safe distance and never approach wild animals.`;
  }
  return `${animal.name} is generally not dangerous to humans, but like all wild animals, should be observed from a safe distance.`;
}

export function generateReproductionFAQ(animal: Animal): string {
  const repro = animal.reproduction ?? {};
  const parts: string[] = [];
  if (hasValue(repro.gestation_period)) {
    parts.push(`gestation period of ${repro.gestation_period!.toLowerCase()}`);
  }
  if (hasValue(repro.average_litter_size)) {
    parts.push(`typically has ${repro.average_litter_size} offspring`);
  }
  if (hasValue(repro.name_of_young)) {
    parts.push(`young are called ${repro.name_of_young!.toLowerCase()}`);
  }
  if (parts.length > 0) return `${animal.name} has a ${parts.join(", ")}.`;
  return "Reproduction information is not available for this species.";
}

export interface FaqItem {
  id: string;
  question: string;
  answer: string;
}

/** Build the full FAQ list for an animal.
 *  Prefers the Wikipedia-grounded `faqs` from the dataset, falling back to
 *  the generated answers when a stored FAQ is missing or empty. */
export function buildFaqList(animal: Animal): FaqItem[] {
  const lowerName = animal.name.toLowerCase();
  const stored = new Map((animal.faqs ?? []).map((f) => [f.id, f]));

  const fallbacks: Record<string, { question: string; answer: string }> = {
    diet: { question: `What does the ${lowerName} eat?`, answer: generateDietFAQ(animal) },
    habitat: { question: `Where does the ${lowerName} live?`, answer: generateHabitatFAQ(animal) },
    size: { question: `How big does the ${lowerName} get?`, answer: generateSizeFAQ(animal) },
    conservation: { question: `What is the conservation status of the ${lowerName}?`, answer: generateConservationFAQ(animal) },
    lifespan: { question: `How long does the ${lowerName} live?`, answer: generateLifespanFAQ(animal) },
    features: { question: `What makes the ${lowerName} unique?`, answer: generateFeaturesFAQ(animal) },
    danger: { question: `Is the ${lowerName} dangerous to humans?`, answer: generateDangerFAQ(animal) },
    reproduction: { question: `How does the ${lowerName} reproduce?`, answer: generateReproductionFAQ(animal) },
  };

  const order = ["diet", "habitat", "size", "conservation", "lifespan", "features", "danger", "reproduction"];
  return order.map((id) => {
    const s = stored.get(id);
    const fb = fallbacks[id];
    // Use the stored answer when it's non-empty, otherwise fall back
    if (s && s.answer && s.answer.trim()) {
      return { id, question: s.question || fb.question, answer: s.answer };
    }
    return { id, question: fb.question, answer: fb.answer };
  });
}

/** Convenience: the five article section bodies for the detail page.
 *  Prefers the Wikipedia-grounded `article` fields from the dataset,
 *  falling back to the generated prose when a section is missing. */
export function buildArticleSections(animal: Animal) {
  const article = animal.article ?? {};
  const summary = animal.summary ?? animal.description ?? "";
  return [
    {
      id: "overview",
      title: "Overview",
      text:
        (article.overview && article.overview.trim()) ||
        displayValue(summary, "No description available.") ||
        "No description available for this species.",
    },
    {
      id: "description",
      title: "Description",
      text: (article.description && article.description.trim()) || generateDescriptionText(animal),
    },
    {
      id: "habitat",
      title: "Habitat & Distribution",
      text: (article.habitat && article.habitat.trim()) || generateHabitatText(animal),
    },
    {
      id: "behavior",
      title: "Behavior & Ecology",
      text: (article.behavior && article.behavior.trim()) || generateBehaviorText(animal),
    },
    {
      id: "conservation",
      title: "Conservation",
      text: (article.conservation && article.conservation.trim()) || generateConservationText(animal),
    },
  ];
}
