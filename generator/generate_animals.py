# generator/generate_animals.py
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

headers = {
    "User-Agent": "WildAtlasBot/1.0 (https://github.com/Hunterthief/WildAtlas)"
}

output = []

# Helper functions
def get_wikidata_claim(claims, pid):
    vals = claims.get(pid)
    if not vals:
        return None
    dat = vals[0].get("mainsnak", {}).get("datavalue", {})
    if dat.get("value", {}).get("id"):
        qid = dat["value"]["id"]
        try:
            lab_resp = requests.get(f"{WIKIDATA_API}{qid}.json", headers=headers, timeout=10).json()
            return lab_resp["entities"][qid]["labels"]["en"]["value"]
        except:
            return None
    return dat.get("value", None)

def get_wikidata_numeric(claims, pid):
    vals = claims.get(pid)
    if vals:
        m = vals[0].get("mainsnak", {}).get("datavalue", {}).get("value", {})
        num = m.get("amount")
        unit = m.get("unit", "")
        if num:
            return f"{num} {unit.split('/')[-1]}" if unit else str(num)
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

for name in animals:
    print(f"\n--- Processing {name} ---")
    sources = []

    # Wikipedia
    wiki_data = {}
    try:
        title = name.replace(" ", "_")
        r = requests.get(WIKI_API + title, headers=headers, timeout=10)
        print(f"  Wikipedia status: {r.status_code}")
        if r.status_code == 200:
            wiki_data = r.json()
            sources.append("Wikipedia")
        else:
            sources.append("Wikipedia FAILED")
            print(f"  Wikipedia failed for {name}")
    except Exception as e:
        sources.append("Wikipedia FAILED")
        print(f"  Wikipedia error: {e}")

    summary = wiki_data.get("extract", "")
    description = wiki_data.get("description", "")
    image = wiki_data.get("thumbnail", {}).get("source", "")

    # Wikidata
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
                classification = {
                    "domain": get_wikidata_claim(claims, "P229"),
                    "kingdom": get_wikidata_claim(claims, "P1047"),
                    "phylum": get_wikidata_claim(claims, "P1083"),
                    "class": get_wikidata_claim(claims, "P1098"),
                    "order": get_wikidata_claim(claims, "P105"),
                    "family": get_wikidata_claim(claims, "P1120"),
                    "genus": get_wikidata_claim(claims, "P2292"),
                    "species": get_wikidata_claim(claims, "P225")
                }
                diet = get_wikidata_claim(claims, "P768") or diet
                length = get_wikidata_numeric(claims, "P2043") or length
                height = get_wikidata_numeric(claims, "P2048") or height
                weight = get_wikidata_numeric(claims, "P2067") or weight
                location = get_wikidata_claim(claims, "P183") or location
                sources.append("Wikidata")
                print(f"  Wikidata fetched for {name}")
            else:
                sources.append("Wikidata EMPTY")
                print(f"  Wikidata claims empty for {name}")
        except Exception as e:
            sources.append("Wikidata FAILED")
            print(f"  Wikidata failed for {name}: {e}")
    else:
        sources.append("Wikidata MISSING")
        print(f"  Wikidata item missing or invalid for {name}")

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
