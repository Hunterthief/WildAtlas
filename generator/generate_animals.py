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

def fetch_wikipedia_section(animal_name, section="Characteristics"):
    """Fetch specific section from Wikipedia using Action API"""
    try:
        safe_name = animal_name.replace(" ", "_")
        params = {
            "action": "parse",
            "page": safe_name,
            "prop": "text",
            "section": section,
            "format": "json"
        }
        r = session.get(WIKI_ACTION_API, params=params, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            text = data.get("parse", {}).get("text", {}).get("*", "")
            # Strip HTML tags
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text
    except Exception as e:
        print(f"    Wikipedia section error: {e}")
    return ""

def extract_physical_stats(text):
    """Extract physical statistics with strict validation"""
    stats = {"weight": None, "length": None, "height": None, "lifespan": None, "top_speed": None}
    if not text:
        return stats
    
    # Weight - strict context + sanity check
    weight_matches = re.findall(r'(\d+(?:[.,]\d+)?)\s*(kg|tonnes?|t\b|lbs?|pounds?)', text, re.IGNORECASE)
    for value, unit in weight_matches:
        try:
            val = float(value.replace(',', '.'))
            unit_clean = unit.lower().strip()
            if unit_clean in ['t', 'tonne', 'tonnes']:
                if 0.1 < val < 10:  # Elephant range
                    stats["weight"] = f"{val} {unit_clean}"
                    break
            elif unit_clean in ['kg', 'kilogram', 'kilograms']:
                if 1 < val < 500:  # Most animals
                    stats["weight"] = f"{val} {unit_clean}"
                    break
            elif unit_clean in ['lb', 'lbs', 'pound', 'pounds']:
                if 2 < val < 1100:
                    stats["weight"] = f"{val} {unit_clean}"
                    break
        except:
            continue
    
    # Length - strict context + sanity check
    length_matches = re.findall(r'(\d+(?:[.,]\d+)?)\s*(m\b|metres?|cm\b|ft\b|feet)', text, re.IGNORECASE)
    for value, unit in length_matches:
        try:
            val = float(value.replace(',', '.'))
            unit_clean = unit.lower().strip()
            if unit_clean in ['m', 'metre', 'metres', 'meter', 'meters']:
                if 0.3 < val < 10:  # Most animals
                    stats["length"] = f"{val} {unit_clean}"
                    break
            elif unit_clean in ['cm', 'centimetre', 'centimetres']:
                if 10 < val < 500:
                    stats["length"] = f"{val} {unit_clean}"
                    break
            elif unit_clean in ['ft', 'feet', 'foot']:
                if 1 < val < 30:
                    stats["length"] = f"{val} {unit_clean}"
                    break
        except:
            continue
    
    # Lifespan
    lifespan_matches = re.findall(r'(\d+(?:-\d+)?)\s*(years?|yrs?)', text, re.IGNORECASE)
    for value, unit in lifespan_matches:
        try:
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
        except:
            continue
    
    # Speed
    speed_matches = re.findall(r'(\d+(?:[.,]\d+)?)\s*(km/h|kmph|mph)', text, re.IGNORECASE)
    for value, unit in speed_matches:
        try:
            val = float(value.replace(',', '.'))
            if 10 < val < 150:
                stats["top_speed"] = f"{val} {unit.lower()}"
                break
        except:
            continue
    
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
    """Fetch distribution/habitat/conservation from GBIF"""
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
        
        conservation_status = species_data.get("conservationStatus")
        habitat = species_data.get("habitat")
        
        locations = []
        
        # Try occurrences with country facet
        if species_key:
            time.sleep(0.5)
            try:
                occ_res = session.get(
                    "https://api.gbif.org/v1/occurrence/search",
                    params={
                        "taxonKey": species_key,
                        "limit": 0,  # We just want facets
                        "facet": "country",
                        "facetLimit": 10
                    },
                    headers=headers,
                    timeout=30
                )
                if occ_res.status_code == 200:
                    occ_data = occ_res.json()
                    facets = occ_data.get("facets", [])
                    for facet in facets:
                        if facet.get("field") == "country":
                            counts = facet.get("counts", [])
                            locations = [c.get("name") for c in counts[:5] if c.get("name")]
                            print(f"    GBIF: Found {len(locations)} countries from facets")
                            break
            except Exception as e:
                print(f"    GBIF facet error: {e}")
        
        # Fallback: Try simple occurrence search
        if not locations and species_key:
            time.sleep(0.5)
            try:
                occ_res = session.get(
                    "https://api.gbif.org/v1/occurrence/search",
                    params={"taxonKey": species_key, "limit": 50},
                    headers=headers,
                    timeout=30
                )
                if occ_res.status_code == 200:
                    occ_data = occ_res.json()
                    occ_results = occ_data.get("results", [])
                    countries = set()
                    for item in occ_results:
                        country = item.get("country")
                        if country:
                            countries.add(country)
                    locations = list(countries)[:5]
                    print(f"    GBIF: Extracted {len(locations)} countries from occurrences")
            except Exception as e:
                print(f"    GBIF occurrences error: {e}")
        
        result = {
            "locations": ", ".join(locations[:5]) if locations else None,
            "habitat": habitat,
            "conservation_status": conservation_status
        }
        print(f"    GBIF: Locations: {result['locations'][:50] if result['locations'] else 'None'}...")
        return result
    except Exception as e:
        print(f"    GBIF error: {e}")
        import traceback
        traceback.print_exc()
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
        
        # 1. Wikipedia (Summary + Characteristics section)
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
                
                # Fetch Characteristics section for physical stats
                print("     Fetching Characteristics section...")
                chars_text = fetch_wikipedia_section(name, "Characteristics")
                all_text = wiki_data["summary"] + " " + chars_text
                
                stats = extract_physical_stats(all_text)
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
        
        # 3. GBIF
        if not animal_data["ecology"]["locations"] or force_update:
            print("  🌍 Fetching distribution from GBIF...")
            gbif_data = fetch_gbif_distribution(sci_name)
            
            if gbif_
                if gbif_data.get("locations"):
                    animal_data["ecology"]["locations"] = gbif_data["locations"]
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
