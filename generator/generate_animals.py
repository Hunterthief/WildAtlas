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
IUCN_API_V4 = "https://api.iucnredlist.org/api/v4"  # ← Updated to v4!

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
    """Extract physical statistics from Wikipedia summary text"""
    stats = {
        "weight": None,
        "length": None,
        "height": None,
        "lifespan": None,
        "top_speed": None
    }
    
    if not text:
        return stats
    
    # Weight
    weight_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(kg|tonnes?|t\b|lbs?|pounds?)', text, re.IGNORECASE)
    if weight_match:
        value = weight_match.group(1).replace(',', '.')
        unit = weight_match.group(2).lower()
        if unit in ['t', 'tonne', 'tonnes', 'ton', 'tons']:
            unit = 't'
        elif unit in ['kg', 'kilogram', 'kilograms']:
            unit = 'kg'
        elif unit in ['lb', 'lbs', 'pound', 'pounds']:
            unit = 'lbs'
        stats["weight"] = f"{value} {unit}"
    
    # Length
    length_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(m\b|metres?|cm\b|ft\b|feet)', text, re.IGNORECASE)
    if length_match:
        value = length_match.group(1).replace(',', '.')
        unit = length_match.group(2).lower()
        if unit in ['m', 'metre', 'metres', 'meter', 'meters']:
            unit = 'm'
        elif unit in ['cm', 'centimetre', 'centimetres']:
            unit = 'cm'
        elif unit in ['ft', 'feet', 'foot']:
            unit = 'ft'
        stats["length"] = f"{value} {unit}"
    
    # Lifespan
    lifespan_match = re.search(r'(\d+(?:-\d+)?)\s*(years?|yrs?)', text, re.IGNORECASE)
    if lifespan_match:
        stats["lifespan"] = f"{lifespan_match.group(1)} years"
    
    # Speed
    speed_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(km/h|kmph|mph)', text, re.IGNORECASE)
    if speed_match:
        stats["top_speed"] = f"{speed_match.group(1)} {speed_match.group(2).lower()}"
    
    return stats

def extract_diet(text):
    """Extract diet type from text"""
    if not text:
        return None
    
    text_lower = text.lower()
    
    if any(word in text_lower for word in ['carnivore', 'meat', 'predator', 'hunts']):
        return "Carnivore"
    elif any(word in text_lower for word in ['herbivore', 'plant', 'vegetation', 'grazes']):
        return "Herbivore"
    elif any(word in text_lower for word in ['omnivore', 'both plants and animals']):
        return "Omnivore"
    
    return None

def fetch_inaturalist_taxonomy(scientific_name):
    """Fetch full taxonomy from iNaturalist API"""
    try:
        print(f"    iNaturalist: Searching for '{scientific_name}'...")
        
        params = {"q": scientific_name, "per_page": 1, "rank": "species"}
        res = session.get(INAT_API, params=params, headers=headers, timeout=30)
        
        if res.status_code != 200:
            print(f"    iNaturalist search error: {res.status_code}")
            return None
        
        data = res.json()
        results = data.get("results", [])
        
        if not results:
            params = {"q": scientific_name, "per_page": 1}
            res = session.get(INAT_API, params=params, headers=headers, timeout=30)
            if res.status_code == 200:
                data = res.json()
                results = data.get("results", [])
        
        if not results:
            print(f"    iNaturalist: No results found")
            return None
        
        taxon = results[0]
        print(f"    iNaturalist: Found '{taxon.get('name')}' (rank: {taxon.get('rank')})")
        
        time.sleep(0.5)
        
        ancestor_ids = taxon.get("ancestor_ids", [])
        print(f"    iNaturalist: Found {len(ancestor_ids)} ancestor IDs")
        
        if not ancestor_ids:
            return None
        
        anc_res = session.get(
            f"{INAT_API}/{','.join(map(str, ancestor_ids))}",
            headers=headers,
            timeout=30
        )
        
        if anc_res.status_code != 200:
            return None
        
        anc_data = anc_res.json()
        ancestors = anc_data.get("results", [])
        
        classification = {field: None for field in CLASSIFICATION_FIELDS}
        classification["species"] = taxon.get("name", scientific_name)
        
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
        
        filled = sum(1 for v in classification.values() if v)
        print(f"    iNaturalist: Classification complete ({filled}/7 fields)")
        
        return classification
    
    except Exception as e:
        print(f"    iNaturalist error: {e}")
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
        
        time.sleep(0.5)
        
        dist_res = session.get(
            f"{GBIF_API}/{species_key}/distribution",
            headers=headers,
            timeout=30
        )
        
        locations = []
        if dist_res.status_code == 200:
            dist_data = dist_res.json()
            dist_results = dist_data.get("results", [])
            for item in dist_results[:10]:
                loc = item.get("locality") or item.get("country")
                if loc:
                    locations.append(loc)
        
        return {
            "locations": ", ".join(locations[:5]) if locations else None,
            "habitat": results[0].get("habitat")
        }
    
    except Exception as e:
        print(f"    GBIF error: {e}")
    return None

def fetch_iucn_conservation(scientific_name):
    """
    Fetch conservation status from IUCN Red List API v4
    Uses Bearer token authentication (not query param like v3)
    """
    if not IUCN_API_KEY:
        print("    ⚠ IUCN_API_KEY not set in environment")
        return None
    
    try:
        # Parse scientific name into genus and species
        name_parts = scientific_name.split(" ")
        if len(name_parts) >= 2:
            genus = name_parts[0]
            species = name_parts[1]
        else:
            genus = scientific_name
            species = ""
        
        # API v4 endpoint with Bearer token auth
        url = f"{IUCN_API_V4}/taxa/scientific_name/{genus}/{species}"
        
        iucn_headers = {
            "Authorization": f"Bearer {IUCN_API_KEY}",
            "Accept": "application/json"
        }
        
        print(f"    IUCN: Fetching from {url}")
        res = session.get(url, headers=iucn_headers, timeout=30)
        
        print(f"    IUCN: Response status: {res.status_code}")
        
        if res.status_code == 403:
            print("    IUCN: 403 Forbidden - Check API key validity")
            return None
        elif res.status_code == 404:
            print("    IUCN: Species not found in Red List")
            return None
        elif res.status_code != 200:
            print(f"    IUCN: API error: {res.status_code} - {res.text[:200]}")
            return None
        
        data = res.json()
        
        # API v4 returns assessments array
        assessments = data.get("assessments", [])
        
        if not assessments:
            print("    IUCN: No assessments found")
            return None
        
        # Get the latest assessment
        latest = assessments[0]
        
        return {
            "conservation_status": latest.get("category"),
            "population_trend": latest.get("population_trend"),
            "assessment_date": latest.get("assessment_date")
        }
    
    except Exception as e:
        print(f"    IUCN error: {e}")
        import traceback
        traceback.print_exc()
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

# --- Main ---
def generate_animal_data(animals_list, force_update=False):
    """Generate or update animal data with smart caching"""
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
        
        # 1. Wikipedia
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
                
                print("     Extracting physical stats from summary...")
                stats = extract_physical_stats(wiki_data["summary"])
                for stat_name, stat_value in stats.items():
                    if stat_value:
                        animal_data["physical"][stat_name] = stat_value
                        print(f"       ✓ {stat_name}: {stat_value}")
                
                diet = extract_diet(wiki_data["summary"])
                if diet:
                    animal_data["ecology"]["diet"] = diet
                    print(f"       ✓ diet: {diet}")
                
                print("     ✓ Summary and stats extracted")
            else:
                print("     ⚠ No Wikipedia data found")
        
        # 2. iNaturalist (Taxonomy)
        if not animal_data["classification"]["kingdom"] or force_update:
            print("  🔬 Fetching taxonomy from iNaturalist...")
            inat_class = fetch_inaturalist_taxonomy(sci_name)
            
            if inat_class:
                animal_data["classification"] = inat_class
                if "iNaturalist" not in animal_data["sources"]:
                    animal_data["sources"].append("iNaturalist")
            else:
                print("     ⚠ iNaturalist data unavailable")
        
        # 3. GBIF (Distribution)
        if not animal_data["ecology"]["locations"] or force_update:
            print("  🌍 Fetching distribution from GBIF...")
            gbif_data = fetch_gbif_distribution(sci_name)
            
            if gbif_
                if gbif_data.get("locations"):
                    animal_data["ecology"]["locations"] = gbif_data["locations"]
                    print(f"     ✓ Locations: {gbif_data['locations'][:50]}...")
                if gbif_data.get("habitat"):
                    animal_data["ecology"]["habitat"] = gbif_data["habitat"]
                
                if "GBIF" not in animal_data["sources"]:
                    animal_data["sources"].append("GBIF")
            else:
                print("     ⚠ GBIF data unavailable")
        
        # 4. IUCN (Conservation Status) - API v4
        if not animal_data["ecology"]["conservation_status"] or force_update:
            print("  🛡️  Fetching conservation status from IUCN (API v4)...")
            iucn_data = fetch_iucn_conservation(sci_name)
            
            if iucn_data:
                if iucn_data.get("conservation_status"):
                    animal_data["ecology"]["conservation_status"] = iucn_data["conservation_status"]
                    print(f"     ✓ Conservation: {iucn_data['conservation_status']}")
                if iucn_data.get("population_trend"):
                    animal_data["ecology"]["estimated_population_size"] = iucn_data["population_trend"]
                    print(f"     ✓ Population trend: {iucn_data['population_trend']}")
                
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
    generate_animal_data(TEST_ANIMALS, force_update=force)
