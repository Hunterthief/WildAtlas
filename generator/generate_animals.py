import requests
import json
import time
import os

os.makedirs("data", exist_ok=True)

animals = [
    "Lion","Tiger","Elephant","Blue Whale","Orca","Great White Shark",
    "Dolphin","Octopus","Penguin","Giraffe","Zebra","Bear","Wolf","Fox",
    "Kangaroo","Koala","Cheetah","Leopard","Hyena","Moose","Walrus",
    "Seal","Sea Lion","Swordfish","Salmon","Tuna","Clownfish",
    "Angelfish","Manta Ray","Stingray","Hammerhead Shark","Barracuda",
    "Pufferfish","Moray Eel","Manatee","Narwhal","Beluga Whale"
]

WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
WIKIDATA_API = "https://www.wikidata.org/wiki/Special:EntityData/"
EOL_SEARCH_API = "https://eol.org/api/search/1.0.json"
EOL_PAGES_API = "https://eol.org/api/pages/1.0/{}.json"

headers = {"User-Agent": "WildAtlasBot/1.0 (https://github.com/Hunterthief/WildAtlas)"}

output = []

# --- Helpers ---
def fetch_wikidata_label(qid):
    try:
        r = requests.get(f"{WIKIDATA_API}{qid}.json", headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()["entities"][qid]["labels"]["en"]["value"]
    except Exception as e:
        print(f"  Wikidata label fetch failed for {qid}: {e}")
        return None

def get_claim_value(claims, pid):
    vals = claims.get(pid)
    if not vals:
        return None
    snak = vals[0].get("mainsnak", {})
    datavalue = snak.get("datavalue", {})
    val = datavalue.get("value")
    if isinstance(val, dict) and val.get("id"):
        label = fetch_wikidata_label(val["id"])
        return label
    elif isinstance(val, (str, int, float)):
        return val
    elif isinstance(val, dict) and "amount" in val:
        amount = val["amount"].lstrip("+")
        unit_url = val.get("unit")
        unit = None
        if unit_url and unit_url.startswith("http://www.wikidata.org/entity/"):
            unit_qid = unit_url.split("/")[-1]
            unit = fetch_wikidata_label(unit_qid)
        return f"{amount} {unit}" if unit else amount
    return None

def fetch_eol(animal_name):
    """Fetch diet, size, location from EOL"""
    try:
        search = requests.get(EOL_SEARCH_API, params={"q": animal_name}, headers=headers, timeout=10).json()
        results = search.get("results")
        if not results:
            return {}
        page_id = results[0]["id"]
        page_data = requests.get(EOL_PAGES_API.format(page_id), headers=headers, timeout=10).json()
        traits = page_data.get("traits", [])
        data = {}
        for trait in traits:
            key = trait.get("trait")
            val = trait.get("value")
            if key and val:
                key = key.lower()
                if key == "diet":
                    data["diet"] = val
                elif key in ["length", "body length"]:
                    data["length"] = val
                elif key in ["height", "shoulder height"]:
                    data["height"] = val
                elif key in ["weight", "mass"]:
                    data["weight"] = val
                elif key in ["distribution", "location"]:
                    data["location"] = val
        return data
    except Exception as e:
        print(f"  EOL fetch failed for {animal_name}: {e}")
        return {}

# Correct Wikidata properties for taxonomy
TAXONOMY_PROPS = {
    "domain": "P158",    # biological domain
    "kingdom": "P75",    # kingdom (verify if missing)
    "phylum": "P105",
    "class": "P279",
    "order": "P105",
    "family": "P171",
    "genus": "P225",
    "species": "P225"
}

NUMERIC_PROPS = {
    "diet": "P768",
    "length": "P2043",
    "height": "P2048",
    "weight": "P2067",
    "location": "P183"
}

# --- Main ---
for name in animals:
    print(f"\n--- Processing {name} ---")
    sources = []

    # Wikipedia
    wiki_data = {}
    try:
        r = requests.get(WIKI_API + name.replace(" ", "_"), headers=headers, timeout=10)
        print(f"  Wikipedia status: {r.status_code}")
        if r.status_code == 200:
            wiki_data = r.json()
            sources.append("Wikipedia")
        else:
            sources.append("Wikipedia FAILED")
    except Exception as e:
        sources.append("Wikipedia FAILED")
        print(f"  Wikipedia error: {e}")

    summary = wiki_data.get("extract", "")
    description = wiki_data.get("description", "")
    image = wiki_data.get("thumbnail", {}).get("source", "")

    classification = {}
    diet = None
    length = None
    height = None
    weight = None
    location = None

    wikibase = wiki_data.get("wikibase_item")
    if wikibase and isinstance(wikibase, str):
        try:
            wd_resp = requests.get(f"{WIKIDATA_API}{wikibase}.json", headers=headers, timeout=10).json()
            claims = wd_resp.get("entities", {}).get(wikibase, {}).get("claims", {})
            if claims:
                for rank, pid in TAXONOMY_PROPS.items():
                    classification[rank] = get_claim_value(claims, pid)
                for field, pid in NUMERIC_PROPS.items():
                    val = get_claim_value(claims, pid)
                    if val:
                        locals()[field] = val
                sources.append("Wikidata")
            else:
                sources.append("Wikidata EMPTY")
        except Exception as e:
            sources.append("Wikidata FAILED")
            print(f"  Wikidata failed: {e}")
    else:
        sources.append("Wikidata MISSING")

    # EOL fallback
    eol_data = fetch_eol(name)
    for field in ["diet", "length", "height", "weight", "location"]:
        if not locals()[field] and eol_data.get(field):
            locals()[field] = eol_data[field]
            if "EOL" not in sources:
                sources.append("EOL")

    output.append({
        "name": name,
        "description": description,
        "summary": summary,
        "image": image,
        "classification": classification,
        "diet": diet,
        "length": length,
        "height": height,
        "weight": weight,
        "location": location,
        "sources": sources
    })

    print(f"  {name} added successfully")
    time.sleep(1)

# Write JSON
with open(os.path.join("data", "animals.json"), "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nanimals.json written to data/animals.json. Total animals fetched: {len(output)}")
