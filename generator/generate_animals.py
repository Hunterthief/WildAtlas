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

# Rank order for sorting hierarchy
RANK_ORDER = ["domain", "kingdom", "phylum", "class", "order", "family", "genus", "species"]

def fetch_wikidata_traits(qid):
    """Fetch direct traits: diet, mass, length, location."""
    # Note: Diet is often not on the species item directly. We might need to look up the chain later, 
    # but for now we try the species item.
    query = f"""
    SELECT ?dietLabel ?mass ?massUnitLabel ?length ?lengthUnitLabel ?locationLabel
    WHERE {{
      BIND(wd:{qid} AS ?item)
      
      OPTIONAL {{ ?item wdt:P768 ?diet . }}
      
      OPTIONAL {{ 
        ?item p:P2067 ?massStmt .
        ?massStmt ps:P2067 ?mass .
        OPTIONAL {{ ?massStmt pq:P5104 ?massUnit . }}
      }}
      
      OPTIONAL {{ 
        ?item p:P2043 ?lenStmt .
        ?lenStmt ps:P2043 ?length .
        OPTIONAL {{ ?lenStmt pq:P5104 ?lengthUnit . }}
      }}

      OPTIONAL {{ ?item wdt:P183 ?location . }}

      SERVICE wikibase:label {{ 
        bd:serviceParam wikibase:language "en". 
        ?diet rdfs:label ?dietLabel .
        ?location rdfs:label ?locationLabel .
        ?massUnit rdfs:label ?massUnitLabel .
        ?lengthUnit rdfs:label ?lengthUnitLabel .
      }}
    }}
    LIMIT 1
    """
    try:
        res = session.get(WIKIDATA_SPARQL, params={"query": query}, headers=headers, timeout=60)
        if res.status_code == 200:
            return res.json().get("results", {}).get("bindings", [])
    except Exception as e:
        print(f"  Error fetching traits: {e}")
    return []

def fetch_classification_chain(qid):
    """
    Walk up the P171 (parent taxon) chain step-by-step to ensure correct rank assignment.
    This avoids the flat-list explosion of recursive queries.
    """
    classification = {k: None for k in RANKS_MAP.values()}
    
    current_qid = qid
    visited = set()
    
    # First, get the species name itself explicitly
    query_species = f"""
    SELECT ?label WHERE {{ wd:{qid} rdfs:label ?label FILTER(LANG(?label) = "en") }} LIMIT 1
    """
    try:
        res = session.get(WIKIDATA_SPARQL, params={"query": query_species}, headers=headers, timeout=30)
        if res.status_code == 200:
            bindings = res.json().get("results", {}).get("bindings", [])
            if bindings:
                classification["species"] = bindings[0]["label"]["value"]
    except: pass

    # Iterate up the chain
    for _ in range(10): # Max depth safety break
        if current_qid in visited: break
        visited.add(current_qid)

        # Query parent and its rank
        query_parent = f"""
        SELECT ?parent ?parentLabel ?rankLabel WHERE {{
          wd:{current_qid} wdt:P171 ?parent .
          ?parent wdt:P105 ?rank .
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }} LIMIT 1
        """
        try:
            res = session.get(WIKIDATA_SPARQL, params={"query": query_parent}, headers=headers, timeout=30)
            if res.status_code != 200: break
            
            bindings = res.json().get("results", {}).get("bindings", [])
            if not bindings: break
            
            b = bindings[0]
            parent_qid = b["parent"]["value"].split("/")[-1]
            rank_label = b.get("rankLabel", {}).get("value", "").lower()
            parent_label = b.get("parentLabel", {}).get("value")
            
            # Map rank to our fields
            if rank_label in RANKS_MAP:
                field = RANKS_MAP[rank_label]
                classification[field] = parent_label
            
            # Special handling for "taxon" or generic ranks if specific ones are missing
            # But mostly we rely on standard Linnaean ranks
            
            current_qid = parent_qid
            
            # Stop if we hit root or common high-level nodes that might loop or aren't useful
            if current_qid == "Q10000": # Break at something generic if needed, though Q7372 chain is safe
                break
                
        except Exception as e:
            print(f"  Error in chain: {e}")
            break
        
        time.sleep(0.2) # Be nice to the API

    return classification

def fetch_wikipedia(animal_name):
    try:
        # Clean name for URL
        safe_name = animal_name.replace(" ", "_")
        r = session.get(f"{WIKI_API}{safe_name}", headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"  Wikipedia error: {e}")
    return {}

def format_unit(value, unit_label):
    if not value: return None
    # Clean up unit labels (often come with quotes or extra text from Wikidata)
    unit = unit_label if unit_label else ""
    if '"' in unit: unit = unit.replace('"', ' inches').replace('""', '') # rough fix
    return f"{value} {unit}".strip()

# --- Main ---
output = []

for a in TEST_ANIMALS:
    name = a["name"]
    qid = a["qid"]
    print(f"\n--- Processing {name} ({qid}) ---")

    # 1. Wikipedia Fallback (Images/Summary)
    wiki_data = fetch_wikipedia(name)
    summary = wiki_data.get("extract", "")
    description = wiki_data.get("description", "")
    image = wiki_data.get("thumbnail", {}).get("source", "")

    # 2. Check Cache
    cache_file = f"data/{qid}.json"
    if os.path.exists(cache_file):
        print("  Using cached data...")
        with open(cache_file, "r", encoding="utf-8") as f:
            cached = json.load(f)
            traits_bindings = cached.get("traits", [])
            classification = cached.get("classification", {})
    else:
        # 3. Fetch Live Data
        traits_bindings = fetch_wikidata_traits(qid)
        classification = fetch_classification_chain(qid)
        
        # Save Cache
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"traits": traits_bindings, "classification": classification}, f, indent=2)

    # 4. Parse Traits
    diet = length = weight = location = None
    sources = []

    if traits_bindings:
        sources.append("Wikidata")
        row = traits_bindings[0]
        
        # Diet
        diet = row.get("dietLabel", {}).get("value")
        
        # Mass
        mass_val = row.get("mass", {}).get("value")
        mass_unit = row.get("massUnitLabel", {}).get("value")
        if mass_val:
            # Simple cleanup for common units if Wikidata label is messy
            if not mass_unit or mass_unit == "kilogram": mass_unit = "kg"
            elif mass_unit == "gram": mass_unit = "g"
            weight = f"{mass_val} {mass_unit}"

        # Length
        len_val = row.get("length", {}).get("value")
        len_unit = row.get("lengthUnitLabel", {}).get("value")
        if len_val:
            if not len_unit or len_unit == "metre": len_unit = "m"
            elif len_unit == "centimetre": len_unit = "cm"
            length = f"{len_val} {len_unit}"

        # Location
        location = row.get("locationLabel", {}).get("value")

    # Fallback for diet if not found on species (common issue)
    # In a full app, we'd search the classification chain for P768, but skipping for brevity
    
    output.append({
        "name": name,
        "description": description,
        "summary": summary,
        "image": image,
        "classification": classification,
        "diet": diet,
        "length": length,
        "height": None, # Height is rarely distinct from length in Wikidata for animals
        "weight": weight,
        "location": location,
        "sources": sources
    })
    print(f"  ✓ {name} processed")
    time.sleep(1)

# Write JSON
with open("data/animals.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nDone. Generated animals.json with {len(output)} animals.")
