import requests
import json
import time
import os
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

os.makedirs("data", exist_ok=True)

# --- Session + retries ---
session = requests.Session()
retry = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry)
session.mount("https://", adapter)

headers = {
    "User-Agent": "WildAtlasBot/1.0 (https://github.com/Hunterthief/WildAtlas)",
    "Accept": "application/sparql-results+json"
}

WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"

# --- Test species with real QIDs ---
TEST_ANIMALS = [
    {"name": "Tiger", "qid": "Q132186"},          # Panthera tigris
    {"name": "Asian Elephant", "qid": "Q7372"},   # Elephas maximus
    {"name": "Bald Eagle", "qid": "Q25319"},      # Haliaeetus leucocephalus
]

# --- Map ranks to classification fields ---
RANKS_MAP = {
    "domain": "domain",
    "kingdom": "kingdom",
    "phylum": "phylum",
    "class": "class",
    "order": "order",
    "family": "family",
    "genus": "genus",
    "species": "species"
}

# --- Fetch main animal traits (species level only) ---
def fetch_wikidata_animal(qid):
    query_main = f"""
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
            res = session.get(WIKIDATA_SPARQL, params={"query": query_main}, headers=headers, timeout=120)
            if res.status_code == 200:
                return res.json()
            elif res.status_code == 504:
                print(f"  504 received, retry {attempt+1}/5...")
        except requests.exceptions.RequestException as e:
            print(f"  Request error {e}, retry {attempt+1}/5")
        time.sleep(5 * (attempt+1))
    print(f"  Failed to fetch {qid} after retries")
    return {}

# --- Fetch full parent classification separately ---
def fetch_parent_classification(qid):
    query_parent = f"""
    SELECT ?parent ?parentLabel ?parentRankLabel
    WHERE {{
      wd:{qid} wdt:P171* ?parent .
      ?parent wdt:P105 ?parentRank .
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    """
    for attempt in range(5):
        try:
            res = session.get(WIKIDATA_SPARQL, params={"query": query_parent}, headers=headers, timeout=120)
            if res.status_code == 200:
                return res.json().get("results", {}).get("bindings", [])
        except requests.exceptions.RequestException:
            time.sleep(5 * (attempt+1))
    return []

# --- Wikipedia fallback ---
def fetch_wikipedia(animal_name):
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

    # Wikipedia fallback
    wiki_data = fetch_wikipedia(name)
    summary = wiki_data.get("extract", "")
    description = wiki_data.get("description", "")
    image = wiki_data.get("thumbnail", {}).get("source", "")

    # Check cache
    cache_file = f"data/{qid}.json"
    if os.path.exists(cache_file):
        data = json.load(open(cache_file, encoding="utf-8"))
        bindings = data.get("results", {}).get("bindings", [])
        parent_bindings = data.get("parent_bindings", [])
    else:
        data = fetch_wikidata_animal(qid)
        bindings = data.get("results", {}).get("bindings", [])
        parent_bindings = fetch_parent_classification(qid)
        # Save cache
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"results": bindings, "parent_bindings": parent_bindings}, f, ensure_ascii=False, indent=2)

    classification = {k: None for k in RANKS_MAP.values()}
    diet = length = height = weight = location = None
    sources = []

    if bindings:
        sources.append("Wikidata")
        for w in bindings:
            # Traits
            diet = w.get("dietLabel", {}).get("value") or diet
            if w.get("mass") and w.get("massUnitLabel"):
                weight = f'{w["mass"]["value"]} {w["massUnitLabel"]["value"]}'
            if w.get("bodyLength") and w.get("bodyLengthUnitLabel"):
                length = f'{w["bodyLength"]["value"]} {w["bodyLengthUnitLabel"]["value"]}'
            loc = w.get("locationLabel", {}).get("value")
            location = loc or location

    # Parent hierarchy
    for p in parent_bindings:
        rank = p.get("parentRankLabel", {}).get("value")
        label = p.get("parentLabel", {}).get("value")
        if rank in RANKS_MAP:
            classification[RANKS_MAP[rank]] = label
    # Include species label
    if bindings and bindings[0].get("taxonLabel", {}).get("value"):
        classification["species"] = bindings[0]["taxonLabel"]["value"]

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
