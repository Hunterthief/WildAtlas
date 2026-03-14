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

WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
WIKI_ACTION_API = "https://en.wikipedia.org/w/api.php"
INAT_API = "https://api.inaturalist.org/v1/taxa"
GBIF_API = "https://api.gbif.org/v1/species"

CLASSIFICATION_FIELDS = ["kingdom", "phylum", "class", "order", "family", "genus", "species"]

def fetch_wikipedia_summary(animal_name):
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

def fetch_wikipedia_all_sections(animal_name):
    """Fetch full article content to search all sections"""
    try:
        safe_name = animal_name.replace(" ", "_")
        params = {
            "action": "parse",
            "page": safe_name,
            "prop": "text|sections",
            "format": "json"
        }
        r = session.get(WIKI_ACTION_API, params=params, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            parse_data = data.get("parse", {})
            sections = parse_data.get("sections", [])
            full_text = parse_data.get("text", {}).get("*", "")
            
            # Strip HTML tags
            text = re.sub(r'<[^>]+>', ' ', full_text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text, sections
    except Exception as e:
        print(f"    Wikipedia sections error: {e}")
    return "", []

def extract_physical_stats(text):
    """Extract physical statistics with range support (e.g., 1.4–2.8 m)"""
    stats = {"weight": None, "length": None, "height": None, "lifespan": None, "top_speed": None}
    if not text:
        return stats
    
    # Weight - support ranges like "200–260 kg" or "200-260 kg"
    weight_patterns = [
        r'weigh\s*(?:of|up to)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to)\s*(\d+(?:[.,]\d+)?)\s*(kg|tonnes?|t\b|lbs?|pounds?)',
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to)\s*(\d+(?:[.,]\d+)?)\s*(kg|tonnes?|t\b|lbs?|pounds?)\s*(?:weight|weigh|mass)',
        r'(\d+(?:[.,]\d+)?)\s*(kg|tonnes?|t\b|lbs?|pounds?)\s*(?:weight|weigh|mass)',
    ]
    for pattern in weight_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            if len(groups) == 3:
                # Single value: 300 kg
                val = float(groups[0].replace(',', '.'))
                unit = groups[1].lower().strip()
                if unit in ['t', 'tonne', 'tonnes'] and 0.1 < val < 10:
                    stats["weight"] = f"{val} {unit}"
                    break
                elif unit in ['kg', 'kilogram', 'kilograms'] and 1 < val < 500:
                    stats["weight"] = f"{val} {unit}"
                    break
                elif unit in ['lb', 'lbs', 'pound', 'pounds'] and 2 < val < 1100:
                    stats["weight"] = f"{val} {unit}"
                    break
            elif len(groups) == 4:
                # Range: 200–260 kg
                val1 = float(groups[0].replace(',', '.'))
                val2 = float(groups[1].replace(',', '.'))
                unit = groups[2].lower().strip()
                if unit in ['kg', 'kilogram', 'kilograms'] and 1 < val1 < val2 < 500:
                    stats["weight"] = f"{val1}–{val2} {unit}"
                    break
                elif unit in ['lb', 'lbs', 'pound', 'pounds'] and 2 < val1 < val2 < 1100:
                    stats["weight"] = f"{val1}–{val2} {unit}"
                    break
    
    # Length - support ranges like "1.4–2.8 m"
    length_patterns = [
        r'length\s*(?:of)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to)\s*(\d+(?:[.,]\d+)?)\s*(m\b|metres?|cm\b|ft\b|feet)',
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to)\s*(\d+(?:[.,]\d+)?)\s*(m\b|metres?|cm\b|ft\b|feet)\s*(?:long|length)',
        r'(\d+(?:[.,]\d+)?)\s*(m\b|metres?|cm\b|ft\b|feet)\s*(?:long|length)',
    ]
    for pattern in length_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            if len(groups) == 3:
                val = float(groups[0].replace(',', '.'))
                unit = groups[1].lower().strip()
                if unit in ['m', 'metre', 'metres', 'meter', 'meters'] and 0.3 < val < 10:
                    stats["length"] = f"{val} {unit}"
                    break
            elif len(groups) == 4:
                val1 = float(groups[0].replace(',', '.'))
                val2 = float(groups[1].replace(',', '.'))
                unit = groups[2].lower().strip()
                if unit in ['m', 'metre', 'metres', 'meter', 'meters'] and 0.3 < val1 < val2 < 10:
                    stats["length"] = f"{val1}–{val2} {unit}"
                    break
    
    # Height - support ranges like "0.8–1.1 m"
    height_patterns = [
        r'(?:stands?|height)\s*(?:of)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to)\s*(\d+(?:[.,]\d+)?)\s*(m\b|metres?|cm\b|ft\b|feet)',
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to)\s*(\d+(?:[.,]\d+)?)\s*(m\b|metres?|cm\b|ft\b|feet)\s*(?:tall|height|shoulder)',
    ]
    for pattern in height_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            if len(groups) == 4:
                val1 = float(groups[0].replace(',', '.'))
                val2 = float(groups[1].replace(',', '.'))
                unit = groups[2].lower().strip()
                if unit in ['m', 'metre', 'metres', 'meter', 'meters'] and 0.3 < val1 < val2 < 5:
                    stats["height"] = f"{val1}–{val2} {unit}"
                    break
    
    # Lifespan
    lifespan_patterns = [
        r'(?:lifespan|longevity|live)\s*(?:of|up to|to)?\s*(\d+(?:-\d+)?)\s*(years?|yrs?)',
        r'(\d+(?:-\d+)?)\s*(years?|yrs?)\s*(?:lifespan|longevity|life)',
    ]
    for pattern in lifespan_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1)
            if '-' in value:
                parts = value.split('-')
                if 1 < int(parts[0]) < 100 and 1 < int(parts[1]) < 100:
                    stats["lifespan"] = f"{value} years"
                    break
            else:
                val = int(value)
                if 1 < val < 100:
                    stats["lifespan"] = f"{value} years"
                    break
    
    # Speed
    speed_patterns = [
        r'(?:speed|run|fast)\s*(?:of|up to)?\s*(\d+(?:[.,]\d+)?)\s*(km/h|kmph|mph)',
        r'(\d+(?:[.,]\d+)?)\s*(km/h|kmph|mph)\s*(?:speed|top)',
    ]
    for pattern in speed_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = float(match.group(1).replace(',', '.'))
            if 10 < val < 150:
                stats["top_speed"] = f"{val} {match.group(2).lower()}"
                break
    
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

def extract_conservation_status(text):
    """Extract conservation status from Wikipedia text"""
    if not text:
        return None
    
    status_keywords = [
        "Endangered", "Critically Endangered", "Vulnerable", 
        "Near Threatened", "Least Concern", "Data Deficient",
        "Extinct in the Wild", "Extinct"
    ]
    
    for status in status_keywords:
        if status.lower() in text.lower():
            return status
    
    return None

def extract_locations(text):
    """Extract geographic locations from text"""
    locations = []
    
    # Common region keywords for animals
    region_patterns = [
        r'(?:native to|found in|distributed across|ranges from)\s*([^.,]+?)(?:[.,]|$)',
        r'(?:Asia|Africa|Europe|North America|South America|Australia|India|China|Russia|Indonesia)',
    ]
    
    # Look for continent/country names
    continents = ["Asia", "Africa", "Europe", "North America", "South America", "Australia", "Antarctica"]
    countries = ["India", "China", "Russia", "Indonesia", "Thailand", "Malaysia", "Bangladesh", "Nepal", "Bhutan"]
    
    for continent in continents:
        if continent.lower() in text.lower():
            locations.append(continent)
    
    for country in countries:
        if country.lower() in text.lower():
            locations.append(country)
    
    return ", ".join(locations[:5]) if locations else None

def fetch_inaturalist_taxonomy(scientific_name):
    try:
        print(f"    iNaturalist: Searching for '{scientific_name}'...")
        params = {"q": scientific_name, "per_page": 1, "rank": "species"}
        res = session.get(INAT_API, params=params, headers=headers, timeout=30)
        
        if res.status_code != 200:
            print(f"    iNaturalist error: {res.status_code}")
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
            print(f"    iNaturalist: No results")
            return None
        
        taxon = results[0]
        print(f"    iNaturalist: Found '{taxon.get('name')}'")
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
    """Fetch distribution from GBIF - but expect limited data"""
    try:
        print(f"    GBIF: Searching for '{scientific_name}'...")
        params = {"q": scientific_name, "type": "SPECIES", "limit": 1}
        res = session.get(f"{GBIF_API}/search", params=params, headers=headers, timeout=30)
        
        if res.status_code != 200:
            print(f"    GBIF search error: {res.status_code}")
            return None
        
        data = res.json()
        results = data.get("results", [])
        
        if not results:
            print(f"    GBIF: No results found")
            return None
        
        species_data = results[0]
        species_key = species_data.get("key")
        print(f"    GBIF: Found species key {species_key}")
        
        # Check if GBIF has occurrence data
        num_occurrences = species_data.get("numOccurrences", 0)
        if num_occurrences == 0:
            print(f"    GBIF: No occurrence data available")
            return None
        
        conservation_status = species_data.get("conservationStatus")
        
        return {
            "locations": None,  # GBIF has no location data for most species
            "habitat": None,
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
        
        # 1. Wikipedia (Summary + Full Article for Stats)
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
                
                # Fetch full article for physical stats (all sections)
                print("     Fetching full article for physical stats...")
                full_text, sections = fetch_wikipedia_all_sections(name)
                
                # Extract physical stats from full article
                stats = extract_physical_stats(full_text)
                for stat_name, stat_value in stats.items():
                    if stat_value:
                        animal_data["physical"][stat_name] = stat_value
                        print(f"       ✓ {stat_name}: {stat_value}")
                
                # Extract diet from summary
                diet = extract_diet(wiki_data["summary"])
                if diet:
                    animal_data["ecology"]["diet"] = diet
                    print(f"       ✓ diet: {diet}")
                
                # Extract conservation status from full text
                conservation = extract_conservation_status(full_text)
                if conservation:
                    animal_data["ecology"]["conservation_status"] = conservation
                    print(f"       ✓ conservation: {conservation}")
                
                # Extract locations from full text
                locations = extract_locations(full_text)
                if locations:
                    animal_data["ecology"]["locations"] = locations
                    print(f"       ✓ locations: {locations[:50]}...")
                
                print("     ✓ Summary and stats extracted")
        
        # 2. iNaturalist (Taxonomy)
        if not animal_data["classification"]["kingdom"] or force_update:
            print("  🔬 Fetching taxonomy from iNaturalist...")
            inat_class = fetch_inaturalist_taxonomy(sci_name)
            
            if inat_class:
                animal_data["classification"] = inat_class
                if "iNaturalist" not in animal_data["sources"]:
                    animal_data["sources"].append("iNaturalist")
        
        # 3. GBIF (Skip if no data - most species have 0 occurrences)
        if not animal_data["ecology"]["locations"] or force_update:
            print("  🌍 Fetching distribution from GBIF...")
            gbif_data = fetch_gbif_distribution(sci_name)
            
            if gbif_
                if gbif_data.get("locations") and not animal_data["ecology"]["locations"]:
                    animal_data["ecology"]["locations"] = gbif_data["locations"]
                if gbif_data.get("conservation_status") and not animal_data["ecology"]["conservation_status"]:
                    animal_data["ecology"]["conservation_status"] = gbif_data["conservation_status"]
                    print(f"     ✓ Conservation: {gbif_data['conservation_status']}")
                
                if "GBIF" not in animal_data["sources"]:
                    animal_data["sources"].append("GBIF")
            else:
                print("     ⚠ GBIF has no occurrence data (using Wikipedia instead)")
        
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
