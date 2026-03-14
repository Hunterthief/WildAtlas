# generator/generate_animals.py
import requests, json, time, os, re
from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

os.makedirs("data", exist_ok=True)
session = requests.Session()
retry = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retry))
headers = {"User-Agent": "WildAtlasBot/1.0", "Accept": "application/json"}

WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
WIKI_MOBILE = "https://en.m.wikipedia.org/wiki/"
INAT_API = "https://api.inaturalist.org/v1/taxa"

CLASSIFICATION_FIELDS = ["kingdom", "phylum", "class", "order", "family", "genus", "species"]

# ============================================================================
# ANIMAL TYPE DETECTION & DYNAMIC NAMING (Works for ALL animal types)
# ============================================================================

YOUNG_NAMES = {
    # Mammals
    "feline": "cub", "canine": "pup", "bear": "cub", "elephant": "calf",
    "deer": "fawn", "bovine": "calf", "equine": "foal", "primate": "infant",
    "rodent": "pup", "bat": "pup", "whale": "calf", "dolphin": "calf",
    "seal": "pup", "rabbit": "kit", "hare": "leveret", "mammal": "young",
    # Birds
    "bird": "chick", "raptor": "eaglet", "owl": "owlet", "duck": "duckling",
    "goose": "gosling", "swan": "cygnet", "chicken": "chick", "penguin": "chick",
    # Fish
    "fish": "fry", "shark": "pup", "ray": "pup", "salmon": "fry", "trout": "fry",
    # Amphibians
    "frog": "tadpole", "toad": "tadpole", "salamander": "larva", "newt": "larva",
    # Reptiles
    "snake": "hatchling", "lizard": "hatchling", "turtle": "hatchling",
    "tortoise": "hatchling", "crocodile": "hatchling", "alligator": "hatchling",
    # Insects & Arthropods
    "insect": "larva", "butterfly": "caterpillar", "moth": "caterpillar",
    "bee": "larva", "ant": "larva", "spider": "spiderling", "crab": "zoea",
    "lobster": "larva", "shrimp": "larva", "default": "young"
}

GROUP_NAMES = {
    # Mammals
    "feline": "streak", "lion": "pride", "canine": "pack", "wolf": "pack",
    "elephant": "herd", "deer": "herd", "bovine": "herd", "equine": "herd",
    "primate": "troop", "bat": "colony", "whale": "pod", "dolphin": "pod",
    "seal": "colony", "rabbit": "colony", "mammal": "population",
    # Birds
    "bird": "flock", "raptor": "kettle", "owl": "parliament", "duck": "flock",
    "goose": "gaggle", "swan": "bevy", "chicken": "flock", "penguin": "colony",
    # Fish
    "fish": "school", "shark": "shiver", "ray": "fever", "salmon": "run",
    # Amphibians
    "frog": "army", "toad": "knot", "salamander": "population",
    # Reptiles
    "snake": "den", "lizard": "population", "turtle": "bale", "crocodile": "bask",
    # Insects & Arthropods
    "insect": "swarm", "butterfly": "swarm", "bee": "colony", "ant": "colony",
    "spider": "cluster", "crab": "consortium", "lobster": "swarm", "default": "population"
}

ANIMAL_TYPE_KEYWORDS = {
    "feline": ["cat", "tiger", "lion", "leopard", "cheetah", "panther", "jaguar", "lynx", "puma"],
    "canine": ["dog", "wolf", "fox", "jackal", "coyote"],
    "bear": ["bear", "panda", "polar bear"],
    "elephant": ["elephant"],
    "primate": ["monkey", "ape", "gorilla", "chimpanzee", "orangutan", "lemur"],
    "rodent": ["mouse", "rat", "squirrel", "beaver", "hamster", "guinea pig"],
    "bat": ["bat"],
    "whale": ["whale", "orca", "porpoise"],
    "dolphin": ["dolphin"],
    "seal": ["seal", "walrus", "sea lion"],
    "deer": ["deer", "elk", "moose", "reindeer", "antelope"],
    "bovine": ["cow", "bull", "bison", "buffalo", "ox"],
    "equine": ["horse", "zebra", "donkey", "mule"],
    "rabbit": ["rabbit", "hare"],
    "bird": ["bird", "eagle", "hawk", "falcon", "owl", "duck", "goose", "swan", 
             "chicken", "rooster", "turkey", "penguin", "parrot", "raven", "crow"],
    "raptor": ["eagle", "hawk", "falcon", "vulture", "kite"],
    "owl": ["owl"],
    "duck": ["duck", "mallard"],
    "goose": ["goose"],
    "swan": ["swan"],
    "chicken": ["chicken", "rooster", "hen"],
    "penguin": ["penguin"],
    "fish": ["fish", "salmon", "trout", "tuna", "cod", "bass", "carp", "goldfish"],
    "shark": ["shark"],
    "ray": ["ray", "stingray", "manta"],
    "frog": ["frog", "toad"],
    "salamander": ["salamander", "newt"],
    "snake": ["snake", "serpent", "python", "cobra", "viper"],
    "lizard": ["lizard", "gecko", "iguana", "chameleon"],
    "turtle": ["turtle", "tortoise", "terrapin"],
    "crocodile": ["crocodile", "alligator", "caiman", "gharial"],
    "insect": ["insect", "beetle", "fly", "mosquito", "wasp", "hornet"],
    "butterfly": ["butterfly", "moth"],
    "bee": ["bee", "bumblebee"],
    "ant": ["ant", "termite"],
    "spider": ["spider", "scorpion", "tarantula"],
    "crab": ["crab", "lobster", "shrimp", "crayfish"]
}

def detect_animal_type(name, classification=None):
    """Detect animal type from name and classification"""
    name_lower = name.lower()
    
    # Check name keywords first
    for animal_type, keywords in ANIMAL_TYPE_KEYWORDS.items():
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
                return "carnivore"
            elif "proboscidea" in order_name: return "elephant"
            elif "primates" in order_name: return "primate"
            elif "cetacea" in order_name:
                if "whale" in name_lower: return "whale"
                return "dolphin"
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
            if any(w in name_lower for w in ["shark", "ray"]): 
                return "shark" if "shark" in name_lower else "ray"
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
            if any(w in name_lower for w in ["spider", "scorpion"]): return "spider"
            return "insect"
        elif "arachnida" in class_name:
            return "spider"
        elif "crustacea" in class_name:
            if "crab" in name_lower: return "crab"
            if "lobster" in name_lower: return "lobster"
            return "crab"
    
    return "default"

def get_young_name(animal_type):
    return YOUNG_NAMES.get(animal_type, YOUNG_NAMES["default"])

def get_group_name(animal_type):
    return GROUP_NAMES.get(animal_type, GROUP_NAMES["default"])

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
# DATA EXTRACTION (GENERALIZED FOR ALL ANIMAL TYPES)
# ============================================================================

def extract_stats(text, animal_type):
    """Extract physical stats - works for all animal types"""
    stats = {"weight": None, "length": None, "height": None, "lifespan": None, "top_speed": None}
    if not text: return stats
    
    # Weight patterns (supports g, kg, t, lb for insects to whales)
    weight_patterns = [
        r'weighs?\s*(?:of)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−)\s*(\d+(?:[.,]\d+)?)\s*(kg|tonnes?|t\b|lbs?|g|grams?|mg|milligrams?)',
        r'weighs?\s*(\d+(?:[.,]\d+)?)\s*(kg|tonnes?|t\b|lbs?|g|grams?|mg)',
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−)\s*(\d+(?:[.,]\d+)?)\s*(kg|tonnes?|t\b|lbs?|g|grams?)\s*weight',
        r'mass\s*(?:of)?\s*(\d+(?:[.,]\d+)?)\s*(kg|tonnes?|t\b|lbs?|g)',
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
                    elif u in ['g','gram','grams'] and 0.01 < v1 < 1000000:
                        stats["weight"] = f"{v1}–{v2} {u}" if v1 != v2 else f"{v1} {u}"
                        break
                    elif u in ['mg','milligram','milligrams'] and 1 < v1 < 10000000:
                        stats["weight"] = f"{v1}–{v2} {u}" if v1 != v2 else f"{v1} {u}"
                        break
                elif len(groups) == 2:
                    v, u = float(groups[0].replace(',','.')), groups[1].lower()
                    if u in ['kg'] and 0.001 < v < 10000:
                        stats["weight"] = f"{v} {u}"
                        break
                    elif u in ['t','tonne','tonnes'] and 0.001 < v < 100:
                        stats["weight"] = f"{v} t"
                        break
            except: pass
    
    # Length patterns (body length, wingspan, etc.)
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
                elif u in ['mm','millimetre','millimetres'] and 1 < v1 < 100000:
                    stats["length"] = f"{v1}–{v2} {u}" if v1 != v2 else f"{v1} {u}"
                    break
                elif u in ['ft','feet','foot'] and 0.01 < v1 < 300:
                    stats["length"] = f"{v1}–{v2} {u}" if v1 != v2 else f"{v1} {u}"
                    break
                elif u in ['in','inch','inches'] and 0.1 < v1 < 3600:
                    stats["length"] = f"{v1}–{v2} {u}" if v1 != v2 else f"{v1} {u}"
                    break
            except: pass
    
    # Height (for standing animals)
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
        r'lifespan\s*(?:of)?\s*(\d+(?:-\d+)?)\s*(years?|yrs?|months?|weeks?|days?)',
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
                elif 'month' in unit:
                    stats["lifespan"] = f"{v} months"
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
    if not text: return None
    t = text.lower()
    
    if any(w in t for w in ['carnivore', 'carnivorous', 'meat-eater', 'predator', 'preys on', 'hunts']):
        return "Carnivore"
    elif any(w in t for w in ['herbivore', 'herbivorous', 'plant-eater', 'grazes', 'browses', 'foliage', 'vegetation']):
        return "Herbivore"
    elif any(w in t for w in ['omnivore', 'omnivorous', 'both plants and animals', 'varied diet']):
        return "Omnivore"
    elif any(w in t for w in ['insectivore', 'insectivorous', 'eats insects', 'insects']):
        return "Insectivore"
    elif any(w in t for w in ['piscivore', 'piscivorous', 'eats fish', 'fish']):
        return "Piscivore"
    elif any(w in t for w in ['filter feeder', 'filter-feeder', 'plankton']):
        return "Filter feeder"
    elif any(w in t for w in ['detritivore', 'detritus', 'decomposer']):
        return "Detritivore"
    elif any(w in t for w in ['parasite', 'parasitic']):
        return "Parasitic"
    
    return None

def extract_conservation(text):
    if not text: return None
    statuses = ["Critically Endangered", "Endangered", "Vulnerable", "Near Threatened", 
                "Least Concern", "Data Deficient", "Extinct in the Wild", "Extinct"]
    for s in statuses:
        if s.lower() in text.lower():
            return s
    return None

def extract_locations(text, animal_type):
    if not text: return None
    
    location_keywords = [
        "Asia", "Africa", "Europe", "North America", "South America", "Australia", "Antarctica",
        "India", "China", "Russia", "Indonesia", "Thailand", "Malaysia", "Bangladesh", "Nepal",
        "United States", "Canada", "Mexico", "Brazil", "Argentina", "Japan", "Philippines",
        "Pacific", "Atlantic", "Indian Ocean", "Arctic", "Southern Ocean"
    ]
    
    locs = []
    for loc in location_keywords:
        if loc.lower() in text.lower():
            locs.append(loc)
    
    return ", ".join(locs[:5]) if locs else None

def extract_habitat(text, animal_type):
    if not text: return None
    
    habitat_keywords = [
        "forest", "grassland", "savanna", "desert", "mountain", "wetland", "swamp", "jungle",
        "woodland", "plain", "tundra", "rainforest", "ocean", "sea", "river", "lake", "pond",
        "coral reef", "kelp forest", "mangrove", "marsh", "bog", "cave", "burrow", "nest"
    ]
    
    found = []
    for keyword in habitat_keywords:
        if keyword in text.lower():
            found.append(keyword)
    
    return ", ".join(list(set(found))[:4]) if found else None

def extract_behavior(text, animal_type):
    if not text: return None
    t = text.lower()
    
    if any(w in t for w in ['solitary', 'alone', 'lives alone', 'mostly solitary', 'solitary life']):
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
    if any(w in t for w in ['invasive species', 'introduced species']):
        threats.append('Invasive species')
    if any(w in t for w in ['disease', 'pathogen', 'virus', 'fungus']):
        threats.append('Disease')
    return ', '.join(threats[:3]) if threats else None

def extract_distinctive_features(text, animal_type):
    """Extract distinctive features from text"""
    features = []
    t = text.lower()
    
    # Common distinctive features
    if any(w in t for w in ['stripe', 'striped', 'stripes']):
        features.append('Striped coat')
    if any(w in t for w in ['spot', 'spotted', 'spots']):
        features.append('Spotted coat')
    if any(w in t for w in ['mane']):
        features.append('Distinctive mane')
    if any(w in t for w in ['trunk']):
        features.append('Long trunk')
    if any(w in t for w in ['tusk', 'tusks']):
        features.append('Large tusks')
    if any(w in t for w in ['horn', 'horns']):
        features.append('Prominent horns')
    if any(w in t for w in ['antler', 'antlers']):
        features.append('Large antlers')
    if any(w in t for w in ['wing', 'wings']):
        features.append('Distinctive wings')
    if any(w in t for w in ['tail']):
        features.append('Long tail')
    if any(w in t for w in ['fin', 'fins']):
        features.append('Distinctive fins')
    if any(w in t for w in ['shell']):
        features.append('Protective shell')
    if any(w in t for w in ['venom', 'venomous', 'poison']):
        features.append('Venomous')
    if any(w in t for w in ['glow', 'bioluminescent']):
        features.append('Bioluminescent')
    if any(w in t for w in ['color', 'colour', 'bright', 'vibrant']):
        features.append('Vibrant coloration')
    
    return features[:3] if features else None

# ============================================================================
# INATURALIST TAXONOMY
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
# CACHE MANAGEMENT
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
# MAIN GENERATOR (facts.app STYLE OUTPUT)
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
            # facts.app style structure
            data = {
                "id": qid,
                "name": name,
                "scientific_name": sci,
                "common_names": [],
                "description": None,
                "summary": None,
                "image": None,
                "wikipedia_url": None,
                
                # Scientific Classification (like facts.app)
                "classification": {f: None for f in CLASSIFICATION_FIELDS},
                
                # Animal Type Info
                "animal_type": None,
                "young_name": None,
                "group_name": None,
                
                # Physical Stats (like facts.app)
                "physical": {
                    "weight": None,
                    "length": None,
                    "height": None,
                    "top_speed": None,
                    "lifespan": None
                },
                
                # Ecology (like facts.app)
                "ecology": {
                    "diet": None,
                    "habitat": None,
                    "locations": None,
                    "group_behavior": None,
                    "conservation_status": None,
                    "biggest_threat": None,
                    "distinctive_features": None
                },
                
                # Reproduction (like facts.app)
                "reproduction": {
                    "gestation_period": None,
                    "average_litter_size": None,
                    "name_of_young": None
                },
                
                "sources": [],
                "last_updated": None
            }
        
        # Wikipedia
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
                
                # Detect animal type
                animal_type = detect_animal_type(name, data["classification"])
                data["animal_type"] = animal_type
                data["young_name"] = get_young_name(animal_type)
                data["group_name"] = get_group_name(animal_type)
                print(f"    ✓ Type: {animal_type}")
                
                # Extract all data
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
                
                behavior = extract_behavior(all_text, animal_type)
                if behavior:
                    data["ecology"]["group_behavior"] = behavior
                    print(f"    ✓ behavior: {behavior}")
                
                features = extract_distinctive_features(all_text, animal_type)
                if features:
                    data["ecology"]["distinctive_features"] = features
                    print(f"    ✓ features: {features}")
                
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
        
        # iNaturalist
        if not data["classification"]["kingdom"] or force:
            print("  🔬 iNaturalist...")
            cl = fetch_inaturalist(sci)
            if cl:
                data["classification"] = cl
                if "iNaturalist" not in data["sources"]: data["sources"].append("iNaturalist")
                
                # Re-detect animal type with classification
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

# ============================================================================
# TEST DATA (MIXED ANIMAL TYPES)
# ============================================================================

TEST_ANIMALS = [
    # Mammals
    {"name": "Tiger", "scientific_name": "Panthera tigris", "qid": "Q132186"},
    {"name": "African Elephant", "scientific_name": "Loxodonta africana", "qid": "Q7372"},
    {"name": "Gray Wolf", "scientific_name": "Canis lupus", "qid": "Q213537"},
    # Birds
    {"name": "Bald Eagle", "scientific_name": "Haliaeetus leucocephalus", "qid": "Q25319"},
    {"name": "Emperor Penguin", "scientific_name": "Aptenodytes forsteri", "qid": "Q43306"},
    # Fish
    {"name": "Great White Shark", "scientific_name": "Carcharodon carcharias", "qid": "Q47164"},
    {"name": "Atlantic Salmon", "scientific_name": "Salmo salar", "qid": "Q39709"},
    # Reptiles
    {"name": "Green Sea Turtle", "scientific_name": "Chelonia mydas", "qid": "Q7785"},
    {"name": "King Cobra", "scientific_name": "Ophiophagus hannah", "qid": "Q189609"},
    # Amphibians
    {"name": "American Bullfrog", "scientific_name": "Lithobates catesbeianus", "qid": "Q270238"},
    # Insects
    {"name": "Monarch Butterfly", "scientific_name": "Danaus plexippus", "qid": "Q165980"},
    {"name": "Honey Bee", "scientific_name": "Apis mellifera", "qid": "Q7316"},
]

if __name__ == "__main__":
    force = "--force" in os.sys.argv
    generate(TEST_ANIMALS, force)
