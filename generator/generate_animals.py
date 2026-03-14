import requests
import json
import time
import os

os.makedirs("data", exist_ok=True)

# Headers
headers = {
    "User-Agent": "WildAtlasBot/1.0 (https://github.com/Hunterthief/WildAtlas)",
    "Accept": "application/sparql-results+json"
}

# Wikidata SPARQL to get all animals (Animalia)
SPARQL_ANIMALS = """
SELECT ?item ?itemLabel ?wikiTitle WHERE {
  ?item wdt:P31 wd:Q16521.        # instance of 'taxon'
  ?item wdt:P105 ?rank.           # has taxonomic rank
  ?item wdt:P171* wd:Q729.        # parent taxon ultimately Animalia
  OPTIONAL {
    ?sitelink schema:about ?item;
              schema:isPartOf <https://en.wikipedia.org/>;
              schema:name ?wikiTitle.
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 500
"""

WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
EOL_SEARCH_API = "https://eol.org/api/search/1.0.json"
EOL_PAGES_API = "https://eol.org/api/pages/1.0/{}.json"

# --- Helpers ---
def fetch_eol(animal_name):
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

def fetch_wikidata_animal(qid):
    query = f"""
    SELECT ?taxon ?taxonLabel ?rankLabel ?dietLabel ?mass ?massUnitLabel ?bodyLength ?bodyLengthUnitLabel ?locationLabel
    WHERE {{
      BIND(wd:{qid} AS ?taxon)

      # Taxonomic hierarchy
      ?taxon wdt:P105 ?rank .
      OPTIONAL {{ ?taxon (wdt:P171)+ ?parent . }}

      # Diet
      OPTIONAL {{ ?taxon wdt:P768 ?diet . }}

      # Mass / weight
      OPTIONAL {{ ?taxon p:P2067 ?massStmt .
                 ?massStmt ps:P2067 ?massVal .
                 ?massStmt pq:P5104 ?massUnit .
      }}

      # Body length
      OPTIONAL {{ ?taxon p:P2043 ?lenStmt .
                 ?lenStmt ps:P2043 ?bodyLength .
                 ?lenStmt pq:P5104 ?bodyLengthUnit .
      }}

      # Location / distribution
      OPTIONAL {{ ?taxon wdt:P183 ?location . }}

      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    """
    return requests.get(WIKIDATA_SPARQL, params={"query": query}, headers=headers, timeout=15).json()

# --- Main ---
output = []

# Step 1: Fetch animal list from Wikidata
print("Fetching animal list from Wikidata...")
res = requests.get(WIKIDATA_SPARQL, params={"query": SPARQL_ANIMALS}, headers=headers, timeout=30).json()
bindings = res.get("results", {}).get("bindings", [])

print(f"Found {len(bindings)} animals")

for b in bindings:
    animal = b.get("itemLabel", {}).get("value")
    wiki_title = b.get("wikiTitle", {}).get("value", animal.replace(" ", "_"))
    qid = b.get("item", {}).get("value", "").split("/")[-1]
    print(f"\n--- Processing {animal} ---")
    sources = []

    # Wikipedia
    wiki_data = {}
    try:
        r = requests.get(WIKI_API + wiki_title, headers=headers, timeout=10)
        print(f"  Wikipedia status: {r.status_code}")
        if r.status_code == 200:
            wiki_data = r.json()
            sources.append("Wikipedia")
        else:
            sources.append("Wikipedia FAILED")
    except Exception as e:
        print(f"  Wikipedia error: {e}")
        sources.append("Wikipedia FAILED")

    summary = wiki_data.get("extract", "")
    description = wiki_data.get("description", "")
    image = wiki_data.get("thumbnail", {}).get("source", "")

    # Wikidata
    classification = {k: None for k in ["domain","kingdom","phylum","class","order","family","genus","species"]}
    diet = length = height = weight = location = None
    try:
        data = fetch_wikidata_animal(qid)
        wikibind = data.get("results", {}).get("bindings", [])
        if wikibind:
            sources.append("Wikidata")
            for w in wikibind:
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
    except Exception as e:
        print(f"  Wikidata SPARQL failed: {e}")
        sources.append("Wikidata FAILED")

    # EOL fallback
    eol_data = fetch_eol(animal)
    for field in ["diet","length","height","weight","location"]:
        if not locals()[field] and eol_data.get(field):
            locals()[field] = eol_data[field]
            if "EOL" not in sources:
                sources.append("EOL")

    output.append({
        "name": animal,
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

    print(f"  {animal} processed")
    time.sleep(1)

# Write JSON
with open("data/animals.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nDone. Generated animals.json with {len(output)} animals.")
