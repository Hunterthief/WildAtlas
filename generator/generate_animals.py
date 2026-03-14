# generator/generate_animals.py
import requests, json, time, os, re
from datetime import datetime
from pathlib import Path
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Setup
os.makedirs("data", exist_ok=True)
CONFIG_DIR = Path(__file__).parent / "config"
session = requests.Session()
retry = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retry))
headers = {"User-Agent": "WildAtlasBot/1.0", "Accept": "application/json"}

WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
WIKI_MOBILE = "https://en.m.wikipedia.org/wiki/"
INAT_API = "https://api.inaturalist.org/v1/taxa"

CLASSIFICATION_FIELDS = ["kingdom", "phylum", "class", "order", "family", "genus", "species"]

# ============================================================================
# LOAD CONFIG FILES
# ============================================================================

def load_config(filename):
    """Load configuration from JSON file"""
    config_path = CONFIG_DIR / filename
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Load all configs
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
    """Detect animal type from name and classification"""
    name_lower = name.lower()
    
    # Check name keywords first (most specific matches first)
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
    
    # Check classification if available
    if classification:
        class_name = classification.get("class", "").lower()
        order_name = classification.get("order", "").lower()
        
        if "mammalia" in class_name:
            if "carnivora" in order_name:
                if any(w in name_lower for w in ["cat", "feline"]): return "feline"
                if any(w in name_lower for w in ["dog", "canine", "wolf"]): return "canine"
                return "feline"
            elif "proboscidea" in order_name: return "elephant"
            elif "primates" in order_name: return "primate"
            elif "cetacea" in order_name: return "whale"
            elif "artiodactyla" in order_name:
                if any(w in name_lower for w in ["deer", "elk", "moose"]): return "deer"
                if any(w in name_lower for w in ["cow", "bison", "buffalo"]): return "bovine"
                if any(w in name_lower for w in ["horse", "zebra"]): return "equine"
            elif "lagomorpha" in order_name: return "rabbit"
            elif "chiroptera" in order_name: return "bat"
            elif "rodentia" in order_name: return "rodent"
            return "mammal"
        elif "aves" in class_name:
            if any(w in name_lower for w in ["eagle", "hawk", "falcon"]): return "raptor"
            if "owl" in name_lower: return "owl"
            if any(w in name_lower for w in ["duck", "mallard"]): return "duck"
            if "goose" in name_lower: return "goose"
            if "swan" in name_lower: return "swan"
            if any(w in name_lower for w in ["chicken", "rooster", "hen"]): return "chicken"
            if "penguin" in name_lower: return "penguin"
            return "bird"
        elif "actinopterygii" in class_name or "chondrichthyes" in class_name:
            if any(w in name_lower for w in ["shark"]): return "shark"
            if any(w in name_lower for w in ["ray", "stingray", "manta"]): return "ray"
            if any(w in name_lower for w in ["salmon", "trout"]): return "salmon"
            return "fish"
        elif "amphibia" in class_name:
            if any(w in name_lower for w in ["frog", "toad"]): return "frog"
            return "salamander"
        elif "reptilia" in class_name:
            if any(w in name_lower for w in ["snake", "serpent"]): return "snake"
            if any(w in name_lower for w in ["lizard", "gecko"]): return "lizard"
            if any(w in name_lower for w in ["turtle", "tortoise"]): return "turtle"
            if any(w in name_lower for w in ["crocodile", "alligator"]): return "crocodile"
            return "reptile"
        elif "insecta" in class_name:
            if any(w in name_lower for w in ["butterfly", "moth"]): return "butterfly"
            if any(w in name_lower for w in ["bee", "wasp"]): return "bee"
            if "ant" in name_lower: return "ant"
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
                "summary": d.get("extract", ""),
                "description": d.get("description", ""),
                "image": d.get("thumbnail", {}).get("source", ""),
                "url": d.get("content_urls", {}).get("desktop", {}).get("page", "")
            }
    except: pass
    return {"summary": "", "description": "", "image": "", "url": ""}

def fetch_wikipedia_full(name):
    try:
        r = session.get(f"{WIKI_MOBILE}{name.replace(' ', '_')}", headers=headers, timeout=15)
        if r.status_code == 200:
            text = re.sub(r'<[^>]+>', ' ', r.text)
            text = re.sub(r'\s+', ' ', text).strip()
            text = re.sub(r'\[\d+\]', '', text)
            return text
    except: pass
    return ""

# ============================================================================
# DATA EXTRACTION
# ============================================================================

def extract_stats(text, animal_type):
    """Extract physical stats"""
    stats = {"weight": None, "length": None, "height": None, "lifespan": None, "top_speed": None}
    if not text: return stats
    
    # Weight
    weight_patterns = [
        r'weighs?\s*(?:of)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−)\s*(\d+(?:[.,]\d+)?)\s*(kg|tonnes?|t\b|lbs?|g|grams?)',
        r'weighs?\s*(\d+(?:[.,]\d+)?)\s*(kg|tonnes?|t\b|lbs?|g|grams?)',
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−)\s*(\d+(?:[.,]\d+)?)\s*(kg|tonnes?|t\b|lbs?|g|grams?)\s*weight',
    ]
    for pattern in weight_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                groups = m.groups()
                if len(groups) >= 3 and groups[0] and groups[1]:
                    v1, v2 = float(groups[0].replace(',','.')), float(groups[1].replace(',','.'))
                    u = groups[2].lower()
                    if u in ['kg'] and 0.001 < v1 < 10000:
                        stats["weight"] = f"{v1}–{v2} {u}" if v1 != v2 else f"{v1} {u}"
                        break
                    elif u in ['t','tonne','tonnes'] and 0.001 < v1 < 100:
                        stats["weight"] = f"{v1}–{v2} t" if v1 != v2 else f"{v1} t"
                        break
                    elif u in ['lb','lbs','pounds'] and 0.01 < v1 < 22000:
                        stats["weight"] = f"{v1}–{v2} {u}" if v1 != v2 else f"{v1} {u}"
                        break
            except: pass
    
    # Length
    length_patterns = [
        r'(?:length|long|wingspan)\s*(?:of)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−)\s*(\d+(?:[.,]\d+)?)\s*(m\b|metres?|cm\b|mm\b|ft\b|in\b)',
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−)\s*(\d+(?:[.,]\d+)?)\s*(m\b|metres?|cm\b|mm\b|ft\b|in\b)\s*(?:long|length)',
    ]
    for pattern in length_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                groups = m.groups()
                v1, v2 = float(groups[0].replace(',','.')), float(groups[1].replace(',','.'))
                u = groups[2].lower()
                if u in ['m','metre','metres','meter','meters'] and 0.001 < v1 < 100:
                    stats["length"] = f"{v1}–{v2} {u}" if v1 != v2 else f"{v1} {u}"
                    break
                elif u in ['cm','centimetre','centimetres'] and 0.1 < v1 < 10000:
                    stats["length"] = f"{v1}–{v2} {u}" if v1 != v2 else f"{v1} {u}"
                    break
            except: pass
    
    # Height
    if any(w in text.lower() for w in ['shoulder', 'stands', 'tall', 'height']):
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−)\s*(\d+(?:[.,]\d+)?)\s*(m\b|metres?|cm\b|ft\b)', text, re.I)
        if m:
            try:
                v1, v2 = float(m.group(1).replace(',','.')), float(m.group(2).replace(',','.'))
                u = m.group(3).lower()
                if u in ['m','metre','metres','meter','meters'] and 0.01 < v1 < 10:
                    stats["height"] = f"{v1}–{v2} {u}" if v1 != v2 else f"{v1} {u}"
            except: pass
    
    # Lifespan
    lifespan_patterns = [
        r'live\s*(\d+(?:-\d+)?)\s*(years?|yrs?|months?|weeks?|days?)',
        r'(\d+(?:-\d+)?)\s*(years?|yrs?|months?|weeks?|days?)\s*(?:lifespan|life|wild|captivity)',
    ]
    for pattern in lifespan_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                v = m.group(1)
                unit = m.group(2).lower()
                if 'year' in unit:
                    if '-' in v:
                        p = v.split('-')
                        if 0 < int(p[0]) < int(p[1]) < 200:
                            stats["lifespan"] = f"{v} years"
                            break
                    elif 0 < int(v) < 200:
                        stats["lifespan"] = f"{v} years"
                        break
            except: pass
    
    # Speed
    if any(w in text.lower() for w in ['speed', 'sprint', 'run', 'fly', 'swim', 'fast']):
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*(km/h|kmph|mph|mi/h|m/s)', text, re.I)
        if m:
            try:
                v = float(m.group(1).replace(',','.'))
                if 0.1 < v < 500:
                    stats["top_speed"] = f"{v} {m.group(2).lower()}"
            except: pass
    
    return stats

def extract_diet(text, animal_type):
    """Extract diet with type-specific defaults"""
    if not text: 
        return get_default_diet(animal_type)
    
    t = text.lower()
    
    # Check for specific diet terms
    if any(w in t for w in ['carnivore', 'carnivorous', 'meat-eater', 'predator', 'preys on', 'hunts']):
        return "Carnivore"
    elif any(w in t for w in ['herbivore', 'herbivorous', 'plant-eater', 'grazes', 'browses', 'foliage', 'vegetation']):
        return "Herbivore"
    elif any(w in t for w in ['omnivore', 'omnivorous', 'both plants and animals', 'varied diet']):
        return "Omnivore"
    elif any(w in t for w in ['insectivore', 'insectivorous', 'eats insects']):
        return "Insectivore"
    elif any(w in t for w in ['piscivore', 'piscivorous', 'eats fish']):
        return "Piscivore"
    
    # Fall back to type-specific default
    return get_default_diet(animal_type)

def extract_conservation(text):
    if not text: return None
    statuses = ["Critically Endangered", "Endangered", "Vulnerable", "Near Threatened", 
                "Least Concern", "Data Deficient", "Extinct in the Wild", "Extinct"]
    for s in statuses:
        if s.lower() in text.lower():
            return s
    return None

def extract_locations(text, animal_type):
    """Extract locations using animal-specific keywords"""
    if not text: return None
    
    # Get animal-specific locations
    animal_locations = LOCATIONS.get("animal_specific", {}).get(animal_type, [])
    if not animal_locations:
        # Fall back to all regions
        animal_locations = []
        for region_locs in LOCATIONS.get("regions", {}).values():
            animal_locations.extend(region_locs)
    
    # Find matching locations
    locs = []
    text_lower = text.lower()
    for loc in animal_locations:
        if loc.lower() in text_lower:
            locs.append(loc)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_locs = []
    for loc in locs:
        if loc.lower() not in seen:
            seen.add(loc.lower())
            unique_locs.append(loc)
    
    return ", ".join(unique_locs[:5]) if unique_locs else None

def extract_habitat(text, animal_type):
    """Extract habitat using animal-specific keywords"""
    if not text: return None
    
    habitat_keywords = HABITATS.get(animal_type, HABITATS.get("default", []))
    found = []
    
    for keyword in habitat_keywords:
        if keyword in text.lower():
            found.append(keyword)
    
    return ", ".join(list(set(found))[:4]) if found else None

def extract_features(text, animal_type):
    """Extract distinctive features based on animal type"""
    if not text: return None
    
    type_features = FEATURES.get(animal_type, {})
    positive = type_features.get("positive", [])
    negative = type_features.get("negative", [])
    
    features = []
    text_lower = text.lower()
    
    # Check positive features
    for feature in positive:
        if feature in text_lower:
            features.append(feature.capitalize())
    
    # Check for common features in text
    common_features = {
        "striped": "Striped coat",
        "stripe": "Striped coat",
        "spotted": "Spotted coat",
        "spot": "Spotted coat",
        "mane": "Distinctive mane",
        "trunk": "Long trunk",
        "tusk": "Large tusks",
        "horn": "Prominent horns",
        "antler": "Large antlers",
        "wing": "Distinctive wings",
        "tail": "Long tail",
        "fin": "Distinctive fins",
        "shell": "Protective shell",
        "venom": "Venomous",
        "color": "Vibrant coloration"
    }
    
    for keyword, feature in common_features.items():
        if keyword in text_lower and feature not in features:
            # Don't add features that don't match animal type
            if feature not in [f.capitalize() for f in negative]:
                features.append(feature)
    
    return features[:3] if features else None

def extract_behavior(text, animal_type):
    """Extract social behavior"""
    if not text: return None
    t = text.lower()
    
    if any(w in t for w in ['solitary', 'alone', 'lives alone', 'mostly solitary']):
        return "Solitary"
    elif any(w in t for w in ['pack', 'group', 'social', 'herd', 'flock', 'school', 'swarm', 'colony']):
        return "Social"
    elif any(w in t for w in ['pair', 'mate', 'family', 'monogamous']):
        return "Family groups"
    
    return None

def extract_reproduction(text, animal_type):
    repro = {
        "gestation_period": None,
        "average_litter_size": None,
        "name_of_young": get_young_name(animal_type)
    }
    
    # Gestation/incubation
    m = re.search(r'(?:gestation|incubation|pregnancy)\s*lasts?\s*(?:around|about|for)?\s*(\d+(?:-\d+)?)\s*(months?|weeks?|days?)', text, re.I)
    if m:
        repro["gestation_period"] = f"{m.group(1)} {m.group(2)}"
    
    # Litter/clutch size
    m = re.search(r'(?:litter|clutch|brood)\s*(?:size|consists?|of)?\s*(?:of|up to|typically|average)?\s*(\d+(?:-\d+)?)\s*(?:eggs|young|offspring|cubs?|chicks?|eggs?)?', text, re.I)
    if m:
        repro["average_litter_size"] = m.group(1)
    
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
    if any(w in t for w in ['climate change', 'global warming', 'ocean acidification']):
        threats.append('Climate change')
    if any(w in t for w in ['pollution', 'pesticide', 'contamination']):
        threats.append('Pollution')
    if any(w in t for w in ['overfishing', 'bycatch', 'fishing']):
        threats.append('Overfishing')
    return ', '.join(threats[:3]) if threats else None

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
                        classification = {f: None for f in CLASSIFICATION_FIELDS}
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
    except: pass
    return None

# ============================================================================
# CACHE
# ============================================================================

def load_cache(qid):
    f = f"data/{qid}.json"
    if os.path.exists(f):
        try:
            with open(f, "r", encoding="utf-8") as fp: return json.load(fp)
        except: pass
    return None

def save_cache(qid, data):
    with open(f"data/{qid}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ============================================================================
# MAIN
# ============================================================================

def generate(animals, force=False):
    output = []
    for i, a in enumerate(animals):
        name, sci, qid = a["name"], a["scientific_name"], a.get("qid", f"animal_{i}")
        print(f"\n{'='*60}")
        print(f"[{i+1}/{len(animals)}] {name} ({sci})")
        print(f"{'='*60}")
        
        cached = load_cache(qid) if not force else None
        
        if cached:
            data = cached
            data["sources"] = list(set(data.get("sources", [])))
        else:
            data = {
                "id": qid, "name": name, "scientific_name": sci, "common_names": [],
                "description": None, "summary": None, "image": None, "wikipedia_url": None,
                "classification": {f: None for f in CLASSIFICATION_FIELDS},
                "animal_type": None, "young_name": None, "group_name": None,
                "physical": {"weight": None, "length": None, "height": None, "top_speed": None, "lifespan": None},
                "ecology": {"diet": None, "habitat": None, "locations": None, "group_behavior": None,
                           "conservation_status": None, "biggest_threat": None, "distinctive_features": None},
                "reproduction": {"gestation_period": None, "average_litter_size": None, "name_of_young": None},
                "sources": [], "last_updated": None
            }
        
        if not data["image"] or force:
            print("  📖 Wikipedia...")
            wiki = fetch_wikipedia_summary(name)
            if wiki["summary"]:
                data["summary"] = wiki["summary"]
                data["description"] = wiki["description"]
                data["image"] = wiki["image"]
                data["wikipedia_url"] = wiki["url"]
                if "Wikipedia" not in data["sources"]: data["sources"].append("Wikipedia")
                
                full = fetch_wikipedia_full(name)
                all_text = wiki["summary"] + " " + full
                
                animal_type = detect_animal_type(name, data["classification"])
                data["animal_type"] = animal_type
                data["young_name"] = get_young_name(animal_type)
                data["group_name"] = get_group_name(animal_type)
                print(f"    ✓ Type: {animal_type}")
                
                stats = extract_stats(all_text, animal_type)
                for k, v in stats.items():
                    if v:
                        data["physical"][k] = v
                        print(f"    ✓ {k}: {v}")
                
                diet = extract_diet(all_text, animal_type)
                if diet:
                    data["ecology"]["diet"] = diet
                    print(f"    ✓ diet: {diet}")
                
                cons = extract_conservation(all_text)
                if cons:
                    data["ecology"]["conservation_status"] = cons
                    print(f"    ✓ conservation: {cons}")
                
                locs = extract_locations(all_text, animal_type)
                if locs:
                    data["ecology"]["locations"] = locs
                    print(f"    ✓ locations: {locs[:50]}...")
                
                habitat = extract_habitat(all_text, animal_type)
                if habitat:
                    data["ecology"]["habitat"] = habitat
                    print(f"    ✓ habitat: {habitat}")
                
                features = extract_features(all_text, animal_type)
                if features:
                    data["ecology"]["distinctive_features"] = features
                    print(f"    ✓ features: {features}")
                
                behavior = extract_behavior(all_text, animal_type)
                if behavior:
                    data["ecology"]["group_behavior"] = behavior
                    print(f"    ✓ behavior: {behavior}")
                
                repro = extract_reproduction(all_text, animal_type)
                for k, v in repro.items():
                    if v:
                        data["reproduction"][k] = v
                        if k != 'name_of_young':
                            print(f"    ✓ {k}: {v}")
                
                threats = extract_threats(all_text)
                if threats:
                    data["ecology"]["biggest_threat"] = threats
                    print(f"    ✓ threats: {threats}")
        
        if not data["classification"]["kingdom"] or force:
            print("  🔬 iNaturalist...")
            cl = fetch_inaturalist(sci)
            if cl:
                data["classification"] = cl
                if "iNaturalist" not in data["sources"]: data["sources"].append("iNaturalist")
                
                # Re-detect with classification
                animal_type = detect_animal_type(name, cl)
                data["animal_type"] = animal_type
                data["young_name"] = get_young_name(animal_type)
                data["group_name"] = get_group_name(animal_type)
                print(f"    ✓ Classification complete")
        
        data["last_updated"] = datetime.now().isoformat()
        save_cache(qid, data)
        output.append(data)
        print(f"  ✅ {name} complete!")
        time.sleep(1)
    
    with open("data/animals.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Done! {len(output)} animals")
    return output

TEST_ANIMALS = [
    {"name": "Tiger", "scientific_name": "Panthera tigris", "qid": "Q132186"},
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
    force = "--force" in os.sys.argv
    generate(TEST_ANIMALS, force)
