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

# Go up from generator/ to repo root
REPO_ROOT = Path(__file__).parent.parent

# Data directories at repo root
DATA_DIR = REPO_ROOT / "data"
ANIMAL_STATS_DIR = DATA_DIR / "animal_stats"

# Create directories
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(ANIMAL_STATS_DIR, exist_ok=True)

# Config directory (stays in generator/)
CONFIG_DIR = Path(__file__).parent / "config"

# Session setup
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

    # Weight
    weight_patterns = [
        r'(?:weigh|weighs|weight)\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|t|lbs?|pounds?)',
        r'weighs?\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|t|lbs?|pounds?)',
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
                elif u in ['t', 'tonne', 'tonnes'] and 0.1 < v1 < 200:
                    stats["weight"] = f"{v1}–{v2} t" if v1 != v2 else f"{v1} t"
                    break
                elif u in ['lb', 'lbs', 'pound', 'pounds'] and 1 < v1 < 22000:
                    stats["weight"] = f"{v1}–{v2} lbs" if v1 != v2 else f"{v1} lbs"
                    break
            except:
                pass

    # Length
    length_patterns = [
        r'(?:length|long)\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet)',
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet)\s*(?:long|length)?',
    ]
    for pattern in length_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                groups = m.groups()
                v1 = float(groups[0].replace(',', '.'))
                v2 = float(groups[1].replace(',', '.')) if len(groups) > 2 else v1
                u = groups[-1].lower().strip()
                if u in ['m', 'metre', 'metres', 'meter', 'meters'] and 0.1 < v1 < 100:
                    stats["length"] = f"{v1}–{v2} m" if v1 != v2 else f"{v1} m"
                    break
                elif u in ['cm', 'centimetre', 'centimetres'] and 1 < v1 < 10000:
                    stats["length"] = f"{v1}–{v2} cm" if v1 != v2 else f"{v1} cm"
                    break
                elif u in ['ft', 'foot', 'feet'] and 0.5 < v1 < 300:
                    stats["length"] = f"{v1}–{v2} ft" if v1 != v2 else f"{v1} ft"
                    break
            except:
                pass

    # Height
    if any(w in text_lower for w in ['shoulder', 'stands', 'tall', 'height']):
        height_patterns = [
            r'(?:stands?|height|tall)\s*(?:about|around|up to)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet)',
        ]
        for pattern in height_patterns:
            m = re.search(pattern, text, re.I)
            if m:
                try:
                    groups = m.groups()
                    v1 = float(groups[0].replace(',', '.'))
                    v2 = float(groups[1].replace(',', '.')) if len(groups) > 2 else v1
                    u = groups[-1].lower().strip()
                    if u in ['m', 'metre', 'metres', 'meter', 'meters'] and 0.1 < v1 < 10:
                        stats["height"] = f"{v1}–{v2} m" if v1 != v2 else f"{v1} m"
                        break
                    elif u in ['cm', 'centimetre', 'centimetres'] and 10 < v1 < 1000:
                        stats["height"] = f"{v1}–{v2} cm" if v1 != v2 else f"{v1} cm"
                        break
                    elif u in ['ft', 'foot', 'feet'] and 0.5 < v1 < 30:
                        stats["height"] = f"{v1}–{v2} ft" if v1 != v2 else f"{v1} ft"
                        break
                except:
                    pass

    # Lifespan
    lifespan_patterns = [
        r'(?:lifespan|life expectancy|live|lives)\s*(?:of|is|up to|about)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs?|months?|weeks?|days?)',
        r'(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs?|months?|weeks?|days?)\s*(?:lifespan|life|old|age)',
    ]
    for pattern in lifespan_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                v = m.group(1).replace(' ', '')
                unit = m.group(2).lower()
                if 'year' in unit:
                    if '-' in v or '–' in v:
                        p = re.split(r'[-–]', v)
                        if len(p) >= 2 and 0 < int(p[0]) < int(p[1]) < 200:
                            stats["lifespan"] = f"{p[0]}–{p[1]} years"
                            break
                    elif 0 < int(v) < 200:
                        stats["lifespan"] = f"{v} years"
                        break
                elif 'month' in unit and 1 < int(v) < 120:
                    stats["lifespan"] = f"{v} months"
                    break
            except:
                pass

    # Speed
    if any(w in text_lower for w in ['speed', 'sprint', 'run', 'fly', 'swim', 'fast', 'km/h', 'mph']):
        speed_patterns = [
            r'(?:speed|sprint|run|swim|fly|can)\s*(?:of|up to|about)?\s*(\d+(?:[.,]\d+)?)\s*(km/h|kmph|mph|mi/h|m/s)',
            r'(\d+(?:[.,]\d+)?)\s*(km/h|kmph|mph|mi/h|m/s)\s*(?:speed|top speed)?',
        ]
        for pattern in speed_patterns:
            m = re.search(pattern, text, re.I)
            if m:
                try:
                    v = float(m.group(1).replace(',', '.'))
                    if 1 < v < 500:
                        stats["top_speed"] = f"{v} {m.group(2).lower()}"
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
    elif any(w in t for w in ['insectivore', 'insectivorous', 'eats insects']):
        return "Insectivore"
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
    common_features = {
        "striped": "Striped coat", "spotted": "Spotted coat",
        "mane": "Distinctive mane", "trunk": "Long trunk",
        "tusk": "Large tusks", "horn": "Prominent horns",
        "wing": "Distinctive wings", "tail": "Long tail",
        "fin": "Distinctive fins", "shell": "Protective shell",
        "venom": "Venomous", "claw": "Sharp claws",
        "fur": "Thick fur", "scale": "Scaled skin"
    }
    for keyword, feature in common_features.items():
        if keyword in text_lower and feature not in features:
            features.append(feature)
    return features[:3] if features else []

def extract_behavior(text, animal_type):
    if not text:
        return "Unknown"
    t = text.lower()
    if any(w in t for w in ['solitary', 'alone', 'lives alone', 'mostly solitary', 'lone']):
        return "Solitary"
    elif any(w in t for w in ['pack', 'herd', 'flock', 'school', 'swarm', 'colony', 'social', 'group']):
        return "Social"
    elif any(w in t for w in ['pair', 'mate', 'family group', 'monogamous', 'pairs']):
        return "Family groups"
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
        r'(\d+(?:\s*[-–]\s*\d+)?)\s*(months?|weeks?|days?)\s*(?:gestation|pregnancy|incubation)',
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
                elif 'week' in unit and 1 <= int(v) <= 100:
                    repro["gestation_period"] = f"{v} weeks"
                    break
                elif 'day' in unit and 1 <= int(v) <= 365:
                    repro["gestation_period"] = f"{v} days"
                    break
            except:
                pass
    litter_patterns = [
        r'(?:litter|clutch|cubs?|young|offspring)?\s*(?:size)?\s*(?:of|up to|typically|average)?\s*(\d+(?:\s*[-–]\s*\d+)?)',
        r'(?:gives birth|lays|produces)\s*(?:to|up to|about)?\s*(\d+(?:\s*[-–]\s*\d+)?)',
    ]
    for pattern in litter_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                v = m.group(1).replace(' ', '')
                if '-' in v or '–' in v:
                    p = re.split(r'[-–]', v)
                    if len(p) >= 2 and 1 <= int(p[0]) <= int(p[1]) <= 50:
                        repro["average_litter_size"] = p[0] if p[0] == p[1] else f"{p[0]}–{p[1]}"
                        break
                elif 1 <= int(v) <= 50:
                    repro["average_litter_size"] = v
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
    if any(w in t for w in ['climate change', 'global warming', 'ocean acidification']):
        threats.append('Climate change')
    if any(w in t for w in ['pollution', 'pesticide', 'contamination']):
        threats.append('Pollution')
    if any(w in t for w in ['overfishing', 'bycatch', 'fishing', 'overhunting']):
        threats.append('Overfishing')
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
# BUILD ANIMAL DATA
# ============================================================================

def build_animal_data(ninja_data, wiki_summary, wiki_full, inat_classification, qid, name, sci_name):
    # Extract Ninja API data
    ninja_taxonomy = {}
    ninja_chars = {}
    ninja_locations = []
    
    if ninja_data:
        ninja_taxonomy = ninja_data.get("taxonomy", {}) or {}
        ninja_chars = ninja_data.get("characteristics", {}) or {}
        ninja_locations = ninja_data.get("locations", []) or []
    
    classification = inat_classification if inat_classification else ninja_taxonomy
    animal_type = detect_animal_type(name, classification)
    young_name = get_young_name(animal_type)
    group_name = get_group_name(animal_type)
    
    all_text = ""
    if wiki_summary and wiki_summary.get("summary") and wiki_summary.get("summary") != "Unknown":
        all_text += wiki_summary.get("summary", "") + " "
    if wiki_full:
        all_text += wiki_full
    
    data = {
        "id": qid,
        "name": name,
        "scientific_name": sci_name,
        "common_names": [],
        "description": wiki_summary.get("description", "Unknown") if wiki_summary else "Unknown",
        "summary": wiki_summary.get("summary", "Unknown") if wiki_summary else "Unknown",
        "image": wiki_summary.get("image", "") if wiki_summary else "",
        "wikipedia_url": wiki_summary.get("url", "Unknown") if wiki_summary else "Unknown",
        "classification": {
            "kingdom": ninja_taxonomy.get("kingdom") or "Unknown",
            "phylum": ninja_taxonomy.get("phylum") or "Unknown",
            "class": ninja_taxonomy.get("class") or "Unknown",
            "order": ninja_taxonomy.get("order") or "Unknown",
            "family": ninja_taxonomy.get("family") or "Unknown",
            "genus": ninja_taxonomy.get("genus") or "Unknown",
            "species": ninja_taxonomy.get("scientific_name") or sci_name
        },
        "animal_type": animal_type,
        "young_name": young_name,
        "group_name": group_name,
        "physical": {
            "weight": ninja_chars.get("weight") or "Unknown",
            "length": "Unknown",
            "height": ninja_chars.get("height") or "Unknown",
            "top_speed": ninja_chars.get("top_speed") or "Unknown",
            "lifespan": ninja_chars.get("lifespan") or "Unknown"
        },
        "ecology": {
            "diet": ninja_chars.get("diet") or "Unknown",
            "habitat": ninja_chars.get("habitat") or "Unknown",
            "locations": ", ".join(ninja_locations) if ninja_locations else "Unknown",
            "group_behavior": ninja_chars.get("group_behavior") or "Unknown",
            "conservation_status": "Unknown",
            "biggest_threat": ninja_chars.get("biggest_threat") or "Unknown",
            "distinctive_features": [ninja_chars.get("most_distinctive_feature")] if ninja_chars.get("most_distinctive_feature") else [],
            "population_trend": "Unknown"
        },
        "reproduction": {
            "gestation_period": ninja_chars.get("gestation_period") or "Unknown",
            "average_litter_size": ninja_chars.get("average_litter_size") or "Unknown",
            "name_of_young": ninja_chars.get("name_of_young") or young_name
        },
        "additional_info": {
            "lifestyle": ninja_chars.get("lifestyle") or "Unknown",
            "color": ninja_chars.get("color") or "Unknown",
            "skin_type": ninja_chars.get("skin_type") or "Unknown",
            "prey": ninja_chars.get("prey") or "Unknown",
            "slogan": ninja_chars.get("slogan") or "Unknown",
            "group": ninja_chars.get("group") or "Unknown",
            "number_of_species": ninja_chars.get("number_of_species") or "Unknown",
            "estimated_population_size": ninja_chars.get("estimated_population_size") or "Unknown",
            "age_of_sexual_maturity": ninja_chars.get("age_of_sexual_maturity") or "Unknown",
            "age_of_weaning": ninja_chars.get("age_of_weaning") or "Unknown",
            "most_distinctive_feature": ninja_chars.get("most_distinctive_feature") or "Unknown"
        },
        "sources": [],
        "last_updated": datetime.now().isoformat()
    }
    
    if ninja_data:
        data["sources"].append("API Ninjas")
    if wiki_summary and wiki_summary.get("summary") and wiki_summary.get("summary") != "Unknown":
        data["sources"].append("Wikipedia")
    
    if all_text:
        if data["physical"]["weight"] == "Unknown":
            stats = extract_stats(all_text, animal_type)
            if stats["weight"] != "Unknown":
                data["physical"]["weight"] = stats["weight"]
        if data["physical"]["length"] == "Unknown":
            stats = extract_stats(all_text, animal_type)
            if stats["length"] != "Unknown":
                data["physical"]["length"] = stats["length"]
        if data["physical"]["height"] == "Unknown":
            stats = extract_stats(all_text, animal_type)
            if stats["height"] != "Unknown":
                data["physical"]["height"] = stats["height"]
        if data["physical"]["top_speed"] == "Unknown":
            stats = extract_stats(all_text, animal_type)
            if stats["top_speed"] != "Unknown":
                data["physical"]["top_speed"] = stats["top_speed"]
        if data["physical"]["lifespan"] == "Unknown":
            stats = extract_stats(all_text, animal_type)
            if stats["lifespan"] != "Unknown":
                data["physical"]["lifespan"] = stats["lifespan"]
        
        if data["ecology"]["diet"] == "Unknown":
            diet = extract_diet(all_text, animal_type)
            if diet != "Unknown":
                data["ecology"]["diet"] = diet
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
        if not data["ecology"]["distinctive_features"]:
            features = extract_features(all_text, animal_type)
            if features:
                data["ecology"]["distinctive_features"] = features
        if data["ecology"]["group_behavior"] == "Unknown":
            behavior = extract_behavior(all_text, animal_type)
            if behavior != "Unknown":
                data["ecology"]["group_behavior"] = behavior
        if data["ecology"]["biggest_threat"] == "Unknown":
            threats = extract_threats(all_text)
            if threats != "Unknown":
                data["ecology"]["biggest_threat"] = threats
        
        if data["reproduction"]["gestation_period"] == "Unknown":
            repro = extract_reproduction(all_text, animal_type)
            if repro["gestation_period"] != "Unknown":
                data["reproduction"]["gestation_period"] = repro["gestation_period"]
            if repro["average_litter_size"] == "Unknown":
                data["reproduction"]["average_litter_size"] = repro["average_litter_size"]
        
        if data["additional_info"]["prey"] == "Unknown":
            prey_match = re.search(r'(?:preys? on|feeds? on|eats|diet consists of|primary food)[:\s]+([^.]+)', all_text, re.I)
            if prey_match:
                data["additional_info"]["prey"] = prey_match.group(1).strip()[:100]
    
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
            else:
                chars = ninja_data.get("characteristics", {})
                print(f"   📊 Ninja API data received: {len(chars)} characteristics")
                print(f"   🔍 Available fields: {', '.join(chars.keys())[:100]}...")

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
