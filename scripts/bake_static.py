#!/usr/bin/env python3
"""Bakes the static catalog JSON for GitHub Pages.
Contains:
  - 13 curated animals with FULL data (from src/data/animals.json)
  - 94 catalog entries with just name/type/wikipediaTitle (fetched client-side on demand)
"""
import json, os, re

CURATED_FILE = "src/data/animals.json"
OUTPUT = "public/animals-data.json"

# Read curated catalog for type info
with open("src/lib/curated-catalog.ts") as f:
    content = f.read()
catalog_entries = re.findall(
    r'\{\s*name:\s*"([^"]+)"\s*,\s*wikipediaTitle:\s*"([^"]+)"\s*,\s*type:\s*"(\w+)"\s*\}',
    content
)

TYPE_KEYWORDS = {
    "mammal": ["mammal","mammalia","feline","canine","bear","elephant","primate","whale","deer","bovine","equine","rabbit","rodent","bat","giraffe","cheetah"],
    "bird": ["bird","aves","raptor","owl","penguin","chicken","duck","goose","swan","eagle"],
    "reptile": ["reptile","reptilia","snake","lizard","turtle","crocodile"],
    "fish": ["fish","shark","ray","salmon"],
    "amphibian": ["amphibian","amphibia","frog","salamander"],
    "insect": ["insect","insecta","butterfly","bee","ant","spider","crab"],
}

def classify(animal):
    at = (animal.get("animal_type") or "").lower()
    ct = (animal.get("classification") or {}).get("class", "").lower()
    for type_, keywords in TYPE_KEYWORDS.items():
        if any(k in at or k in ct for k in keywords):
            return type_
    return "mammal"

# Load curated animals (13 featured, with full data)
curated = json.load(open(CURATED_FILE))
curated_names = {a["name"].lower() for a in curated}

all_animals = []
for a in curated:
    entry = dict(a)
    entry["featured"] = True
    entry["type"] = classify(a)
    entry["wikipediaTitle"] = a.get("name", "")
    all_animals.append(entry)

# Add catalog entries (non-featured, lightweight)
for name, wiki_title, type_ in catalog_entries:
    if name.lower() in curated_names:
        continue
    all_animals.append({
        "id": f"cat:{wiki_title}",
        "name": name,
        "scientific_name": "",
        "featured": False,
        "type": type_,
        "wikipediaTitle": wiki_title,
        "image": "",
    })

# Write the static JSON
os.makedirs("public", exist_ok=True)
json.dump({"count": len(all_animals), "animals": all_animals},
          open(OUTPUT, "w"), indent=2, ensure_ascii=False)

print(f"Baked {len(all_animals)} animals to {OUTPUT}")
print(f"  Featured (full data): {len(curated)}")
print(f"  Catalog (client-side fetch): {len(all_animals) - len(curated)}")
