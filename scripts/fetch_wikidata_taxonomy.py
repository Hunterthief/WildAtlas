#!/usr/bin/env python3
"""Fetch taxonomic classification from Wikidata for each animal.
Uses the Wikipedia REST API (more permissive) to get the QID, then
fetches taxonomy from Wikidata with 2s delays to avoid rate limits."""
import json, os, re, urllib.request, urllib.parse, time

CACHE_DIR = "data/cache/wikipedia"
HEADERS = {"User-Agent": "WildAtlasBot/1.0 (educational project)"}

def fetch_json(url, timeout=10):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)

def get_qid_via_rest(wikipedia_title):
    """Get Wikidata Q ID via the REST API (more permissive than action API)."""
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(wikipedia_title)}"
        data = fetch_json(url)
        return data.get("wikibase_item")
    except:
        return None

def get_wikidata_taxonomy(qid):
    """Fetch taxonomy from Wikidata by following the parent taxon chain."""
    classification = {}
    sci_name = ""
    conservation = ""

    current_qid = qid
    visited = set()

    for _ in range(12):  # max 12 levels up
        if current_qid in visited:
            break
        visited.add(current_qid)

        try:
            url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={current_qid}&props=claims|labels&languages=en&format=json"
            data = fetch_json(url)
            entity = data.get("entities", {}).get(current_qid, {})
            claims = entity.get("claims", {})
            label = entity.get("labels", {}).get("en", {}).get("value", "")

            # Scientific name (P225)
            if current_qid == qid and "P225" in claims:
                sci_name = claims["P225"][0]["mainsnak"]["datavalue"]["value"]

            # Taxon rank (P105)
            if "P105" in claims:
                rank_id = claims["P105"][0]["mainsnak"]["datavalue"]["value"]["id"]
                rank_name = get_label(rank_id).lower()

                rank_map = {
                    "kingdom": "kingdom", "phylum": "phylum", "class": "class",
                    "order": "order", "family": "family", "genus": "genus",
                    "species": "species", "subspecies": "species",
                    "subgenus": "genus", "subfamily": "family", "suborder": "order",
                    "subclass": "class", "subphylum": "phylum",
                    "infraclass": "class", "superfamily": "family",
                    "infraorder": "order", "tribe": "family",
                    "subtribe": "family", "superorder": "order",
                }
                if rank_name in rank_map:
                    key = rank_map[rank_name]
                    if key not in classification:
                        if "P225" in claims:
                            classification[key] = claims["P225"][0]["mainsnak"]["datavalue"]["value"]
                        else:
                            classification[key] = label

            # IUCN status (P141) — only for the species itself
            if current_qid == qid and "P141" in claims:
                iucn_id = claims["P141"][0]["mainsnak"]["datavalue"]["value"]["id"]
                iucn_label = get_label(iucn_id).lower()
                iucn_map = {
                    "least concern": "Least Concern",
                    "near threatened": "Near Threatened",
                    "vulnerable": "Vulnerable",
                    "endangered": "Endangered",
                    "critically endangered": "Critically Endangered",
                    "extinct in the wild": "Extinct in the Wild",
                    "extinct": "Extinct",
                    "data deficient": "Data Deficient",
                }
                for k, v in iucn_map.items():
                    if k in iucn_label:
                        conservation = v
                        break

            # Follow parent taxon (P171)
            if "P171" in claims:
                current_qid = claims["P171"][0]["mainsnak"]["datavalue"]["value"]["id"]
            else:
                break
            time.sleep(0.5)
        except Exception as e:
            break

    return {
        "scientific_name": sci_name,
        "classification": classification,
        "conservation_status": conservation,
    }

def get_label(qid):
    try:
        url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={qid}&props=labels&languages=en&format=json"
        data = fetch_json(url)
        return data.get("entities", {}).get(qid, {}).get("labels", {}).get("en", {}).get("value", "")
    except:
        return ""

def merge(animal, wiki_data):
    if not wiki_data: return animal
    if wiki_data.get("scientific_name", "").strip():
        animal["scientific_name"] = wiki_data["scientific_name"].strip()
    if wiki_data.get("classification"):
        animal["classification"] = {**(animal.get("classification") or {}), **wiki_data["classification"]}
    if wiki_data.get("conservation_status"):
        animal["ecology"] = {**(animal.get("ecology") or {}), "conservation_status": wiki_data["conservation_status"]}
    return animal

# Read catalog
with open("src/lib/curated-catalog.ts") as f:
    content = f.read()
CATALOG = re.findall(
    r'\{\s*name:\s*"([^"]+)"\s*,\s*wikipediaTitle:\s*"([^"]+)"\s*,\s*type:\s*"(\w+)"\s*\}',
    content
)

def slugify(name):
    return ''.join(c if c.isalnum() else '-' for c in name.lower()).strip('-')

# Process all catalog animals that lack classification
processed = 0
for name, wiki_title, type_ in CATALOG:
    slug = slugify(name)
    cache_file = os.path.join(CACHE_DIR, f"{slug}.json")
    if not os.path.exists(cache_file):
        continue

    animal = json.load(open(cache_file))
    cls = animal.get("classification") or {}
    if cls.get("class") and cls.get("order") and cls.get("family"):
        continue  # already complete

    print(f"[{processed+1}] {name}...", end=" ", flush=True)

    qid = get_qid_via_rest(wiki_title)
    if not qid:
        print("no QID")
        continue
    time.sleep(1)

    wiki_data = get_wikidata_taxonomy(qid)
    animal = merge(animal, wiki_data)
    json.dump(animal, open(cache_file, "w"), indent=2, ensure_ascii=False)

    sci = animal.get("scientific_name", "?")
    cls = animal.get("classification") or {}
    cons = (animal.get("ecology") or {}).get("conservation_status", "?")
    print(f"sci={sci} class={cls.get('class','?')} order={cls.get('order','?')} family={cls.get('family','?')} cons={cons}")
    processed += 1
    time.sleep(2)

print(f"\nProcessed {processed} animals")
