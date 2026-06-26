#!/usr/bin/env python3
"""Re-enrich animals that still lack classification. Uses a simpler, more
focused prompt that asks ONLY for the missing fields."""
import json, os, re, subprocess, time, sys

CACHE_DIR = "data/cache/wikipedia"

def slugify(name):
    return ''.join(c if c.isalnum() else '-' for c in name.lower()).strip('-')

def llm_extract_focused(name, text, sci_name=""):
    """Simpler prompt focused on getting complete classification + stats."""
    prompt = f"""Extract structured data about the animal "{name}" from this Wikipedia text. The scientific name is "{sci_name}".

Return ONLY a JSON object (no markdown, no explanation) with ALL of these fields filled from the text:
{{
  "scientific_name": "{sci_name}",
  "classification": {{
    "kingdom": "Animalia",
    "phylum": "",
    "class": "",
    "order": "",
    "family": "",
    "genus": "",
    "species": ""
  }},
  "physical": {{
    "length": "",
    "height": "",
    "weight": "",
    "top_speed": "",
    "lifespan": ""
  }},
  "ecology": {{
    "diet": "",
    "habitat": "",
    "conservation_status": "",
    "locations": ""
  }},
  "reproduction": {{
    "gestation_period": "",
    "average_litter_size": "",
    "name_of_young": ""
  }},
  "young_name": "",
  "group_name": ""
}}

IMPORTANT: 
- Fill kingdom as "Animalia" for all animals.
- For the class, use: Mammalia (mammals), Aves (birds), Reptilia (reptiles), Actinopterygii/Chondrichthyes (fish), Amphibia (amphibians), Insecta (insects).
- Extract phylum, order, family, genus, species from the text if mentioned.
- Extract physical stats (length, weight, speed, lifespan) with units.
- diet must be one of: Carnivore, Herbivore, Omnivore, Piscivore, Insectivore, Nectarivore, Scavenger, Filter feeder
- conservation_status must be one of: Least Concern, Near Threatened, Vulnerable, Endangered, Critically Endangered, Extinct in the Wild, Extinct, Data Deficient
- Leave blank only if truly not in the text.

Text:
{text[:4000]}"""

    for attempt in range(3):
        try:
            result = subprocess.run(["z-ai", "chat", "-p", prompt], capture_output=True, text=True, timeout=30)
            m = re.search(r'\{[\s\S]*"choices"[\s\S]*\}', result.stdout)
            if not m:
                time.sleep(5)
                continue
            resp = json.loads(m.group(0))
            content = resp["choices"][0]["message"]["content"]
            content = re.sub(r'^```(?:json)?\s*', '', content.strip())
            content = re.sub(r'\s*```$', '', content)
            try:
                return json.loads(content)
            except:
                m2 = re.search(r'\{[\s\S]*\}', content)
                return json.loads(m2.group(0)) if m2 else {}
        except:
            time.sleep(3)
    return {}

def merge(animal, extracted):
    if not extracted: return animal
    if extracted.get("scientific_name", "").strip():
        animal["scientific_name"] = extracted["scientific_name"].strip()
    if extracted.get("young_name", "").strip():
        animal["young_name"] = extracted["young_name"].strip()
    if extracted.get("group_name", "").strip():
        animal["group_name"] = extracted["group_name"].strip()
    for section in ["physical", "ecology", "classification", "reproduction"]:
        if extracted.get(section):
            animal[section] = {**(animal.get(section) or {})}
            for k, v in extracted[section].items():
                if isinstance(v, str) and v.strip():
                    animal[section][k] = v
                elif isinstance(v, list) and v:
                    animal[section][k] = v
    return animal

# Process all animals that lack classification.class
processed = 0
for fn in sorted(os.listdir(CACHE_DIR)):
    if not fn.endswith('.json'): continue
    cache_file = os.path.join(CACHE_DIR, fn)
    animal = json.load(open(cache_file))

    has_class = bool((animal.get("classification") or {}).get("class", "").strip())
    if has_class:
        continue  # already has classification

    name = animal.get("name", "")
    sci = animal.get("scientific_name", "")

    # Build text blob
    art = animal.get("article") or {}
    blob = [animal.get("summary", ""), art.get("overview", ""), art.get("description", ""),
            art.get("habitat", ""), art.get("behavior", ""), art.get("conservation", "")]
    text = "\n\n".join(p for p in blob if p)[:4000]

    if not text.strip():
        continue

    print(f"[{processed+1}] {name}...", end=" ", flush=True)
    extracted = llm_extract_focused(name, text, sci)
    animal = merge(animal, extracted)
    json.dump(animal, open(cache_file, "w"), indent=2, ensure_ascii=False)

    cls = (animal.get("classification") or {}).get("class", "?")
    sci_new = animal.get("scientific_name", "?")
    print(f"class={cls} sci={sci_new}")
    processed += 1
    time.sleep(2)

print(f"\nProcessed {processed} animals")
