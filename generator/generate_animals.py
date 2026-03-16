# generator/generate_animals.py
import requests, json, time, os, re, sys
from datetime import datetime
from pathlib import Path
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Import Ninja API module
sys.path.insert(0, str(Path(__file__).parent))
from modules.api_ninjas import fetch_animal_data

# ============================================================================
# SETUP - FIXED PATHS TO REPO ROOT
# ============================================================================

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data"
ANIMAL_STATS_DIR = DATA_DIR / "animal_stats"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(ANIMAL_STATS_DIR, exist_ok=True)

CONFIG_DIR = Path(__file__).parent / "config"

session = requests.Session()
retry = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retry))
headers = {"User-Agent": "WildAtlasBot/1.0 (contact@example.com)", "Accept": "application/json"}

WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
WIKI_MOBILE = "https://en.m.wikipedia.org/wiki/"
INAT_API = "https://api.inaturalist.org/v1/taxa"

CLASSIFICATION_FIELDS = ["kingdom", "phylum", "class", "order", "family", "genus", "species"]

# ============================================================================
# LOAD CONFIG FILES
# ============================================================================

def load_config(filename):
    config_path = CONFIG_DIR / filename
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

ANIMAL_TYPES = load_config("animal_types.json")
YOUNG_NAMES = load_config("young_names.json")
GROUP_NAMES = load_config("group_names.json")
LOCATIONS = load_config("locations.json")
HABITATS = load_config("habitats.json")
FEATURES = load_config("features.json")
DIETS = load_config("diets.json")

# ============================================================================
# ANIMAL TYPE DETECTION
# ============================================================================

def detect_animal_type(name, classification=None):
    name_lower = name.lower()
    priority_types = ["raptor", "owl", "duck", "goose", "swan", "chicken", "penguin",
                     "shark", "ray", "salmon", "frog", "salamander", "snake", "lizard",
                     "turtle", "crocodile", "butterfly", "bee", "ant", "spider", "crab",
                     "feline", "canine", "bear", "elephant", "primate", "rodent",
                     "bat", "whale", "deer", "bovine", "equine", "rabbit"]

    for animal_type in priority_types:
        config = ANIMAL_TYPES.get(animal_type, {})
        keywords = config.get("keywords", [])
        for keyword in keywords:
            if keyword in name_lower:
                return animal_type

    if classification:
        class_name = classification.get("class", "").lower()
        order_name = classification.get("order", "").lower()
        family_name = classification.get("family", "").lower()

        if "mammalia" in class_name:
            if "carnivora" in order_name:
                if "felidae" in family_name or any(w in name_lower for w in ["cat", "tiger", "lion", "leopard", "cheetah", "jaguar"]):
                    return "feline"
                if "canidae" in family_name or any(w in name_lower for w in ["dog", "wolf", "fox", "jackal", "coyote"]):
                    return "canine"
                if "ursidae" in family_name or "bear" in name_lower:
                    return "bear"
            elif "proboscidea" in order_name or "elephant" in name_lower:
                return "elephant"
            elif "primates" in order_name:
                return "primate"
            elif "cetacea" in order_name:
                return "whale"
            elif "artiodactyla" in order_name:
                if any(w in name_lower for w in ["deer", "elk", "moose"]):
                    return "deer"
                if any(w in name_lower for w in ["cow", "bison", "buffalo", "ox"]):
                    return "bovine"
                if any(w in name_lower for w in ["horse", "zebra", "donkey"]):
                    return "equine"
            elif "lagomorpha" in order_name:
                return "rabbit"
            elif "chiroptera" in order_name:
                return "bat"
            elif "rodentia" in order_name:
                return "rodent"
            return "mammal"
        elif "aves" in class_name:
            if any(w in name_lower for w in ["eagle", "hawk", "falcon", "vulture", "kite"]):
                return "raptor"
            if "owl" in name_lower:
                return "owl"
            if any(w in name_lower for w in ["duck", "mallard"]):
                return "duck"
            if "penguin" in name_lower:
                return "penguin"
            return "bird"
        elif "actinopterygii" in class_name or "chondrichthyes" in class_name:
            if any(w in name_lower for w in ["shark"]):
                return "shark"
            if any(w in name_lower for w in ["ray", "stingray", "manta"]):
                return "ray"
            return "fish"
        elif "amphibia" in class_name:
            return "frog"
        elif "reptilia" in class_name:
            if any(w in name_lower for w in ["snake", "cobra", "python", "viper"]):
                return "snake"
            if any(w in name_lower for w in ["turtle", "tortoise", "terrapin"]):
                return "turtle"
            return "reptile"
        elif "insecta" in class_name:
            if any(w in name_lower for w in ["butterfly", "moth"]):
                return "butterfly"
            if any(w in name_lower for w in ["bee", "wasp", "hornet"]):
                return "bee"
            if "ant" in name_lower:
                return "ant"
            return "insect"
        elif "arachnida" in class_name:
            return "spider"
        elif "crustacea" in class_name:
            return "crab"

    return "default"

def get_young_name(animal_type):
    return YOUNG_NAMES.get(animal_type, YOUNG_NAMES.get("default", "young"))

def get_group_name(animal_type):
    return GROUP_NAMES.get(animal_type, GROUP_NAMES.get("default", "population"))

def get_default_diet(animal_type):
    return DIETS.get(animal_type, DIETS.get("default", "Unknown"))

# ============================================================================
# WIKIPEDIA FETCHING
# ============================================================================

def fetch_wikipedia_summary(name):
    try:
        r = session.get(f"{WIKI_API}{name.replace(' ', '_')}", headers=headers, timeout=15)
        if r.status_code == 200:
            d = r.json()
            return {
                "summary": d.get("extract", "Unknown"),
                "description": d.get("description", "Unknown"),
                "image": d.get("thumbnail", {}).get("source", "").strip(),
                "url": d.get("content_urls", {}).get("desktop", {}).get("page", "").strip()
            }
    except Exception as e:
        print(f" ⚠ Wikipedia summary error: {e}")
    return {"summary": "Unknown", "description": "Unknown", "image": "", "url": "Unknown"}

def fetch_wikipedia_full(name):
    try:
        r = session.get(f"{WIKI_MOBILE}{name.replace(' ', '_')}", headers=headers, timeout=15)
        if r.status_code == 200:
            text = re.sub(r'<[^>]+>', ' ', r.text)
            text = re.sub(r'\s+', ' ', text).strip()
            text = re.sub(r'\[\d+\]', '', text)
            return text
    except Exception as e:
        print(f" ⚠ Wikipedia full error: {e}")
    return ""

# ============================================================================
# DATA EXTRACTION
# ============================================================================

def extract_stats(text, animal_type):
    stats = {"weight": "Unknown", "length": "Unknown", "height": "Unknown", "lifespan": "Unknown", "top_speed": "Unknown"}
    if not text:
        return stats
    text_lower = text.lower()
    
    weight_patterns = [
        r'(?:weigh|weighs|weight)\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|t|lbs?|pounds?)',
    ]
    for pattern in weight_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                groups = m.groups()
                v1 = float(groups[0].replace(',', '.'))
                v2 = float(groups[1].replace(',', '.')) if len(groups) > 2 else v1
                u = groups[-1].lower().strip()
                if u in ['kg', 'kilogram', 'kilograms'] and 0.1 < v1 < 10000:
                    stats["weight"] = f"{v1}–{v2} kg" if v1 != v2 else f"{v1} kg"
                    break
            except:
                pass
    return stats

def extract_diet(text, animal_type):
    if not text:
        return get_default_diet(animal_type)
    t = text.lower()
    if any(w in t for w in ['carnivore', 'carnivorous', 'meat-eater', 'predator', 'preys on', 'hunts']):
        return "Carnivore"
    elif any(w in t for w in ['herbivore', 'herbivorous', 'plant-eater', 'grazes', 'browses', 'vegetation']):
        return "Herbivore"
    elif any(w in t for w in ['omnivore', 'omnivorous', 'both plants and animals', 'varied diet']):
        return "Omnivore"
    return get_default_diet(animal_type)

def extract_conservation(text):
    if not text:
        return "Unknown"
    statuses = ["Critically Endangered", "Endangered", "Vulnerable", "Near Threatened",
               "Least Concern", "Data Deficient", "Extinct in the Wild", "Extinct"]
    for s in statuses:
        if s.lower() in text.lower():
            return s
    return "Unknown"

def extract_locations(text, animal_type):
    if not text:
        return "Unknown"
    animal_locations = LOCATIONS.get("animal_specific", {}).get(animal_type, [])
    for region, locs in LOCATIONS.get("regions", {}).items():
        animal_locations.extend(locs)
    locs = []
    text_lower = text.lower()
    for loc in animal_locations:
        if loc.lower() in text_lower:
            locs.append(loc)
    seen = set()
    unique_locs = []
    for loc in locs:
        loc_lower = loc.lower()
        if loc_lower not in seen:
            seen.add(loc_lower)
            unique_locs.append(loc)
    return ", ".join(unique_locs[:5]) if unique_locs else "Unknown"

def extract_habitat(text, animal_type):
    if not text:
        return "Unknown"
    habitat_keywords = HABITATS.get(animal_type, HABITATS.get("default", []))
    common_habitats = ['forest', 'jungle', 'savanna', 'grassland', 'desert',
                      'mountain', 'ocean', 'sea', 'river', 'lake', 'wetland',
                      'swamp', 'marsh', 'tundra', 'rainforest', 'woodland',
                      'coastal', 'coral reef', 'mangrove', 'temperate', 'tropical']
    habitat_keywords.extend(common_habitats)
    found = []
    text_lower = text.lower()
    for keyword in habitat_keywords:
        if keyword.lower() in text_lower:
            found.append(keyword)
    return ", ".join(list(set(found))[:4]) if found else "Unknown"

def extract_features(text, animal_type):
    if not text:
        return []
    type_features = FEATURES.get(animal_type, FEATURES.get("default", {}))
    positive = type_features.get("positive", [])
    features = []
    text_lower = text.lower()
    for feature in positive:
        if feature in text_lower:
            display_feature = feature.replace('_', ' ').title()
            if display_feature not in features:
                features.append(display_feature)
    return features[:3] if features else []

def extract_behavior(text, animal_type):
    if not text:
        return "Unknown"
    t = text.lower()
    if any(w in t for w in ['solitary', 'alone', 'lives alone', 'mostly solitary', 'lone']):
        return "Solitary"
    elif any(w in t for w in ['pack', 'herd', 'flock', 'school', 'swarm', 'colony', 'social', 'group']):
        return "Social"
    return "Solitary"

def extract_reproduction(text, animal_type):
    repro = {
        "gestation_period": "Unknown",
        "average_litter_size": "Unknown",
        "name_of_young": get_young_name(animal_type)
    }
    if not text:
        return repro
    gestation_patterns = [
        r'(?:gestation|pregnancy|incubation)\s*(?:period|lasts?|is)?\s*(?:around|about)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(months?|weeks?|days?)',
    ]
    for pattern in gestation_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                v = m.group(1).replace(' ', '')
                unit = m.group(2).lower()
                if 'month' in unit:
                    if '-' in v or '–' in v:
                        p = re.split(r'[-–]', v)
                        if len(p) >= 2 and 1 <= int(p[0]) <= int(p[1]) <= 24:
                            repro["gestation_period"] = f"{p[0]}–{p[1]} months"
                            break
                    elif 1 <= int(v) <= 24:
                        repro["gestation_period"] = f"{v} months"
                        break
                elif 'day' in unit and 1 <= int(v) <= 365:
                    repro["gestation_period"] = f"{v} days"
                    break
            except:
                pass
    return repro

def extract_threats(text):
    threats = []
    t = text.lower()
    if any(w in t for w in ['poach', 'illegal trade', 'body parts', 'fur trade', 'ivory']):
        threats.append('Poaching')
    if any(w in t for w in ['habitat loss', 'deforestation', 'habitat destruction', 'habitat fragmentation']):
        threats.append('Habitat loss')
    if any(w in t for w in ['human-wildlife conflict', 'livestock', 'retaliation', 'persecution']):
        threats.append('Human-wildlife conflict')
    return ', '.join(threats[:3]) if threats else "Unknown"

# ============================================================================
# INATURALIST
# ============================================================================

def fetch_inaturalist(sci_name):
    try:
        params = {"q": sci_name, "per_page": 1, "rank": "species"}
        r = session.get(INAT_API, params=params, headers=headers, timeout=30)
        if r.status_code != 200:
            params = {"q": sci_name, "per_page": 1}
            r = session.get(INAT_API, params=params, headers=headers, timeout=30)
        if r.status_code == 200:
            results = r.json().get("results", [])
            if results:
                taxon = results[0]
                time.sleep(0.5)
                anc_ids = taxon.get("ancestor_ids", [])
                if anc_ids:
                    r = session.get(f"{INAT_API}/{','.join(map(str, anc_ids))}", headers=headers, timeout=30)
                    if r.status_code == 200:
                        classification = {f: "Unknown" for f in CLASSIFICATION_FIELDS}
                        classification["species"] = taxon.get("name", sci_name)
                        for a in r.json().get("results", []):
                            rank = a.get("rank", "").lower()
                            name = a.get("name")
                            if rank == "kingdom": classification["kingdom"] = name
                            elif rank == "phylum": classification["phylum"] = name
                            elif rank == "class": classification["class"] = name
                            elif rank == "order": classification["order"] = name
                            elif rank == "family": classification["family"] = name
                            elif rank == "genus": classification["genus"] = name
                        return classification
    except Exception as e:
        print(f" ⚠ iNaturalist error: {e}")
    return None

# ============================================================================
# FILE NAMING & CACHING
# ============================================================================

def get_animal_filename(name, qid):
    clean_name = name.lower().replace(' ', '_').replace('-', '_').replace("'", "")
    return f"{clean_name}_{{QID={qid}}}.json"

def load_cache(qid, name=None):
    if name:
        filename = get_animal_filename(name, qid)
        f = ANIMAL_STATS_DIR / filename
        if f.exists():
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    return json.load(fp)
            except:
                pass
    return None

def save_animal_file(data, name, qid):
    filename = get_animal_filename(name, qid)
    filepath = ANIMAL_STATS_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f" 💾 Saved: {filename}")
    return filepath

# ============================================================================
# BUILD ANIMAL DATA - FIXED TO PROPERLY MAP ALL NINJA API FIELDS
# ============================================================================

def build_animal_data(ninja_data, wiki_summary, wiki_full, inat_classification, qid, name, sci_name):
    # Extract Ninja API data with explicit checks
    ninja_taxonomy = {}
    ninja_chars = {}
    ninja_locations = []
    
    if ninja_data:
        ninja_taxonomy = ninja_data.get("taxonomy") if ninja_data.get("taxonomy") else {}
        ninja_chars = ninja_data.get("characteristics") if ninja_data.get("characteristics") else {}
        ninja_locations = ninja_data.get("locations") if ninja_data.get("locations") else []
        
        # Debug output
        print(f"   📋 Ninja characteristics: {len(ninja_chars)} fields")
        for key in ['prey', 'group', 'number_of_species', 'estimated_population_size', 
                    'age_of_sexual_maturity', 'age_of_weaning', 'most_distinctive_feature', 
                    'gestation_period', 'lifestyle', 'color', 'skin_type', 'slogan']:
            val = ninja_chars.get(key)
            print(f"      {key}: {val}")
    
    classification = inat_classification if inat_classification else ninja_taxonomy
    animal_type = detect_animal_type(name, classification)
    young_name = get_young_name(animal_type)
    group_name = get_group_name(animal_type)
    
    all_text = ""
    if wiki_summary and wiki_summary.get("summary") and wiki_summary.get("summary") != "Unknown":
        all_text += wiki_summary.get("summary", "") + " "
    if wiki_full:
        all_text += wiki_full
    
    # Build data structure - use .get() with explicit None check
    data = {
        "id": qid,
        "name": name,
        "scientific_name": sci_name,
        "common_names": [],
        "description": wiki_summary.get("description") if wiki_summary and wiki_summary.get("description") else "Unknown",
        "summary": wiki_summary.get("summary") if wiki_summary and wiki_summary.get("summary") else "Unknown",
        "image": wiki_summary.get("image", "") if wiki_summary else "",
        "wikipedia_url": wiki_summary.get("url") if wiki_summary and wiki_summary.get("url") else "Unknown",
        
        "classification": {
            "kingdom": ninja_taxonomy.get("kingdom") if ninja_taxonomy and ninja_taxonomy.get("kingdom") else "Unknown",
            "phylum": ninja_taxonomy.get("phylum") if ninja_taxonomy and ninja_taxonomy.get("phylum") else "Unknown",
            "class": ninja_taxonomy.get("class") if ninja_taxonomy and ninja_taxonomy.get("class") else "Unknown",
            "order": ninja_taxonomy.get("order") if ninja_taxonomy and ninja_taxonomy.get("order") else "Unknown",
            "family": ninja_taxonomy.get("family") if ninja_taxonomy and ninja_taxonomy.get("family") else "Unknown",
            "genus": ninja_taxonomy.get("genus") if ninja_taxonomy and ninja_taxonomy.get("genus") else "Unknown",
            "species": ninja_taxonomy.get("scientific_name") if ninja_taxonomy and ninja_taxonomy.get("scientific_name") else sci_name
        },
        
        "animal_type": animal_type,
        "young_name": young_name,
        "group_name": group_name,
        
        "physical": {
            "weight": ninja_chars.get("weight") if ninja_chars and ninja_chars.get("weight") else "Unknown",
            "length": "Unknown",
            "height": ninja_chars.get("height") if ninja_chars and ninja_chars.get("height") else "Unknown",
            "top_speed": ninja_chars.get("top_speed") if ninja_chars and ninja_chars.get("top_speed") else "Unknown",
            "lifespan": ninja_chars.get("lifespan") if ninja_chars and ninja_chars.get("lifespan") else "Unknown"
        },
        
        "ecology": {
            "diet": ninja_chars.get("diet") if ninja_chars and ninja_chars.get("diet") else "Unknown",
            "habitat": ninja_chars.get("habitat") if ninja_chars and ninja_chars.get("habitat") else "Unknown",
            "locations": ", ".join(ninja_locations) if ninja_locations else "Unknown",
            "group_behavior": ninja_chars.get("group_behavior") if ninja_chars and ninja_chars.get("group_behavior") else "Unknown",
            "conservation_status": "Unknown",
            "biggest_threat": ninja_chars.get("biggest_threat") if ninja_chars and ninja_chars.get("biggest_threat") else "Unknown",
            "distinctive_features": [ninja_chars.get("most_distinctive_feature")] if ninja_chars and ninja_chars.get("most_distinctive_feature") else [],
            "population_trend": "Unknown"
        },
        
        "reproduction": {
            "gestation_period": ninja_chars.get("gestation_period") if ninja_chars and ninja_chars.get("gestation_period") else "Unknown",
            "average_litter_size": ninja_chars.get("average_litter_size") if ninja_chars and ninja_chars.get("average_litter_size") else "Unknown",
            "name_of_young": ninja_chars.get("name_of_young") if ninja_chars and ninja_chars.get("name_of_young") else young_name
        },
        
        "additional_info": {
            "lifestyle": ninja_chars.get("lifestyle") if ninja_chars and ninja_chars.get("lifestyle") else "Unknown",
            "color": ninja_chars.get("color") if ninja_chars and ninja_chars.get("color") else "Unknown",
            "skin_type": ninja_chars.get("skin_type") if ninja_chars and ninja_chars.get("skin_type") else "Unknown",
            "prey": ninja_chars.get("prey") if ninja_chars and ninja_chars.get("prey") else "Unknown",
            "slogan": ninja_chars.get("slogan") if ninja_chars and ninja_chars.get("slogan") else "Unknown",
            "group": ninja_chars.get("group") if ninja_chars and ninja_chars.get("group") else "Unknown",
            "number_of_species": ninja_chars.get("number_of_species") if ninja_chars and ninja_chars.get("number_of_species") else "Unknown",
            "estimated_population_size": ninja_chars.get("estimated_population_size") if ninja_chars and ninja_chars.get("estimated_population_size") else "Unknown",
            "age_of_sexual_maturity": ninja_chars.get("age_of_sexual_maturity") if ninja_chars and ninja_chars.get("age_of_sexual_maturity") else "Unknown",
            "age_of_weaning": ninja_chars.get("age_of_weaning") if ninja_chars and ninja_chars.get("age_of_weaning") else "Unknown",
            "most_distinctive_feature": ninja_chars.get("most_distinctive_feature") if ninja_chars and ninja_chars.get("most_distinctive_feature") else "Unknown"
        },
        
        "sources": [],
        "last_updated": datetime.now().isoformat()
    }
    
    # Add sources
    if ninja_data:
        data["sources"].append("API Ninjas")
    if wiki_summary and wiki_summary.get("summary") and wiki_summary.get("summary") != "Unknown":
        data["sources"].append("Wikipedia")
    
    # Supplement with Wikipedia extraction (only if Ninja data is Unknown)
    if all_text:
        if data["physical"]["weight"] == "Unknown":
            stats = extract_stats(all_text, animal_type)
            if stats["weight"] != "Unknown":
                data["physical"]["weight"] = stats["weight"]
        if data["physical"]["length"] == "Unknown":
            stats = extract_stats(all_text, animal_type)
            if stats["length"] != "Unknown":
                data["physical"]["length"] = stats["length"]
        if data["ecology"]["conservation_status"] == "Unknown":
            cons = extract_conservation(all_text)
            if cons != "Unknown":
                data["ecology"]["conservation_status"] = cons
        if data["ecology"]["locations"] == "Unknown":
            locs = extract_locations(all_text, animal_type)
            if locs != "Unknown":
                data["ecology"]["locations"] = locs
        if data["ecology"]["habitat"] == "Unknown":
            habitat = extract_habitat(all_text, animal_type)
            if habitat != "Unknown":
                data["ecology"]["habitat"] = habitat
        if data["ecology"]["biggest_threat"] == "Unknown":
            threats = extract_threats(all_text)
            if threats != "Unknown":
                data["ecology"]["biggest_threat"] = threats
        if data["reproduction"]["gestation_period"] == "Unknown":
            repro = extract_reproduction(all_text, animal_type)
            if repro["gestation_period"] != "Unknown":
                data["reproduction"]["gestation_period"] = repro["gestation_period"]
    
    # Merge iNaturalist classification
    if inat_classification:
        for field in CLASSIFICATION_FIELDS:
            if data["classification"][field] == "Unknown" and inat_classification.get(field):
                data["classification"][field] = inat_classification[field]
        if "iNaturalist" not in data["sources"]:
            data["sources"].append("iNaturalist")
    
    return data

# ============================================================================
# MAIN GENERATION
# ============================================================================

def generate(animals, force=False):
    output = []
    ninja_api_key = os.environ.get("API_NINJAS_KEY", "")
    
    if not ninja_api_key:
        print(" ⚠ WARNING: API_NINJAS_KEY not set! API calls will fail.")
        print("   Set it in GitHub Secrets as 'API_NINJAS_KEY'")
    
    for i, a in enumerate(animals):
        name, sci, qid = a["name"], a["scientific_name"], a.get("qid", f"animal_{i}")
        print(f"\n{'='*60}")
        print(f"[{i+1}/{len(animals)}] {name} ({sci})")
        print(f"{'='*60}")

        cached = load_cache(qid, name) if not force else None

        if cached and not force:
            data = cached
            print(" 📦 Using cached data")
        else:
            print(" 🥷 Fetching from Ninja API...")
            ninja_data = fetch_animal_data(name, ninja_api_key)
            
            if not ninja_data:
                print(f" ⚠ No data from Ninja API for {name}")
                ninja_data = {
                    "name": name,
                    "taxonomy": {"scientific_name": sci},
                    "locations": [],
                    "characteristics": {}
                }

            print(" 📖 Fetching from Wikipedia...")
            wiki_summary = fetch_wikipedia_summary(name)
            wiki_full = fetch_wikipedia_full(name)
            
            print(" 🔬 Fetching from iNaturalist...")
            inat_classification = fetch_inaturalist(sci)
            
            data = build_animal_data(ninja_data, wiki_summary, wiki_full, inat_classification, qid, name, sci)
            save_animal_file(data, name, qid)

        output.append(data)
        print(f" ✅ {name} complete!")
        time.sleep(1)

    with open(DATA_DIR / "animals.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Done! {len(output)} animals saved:")
    print(f"   • Individual files: {ANIMAL_STATS_DIR}/")
    print(f"   • Combined file: {DATA_DIR}/animals.json")
    return output

TEST_ANIMALS = [
    {"name": "Tiger", "scientific_name": "Panthera tigris", "qid": "Q132186"},
    {"name": "Cheetah", "scientific_name": "Acinonyx jubatus", "qid": "Q35625"},
    {"name": "African Elephant", "scientific_name": "Loxodonta africana", "qid": "Q7372"},
    {"name": "Gray Wolf", "scientific_name": "Canis lupus", "qid": "Q213537"},
    {"name": "Bald Eagle", "scientific_name": "Haliaeetus leucocephalus", "qid": "Q25319"},
    {"name": "Emperor Penguin", "scientific_name": "Aptenodytes forsteri", "qid": "Q43306"},
    {"name": "Great White Shark", "scientific_name": "Carcharodon carcharias", "qid": "Q47164"},
    {"name": "Atlantic Salmon", "scientific_name": "Salmo salar", "qid": "Q39709"},
    {"name": "Green Sea Turtle", "scientific_name": "Chelonia mydas", "qid": "Q7785"},
    {"name": "King Cobra", "scientific_name": "Ophiophagus hannah", "qid": "Q189609"},
    {"name": "American Bullfrog", "scientific_name": "Lithobates catesbeianus", "qid": "Q270238"},
    {"name": "Monarch Butterfly", "scientific_name": "Danaus plexippus", "qid": "Q165980"},
    {"name": "Honey Bee", "scientific_name": "Apis mellifera", "qid": "Q7316"},
]

if __name__ == "__main__":
    force = "--force" in sys.argv
    generate(TEST_ANIMALS, force)
