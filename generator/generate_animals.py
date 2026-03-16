# generator/generate_animals.py
import requests, json, time, os, re, sys
from datetime import datetime
from pathlib import Path
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Import Ninja API module
sys.path.insert(0, str(Path(__file__).parent))
from modules.api_ninjas import fetch_animal_data

# Setup
os.makedirs("data", exist_ok=True)
os.makedirs("data/animal_stats", exist_ok=True)
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
            if "goose" in name_lower:
                return "goose"
            if "swan" in name_lower:
                return "swan"
            if any(w in name_lower for w in ["chicken", "rooster", "hen"]):
                return "chicken"
            if "penguin" in name_lower:
                return "penguin"
            return "bird"
        elif "actinopterygii" in class_name or "chondrichthyes" in class_name:
            if any(w in name_lower for w in ["shark"]):
                return "shark"
            if any(w in name_lower for w in ["ray", "stingray", "manta"]):
                return "ray"
            if any(w in name_lower for w in ["salmon", "trout", "tuna"]):
                return "salmon"
            return "fish"
        elif "amphibia" in class_name:
            if any(w in name_lower for w in ["frog", "toad"]):
                return "frog"
            return "salamander"
        elif "reptilia" in class_name:
            if any(w in name_lower for w in ["snake", "serpent", "cobra", "python", "viper"]):
                return "snake"
            if any(w in name_lower for w in ["lizard", "gecko", "iguana"]):
                return "lizard"
            if any(w in name_lower for w in ["turtle", "tortoise", "terrapin"]):
                return "turtle"
            if any(w in name_lower for w in ["crocodile", "alligator", "caiman"]):
                return "crocodile"
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
# DATA EXTRACTION (ALL EXISTING EXTRACTORS)
# ============================================================================

def extract_stats(text, animal_type):
    """Extract physical stats from Wikipedia text"""
    stats = {"weight": "Unknown", "length": "Unknown", "height": "Unknown", "lifespan": "Unknown", "top_speed": "Unknown"}
    if not text:
        return stats

    text_lower = text.lower()

    # ========== WEIGHT ==========
    weight_patterns = [
        r'(?:males?|females?|adults?|individuals?|they|it)\s*(?:weigh|weighs|weight)\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|t|lbs?|pounds?|g|grams?)',
        r'weighs?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|t|lbs?|pounds?)',
        r'(?:weigh|weight|weighing|up to|over|about|around)\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|t|lbs?|pounds?)',
        r'weighs?\s*(?:around|about|approximately|up to)?\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|t|lbs?|pounds?)',
    ]

    for pattern in weight_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                groups = m.groups()
                if len(groups) >= 2:
                    v1 = float(groups[0].replace(',', '.'))
                    v2 = float(groups[1].replace(',', '.')) if len(groups) > 2 and groups[1] and groups[1].replace(',','').replace('.','').isdigit() else v1
                    u = groups[-1].lower().strip()

                    if u in ['kg', 'kilogram', 'kilograms']:
                        if animal_type in ['feline', 'canine', 'bear'] and 10 < v1 < 500:
                            stats["weight"] = f"{v1}–{v2} kg" if v1 != v2 else f"{v1} kg"
                            break
                        elif animal_type in ['elephant', 'whale'] and 100 < v1 < 10000:
                            stats["weight"] = f"{v1}–{v2} kg" if v1 != v2 else f"{v1} kg"
                            break
                        elif 0.1 < v1 < 10000:
                            stats["weight"] = f"{v1}–{v2} kg" if v1 != v2 else f"{v1} kg"
                            break
                    elif u in ['t', 'tonne', 'tonnes', 'ton'] and 0.1 < v1 < 200:
                        stats["weight"] = f"{v1}–{v2} t" if v1 != v2 else f"{v1} t"
                        break
                    elif u in ['lb', 'lbs', 'pound', 'pounds'] and 1 < v1 < 22000:
                        stats["weight"] = f"{v1}–{v2} lbs" if v1 != v2 else f"{v1} lbs"
                        break
            except Exception as e:
                print(f" ⚠ Weight parse error: {e}")

    # ========== LENGTH ==========
    length_patterns = [
        r'(?:head[- ]?body|body|total)?\s*(?:length|long)\s*(?:of|is|ranges from|between)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|mm|ft|feet|in|inches?)',
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet)\s*(?:long|length|in length)?',
        r'(?:grows|reaches|measures)\s*(?:up to|to|about)?\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet)',
        r'wingspan\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet)',
    ]

    for pattern in length_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                groups = m.groups()
                v1 = float(groups[0].replace(',', '.'))
                v2 = float(groups[1].replace(',', '.')) if len(groups) > 2 and groups[1] else v1
                u = groups[-1].lower().strip()

                if u in ['m', 'metre', 'metres', 'meter', 'meters'] and 0.1 < v1 < 100:
                    stats["length"] = f"{v1}–{v2} m" if v1 != v2 else f"{v1} m"
                    break
                elif u in ['cm', 'centimetre', 'centimetres', 'centimeter', 'centimeters'] and 1 < v1 < 10000:
                    stats["length"] = f"{v1}–{v2} cm" if v1 != v2 else f"{v1} cm"
                    break
                elif u in ['ft', 'foot', 'feet'] and 0.5 < v1 < 300:
                    stats["length"] = f"{v1}–{v2} ft" if v1 != v2 else f"{v1} ft"
                    break
            except Exception as e:
                print(f" ⚠ Length parse error: {e}")

    # ========== HEIGHT ==========
    if any(w in text_lower for w in ['shoulder', 'stands', 'tall', 'height', 'at the shoulder']):
        height_patterns = [
            r'(?:stands?|stand|height|tall|at the shoulder)\s*(?:about|around|up to|of)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet)',
            r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet)\s*(?:tall|height|shoulder|at the shoulder)',
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
                except Exception as e:
                    print(f" ⚠ Height parse error: {e}")

    # ========== LIFESPAN ==========
    lifespan_patterns = [
        r'(?:lifespan|life expectancy|live|lives|live up to)\s*(?:of|is|up to|about|around)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs?|months?|weeks?|days?)',
        r'(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs?|months?|weeks?|days?)\s*(?:lifespan|life|in wild|in captivity|old|age)',
        r'(?:up to|about|around|approximately)\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs?)\s*(?:old|age|lifespan)',
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
            except Exception as e:
                print(f" ⚠ Lifespan parse error: {e}")

    # ========== SPEED ==========
    if any(w in text_lower for w in ['speed', 'sprint', 'run', 'fly', 'swim', 'fast', 'km/h', 'mph', 'kilometers per hour']):
        speed_patterns = [
            r'(?:speed|sprint|run|swim|fly|can|capable of)\s*(?:of|up to|about|around)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−)?\s*(\d+(?:[.,]\d+)?)?\s*(km/h|kmph|mph|mi/h|m/s|kilometers? per hour|miles? per hour)',
            r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−)?\s*(\d+(?:[.,]\d+)?)?\s*(km/h|kmph|mph|mi/h|m/s)\s*(?:speed|top speed|maximum)?',
            r'(?:up to|about|around|approximately|can)\s*(\d+(?:[.,]\d+)?)\s*(km/h|kmph|mph|mi/h|m/s)',
        ]

        for pattern in speed_patterns:
            m = re.search(pattern, text, re.I)
            if m:
                try:
                    v = float(m.group(1).replace(',', '.'))
                    if 1 < v < 500:
                        stats["top_speed"] = f"{v} {m.group(3).lower()}"
                        break
                except Exception as e:
                    print(f" ⚠ Speed parse error: {e}")

    return stats

def extract_diet(text, animal_type):
    """Extract diet with type-specific defaults"""
    if not text:
        return get_default_diet(animal_type)

    t = text.lower()

    if any(w in t for w in ['carnivore', 'carnivorous', 'meat-eater', 'predator', 'preys on', 'hunts', 'feeds on animals']):
        return "Carnivore"
    elif any(w in t for w in ['herbivore', 'herbivorous', 'plant-eater', 'grazes', 'browses', 'foliage', 'vegetation', 'feeds on plants']):
        return "Herbivore"
    elif any(w in t for w in ['omnivore', 'omnivorous', 'both plants and animals', 'varied diet', 'eats both']):
        return "Omnivore"
    elif any(w in t for w in ['insectivore', 'insectivorous', 'eats insects', 'insects']):
        return "Insectivore"
    elif any(w in t for w in ['piscivore', 'piscivorous', 'eats fish', 'fish']):
        return "Piscivore"

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
    """Extract locations with proper filtering"""
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
        if animal_type == 'elephant' and any(w in loc_lower for w in ['asia', 'china', 'indonesia']):
            continue
        if animal_type == 'raptor' and 'asia' in loc_lower and 'bald' in text_lower:
            continue
        if animal_type == 'penguin' and any(w in loc_lower for w in ['asia', 'africa', 'north america']):
            continue
        if loc_lower not in seen:
            seen.add(loc_lower)
            unique_locs.append(loc)

    return ", ".join(unique_locs[:5]) if unique_locs else "Unknown"

def extract_habitat(text, animal_type):
    """Extract habitat using animal-specific keywords"""
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
    """Extract features with better filtering"""
    if not text:
        return []

    type_features = FEATURES.get(animal_type, FEATURES.get("default", {}))
    positive = type_features.get("positive", [])
    negative = type_features.get("negative", [])

    features = []
    text_lower = text.lower()

    for feature in positive:
        if feature in text_lower:
            display_feature = feature.replace('_', ' ').title()
            if display_feature not in features:
                features.append(display_feature)

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
        "claw": "Sharp claws",
        "fang": "Large fangs",
        "beak": "Distinctive beak",
        "feather": "Distinctive plumage",
        "scale": "Scaled skin",
        "fur": "Thick fur"
    }

    for keyword, feature in common_features.items():
        if keyword in text_lower and feature not in features:
            blocked = False
            for neg in negative:
                if neg in keyword or keyword in neg:
                    blocked = True
                    break

            if animal_type not in ['fish', 'shark', 'ray'] and 'fin' in keyword:
                blocked = True
            if animal_type not in ['bird', 'raptor', 'penguin', 'butterfly', 'bee', 'bat'] and 'wing' in keyword:
                blocked = True
            if animal_type not in ['turtle'] and 'shell' in keyword:
                blocked = True
            if animal_type not in ['elephant'] and 'trunk' in keyword:
                blocked = True
            if animal_type not in ['elephant', 'bovine', 'deer'] and 'tusk' in keyword:
                blocked = True
            if animal_type not in ['feline'] and 'stripe' in keyword:
                blocked = True

            if not blocked:
                features.append(feature)

    return features[:3] if features else []

def extract_behavior(text, animal_type):
    """Extract behavior with animal-specific logic"""
    if not text:
        return "Unknown"

    t = text.lower()

    social_indicators = {
        'elephant': ['herd', 'family', 'matriarch', 'social', 'group'],
        'bee': ['colony', 'hive', 'social', 'eusocial', 'worker', 'queen'],
        'penguin': ['colony', 'rookery', 'huddle', 'group', 'social'],
        'canine': ['pack', 'social', 'group', 'hunting together'],
        'ant': ['colony', 'social', 'eusocial', 'worker', 'queen']
    }

    if animal_type in social_indicators:
        for indicator in social_indicators[animal_type]:
            if indicator in t:
                return "Social"

    if any(w in t for w in ['solitary', 'alone', 'lives alone', 'mostly solitary', 'lives singly', 'lone', 'territorial']):
        return "Solitary"
    elif any(w in t for w in ['pack', 'herd', 'flock', 'school', 'swarm', 'colony', 'social', 'group living', 'highly social', 'live in groups']):
        return "Social"
    elif any(w in t for w in ['pair', 'mate', 'family group', 'monogamous', 'nuclear family', 'pairs']):
        return "Family groups"

    social_types = ['elephant', 'bee', 'ant', 'penguin', 'canine', 'whale']
    if animal_type in social_types:
        return "Social"

    return "Solitary"

def extract_reproduction(text, animal_type):
    """Extract reproduction data from Wikipedia text"""
    repro = {
        "gestation_period": "Unknown",
        "average_litter_size": "Unknown",
        "name_of_young": get_young_name(animal_type)
    }

    if not text:
        return repro

    text_lower = text.lower()

    gestation_patterns = [
        r'(?:gestation|pregnancy|incubation)\s*(?:period|lasts?|is|of)?\s*(?:around|about|approximately|over)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(months?|weeks?|days?)',
        r'(\d+(?:\s*[-–]\s*\d+)?)\s*(months?|weeks?|days?)\s*(?:gestation|pregnancy|incubation|period)',
        r'(?:pregnant|carries young)\s*(?:for)?\s*(?:around|about)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(months?|weeks?|days?)',
        r'after\s*(?:around|about)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(months?|weeks?|days?)\s*(?:of\s*)?(?:pregnancy|gestation)',
        r'lasts?\s*(?:around|about|approximately|over|up to)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(months?|weeks?|days?)',
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
            except Exception as e:
                print(f" ⚠ Gestation parse error: {e}")

    litter_patterns = [
        r'(?:litter|clutch|brood|cubs?|young|offspring|chicks?|pups?)?\s*(?:size|consists?|of|contains|are|is)?\s*(?:of|up to|typically|average|more)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(?:eggs?|young|offspring|cubs?|chicks?|pups?)?',
        r'(?:as many as|up to|about|around|typically|usually)\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(?:eggs?|young|offspring|cubs?|chicks?|pups?)?',
        r'(\d+(?:\s*[-–]\s*\d+)?)\s*(?:eggs?|young|offspring|cubs?|chicks?|pups?)?\s*(?:per\s*)?(?:litter|clutch|brood)',
        r'(?:gives birth|lays|produces)\s*(?:to|up to|about)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(?:eggs?|young|offspring|cubs?|chicks?|pups?)?',
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
            except Exception as e:
                print(f" ⚠ Litter size parse error: {e}")

    return repro

def extract_threats(text):
    threats = []
    t = text.lower()
    if any(w in t for w in ['poach', 'illegal trade', 'body parts', 'fur trade', 'ivory', 'horn trade']):
        threats.append('Poaching')
    if any(w in t for w in ['habitat loss', 'deforestation', 'habitat destruction', 'habitat fragmentation', 'loss of habitat']):
        threats.append('Habitat loss')
    if any(w in t for w in ['human-wildlife conflict', 'livestock', 'retaliation', 'persecution', 'killed by humans']):
        threats.append('Human-wildlife conflict')
    if any(w in t for w in ['climate change', 'global warming', 'ocean acidification', 'rising temperatures']):
        threats.append('Climate change')
    if any(w in t for w in ['pollution', 'pesticide', 'contamination', 'pollutants']):
        threats.append('Pollution')
    if any(w in t for w in ['overfishing', 'bycatch', 'fishing', 'overhunting', 'hunting']):
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
    """Generate filename for individual animal file"""
    clean_name = name.lower().replace(' ', '_').replace('-', '_').replace("'", "")
    return f"{clean_name}_{{QID={qid}}}.json"

def load_cache(qid, name=None):
    """Load cached data from individual animal file"""
    if name:
        filename = get_animal_filename(name, qid)
        f = f"data/animal_stats/{filename}"
        if os.path.exists(f):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    return json.load(fp)
            except:
                pass
    return None

def save_animal_file(data, name, qid):
    """Save individual animal data to its own file"""
    filename = get_animal_filename(name, qid)
    filepath = f"data/animal_stats/{filename}"
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f" 💾 Saved: {filename}")
    return filepath

# ============================================================================
# BUILD ANIMAL DATA (MERGES NINJA + WIKIPEDIA + INATURALIST)
# ============================================================================

def build_animal_data(ninja_data, wiki_summary, wiki_full, inat_classification, qid, name, sci_name):
    """
    Build complete animal data structure.
    Priority: Ninja API > Wikipedia extraction > iNaturalist > Defaults
    NO NULL VALUES - everything has actual data or 'Unknown'
    """
    
    # Get animal type from Ninja taxonomy first, then refine with iNaturalist
    ninja_taxonomy = ninja_data.get("taxonomy", {}) if ninja_data else {}
    classification = inat_classification if inat_classification else ninja_taxonomy
    
    animal_type = detect_animal_type(name, classification)
    young_name = get_young_name(animal_type)
    group_name = get_group_name(animal_type)
    
    # Combine all text for extraction
    all_text = ""
    if wiki_summary and wiki_summary.get("summary") and wiki_summary.get("summary") != "Unknown":
        all_text += wiki_summary.get("summary", "") + " "
    if wiki_full:
        all_text += wiki_full
    
    # ========== BUILD DATA STRUCTURE (NO NULLS) ==========
    data = {
        "id": qid,
        "name": name,
        "scientific_name": sci_name,
        "common_names": [],
        "description": "Unknown",
        "summary": "Unknown",
        "image": "",
        "wikipedia_url": "Unknown",
        "classification": {
            "kingdom": "Unknown",
            "phylum": "Unknown",
            "class": "Unknown",
            "order": "Unknown",
            "family": "Unknown",
            "genus": "Unknown",
            "species": "Unknown"
        },
        "animal_type": animal_type,
        "young_name": young_name,
        "group_name": group_name,
        "physical": {
            "weight": "Unknown",
            "length": "Unknown",
            "height": "Unknown",
            "top_speed": "Unknown",
            "lifespan": "Unknown"
        },
        "ecology": {
            "diet": "Unknown",
            "habitat": "Unknown",
            "locations": "Unknown",
            "group_behavior": "Unknown",
            "conservation_status": "Unknown",
            "biggest_threat": "Unknown",
            "distinctive_features": [],
            "population_trend": "Unknown"
        },
        "reproduction": {
            "gestation_period": "Unknown",
            "average_litter_size": "Unknown",
            "name_of_young": young_name
        },
        "additional_info": {
            "lifestyle": "Unknown",
            "color": "Unknown",
            "skin_type": "Unknown",
            "prey": "Unknown",
            "slogan": "Unknown",
            "group": "Unknown",
            "number_of_species": "Unknown",
            "estimated_population_size": "Unknown",
            "age_of_sexual_maturity": "Unknown",
            "age_of_weaning": "Unknown",
            "most_distinctive_feature": "Unknown"
        },
        "sources": [],
        "last_updated": datetime.now().isoformat()
    }
    
    # ========== MERGE NINJA API DATA (ALL FIELDS PRESERVED) ==========
    if ninja_data:
        chars = ninja_data.get("characteristics", {})
        taxonomy = ninja_data.get("taxonomy", {})
        locations = ninja_data.get("locations", [])
        
        # Classification from Ninja
        if taxonomy:
            data["classification"]["kingdom"] = taxonomy.get("kingdom", "Unknown") or "Unknown"
            data["classification"]["phylum"] = taxonomy.get("phylum", "Unknown") or "Unknown"
            data["classification"]["class"] = taxonomy.get("class", "Unknown") or "Unknown"
            data["classification"]["order"] = taxonomy.get("order", "Unknown") or "Unknown"
            data["classification"]["family"] = taxonomy.get("family", "Unknown") or "Unknown"
            data["classification"]["genus"] = taxonomy.get("genus", "Unknown") or "Unknown"
            data["scientific_name"] = taxonomy.get("scientific_name", sci_name) or sci_name
            data["classification"]["species"] = taxonomy.get("scientific_name", "Unknown") or "Unknown"
        
        # Locations from Ninja
        if locations and len(locations) > 0:
            data["ecology"]["locations"] = ", ".join(locations)
        
        # All characteristics from Ninja (EVERY FIELD)
        if chars:
            data["physical"]["weight"] = chars.get("weight") or "Unknown"
            data["physical"]["height"] = chars.get("height") or "Unknown"
            data["physical"]["top_speed"] = chars.get("top_speed") or "Unknown"
            data["physical"]["lifespan"] = chars.get("lifespan") or "Unknown"
            
            data["ecology"]["diet"] = chars.get("diet") or "Unknown"
            data["ecology"]["habitat"] = chars.get("habitat") or "Unknown"
            data["ecology"]["group_behavior"] = chars.get("group_behavior") or "Unknown"
            data["ecology"]["biggest_threat"] = chars.get("biggest_threat") or "Unknown"
            
            data["reproduction"]["gestation_period"] = chars.get("gestation_period") or "Unknown"
            data["reproduction"]["average_litter_size"] = chars.get("average_litter_size") or "Unknown"
            data["reproduction"]["name_of_young"] = chars.get("name_of_young") or young_name
            
            data["additional_info"]["lifestyle"] = chars.get("lifestyle") or "Unknown"
            data["additional_info"]["color"] = chars.get("color") or "Unknown"
            data["additional_info"]["skin_type"] = chars.get("skin_type") or "Unknown"
            data["additional_info"]["prey"] = chars.get("prey") or "Unknown"
            data["additional_info"]["slogan"] = chars.get("slogan") or "Unknown"
            data["additional_info"]["group"] = chars.get("group") or "Unknown"
            data["additional_info"]["number_of_species"] = chars.get("number_of_species") or "Unknown"
            data["additional_info"]["estimated_population_size"] = chars.get("estimated_population_size") or "Unknown"
            data["additional_info"]["age_of_sexual_maturity"] = chars.get("age_of_sexual_maturity") or "Unknown"
            data["additional_info"]["age_of_weaning"] = chars.get("age_of_weaning") or "Unknown"
            data["additional_info"]["most_distinctive_feature"] = chars.get("most_distinctive_feature") or "Unknown"
            
            # Distinctive features
            distinct_feature = chars.get("most_distinctive_feature")
            if distinct_feature:
                data["ecology"]["distinctive_features"] = [distinct_feature]
        
        data["sources"].append("API Ninjas")
    
    # ========== MERGE WIKIPEDIA DATA ==========
    if wiki_summary:
        if wiki_summary.get("summary") and wiki_summary.get("summary") != "Unknown":
            data["summary"] = wiki_summary.get("summary")
        if wiki_summary.get("description") and wiki_summary.get("description") != "Unknown":
            data["description"] = wiki_summary.get("description")
        if wiki_summary.get("image"):
            data["image"] = wiki_summary.get("image")
        if wiki_summary.get("url") and wiki_summary.get("url") != "Unknown":
            data["wikipedia_url"] = wiki_summary.get("url")
        
        if "Wikipedia" not in data["sources"]:
            data["sources"].append("Wikipedia")
    
    # ========== EXTRACT FROM WIKIPEDIA TEXT (SUPPLEMENT NINJA DATA) ==========
    if all_text:
        # Only extract if Ninja didn't provide data or data is Unknown
        if data["physical"]["weight"] == "Unknown":
            stats = extract_stats(all_text, animal_type)
            if stats["weight"] and stats["weight"] != "Unknown":
                data["physical"]["weight"] = stats["weight"]
            if stats["length"] and stats["length"] != "Unknown":
                data["physical"]["length"] = stats["length"]
            if stats["height"] == "Unknown" and stats.get("height"):
                data["physical"]["height"] = stats["height"]
            if stats["top_speed"] and stats["top_speed"] != "Unknown":
                data["physical"]["top_speed"] = stats["top_speed"]
            if stats["lifespan"] and stats["lifespan"] != "Unknown":
                data["physical"]["lifespan"] = stats["lifespan"]
        
        if data["ecology"]["diet"] == "Unknown":
            diet = extract_diet(all_text, animal_type)
            if diet and diet != "Unknown":
                data["ecology"]["diet"] = diet
        
        if data["ecology"]["conservation_status"] == "Unknown":
            cons = extract_conservation(all_text)
            if cons and cons != "Unknown":
                data["ecology"]["conservation_status"] = cons
        
        if data["ecology"]["locations"] == "Unknown":
            locs = extract_locations(all_text, animal_type)
            if locs and locs != "Unknown":
                data["ecology"]["locations"] = locs
        
        if data["ecology"]["habitat"] == "Unknown":
            habitat = extract_habitat(all_text, animal_type)
            if habitat and habitat != "Unknown":
                data["ecology"]["habitat"] = habitat
        
        if not data["ecology"]["distinctive_features"]:
            features = extract_features(all_text, animal_type)
            if features:
                data["ecology"]["distinctive_features"] = features
        
        if data["ecology"]["group_behavior"] == "Unknown":
            behavior = extract_behavior(all_text, animal_type)
            if behavior and behavior != "Unknown":
                data["ecology"]["group_behavior"] = behavior
        
        if data["reproduction"]["gestation_period"] == "Unknown":
            repro = extract_reproduction(all_text, animal_type)
            if repro["gestation_period"] and repro["gestation_period"] != "Unknown":
                data["reproduction"]["gestation_period"] = repro["gestation_period"]
            if repro["average_litter_size"] and repro["average_litter_size"] != "Unknown":
                data["reproduction"]["average_litter_size"] = repro["average_litter_size"]
        
        if data["ecology"]["biggest_threat"] == "Unknown":
            threats = extract_threats(all_text)
            if threats and threats != "Unknown":
                data["ecology"]["biggest_threat"] = threats
    
    # ========== MERGE INATURALIST CLASSIFICATION ==========
    if inat_classification:
        for field in CLASSIFICATION_FIELDS:
            if inat_classification.get(field) and inat_classification[field] != "Unknown":
                if data["classification"][field] == "Unknown":
                    data["classification"][field] = inat_classification[field]
        
        if "iNaturalist" not in data["sources"]:
            data["sources"].append("iNaturalist")
    
    return data

# ============================================================================
# MAIN GENERATION
# ============================================================================

def generate(animals, force=False):
    output = []
    ninja_api_key = os.environ.get("NINJA_API_KEY", "")
    
    if not ninja_api_key:
        print(" ⚠ WARNING: NINJA_API_KEY not set! API calls will fail.")
        print("   Set it with: export NINJA_API_KEY='your_key_here'")
    
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
            # 1. Fetch from Ninja API
            print(" 🥷 Fetching from Ninja API...")
            ninja_data = fetch_animal_data(name, ninja_api_key)
            
            if not ninja_
                print(f" ⚠ No data from Ninja API for {name}")
                ninja_data = {
                    "name": name,
                    "taxonomy": {"scientific_name": sci},
                    "locations": [],
                    "characteristics": {}
                }

            # 2. Fetch from Wikipedia
            print(" 📖 Fetching from Wikipedia...")
            wiki_summary = fetch_wikipedia_summary(name)
            wiki_full = fetch_wikipedia_full(name)
            
            # 3. Fetch from iNaturalist
            print(" 🔬 Fetching from iNaturalist...")
            inat_classification = fetch_inaturalist(sci)
            
            # 4. Build complete data structure (merges all sources)
            data = build_animal_data(ninja_data, wiki_summary, wiki_full, inat_classification, qid, name, sci)
            
            # 5. Save individual file
            save_animal_file(data, name, qid)

        output.append(data)
        print(f" ✅ {name} complete!")
        time.sleep(1)

    # 6. Save combined file (backward compatible)
    with open("data/animals.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Done! {len(output)} animals saved:")
    print(f"   • Individual files: data/animal_stats/")
    print(f"   • Combined file: data/animals.json")
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
