# generator/generate_animals.py
import requests
import json
import time
import os
from bs4 import BeautifulSoup

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

def get_wikidata_claim(claims, pid):
    vals = claims.get(pid)
    if not vals:
        return ""
    dat = vals[0].get("mainsnak", {}).get("datavalue", {})
    if dat.get("value", {}).get("id"):
        qid = dat["value"]["id"]
        try:
            lab_resp = requests.get(f"{WIKIDATA_API}{qid}.json", headers=headers, timeout=10).json()
            return lab_resp["entities"][qid]["labels"]["en"]["value"]
        except Exception as e:
            print(f"  Wikidata sub-request failed for {pid}: {e}")
            return ""
    return dat.get("value", "")

def get_wikidata_numeric(claims, pid):
    vals = claims.get(pid)
    if vals:
        m = vals[0].get("mainsnak", {}).get("datavalue", {}).get("value", {})
        num = m.get("amount")
        unit = m.get("unit", "")
        if num:
            return f"{num} {unit.split('/')[-1]}"
    return ""

def fetch_eol_data(animal_name):
    try:
        search = requests.get(EOL_SEARCH_API, params={"q": animal_name}, headers=headers, timeout=10).json()
        results = search.get("results")
        if not results:
            print(f"  EOL search: no results for {animal_name}")
            return {}
        page_id = results[0]["id"]
        page_data = requests.get(EOL_PAGES_API.format(page_id), headers=headers, timeout=10).json()
        data = {}
        for trait in page_data.get("traits", []):
            trait_name = trait.get("trait")
            value = trait.get("value")
            if trait_name and value:
                data[trait_name.lower()] = value
        print(f"  EOL fetched for {animal_name}")
        return data
    except Exception as e:
        print(f"  EOL fetch failed for {animal_name}: {e}")
        return {}

for name in animals:
    print(f"\n--- Processing {name} ---")
    try:
        # Wikipedia summary
        title = name.replace(" ", "_")
        wiki_resp = requests.get(WIKI_API + title, headers=headers, timeout=10)
        print(f"  Wikipedia status: {wiki_resp.status_code}")
        if wiki_resp.status_code != 200:
            print(f"  Wikipedia failed for {name}")
            wiki_json = {}
        else:
            wiki_json = wiki_resp.json()

        summary = wiki_json.get("extract", "")
        description = wiki_json.get("description", "")
        image = wiki_json.get("thumbnail", {}).get("source", "")

        # Wikidata
        wikibase = wiki_json.get("wikibase_item")
        classification = {}
        diet = ""
        length = ""
        height = ""
        weight = ""
        location = ""
        if wikibase:
            try:
                wd_resp = requests.get(f"{WIKIDATA_API}{wikibase}.json", headers=headers, timeout=10).json()
                claims = wd_resp.get("entities", {}).get(wikibase, {}).get("claims", {})
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
                diet = get_wikidata_claim(claims, "P768")
                length = get_wikidata_numeric(claims, "P2043")
                height = get_wikidata_numeric(claims, "P2048")
                weight = get_wikidata_numeric(claims, "P2067")
                location = get_wikidata_claim(claims, "P183")
                print(f"  Wikidata fetched for {name}")
            except Exception as e:
                print(f"  Wikidata failed for {name}: {e}")

        # EOL fallback
        eol_data = fetch_eol_data(name)
        diet = diet or eol_data.get("diet")
        length = length or eol_data.get("length")
        height = height or eol_data.get("height")
        weight = weight or eol_data.get("weight")
        location = location or eol_data.get("distribution")

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
            "sources": [
                "Wikipedia" if wiki_json else "Wikipedia FAILED",
                "Wikidata" if wikibase else "Wikidata FAILED",
                "EOL" if eol_data else "EOL FAILED"
            ]
        })

        print(f"  {name} added successfully")
        time.sleep(1)

    except Exception as e:
        print(f"  Error processing {name}: {e}")

# Save JSON
with open(os.path.join("data", "animals.json"), "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nanimals.json written to data/animals.json. Total animals fetched: {len(output)}")
