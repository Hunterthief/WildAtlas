import requests
import json
import time
import os
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

os.makedirs("data", exist_ok=True)

# --- Session + retries ---
session = requests.Session()
retry = Retry(total=5, backoff_factor=2, status_forcelist=[429,500,502,503,504])
adapter = HTTPAdapter(max_retries=retry)
session.mount("https://", adapter)

headers = {
    "User-Agent": "WildAtlasBot/1.0 (https://github.com/Hunterthief/WildAtlas)",
    "Accept": "application/sparql-results+json"
}

# --- SPARQL endpoint ---
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"

# --- Static test list for development ---
TEST_ANIMALS = [
    {"name": "Tiger", "qid": "Q16521"},  # Panthera tigris
    {"name": "Elephant", "qid": "Q7374"}, # Elephantidae
    {"name": "Bald Eagle", "qid": "Q25319"}, # Haliaeetus leucocephalus
]

# --- Helpers ---
def fetch_wikidata_animal(qid):
    query = f"""
    SELECT ?taxon ?taxonLabel ?rankLabel ?dietLabel ?mass ?massUnitLabel ?bodyLength ?bodyLengthUnitLabel ?locationLabel
    WHERE {{
      BIND(wd:{qid} AS ?taxon)
      OPTIONAL {{ ?taxon wdt:P105 ?rank . }}
      OPTIONAL {{ ?taxon wdt:P768 ?diet . }}
      OPTIONAL {{ ?taxon p:P2067 ?massStmt .
                 ?massStmt ps:P2067 ?mass .
                 ?massStmt pq:P5104 ?massUnitLabel . }}
      OPTIONAL {{ ?taxon p:P2043 ?lenStmt .
                 ?lenStmt ps:P2043 ?bodyLength .
                 ?lenStmt pq:P5104 ?bodyLengthUnitLabel . }}
      OPTIONAL {{ ?taxon wdt:P183 ?locationLabel . }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    """
    for attempt in range(5):
        try:
            res = session.get(WIKIDATA_SPARQL, params={"query": query}, headers=headers, timeout=180).json()
            return res
        except requests.exceptions.ReadTimeout:
            print(f"  Timeout on {qid}, retry {attempt+1}/5...")
            time.sleep(5 * (attempt+1))
    print(f"  Failed to fetch {qid} after retries")
    return {}

def fetch_wikipedia(animal_name):
    WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
    try:
        r = session.get(WIKI_API + animal_name.replace(" ", "_"), headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"  Wikipedia error: {e}")
    return {}

# --- Main ---
output = []

for a in TEST_ANIMALS:
    name = a["name"]
    qid = a["qid"]
    print(f"\n--- Processing {name} ({qid}) ---")

    # Wikipedia
    wiki_data = fetch_wikipedia(name)
    summary = wiki_data.get("extract", "")
    description = wiki_data.get("description", "")
    image = wiki_data.get("thumbnail", {}).get("source", "")

    # Wikidata
    classification = {k: None for k in ["domain","kingdom","phylum","class","order","family","genus","species"]}
    diet = length = height = weight = location = None
    data = fetch_wikidata_animal(qid)
    bindings = data.get("results", {}).get("bindings", [])
    sources = []

    if bindings:
        sources.append("Wikidata")
        for w in bindings:
            rank = w.get("rankLabel", {}).get("value")
            label = w.get("taxonLabel", {}).get("value")
            rank_map = {
                "species":"species","genus":"genus","family":"family","order":"order",
                "class":"class","phylum":"phylum","kingdom":"kingdom","domain":"domain"
            }
            if rank in rank_map:
                classification[rank_map[rank]] = label
            diet = w.get("dietLabel", {}).get("value") or diet
            if w.get("mass") and w.get("massUnitLabel"):
                weight = f'{w["mass"]["value"]} {w["massUnitLabel"]["value"]}'
            if w.get("bodyLength") and w.get("bodyLengthUnitLabel"):
                length = f'{w["bodyLength"]["value"]} {w["bodyLengthUnitLabel"]["value"]}'
            loc = w.get("locationLabel", {}).get("value")
            location = loc or location
    else:
        sources.append("Wikidata EMPTY")

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
    print(f"  {name} processed")
    time.sleep(1)

# Write JSON
with open("data/animals.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nDone. Generated animals.json with {len(output)} animals.")
