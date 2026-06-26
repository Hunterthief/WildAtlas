// ============================================
// WildAtlas - Curated Starter Catalog
//
// A hand-picked list of ~100 well-known animal species
// across the six encyclopedia sections. This gives users an
// instant browsable catalog without any API calls. For anything
// NOT in this list, the live Wikipedia search lets users find
// any animal article on Wikipedia, and the detail page fetches
// it on demand (cached to the filesystem).
//
// Each entry is lightweight: a display name + the English
// Wikipedia article title (usually identical to the name).
// ============================================

export interface CatalogEntry {
  /** Display name (common name) */
  name: string;
  /** English Wikipedia article title */
  wikipediaTitle: string;
  /** Encyclopedia section */
  type: "mammal" | "bird" | "reptile" | "fish" | "amphibian" | "insect";
}

export const CURATED_CATALOG: CatalogEntry[] = [
  // ----- Mammals -----
  { name: "Lion", wikipediaTitle: "Lion", type: "mammal" },
  { name: "Tiger", wikipediaTitle: "Tiger", type: "mammal" },
  { name: "Cheetah", wikipediaTitle: "Cheetah", type: "mammal" },
  { name: "Leopard", wikipediaTitle: "Leopard", type: "mammal" },
  { name: "Jaguar", wikipediaTitle: "Jaguar", type: "mammal" },
  { name: "Snow leopard", wikipediaTitle: "Snow leopard", type: "mammal" },
  { name: "African elephant", wikipediaTitle: "African bush elephant", type: "mammal" },
  { name: "Asian elephant", wikipediaTitle: "Asian elephant", type: "mammal" },
  { name: "Gray wolf", wikipediaTitle: "Wolf", type: "mammal" },
  { name: "Brown bear", wikipediaTitle: "Brown bear", type: "mammal" },
  { name: "Polar bear", wikipediaTitle: "Polar bear", type: "mammal" },
  { name: "Giant panda", wikipediaTitle: "Giant panda", type: "mammal" },
  { name: "Red fox", wikipediaTitle: "Red fox", type: "mammal" },
  { name: "Koala", wikipediaTitle: "Koala", type: "mammal" },
  { name: "Red kangaroo", wikipediaTitle: "Red kangaroo", type: "mammal" },
  { name: "Giraffe", wikipediaTitle: "Giraffe", type: "mammal" },
  { name: "Plains zebra", wikipediaTitle: "Plains zebra", type: "mammal" },
  { name: "Hippopotamus", wikipediaTitle: "Hippopotamus", type: "mammal" },
  { name: "White rhinoceros", wikipediaTitle: "White rhinoceros", type: "mammal" },
  { name: "Western gorilla", wikipediaTitle: "Western gorilla", type: "mammal" },
  { name: "Chimpanzee", wikipediaTitle: "Chimpanzee", type: "mammal" },
  { name: "Orangutan", wikipediaTitle: "Orangutan", type: "mammal" },
  { name: "Horse", wikipediaTitle: "Horse", type: "mammal" },
  { name: "Cattle", wikipediaTitle: "Cattle", type: "mammal" },
  { name: "Domestic pig", wikipediaTitle: "Domestic pig", type: "mammal" },
  { name: "Domestic rabbit", wikipediaTitle: "European rabbit", type: "mammal" },
  { name: "Eastern gray squirrel", wikipediaTitle: "Eastern gray squirrel", type: "mammal" },
  { name: "Blue whale", wikipediaTitle: "Blue whale", type: "mammal" },
  { name: "Humpback whale", wikipediaTitle: "Humpback whale", type: "mammal" },
  { name: "Killer whale", wikipediaTitle: "Killer whale", type: "mammal" },
  { name: "Sperm whale", wikipediaTitle: "Sperm whale", type: "mammal" },
  { name: "Bottlenose dolphin", wikipediaTitle: "Common bottlenose dolphin", type: "mammal" },

  // ----- Birds -----
  { name: "Bald eagle", wikipediaTitle: "Bald eagle", type: "bird" },
  { name: "Golden eagle", wikipediaTitle: "Golden eagle", type: "bird" },
  { name: "Peregrine falcon", wikipediaTitle: "Peregrine falcon", type: "bird" },
  { name: "Red-tailed hawk", wikipediaTitle: "Red-tailed hawk", type: "bird" },
  { name: "Barn owl", wikipediaTitle: "Barn owl", type: "bird" },
  { name: "Snowy owl", wikipediaTitle: "Snowy owl", type: "bird" },
  { name: "American flamingo", wikipediaTitle: "American flamingo", type: "bird" },
  { name: "Indian peafowl", wikipediaTitle: "Indian peafowl", type: "bird" },
  { name: "Common ostrich", wikipediaTitle: "Common ostrich", type: "bird" },
  { name: "Emu", wikipediaTitle: "Emu", type: "bird" },
  { name: "Emperor penguin", wikipediaTitle: "Emperor penguin", type: "bird" },
  { name: "King penguin", wikipediaTitle: "King penguin", type: "bird" },
  { name: "Mute swan", wikipediaTitle: "Mute swan", type: "bird" },
  { name: "Canada goose", wikipediaTitle: "Canada goose", type: "bird" },
  { name: "Mallard", wikipediaTitle: "Mallard", type: "bird" },
  { name: "Chicken", wikipediaTitle: "Chicken", type: "bird" },
  { name: "Wild turkey", wikipediaTitle: "Wild turkey", type: "bird" },
  { name: "Rock dove", wikipediaTitle: "Rock dove", type: "bird" },
  { name: "American crow", wikipediaTitle: "American crow", type: "bird" },
  { name: "Common raven", wikipediaTitle: "Common raven", type: "bird" },
  { name: "Scarlet macaw", wikipediaTitle: "Scarlet macaw", type: "bird" },
  { name: "Ruby-throated hummingbird", wikipediaTitle: "Ruby-throated hummingbird", type: "bird" },

  // ----- Reptiles -----
  { name: "King cobra", wikipediaTitle: "King cobra", type: "reptile" },
  { name: "Reticulated python", wikipediaTitle: "Reticulated python", type: "reptile" },
  { name: "Western diamondback rattlesnake", wikipediaTitle: "Western diamondback rattlesnake", type: "reptile" },
  { name: "Black mamba", wikipediaTitle: "Black mamba", type: "reptile" },
  { name: "Komodo dragon", wikipediaTitle: "Komodo dragon", type: "reptile" },
  { name: "Marine iguana", wikipediaTitle: "Marine iguana", type: "reptile" },
  { name: "Veiled chameleon", wikipediaTitle: "Veiled chameleon", type: "reptile" },
  { name: "Green sea turtle", wikipediaTitle: "Green sea turtle", type: "reptile" },
  { name: "Loggerhead sea turtle", wikipediaTitle: "Loggerhead sea turtle", type: "reptile" },
  { name: "Leatherback sea turtle", wikipediaTitle: "Leatherback sea turtle", type: "reptile" },
  { name: "Galapagos giant tortoise", wikipediaTitle: "Galápagos giant tortoise", type: "reptile" },
  { name: "Nile crocodile", wikipediaTitle: "Nile crocodile", type: "reptile" },
  { name: "Saltwater crocodile", wikipediaTitle: "Saltwater crocodile", type: "reptile" },
  { name: "American alligator", wikipediaTitle: "American alligator", type: "reptile" },

  // ----- Fish -----
  { name: "Great white shark", wikipediaTitle: "Great white shark", type: "fish" },
  { name: "Hammerhead shark", wikipediaTitle: "Great hammerhead", type: "fish" },
  { name: "Tiger shark", wikipediaTitle: "Tiger shark", type: "fish" },
  { name: "Whale shark", wikipediaTitle: "Whale shark", type: "fish" },
  { name: "Atlantic salmon", wikipediaTitle: "Atlantic salmon", type: "fish" },
  { name: "Atlantic cod", wikipediaTitle: "Atlantic cod", type: "fish" },
  { name: "Ocellaris clownfish", wikipediaTitle: "Ocellaris clownfish", type: "fish" },
  { name: "Anglerfish", wikipediaTitle: "Anglerfish", type: "fish" },
  { name: "Swordfish", wikipediaTitle: "Swordfish", type: "fish" },
  { name: "Blue marlin", wikipediaTitle: "Blue marlin", type: "fish" },
  { name: "European eel", wikipediaTitle: "European eel", type: "fish" },
  { name: "Great seahorse", wikipediaTitle: "Seahorse", type: "fish" },
  { name: "Pufferfish", wikipediaTitle: "Tetraodontidae", type: "fish" },
  { name: "Red-bellied piranha", wikipediaTitle: "Red-bellied piranha", type: "fish" },
  { name: "Goldfish", wikipediaTitle: "Goldfish", type: "fish" },

  // ----- Amphibians -----
  { name: "American bullfrog", wikipediaTitle: "American bullfrog", type: "amphibian" },
  { name: "Blue poison dart frog", wikipediaTitle: "Blue poison dart frog", type: "amphibian" },
  { name: "Golden poison frog", wikipediaTitle: "Golden poison frog", type: "amphibian" },
  { name: "European tree frog", wikipediaTitle: "European tree frog", type: "amphibian" },
  { name: "Fire salamander", wikipediaTitle: "Fire salamander", type: "amphibian" },
  { name: "Eastern newt", wikipediaTitle: "Eastern newt", type: "amphibian" },
  { name: "Axolotl", wikipediaTitle: "Axolotl", type: "amphibian" },
  { name: "Common toad", wikipediaTitle: "Common toad", type: "amphibian" },

  // ----- Insects & arthropods -----
  { name: "Monarch butterfly", wikipediaTitle: "Monarch butterfly", type: "insect" },
  { name: "Western honey bee", wikipediaTitle: "Western honey bee", type: "insect" },
  { name: "Buff-tailed bumblebee", wikipediaTitle: "Buff-tailed bumblebee", type: "insect" },
  { name: "Western carpenter ant", wikipediaTitle: "Black carpenter ant", type: "insect" },
  { name: "Termite", wikipediaTitle: "Termite", type: "insect" },
  { name: "Common dragonfly", wikipediaTitle: "Anax imperator", type: "insect" },
  { name: "Migratory locust", wikipediaTitle: "Migratory locust", type: "insect" },
  { name: "House cricket", wikipediaTitle: "House cricket", type: "insect" },
  { name: "Seven-spot ladybird", wikipediaTitle: "Coccinella septempunctata", type: "insect" },
  { name: "Common firefly", wikipediaTitle: "Photinus pyralis", type: "insect" },
  { name: "Yellow fever mosquito", wikipediaTitle: "Aedes aegypti", type: "insect" },
  { name: "Housefly", wikipediaTitle: "Housefly", type: "insect" },
  { name: "Japanese rhinoceros beetle", wikipediaTitle: "Japanese rhinoceros beetle", type: "insect" },
  { name: "Atlas moth", wikipediaTitle: "Atlas moth", type: "insect" },
  { name: "European mantis", wikipediaTitle: "Mantis religiosa", type: "insect" },
];
