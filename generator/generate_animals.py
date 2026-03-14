# generator/generate_animals.py
import requests
import json
import time
import os
import re
from datetime import datetime
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

# --- API Keys from GitHub Secrets ---
IUCN_API_KEY = os.getenv("IUCN_API_KEY", "")

# --- APIs ---
WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
INAT_API = "https://api.inaturalist.org/v1/taxa"
GBIF_API = "https://api.gbif.org/v1/species"
IUCN_API = "https://apiv3.iucnredlist.org/api/v3"

# --- Classification fields ---
CLASSIFICATION_FIELDS = ["kingdom", "phylum", "class", "order", "family", "genus", "species"]

def fetch_wikipedia(animal_name):
    """Fetch summary, description, and image from Wikipedia"""
    try:
        safe_name = animal_name.replace(" ", "_")
        r = session.get(f"{WIKI_API}{safe_name}", headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            return {
                "summary": data.get("extract", ""),
                "description": data.get("description", ""),
                "image": data.get("thumbnail", {}).get("source", ""),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                "title": data.get("title", "")
            }
    except Exception as e:
        print(f"    Wikipedia error: {e}")
    return {"summary": "", "description": "", "image": "", "url": "", "title": ""}

def extract_physical_stats(text):
    """Extract physical statistics from text using regex patterns"""
    stats = {
        "weight": None,
        "length": None,
        "height": None,
        "lifespan": None,
        "top_speed": None
    }
    
    if not text:
        return stats
    
    # Weight patterns (e.g., "300 kg", "4 t", "660 lbs")
    weight_patterns = [
        r'(\d+(?:\.\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t\b|lbs?|pounds?)',
        r'weighs?\s*(?:around|about|approximately)?\s*(\d+(?:\.\d+)?)\s*(kg|tonnes?|lbs?)',
        r'mass\s*(?:of)?\s*(\d+(?:\.\d+)?)\s*(kg|tonnes?|lbs?)'
    ]
    for pattern in weight_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            stats["weight"] = f"{match.group(1)} {match.group(2)}".strip()
            break
    
    # Length patterns (e.g., "2.8 m", "10 ft", "300 cm")
    length_patterns = [
        r'(\d+(?:\.\d+)?)\s*(m|metres?|cm|centimetres?|mm|millimetres?|ft|feet|in|inches?)',
        r'length\s*(?:of)?\s*(\d+(?:\.\d+)?)\s*(m|cm|ft)',
        r'long\b.*?(\d+(?:\.\d+)?)\s*(m|ft|cm)'
    ]
    for pattern in length_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            stats["length"] = f"{match.group(1)} {match.group(2)}".strip()
            break
    
    # Height patterns
    height_patterns = [
        r'(\d+(?:\.\d+)?)\s*(m|metres?|cm|centimetres?|ft|feet)\s*(?:tall|height|high)',
        r'height\s*(?:of)?\s*(\d+(?:\.\d+)?)\s*(m|cm|ft)'
    ]
    for pattern in height_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            stats["height"] = f"{match.group(1)} {match.group(2)}".strip()
            break
    
    # Lifespan patterns (e.g., "10-15 years", "20 year lifespan")
    lifespan_patterns = [
        r'(\d+(?:-\d+)?)\s*(years?|yrs?|year\s*old)',
        r'lifespan\s*(?:of)?\s*(\d+(?:-\d+)?)\s*(years?)',
        r'live\s*(?:for)?\s*(\d+(?:-\d+)?)\s*(years?)'
    ]
    for pattern in lifespan_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            stats["lifespan"] = f"{match.group(1)} years".replace('year', '').replace('-', '-').strip()
            if '-' not in stats["lifespan"]:
                stats["lifespan"] = stats["lifespan"].replace('years', 'years').strip()
            break
    
    # Speed patterns
    speed_patterns = [
        r'(\d+(?:\.\d+)?)\s*(km/h|kmph|mph|mi/h|kilometres? per hour|miles? per hour)',
        r'speed\s*(?:of)?\s*(\d+(?:\.\d+)?)\s*(km/h|mph)'
    ]
    for pattern in speed_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            stats["top_speed"] = f"{match.group(1)} {match.group(2)}".strip()
            break
    
    return stats

def extract_diet(text):
    """Extract diet type from text"""
    if not text:
        return None
    
    text_lower = text.lower()
    
    # Check for specific diet keywords
    if any(word in text_lower for word in ['carnivore', 'meat-eater', 'predator', 'hunts', 'prey']):
        if 'exclusively' in text_lower or 'obligate' in text_lower:
            return "Carnivore"
        return "Carnivore"
    elif any(word in text_lower for word in ['herbivore', 'plant-eater', 'vegetation', 'grazes', 'browses']):
        return "Herbivore"
    elif any(word in text_lower for word in ['omnivore', 'both plants and animals', 'varied diet']):
        return "Omnivore"
    
    return None

def fetch_inaturalist_taxonomy(scientific_name):
    """
    Fetch full taxonomy from iNaturalist API [[1], [2]]
    Returns classification dict with all ranks
    """
    try:
        # Step 1: Find the species
        params = {"q": scientific_name, "per_page": 1, "rank": "species"}
        res = session.get(INAT_API, params=params, headers=headers, timeout=30)
        
        if res.status_code != 200:
            print(f"    iNaturalist search error: {res.status_code}")
            return None
        
        data = res.json()
        results = data.get("results", [])
        
        if not results:
            # Try without rank filter
            params = {"q": scientific_name, "per_page": 1}
            res = session.get(INAT_API, params=params, headers=headers, timeout=30)
            if res.status_code == 200:
                data = res.json()
                results = data.get("results", [])
        
        if not results:
            return None
        
        taxon = results[0]
        time.sleep(0.5)  # Rate limiting
        
        # Step 2: Fetch all ancestors
        ancestor_ids = taxon.get("ancestor_ids", [])
        if not ancestor_ids:
            return None
        
        # Fetch ancestor details (comma-separated IDs)
        anc_res = session.get(
            f"{INAT_API}/{','.join(map(str, ancestor_ids))}",
            headers=headers,
            timeout=30
        )
        
        if anc_res.status_code != 200:
            return None
        
        anc_data = anc_res.json()
        ancestors = anc_data.get("results", [])
        
        # Build classification
        classification = {field: None for field in CLASSIFICATION_FIELDS}
        classification["species"] = taxon.get("name", scientific_name)
        
        for anc in ancestors:
            rank = anc.get("rank", "").lower()
            name = anc.get("name")
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
        print(f"    iNaturalist error: {e}")
    return None

def fetch_gbif_distribution(scientific_name):
    """
    Fetch distribution/habitat data from GBIF [[16], [19]]
    """
    try:
        # Search for species
        params = {"q": scientific_name, "type": "SPECIES", "limit": 1}
        res = session.get(f"{GBIF_API}/search", params=params, headers=headers, timeout=30)
        
        if res.status_code != 200:
            return None
        
        data = res.json()
        results = data.get("results", [])
        
        if not results:
            return None
        
        species_key = results[0].get("key")
        if not species_key:
            return None
        
        time.sleep(0.5)  # Rate limiting
        
        # Get distribution data
        dist_res = session.get(
            f"{GBIF_API}/{species_key}/distribution",
            headers=headers,
            timeout=30
        )
        
        locations = []
        if dist_res.status_code == 200:
            dist_data = dist_res.json()
            results = dist_data.get("results", [])
            # Extract country/locality names
            for item in results[:10]:  # Limit to 10 locations
                loc = item.get("locality") or item.get("country")
                if loc:
                    locations.append(loc)
        
        return {
            "locations": ", ".join(locations[:5]) if locations else None,
            "habitat": results[0].get("habitat") if results else None
        }
    
    except Exception as e:
        print(f"    GBIF error: {e}")
    return None

def fetch_iucn_conservation(scientific_name):
    """
    Fetch conservation status from IUCN Red List API v3 [[21], [27]]
    Requires API key from https://apiv3.iucnredlist.org/api/v3/token
    """
    if not IUCN_API_KEY:
        return None
    
    try:
        url = f"{IUCN_API}/taxonomicname/{scientific_name.replace(' ', '%20')}"
        res = session.get(url, params={"key": IUCN_API_KEY}, timeout=30)
        
        if res.status_code != 200:
            return None
        
        data = res.json()
        result = data.get("result", [])
        
        if result:
            return {
                "conservation_status": result[0].get("category"),
                "population_trend": result[0].get("population_trend")
            }
    
    except Exception as e:
        print(f"    IUCN error: {e}")
    return None

def load_cached_data(qid):
    """Load existing cached data for an animal"""
    cache_file = f"data/{qid}.json"
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return None

def save_cached_data(qid, data):
    """Save data to cache file"""
    cache_file = f"data/{qid}.json"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def needs_update(cached, field_path, new_value):
    """Check if a field needs updating (null, missing, or old)"""
    if new_value is None:
        return False
    
    # Navigate to field in cached data
    parts = field_path.split(".")
    current = cached
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return True
    
    # Update if null or empty
    if current is None or current == "":
        return True
    
    return False

def update_nested_dict(d, path, value):
    """Update a nested dictionary value using dot notation path"""
    keys = path.split(".")
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value

# --- Main ---
def generate_animal_data(animals_list, force_update=False):
    """
    Generate or update animal data with smart caching
    
    Args:
        animals_list: List of {"name": str, "scientific_name": str, "qid": str}
        force_update: If True, re-fetch all data even if cached
    """
    output = []
    
    for i, a in enumerate(animals_list):
        name = a["name"]
        sci_name = a["scientific_name"]
        qid = a.get("qid", f"animal_{i}")
        
        print(f"\n{'='*60}")
        print(f"[{i+1}/{len(animals_list)}] Processing: {name} ({sci_name})")
        print(f"{'='*60}")
        
        # Load cached data
        cached = load_cached_data(qid) if not force_update else None
        
        if cached and not force_update:
            print(f"  📁 Found cached data from {cached.get('last_updated', 'unknown')}")
        
        # Initialize or load data structure
        if cached:
            animal_data = cached
            animal_data["sources"] = list(set(animal_data.get("sources", [])))
        else:
            animal_data = {
                "name": name,
                "scientific_name": sci_name,
                "qid": qid,
                "name_meaning": None,
                "description": None,
                "summary": None,
                "image": None,
                "wikipedia_url": None,
                "classification": {field: None for field in CLASSIFICATION_FIELDS},
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
                "reproduction": {
                    "gestation_period": None,
                    "average_litter_size": None,
                    "name_of_young": None
                },
                "fun_facts": {
                    "slogan": None
                },
                "sources": [],
                "last_updated": None
            }
        
        # 1. Wikipedia (Images, Summary, Description)
        if not animal_data["image"] or force_update:
            print("  📖 Fetching from Wikipedia...")
            wiki_data = fetch_wikipedia(name)
            
            if wiki_data["summary"]:
                animal_data["summary"] = wiki_data["summary"]
                animal_data["description"] = wiki_data["description"]
                animal_data["image"] = wiki_data["image"]
                animal_data["wikipedia_url"] = wiki_data["url"]
                
                if "Wikipedia" not in animal_data["sources"]:
                    animal_data["sources"].append("Wikipedia")
                
                # Extract physical stats from summary
                stats = extract_physical_stats(wiki_data["summary"])
                for stat_name, stat_value in stats.items():
                    if stat_value and not animal_data["physical"].get(stat_name):
                        animal_data["physical"][stat_name] = stat_value
                
                # Extract diet
                diet = extract_diet(wiki_data["summary"])
                if diet and not animal_data["ecology"].get("diet"):
                    animal_data["ecology"]["diet"] = diet
                
                print("     ✓ Summary, image, and stats extracted")
            else:
                print("     ⚠ No Wikipedia data found")
        
        # 2. iNaturalist (Taxonomy) - Only if classification is incomplete
        if not animal_data["classification"]["kingdom"] or force_update:
            print("  🔬 Fetching taxonomy from iNaturalist...")
            inat_class = fetch_inaturalist_taxonomy(sci_name)
            
            if inat_class:
                animal_data["classification"] = inat_class
                if "iNaturalist" not in animal_data["sources"]:
                    animal_data["sources"].append("iNaturalist")
                print("     ✓ Classification complete")
            else:
                print("     ⚠ iNaturalist data unavailable")
        
        # 3. GBIF (Distribution) - Only if locations is empty
        if not animal_data["ecology"]["locations"] or force_update:
            print("  🌍 Fetching distribution from GBIF...")
            gbif_data = fetch_gbif_distribution(sci_name)
            
            if gbif_data:
                if gbif_data.get("locations") and not animal_data["ecology"]["locations"]:
                    animal_data["ecology"]["locations"] = gbif_data["locations"]
                if gbif_data.get("habitat") and not animal_data["ecology"]["habitat"]:
                    animal_data["ecology"]["habitat"] = gbif_data["habitat"]
                
                if "GBIF" not in animal_data["sources"]:
                    animal_data["sources"].append("GBIF")
                print("     ✓ Distribution data added")
            else:
                print("     ⚠ GBIF data unavailable")
        
        # 4. IUCN (Conservation Status) - Only if not set
        if not animal_data["ecology"]["conservation_status"] or force_update:
            print("  🛡️  Fetching conservation status from IUCN...")
            iucn_data = fetch_iucn_conservation(sci_name)
            
            if iucn_data:
                if iucn_data.get("conservation_status"):
                    animal_data["ecology"]["conservation_status"] = iucn_data["conservation_status"]
                if iucn_data.get("population_trend") and not animal_data["ecology"]["estimated_population_size"]:
                    animal_data["ecology"]["estimated_population_size"] = iucn_data["population_trend"]
                
                if "IUCN" not in animal_data["sources"]:
                    animal_data["sources"].append("IUCN")
                print(f"     ✓ Conservation: {iucn_data.get('conservation_status')}")
            else:
                print("     ⚠ IUCN data unavailable (check API key)")
        
        # Update timestamp
        animal_data["last_updated"] = datetime.now().isoformat()
        
        # Save individual cache
        save_cached_data(qid, animal_data)
        
        output.append(animal_data)
        print(f"  ✅ {name} complete!")
        
        # Rate limiting
        time.sleep(1)
    
    # Write combined output
    with open("data/animals.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"✅ Done! Generated data/animals.json with {len(output)} animals")
    print(f"{'='*60}")
    
    return output

# --- Test animals ---
TEST_ANIMALS = [
    {"name": "Tiger", "scientific_name": "Panthera tigris", "qid": "Q132186"},
    {"name": "Asian Elephant", "scientific_name": "Elephas maximus", "qid": "Q7372"},
    {"name": "Bald Eagle", "scientific_name": "Haliaeetus leucocephalus", "qid": "Q25319"},
]

if __name__ == "__main__":
    # Check if we should force update all
    force = "--force" in os.sys.argv
    
    generate_animal_data(TEST_ANIMALS, force_update=force)
