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

def fetch_wikipedia_summary(animal_name):
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

def fetch_wikipedia_infobox(animal_name):
    """
    Fetch Wikipedia infobox data which contains physical stats
    Uses Wikipedia's mobile HTML which has structured infobox data
    """
    try:
        safe_name = animal_name.replace(" ", "_")
        # Fetch the page HTML to parse infobox
        r = session.get(f"https://en.m.wikipedia.org/wiki/{safe_name}", headers=headers, timeout=15)
        if r.status_code == 200:
            html = r.text
            return extract_infobox_data(html)
    except Exception as e:
        print(f"    Wikipedia infobox error: {e}")
    return {}

def extract_infobox_data(html):
    """Extract key-value pairs from Wikipedia infobox HTML"""
    data = {}
    
    # Common infobox patterns
    patterns = {
        "weight": [r'Mass[^<]*</th>\s*<td[^>]*>([^<]+)', r'Weight[^<]*</th>\s*<td[^>]*>([^<]+)'],
        "length": [r'Length[^<]*</th>\s*<td[^>]*>([^<]+)', r'Body length[^<]*</th>\s*<td[^>]*>([^<]+)'],
        "height": [r'Height[^<]*</th>\s*<td[^>]*>([^<]+)'],
        "lifespan": [r'Lifespan[^<]*</th>\s*<td[^>]*>([^<]+)', r'Longevity[^<]*</th>\s*<td[^>]*>([^<]+)'],
        "diet": [r'Diet[^<]*</th>\s*<td[^>]*>([^<]+)'],
        "habitat": [r'Habitat[^<]*</th>\s*<td[^>]*>([^<]+)'],
        "location": [r'Range[^<]*</th>\s*<td[^>]*>([^<]+)', r'Distribution[^<]*</th>\s*<td[^>]*>([^<]+)'],
    }
    
    for key, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
            if match:
                value = re.sub(r'<[^>]+>', '', match.group(1)).strip()
                # Clean up references like [1], [citation needed]
                value = re.sub(r'\[\d+\]', '', value)
                value = re.sub(r'\[citation needed\]', '', value, flags=re.IGNORECASE)
                data[key] = value.strip()
                break
    
    return data

def fetch_inaturalist_taxonomy(scientific_name):
    """
    Fetch full taxonomy from iNaturalist API
    Uses the taxa endpoint with ancestors included
    """
    try:
        # Search for the taxon with ancestors
        params = {
            "q": scientific_name,
            "per_page": 1,
            "include_ancestors": "true"
        }
        res = session.get(INAT_API, params=params, headers=headers, timeout=30)
        
        if res.status_code != 200:
            print(f"    iNaturalist API error: {res.status_code}")
            print(f"    Response: {res.text[:200]}")
            return None
        
        data = res.json()
        results = data.get("results", [])
        
        if not results:
            print(f"    iNaturalist: No results for '{scientific_name}'")
            return None
        
        taxon = results[0]
        print(f"    iNaturalist: Found '{taxon.get('name')}' (rank: {taxon.get('rank')})")
        
        # Build classification from ancestors
        classification = {field: None for field in CLASSIFICATION_FIELDS}
        classification["species"] = taxon.get("name", scientific_name)
        
        # Ancestors are returned in the response
        ancestors = taxon.get("ancestors", [])
        print(f"    iNaturalist: Found {len(ancestors)} ancestors")
        
        for anc in ancestors:
            rank = anc.get("rank", "").lower()
            name = anc.get("name")
            print(f"      - {rank}: {name}")
            
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
        import traceback
        traceback.print_exc()
    return None

def fetch_gbif_distribution(scientific_name):
    """Fetch distribution/habitat data from GBIF"""
    try:
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
        
        time.sleep(0.3)
        
        # Get distribution
        dist_res = session.get(
            f"{GBIF_API}/{species_key}/distribution",
            headers=headers,
            timeout=30
        )
        
        locations = []
        if dist_res.status_code == 200:
            dist_data = dist_res.json()
            dist_results = dist_data.get("results", [])
            for item in dist_results[:20]:
                loc = item.get("locality") or item.get("country")
                if loc and loc not in locations:
                    locations.append(loc)
        
        habitat = results[0].get("habitat")
        
        return {
            "locations": ", ".join(locations[:10]) if locations else None,
            "habitat": habitat
        }
    
    except Exception as e:
        print(f"    GBIF error: {e}")
    return None

def fetch_iucn_conservation(scientific_name):
    """Fetch conservation status from IUCN Red List API v3"""
    if not IUCN_API_KEY:
        print("    ⚠ IUCN_API_KEY not set")
        return None
    
    try:
        # Try species_name endpoint first
        url = f"{IUCN_API}/species_name/{scientific_name.replace(' ', '%20')}"
        res = session.get(url, params={"key": IUCN_API_KEY}, timeout=30)
        
        if res.status_code == 200:
            data = res.json()
            result = data.get("result", [])
            if result:
                return {
                    "conservation_status": result[0].get("category"),
                    "population_trend": result[0].get("population_trend")
                }
        
        # Fallback to taxonomicname
        url = f"{IUCN_API}/taxonomicname/{scientific_name.replace(' ', '%20')}"
        res = session.get(url, params={"key": IUCN_API_KEY}, timeout=30)
        
        if res.status_code == 200:
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
    """Load existing cached data"""
    cache_file = f"data/{qid}.json"
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return None

def save_cached_data(qid, data):
    """Save data to cache"""
    cache_file = f"data/{qid}.json"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# --- Main ---
def generate_animal_data(animals_list, force_update=False, debug=False):
    """Generate animal data with comprehensive API fetching"""
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
        
        # Initialize data structure
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
        
        # 1. Wikipedia Summary + Infobox
        if not animal_data["image"] or force_update:
            print("  📖 Fetching from Wikipedia...")
            wiki_data = fetch_wikipedia_summary(name)
            
            if wiki_data["summary"]:
                animal_data["summary"] = wiki_data["summary"]
                animal_data["description"] = wiki_data["description"]
                animal_data["image"] = wiki_data["image"]
                animal_data["wikipedia_url"] = wiki_data["url"]
                
                if "Wikipedia" not in animal_data["sources"]:
                    animal_data["sources"].append("Wikipedia")
                
                # Fetch infobox for physical stats
                print("     📋 Fetching infobox data...")
                infobox = fetch_wikipedia_infobox(name)
                
                if infobox:
                    for key, value in infobox.items():
                        if key in animal_data["physical"] and not animal_data["physical"][key]:
                            animal_data["physical"][key] = value
                            print(f"        ✓ {key}: {value}")
                        elif key in animal_data["ecology"] and not animal_data["ecology"][key]:
                            animal_data["ecology"][key] = value
                            print(f"        ✓ {key}: {value}")
                
                print("     ✓ Summary and infobox fetched")
            else:
                print("     ⚠ No Wikipedia data found")
        
        # 2. iNaturalist Taxonomy (with debug output)
        if not animal_data["classification"]["kingdom"] or force_update:
            print("  🔬 Fetching taxonomy from iNaturalist...")
            inat_class = fetch_inaturalist_taxonomy(sci_name)
            
            if inat_class:
                animal_data["classification"] = inat_class
                if "iNaturalist" not in animal_data["sources"]:
                    animal_data["sources"].append("iNaturalist")
                
                # Verify classification was populated
                filled = sum(1 for v in inat_class.values() if v)
                print(f"     ✓ Classification: {filled}/7 fields filled")
            else:
                print("     ⚠ iNaturalist data unavailable")
        
        # 3. GBIF Distribution
        if not animal_data["ecology"]["locations"] or force_update:
            print("  🌍 Fetching distribution from GBIF...")
            gbif_data = fetch_gbif_distribution(sci_name)
            
            if gbif_data:
                if gbif_data.get("locations") and not animal_data["ecology"]["locations"]:
                    animal_data["ecology"]["locations"] = gbif_data["locations"]
                    print(f"     ✓ Locations: {gbif_data['locations'][:60]}...")
                if gbif_data.get("habitat") and not animal_data["ecology"]["habitat"]:
                    animal_data["ecology"]["habitat"] = gbif_data["habitat"]
                
                if "GBIF" not in animal_data["sources"]:
                    animal_data["sources"].append("GBIF")
            else:
                print("     ⚠ GBIF data unavailable")
        
        # 4. IUCN Conservation
        if not animal_data["ecology"]["conservation_status"] or force_update:
            print("  🛡️  Fetching conservation status from IUCN...")
            iucn_data = fetch_iucn_conservation(sci_name)
            
            if iucn_data:
                if iucn_data.get("conservation_status"):
                    animal_data["ecology"]["conservation_status"] = iucn_data["conservation_status"]
                    print(f"     ✓ Conservation: {iucn_data['conservation_status']}")
                
                if "IUCN" not in animal_data["sources"]:
                    animal_data["sources"].append("IUCN")
            else:
                print("     ⚠ IUCN data unavailable")
        
        # Update timestamp
        animal_data["last_updated"] = datetime.now().isoformat()
        
        # Save cache
        save_cached_data(qid, animal_data)
        
        output.append(animal_data)
        print(f"  ✅ {name} complete!")
        
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
    force = "--force" in os.sys.argv
    debug = "--debug" in os.sys.argv
    generate_animal_data(TEST_ANIMALS, force_update=force, debug=debug)
