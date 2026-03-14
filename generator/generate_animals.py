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

session = requests.Session()
retry = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry)
session.mount("https://", adapter)

headers = {
    "User-Agent": "WildAtlasBot/1.0 (https://github.com/Hunterthief/WildAtlas)",
    "Accept": "application/json"
}

IUCN_API_KEY = os.getenv("IUCN_API_KEY", "")

WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
INAT_API = "https://api.inaturalist.org/v1/taxa"
GBIF_API = "https://api.gbif.org/v1/species"

CLASSIFICATION_FIELDS = ["kingdom", "phylum", "class", "order", "family", "genus", "species"]

def fetch_wikipedia(animal_name):
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
    stats = {"weight": None, "length": None, "height": None, "lifespan": None, "top_speed": None}
    if not text:
        return stats
    
    weight_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(kg|tonnes?|t\b|lbs?|pounds?)', text, re.IGNORECASE)
    if weight_match:
        value = weight_match.group(1).replace(',', '.')
        unit = weight_match.group(2).lower()
        if unit in ['t', 'tonne', 'tonnes']: unit = 't'
        elif unit in ['kg', 'kilogram', 'kilograms']: unit = 'kg'
        elif unit in ['lb', 'lbs', 'pound', 'pounds']: unit = 'lbs'
        stats["weight"] = f"{value} {unit}"
    
    length_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(m\b|metres?|cm\b|ft\b|feet)', text, re.IGNORECASE)
    if length_match:
        value = length_match.group(1).replace(',', '.')
        unit = length_match.group(2).lower()
        if unit in ['m', 'metre', 'metres', 'meter', 'meters']: unit = 'm'
        elif unit in ['cm', 'centimetre', 'centimetres']: unit = 'cm'
        elif unit in ['ft', 'feet', 'foot']: unit = 'ft'
        stats["length"] = f"{value} {unit}"
    
    lifespan_match = re.search(r'(\d+(?:-\d+)?)\s*(years?|yrs?)', text, re.IGNORECASE)
    if lifespan_match:
        stats["lifespan"] = f"{lifespan_match.group(1)} years"
    
    speed_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(km/h|kmph|mph)', text, re.IGNORECASE)
    if speed_match:
        stats["top_speed"] = f"{speed_match.group(1)} {speed_match.group(2).lower()}"
    
    return stats

def extract_diet(text):
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
    try:
        print(f"    iNaturalist: Searching for '{scientific_name}'...")
        params = {"q": scientific_name, "per_page": 1, "rank": "species"}
        res = session.get(INAT_API, params=params, headers=headers, timeout=30)
        
        if res.status_code != 200:
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
            return None
        
        taxon = results[0]
        print(f"    iNaturalist: Found '{taxon.get('name')}' (rank: {taxon.get('rank')})")
        time.sleep(0.5)
        
        ancestor_ids = taxon.get("ancestor_ids", [])
        if not ancestor_ids:
            return None
        
        anc_res = session.get(f"{INAT_API}/{','.join(map(str, ancestor_ids))}", headers=headers, timeout=30)
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
            if rank == "kingdom": classification["kingdom"] = name
            elif rank == "phylum": classification["phylum"] = name
            elif rank == "class": classification["class"] = name
            elif rank == "order": classification["order"] = name
            elif rank == "family": classification["family"] = name
            elif rank == "genus": classification["genus"] = name
        
        filled = sum(1 for v in classification.values() if v)
        print(f"    iNaturalist: Classification complete ({filled}/7 fields)")
        return classification
    except Exception as e:
        print(f"    iNaturalist error: {e}")
    return None

def fetch_gbif_distribution(scientific_name):
    """Fetch distribution/habitat/conservation from GBIF"""
    try:
        params = {"q": scientific_name, "type": "SPECIES", "limit": 1}
        res = session.get(f"{GBIF_API}/search", params=params, headers=headers, timeout=30)
        
        if res.status_code != 200:
            return None
        
        data = res.json()
        results = data.get("results", [])
        
        if not results:
            return None
        
        species_data = results[0]
        species_key = species_data.get("key")
        
        # Extract conservation status from GBIF
        conservation_status = species_data.get("conservationStatus")
        
        time.sleep(0.5)
        
        locations = []
        if species_key:
            dist_res = session.get(f"{GBIF_API}/{species_key}/distribution", headers=headers, timeout=30)
            if dist_res.status_code == 200:
                dist_data = dist_res.json()
                dist_results = dist_data.get("results", [])
                for item in dist_results[:10]:
                    loc = item.get("locality") or item.get("country")
                    if loc:
                        locations.append(loc)
        
        return {
            "locations": ", ".join(locations[:5]) if locations else None,
            "habitat": species_data.get("habitat"),
            "conservation_status": conservation_status
        }
    except Exception as e:
        print(f"    GBIF error: {e}")
    return None

def load_cached_data(qid):
    cache_file = f"data/{qid}.json"
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return None

def save_cached_data(qid, data):
    cache_file = f"data/{qid}.json"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def generate_animal_data(animals_list, force_update=False):
    output = []
    
    for i, a in enumerate(animals_list):
        name = a["name"]
        sci_name = a["scientific_name"]
        qid = a.get("qid", f"animal_{i}")
        
        print(f"\n{'='*60}")
        print(f"[{i+1}/{len(animals_list)}] Processing: {name} ({sci_name})")
        print(f"{'='*60}")
        
        cached = load_cached_data(qid) if not force_update else None
        
        if cached and not force_update:
            print(f"  📁 Found cached data from {cached.get('last_updated', 'unknown')}")
        
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
                "physical": {"weight": None, "height": None, "length": None, "top_speed": None, "lifespan": None, "color": None, "skin_type": None, "most_distinctive_feature": None},
                "ecology": {"diet": None, "prey": None, "habitat": None, "locations": None, "group_behavior": None, "lifestyle": None, "biggest_threat": None, "conservation_status": None, "estimated_population_size": None},
                "reproduction": {"gestation_period": None, "average_litter_size": None, "name_of_young": None},
                "fun_facts": {"slogan": None},
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
        
        # 2. iNaturalist
        if not animal_data["classification"]["kingdom"] or force_update:
            print("  🔬 Fetching taxonomy from iNaturalist...")
            inat_class = fetch_inaturalist_taxonomy(sci_name)
            
            if inat_class:
                animal_data["classification"] = inat_class
                if "iNaturalist" not in animal_data["sources"]:
                    animal_data["sources"].append("iNaturalist")
        
        # 3. GBIF (includes conservation status)
        if not animal_data["ecology"]["locations"] or force_update:
            print("  🌍 Fetching distribution from GBIF...")
            gbif_data = fetch_gbif_distribution(sci_name)
            
            if gbif_data:
                if gbif_data.get("locations"):
                    animal_data["ecology"]["locations"] = gbif_data["locations"]
                    print(f"     ✓ Locations: {gbif_data['locations'][:50]}...")
                if gbif_data.get("habitat"):
                    animal_data["ecology"]["habitat"] = gbif_data["habitat"]
                if gbif_data.get("conservation_status"):
                    animal_data["ecology"]["conservation_status"] = gbif_data["conservation_status"]
                    print(f"     ✓ Conservation: {gbif_data['conservation_status']}")
                
                if "GBIF" not in animal_data["sources"]:
                    animal_data["sources"].append("GBIF")
            else:
                print("     ⚠ GBIF data unavailable")
        
        animal_data["last_updated"] = datetime.now().isoformat()
        save_cached_data(qid, animal_data)
        output.append(animal_data)
        print(f"  ✅ {name} complete!")
        time.sleep(1)
    
    with open("data/animals.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"✅ Done! Generated data/animals.json with {len(output)} animals")
    print(f"{'='*60}")
    
    return output

TEST_ANIMALS = [
    {"name": "Tiger", "scientific_name": "Panthera tigris", "qid": "Q132186"},
    {"name": "Asian Elephant", "scientific_name": "Elephas maximus", "qid": "Q7372"},
    {"name": "Bald Eagle", "scientific_name": "Haliaeetus leucocephalus", "qid": "Q25319"},
]

if __name__ == "__main__":
    force = "--force" in os.sys.argv
    generate_animal_data(TEST_ANIMALS, force_update=force)
