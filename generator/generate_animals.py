# generator/generate_animals.py
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
    "Accept": "application/json"
}

# --- API Keys from Environment (GitHub Secrets) ---
IUCN_API_KEY = os.getenv("IUCN_API_KEY", "")

# --- Free APIs (No Key Required) ---
WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
INAT_API = "https://api.inaturalist.org/v1/taxa"
GBIF_API = "https://api.gbif.org/v1/species"

# --- Test animals ---
TEST_ANIMALS = [
    {"name": "Tiger", "scientific_name": "Panthera tigris"},
    {"name": "Asian Elephant", "scientific_name": "Elephas maximus"},
    {"name": "Bald Eagle", "scientific_name": "Haliaeetus leucocephalus"},
]

# --- Etymology Database ---
ETYMOLOGY = {
    "Panthera tigris": "From Greek 'panther' (all beast) + Latin 'tigris' (arrow, referring to speed)",
    "Elephas maximus": "From Greek 'elephas' (ivory) + Latin 'maximus' (greatest)",
    "Haliaeetus leucocephalus": "From Greek 'haliaetos' (sea eagle) + 'leukokephalos' (white-headed)",
}

def fetch_wikipedia(animal_name):
    """Fetch summary, description, and image from Wikipedia"""
    try:
        safe_name = animal_name.replace(" ", "_")
        r = session.get(f"{WIKI_API}{safe_name}", headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return {
                "summary": data.get("extract", ""),
                "description": data.get("description", ""),
                "image": data.get("thumbnail", {}).get("source", ""),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", "")
            }
    except Exception as e:
        print(f"  Wikipedia error: {e}")
    return {"summary": "", "description": "", "image": "", "url": ""}

def fetch_inaturalist_taxonomy(scientific_name):
    """
    Fetch full taxonomy from iNaturalist (FREE, no key needed) [[1], [2]
    Returns classification dict
    """
    try:
        res = session.get(
            INAT_API,
            params={"q": scientific_name, "per_page": 1},
            headers=headers,
            timeout=30
        )
        if res.status_code == 200:
            data = res.json()
            results = data.get("results", [])
            if results:
                taxon = results[0]
                classification = {
                    "kingdom": None,
                    "phylum": None,
                    "class": None,
                    "order": None,
                    "family": None,
                    "genus": None,
                    "species": scientific_name
                }
                
                # Parse ancestry (iNaturalist returns full taxonomic tree)
                ancestry = taxon.get("ancestry", [])
                for ancestor in ancestry:
                    rank = ancestor.get("rank", "").lower()
                    name = ancestor.get("name")
                    if rank == "kingdom":
                        classification["kingdom"] = name
                    elif rank == "phylum":
                        classification["phylum"] = name
                    elif rank == "class":
                        classification["class"] = name
                    elif rank == "order":
                        classification["order"] = name
                    elif rank == "family":
                        classification["family"] = name
                    elif rank == "genus":
                        classification["genus"] = name
                
                return classification
    except Exception as e:
        print(f"  iNaturalist error: {e}")
    return None

def fetch_gbif_species(scientific_name):
    """
    Fetch species data from GBIF (FREE, no key needed) [[3], [4]
    Returns: conservation status, distribution, physical info
    """
    try:
        # Search for species
        res = session.get(
            f"{GBIF_API}/search",
            params={"q": scientific_name, "type": "SPECIES"},
            headers=headers,
            timeout=30
        )
        if res.status_code == 200:
            data = res.json()
            results = data.get("results", [])
            if results:
                species = results[0]
                return {
                    "conservation_status": species.get("conservationStatus", "Not Evaluated"),
                    "distribution": species.get("distribution", []),
                    "habitat": species.get("habitat", ""),
                }
    except Exception as e:
        print(f"  GBIF error: {e}")
    return None

def fetch_iucn_conservation(scientific_name):
    """
    Fetch conservation status from IUCN Red List (requires API key) [[5], [6]
    """
    if not IUCN_API_KEY:
        print("  ⚠ IUCN_API_KEY not set in environment")
        return "Not Evaluated"
    
    try:
        # IUCN API v3 endpoint
        url = f"https://apiv3.iucnredlist.org/api/v3/taxonomicname/{scientific_name.replace(' ', '%20')}"
        res = session.get(
            url,
            params={"key": IUCN_API_KEY},
            timeout=30
        )
        if res.status_code == 200:
            data = res.json()
            result = data.get("result", [])
            if result:
                return result[0].get("category", "Not Evaluated")
    except Exception as e:
        print(f"  IUCN error: {e}")
    return "Not Evaluated"

def extract_physical_stats_from_wikipedia(summary):
    """
    Extract physical stats from Wikipedia summary using simple patterns
    (Weight, length, lifespan often mentioned in first paragraph)
    """
    import re
    
    stats = {
        "weight": None,
        "length": None,
        "height": None,
        "lifespan": None,
        "top_speed": None
    }
    
    # Weight patterns (e.g., "4 t", "300 kg", "660 lbs")
    weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(t|kg|lb|lbs|tonnes?|tons?)', summary, re.IGNORECASE)
    if weight_match:
        stats["weight"] = f"{weight_match.group(1)} {weight_match.group(2)}"
    
    # Length patterns (e.g., "2.8 m", "10 ft")
    length_match = re.search(r'(\d+(?:\.\d+)?)\s*(m|cm|mm|ft|feet|inches?)', summary, re.IGNORECASE)
    if length_match and not stats["weight"]:  # Avoid duplicate matches
        stats["length"] = f"{length_match.group(1)} {length_match.group(2)}"
    
    # Lifespan patterns (e.g., "10-15 years", "20 year")
    lifespan_match = re.search(r'(\d+(?:-\d+)?)\s*(years?|yrs?)', summary, re.IGNORECASE)
    if lifespan_match:
        stats["lifespan"] = f"{lifespan_match.group(1)} years"
    
    return stats

def get_diet_from_wikipedia(summary):
    """Extract diet type from Wikipedia summary"""
    summary_lower = summary.lower()
    if "carnivore" in summary_lower or "meat" in summary_lower or "predator" in summary_lower:
        return "Carnivore"
    elif "herbivore" in summary_lower or "plant" in summary_lower or "vegetation" in summary_lower:
        return "Herbivore"
    elif "omnivore" in summary_lower:
        return "Omnivore"
    return "Unknown"

# --- Main ---
output = []

for a in TEST_ANIMALS:
    name = a["name"]
    sci_name = a["scientific_name"]
    print(f"\n{'='*60}")
    print(f"🦁 Processing: {name} ({sci_name})")
    print(f"{'='*60}")

    # Initialize data structure (facts.app style)
    animal_data = {
        "name": name,
        "scientific_name": sci_name,
        "name_meaning": ETYMOLOGY.get(sci_name, f"Scientific name: {sci_name}"),
        "description": "",
        "summary": "",
        "image": "",
        "wikipedia_url": "",
        
        # Scientific Classification
        "classification": {
            "kingdom": None,
            "phylum": None,
            "class": None,
            "order": None,
            "family": None,
            "genus": None,
            "species": sci_name
        },
        
        # Physical Characteristics
        "physical": {
            "weight": None,
            "height": None,
            "length": None,
            "top_speed": None,
            "lifespan": None,
            "color": None,
            "skin_type": None,
            "most_distinctive_feature": None
        },
        
        # Ecology & Behavior
        "ecology": {
            "diet": None,
            "prey": None,
            "habitat": None,
            "locations": None,
            "group_behavior": None,
            "lifestyle": None,
            "biggest_threat": None,
            "conservation_status": None,
            "estimated_population_size": None
        },
        
        # Reproduction
        "reproduction": {
            "gestation_period": None,
            "average_litter_size": None,
            "name_of_young": None
        },
        
        # Fun Facts
        "fun_facts": {
            "slogan": None
        },
        
        "sources": []
    }

    # 1. Wikipedia (Images, Summary, Description)
    print("  📖 Fetching from Wikipedia...")
    wiki_data = fetch_wikipedia(name)
    animal_data["summary"] = wiki_data["summary"]
    animal_data["description"] = wiki_data["description"]
    animal_data["image"] = wiki_data["image"]
    animal_data["wikipedia_url"] = wiki_data["url"]
    if wiki_data["summary"]:
        animal_data["sources"].append("Wikipedia")
        print("     ✓ Summary & Image")
        
        # Extract physical stats from summary
        physical_stats = extract_physical_stats_from_wikipedia(wiki_data["summary"])
        for key, value in physical_stats.items():
            if value and key in animal_data["physical"]:
                animal_data["physical"][key] = value
        
        # Extract diet
        animal_data["ecology"]["diet"] = get_diet_from_wikipedia(wiki_data["summary"])

    # 2. iNaturalist (Taxonomy/Classification) - FREE [[1], [2]
    print("  🔬 Fetching taxonomy from iNaturalist...")
    inat_class = fetch_inaturalist_taxonomy(sci_name)
    if inat_class:
        animal_data["classification"] = inat_class
        animal_data["sources"].append("iNaturalist")
        print("     ✓ Classification complete")

    # 3. GBIF (Distribution, Habitat) - FREE [[3], [4]
    print("  🌍 Fetching distribution from GBIF...")
    gbif_data = fetch_gbif_species(sci_name)
    if gbif_data:
        animal_data["ecology"]["habitat"] = gbif_data.get("habitat")
        animal_data["ecology"]["locations"] = ", ".join(gbif_data.get("distribution", [])[:5])
        if gbif_data.get("conservation_status") != "Not Evaluated":
            animal_data["ecology"]["conservation_status"] = gbif_data["conservation_status"]
        print("     ✓ Distribution data")

    # 4. IUCN (Conservation Status) - Requires API Key [[5], [6]
    print("  🛡️  Fetching conservation status from IUCN...")
    iucn_status = fetch_iucn_conservation(sci_name)
    if iucn_status != "Not Evaluated":
        animal_data["ecology"]["conservation_status"] = iucn_status
        print(f"     ✓ Conservation: {iucn_status}")
    else:
        print("     ⚠ IUCN status unavailable")

    # 5. Add distinctive features (manual curation for now)
    distinctive_features = {
        "Tiger": "Dark vertical stripes on orange-brown fur",
        "Asian Elephant": "Long trunk with single finger-like process, large ears",
        "Bald Eagle": "White head and tail contrasting with dark brown body",
    }
    animal_data["physical"]["most_distinctive_feature"] = distinctive_features.get(name)
    animal_data["physical"]["skin_type"] = "Fur" if "Elephant" not in name else "Skin"

    # 6. Add fun slogan
    slogans = {
        "Tiger": "The largest cat species in the world!",
        "Asian Elephant": "The largest land animal in Asia!",
        "Bald Eagle": "The national bird of the United States!",
    }
    animal_data["fun_facts"]["slogan"] = slogans.get(name)

    output.append(animal_data)
    print(f"  ✅ {name} complete!")
    time.sleep(1)  # Rate limiting

# Write JSON
with open("data/animals.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\n{'='*60}")
print(f"✅ Done! Generated data/animals.json with {len(output)} animals")
print(f"{'='*60}")
