#!/usr/bin/env python3
"""Batch-enrich cached animals using the z-ai CLI (one process per animal).
Rate-limit-safe: 3s delay between calls."""
import json, os, re, subprocess, time, sys

CACHE_DIR = "data/cache/wikipedia"
PROMPT = """You are a precise wildlife data extractor. Given the Wikipedia article text about an animal, extract structured facts. Only include values actually stated in the text. Use metric units.

Output STRICT JSON (no markdown fences) with this shape:
{"scientific_name":"","young_name":"","group_name":"","physical":{"length":"","height":"","weight":"","top_speed":"","lifespan":""},"ecology":{"diet":"","habitat":"","locations":"","group_behavior":"","conservation_status":"","biggest_threat":"","distinctive_features":[]},"classification":{"kingdom":"","phylum":"","class":"","order":"","family":"","genus":"","species":""},"reproduction":{"gestation_period":"","average_litter_size":"","name_of_young":""},"time_period_text":""}

diet: one of Carnivore/Herbivore/Omnivore/Piscivore/Insectivore/Nectarivore/Scavenger/Filter feeder. conservation_status: one of Least Concern/Near Threatened/Vulnerable/Endangered/Critically Endangered/Extinct in the Wild/Extinct/Data Deficient. Use ranges with en-dash. For egg-layers: gestation=incubation, litter=clutch. Do NOT invent values.

Animal name: {name}

Wikipedia article text:
{text}"""

def merge(animal, extracted):
    if not extracted:
        return animal
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
    if extracted.get("time_period_text", "").strip():
        animal["time_period"] = {
            "text": extracted["time_period_text"].strip(),
            "width": "50%", "start": "Ancient", "end": "Present"
        }
    return animal

def enrich_one(cache_file):
    animal = json.load(open(cache_file))
    if animal.get("scientific_name", "").strip() and (animal.get("classification") or {}).get("class", "").strip():
        return "skip"
    art = animal.get("article") or {}
    parts = [animal.get("summary",""), art.get("overview",""), art.get("description",""),
             art.get("habitat",""), art.get("behavior",""), art.get("conservation","")]
    text = "\n\n".join(p for p in parts if p)[:5000]
    if not text.strip():
        return "no-text"
    prompt = PROMPT.replace("{name}", animal["name"]).replace("{text}", text)
    try:
        result = subprocess.run(["z-ai", "chat", "-p", prompt], capture_output=True, text=True, timeout=30)
        m = re.search(r'\{[\s\S]*"choices"[\s\S]*\}', result.stdout)
        if not m:
            return "no-json"
        resp = json.loads(m.group(0))
        content = resp["choices"][0]["message"]["content"]
        content = re.sub(r'^```(?:json)?\s*', '', content.strip())
        content = re.sub(r'\s*```$', '', content)
        try:
            extracted = json.loads(content)
        except:
            m2 = re.search(r'\{[\s\S]*\}', content)
            extracted = json.loads(m2.group(0)) if m2 else {}
        enriched = merge(animal, extracted)
        json.dump(enriched, open(cache_file, "w"), indent=2, ensure_ascii=False)
        return f"ok: sci={enriched.get('scientific_name','?')} class={(enriched.get('classification') or {}).get('class','?')}"
    except Exception as e:
        return f"error: {str(e)[:60]}"

files = sorted(f for f in os.listdir(CACHE_DIR) if f.endswith(".json"))
total = len(files)
processed = ok = skipped = failed = 0

for i, fn in enumerate(files):
    cache_file = os.path.join(CACHE_DIR, fn)
    result = enrich_one(cache_file)
    processed += 1
    if result == "skip":
        skipped += 1
        continue
    elif result.startswith("ok"):
        ok += 1
        print(f"[{processed}/{total}] OK {result}", flush=True)
    else:
        failed += 1
        print(f"[{processed}/{total}] FAIL {fn}: {result}", flush=True)
    time.sleep(3)

print(f"\nDone: {ok} enriched, {skipped} skipped, {failed} failed")
