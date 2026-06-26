#!/usr/bin/env python3
"""Bakes ALL animal data (curated + enriched cache) into a single static JSON
file at public/animals-data.json for GitHub Pages deployment.
Each animal gets its FULL enriched data (scientific name, classification,
physical stats, ecology, reproduction, article sections, etc.)."""
import json, os, re

CURATED_FILE = "src/data/animals.json"
CACHE_DIR = "data/cache/wikipedia"
OUTPUT = "public/animals-data.json"

# Read curated catalog for type info
with open("src/lib/curated-catalog.ts") as f:
    content = f.read()
catalog_entries = re.findall(
    r'\{\s*name:\s*"([^"]+)"\s*,\s*wikipediaTitle:\s*"([^"]+)"\s*,\s*type:\s*"(\w+)"\s*\}',
    content
)
catalog_map = {name: {"wikipediaTitle": title, "type": t} for name, title, t in catalog_entries}

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

# Load ALL cached animals (enriched with Wikipedia + LLM data)
seen_names = {a["name"].lower() for a in all_animals}
for fn in sorted(os.listdir(CACHE_DIR)):
    if not fn.endswith(".json"):
        continue
    a = json.load(open(os.path.join(CACHE_DIR, fn)))
    name = a.get("name", "")
    if not name or name.lower() in seen_names:
        continue
    seen_names.add(name.lower())
    entry = dict(a)
    entry["featured"] = False
    cat_info = catalog_map.get(name, {})
    entry["type"] = cat_info.get("type") or classify(a)
    entry["wikipediaTitle"] = cat_info.get("wikipediaTitle") or name
    all_animals.append(entry)

# Write the static JSON
os.makedirs("public", exist_ok=True)
json.dump({"count": len(all_animals), "animals": all_animals},
          open(OUTPUT, "w"), indent=2, ensure_ascii=False)

# Stats
full = sum(1 for a in all_animals if a.get("scientific_name", "").strip() and (a.get("classification") or {}).get("class", "").strip())
has_text = sum(1 for a in all_animals if (a.get("summary", "") or (a.get("article") or {}).get("overview", "")).strip())
print(f"Baked {len(all_animals)} animals to {OUTPUT}")
print(f"  Full data (sci name + classification): {full}/{len(all_animals)}")
print(f"  Has Wikipedia text: {has_text}/{len(all_animals)}")
