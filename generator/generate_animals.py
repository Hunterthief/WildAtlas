# generator/generate_animals.py
import requests, json, time, os, re, sys
from datetime import datetime
from pathlib import Path
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

sys.path.insert(0, str(Path(__file__).parent))
from modules.api_ninjas import fetch_animal_data

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

# Load configs
def load_config(filename):
    config_path = CONFIG_DIR / filename
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

YOUNG_NAMES = load_config("young_names.json")
GROUP_NAMES = load_config("group_names.json")
LOCATIONS = load_config("locations.json")
HABITATS = load_config("habitats.json")
FEATURES = load_config("features.json")

def get_young_name(animal_type):
    return YOUNG_NAMES.get(animal_type, YOUNG_NAMES.get("default", "young"))

def get_group_name(animal_type):
    return GROUP_NAMES.get(animal_type, GROUP_NAMES.get("default", "population"))

# Wikipedia
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
    except Exception as e:
        print(f" ⚠ Wikipedia error: {e}")
    return {"summary": "", "description": "", "image": "", "url": ""}

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

# iNaturalist
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
                        classification = {f: "" for f in CLASSIFICATION_FIELDS}
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

# Extractors
def extract_stats(text, animal_type):
    stats = {"weight": "", "length": "", "height": "", "lifespan": "", "top_speed": ""}
    if not text:
        return stats
    
    # Weight
    m = re.search(r'weighs?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms)', text, re.I)
    if m:
        stats["weight"] = f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    # Length
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|cm)\s*(?:long|length)', text, re.I)
    if m:
        stats["length"] = f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    # Height
    if 'shoulder' in text.lower() or 'stands' in text.lower():
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|cm)\s*(?:tall|height|shoulder)', text, re.I)
        if m:
            stats["height"] = f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    # Lifespan
    m = re.search(r'(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)', text, re.I)
    if m:
        stats["lifespan"] = f"{m.group(1)} {m.group(2)}"
    
    # Speed
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*(km/h|kmph|mph|mi/h)', text, re.I)
    if m:
        stats["top_speed"] = f"{m.group(1)} {m.group(2)}"
    
    return stats

def extract_conservation(text):
    if not text:
        return ""
    statuses = ["Critically Endangered", "Endangered", "Vulnerable", "Near Threatened", "Least Concern"]
    for s in statuses:
        if s.lower() in text.lower():
            return s
    return ""

def extract_features(text, animal_type):
    if not text:
        return []
    features = []
    text_lower = text.lower()
    
    common = {
        "striped": "Striped coat", "stripe": "Striped coat",
        "spotted": "Spotted coat", "spot": "Spotted coat",
        "mane": "Distinctive mane", "trunk": "Long trunk",
        "tusk": "Large tusks", "horn": "Prominent horns",
        "wing": "Distinctive wings", "tail": "Long tail",
        "fin": "Distinctive fins", "shell": "Protective shell",
        "venom": "Venomous", "claw": "Sharp claws",
        "fur": "Thick fur"
    }
    
    for keyword, feature in common.items():
        if keyword in text_lower and feature not in features:
            features.append(feature)
    
    return features[:3]

def extract_behavior(text):
    if not text:
        return ""
    t = text.lower()
    if any(w in t for w in ['solitary', 'alone', 'lives alone']):
        return "Solitary"
    elif any(w in t for w in ['pack', 'herd', 'flock', 'colony', 'social', 'group']):
        return "Social"
    elif any(w in t for w in ['pair', 'pairs', 'mate']):
        return "Pairs"
    return ""

def extract_reproduction(text):
    repro = {"gestation_period": "", "average_litter_size": ""}
    if not text:
        return repro
    
    # Gestation
    m = re.search(r'(?:gestation|pregnancy)\s*(?:period)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(days?|months?|weeks?)', text, re.I)
    if m:
        repro["gestation_period"] = f"{m.group(1)} {m.group(2)}"
    
    # Litter
    m = re.search(r'(?:litter|cubs?|young)\s*(?:size)?\s*(\d+(?:\s*[-–]\s*\d+)?)', text, re.I)
    if m:
        repro["average_litter_size"] = m.group(1)
    
    return repro

def extract_threats(text):
    if not text:
        return ""
    threats = []
    t = text.lower()
    if any(w in t for w in ['poach', 'illegal trade']):
        threats.append('Poaching')
    if any(w in t for w in ['habitat loss', 'deforestation']):
        threats.append('Habitat loss')
    if any(w in t for w in ['human-wildlife conflict', 'retaliation']):
        threats.append('Human-wildlife conflict')
    return ', '.join(threats[:3])

def extract_prey(text):
    if not text:
        return ""
    m = re.search(r'(?:preys? on|feeds? on|hunts?|eats?|diet)[:\s]+([^.]{10,100})', text, re.I)
    if m:
        return m.group(1).strip()[:80]
    return ""

# File operations
def get_animal_filename(name, qid):
    clean_name = name.lower().replace(' ', '_').replace('-', '_').replace("'", "")
    return f"{clean_name}_{{QID={qid}}}.json"

def save_animal_file(data, name, qid):
    filename = get_animal_filename(name, qid)
    filepath = ANIMAL_STATS_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f" 💾 Saved: {filename}")

# Build data from ALL sources
def build_animal_data(ninja_data, wiki_summary, wiki_full, inat_classification, qid, name, sci_name):
    # Get data from each source
    ninja_chars = ninja_data.get("characteristics", {}) if ninja_data else {}
    ninja_taxonomy = ninja_data.get("taxonomy", {}) if ninja_data else {}
    ninja_locations = ninja_data.get("locations", []) if ninja_data else []
    
    # Animal type
    animal_type = "default"
    taxonomy_to_use = inat_classification if inat_classification else ninja_taxonomy
    if taxonomy_to_use:
        family = taxonomy_to_use.get("family", "").lower()
        if "felidae" in family:
            animal_type = "feline"
        elif "canidae" in family:
            animal_type = "canine"
        elif "ursidae" in family:
            animal_type = "bear"
        elif "elephantidae" in family:
            animal_type = "elephant"
    
    young_name = ninja_chars.get("name_of_young", "") or get_young_name(animal_type)
    
    # Build data - Ninja API first, then fill gaps with Wikipedia/iNaturalist
    data = {
        "id": qid,
        "name": name,
        "scientific_name": sci_name,
        "common_names": [],
        
        # Wikipedia for summary/image
        "description": wiki_summary.get("description", "") if wiki_summary else "",
        "summary": wiki_summary.get("summary", "") if wiki_summary else "",
        "image": wiki_summary.get("image", "") if wiki_summary else "",
        "wikipedia_url": wiki_summary.get("url", "") if wiki_summary else "",
        
        # iNaturalist for classification (more accurate)
        "classification": {
            "kingdom": inat_classification.get("kingdom", "") if inat_classification else ninja_taxonomy.get("kingdom", ""),
            "phylum": inat_classification.get("phylum", "") if inat_classification else ninja_taxonomy.get("phylum", ""),
            "class": inat_classification.get("class", "") if inat_classification else ninja_taxonomy.get("class", ""),
            "order": inat_classification.get("order", "") if inat_classification else ninja_taxonomy.get("order", ""),
            "family": inat_classification.get("family", "") if inat_classification else ninja_taxonomy.get("family", ""),
            "genus": inat_classification.get("genus", "") if inat_classification else ninja_taxonomy.get("genus", ""),
            "species": inat_classification.get("species", "") if inat_classification else ninja_taxonomy.get("scientific_name", sci_name)
        },
        
        "animal_type": animal_type,
        "young_name": young_name,
        "group_name": get_group_name(animal_type),
        
        # Physical - Ninja API primary
        "physical": {
            "weight": ninja_chars.get("weight", ""),
            "length": "",
            "height": ninja_chars.get("height", ""),
            "top_speed": ninja_chars.get("top_speed", ""),
            "lifespan": ninja_chars.get("lifespan", "")
        },
        
        # Ecology - Ninja API primary
        "ecology": {
            "diet": ninja_chars.get("diet", ""),
            "habitat": ninja_chars.get("habitat", ""),
            "locations": ", ".join(ninja_locations) if ninja_locations else "",
            "group_behavior": ninja_chars.get("group_behavior", ""),
            "conservation_status": "",
            "biggest_threat": ninja_chars.get("biggest_threat", ""),
            "distinctive_features": [ninja_chars.get("most_distinctive_feature")] if ninja_chars.get("most_distinctive_feature") else [],
            "population_trend": ""
        },
        
        # Reproduction - Ninja API primary
        "reproduction": {
            "gestation_period": ninja_chars.get("gestation_period", ""),
            "average_litter_size": ninja_chars.get("average_litter_size", ""),
            "name_of_young": young_name
        },
        
        # Additional Info - Ninja API primary
        "additional_info": {
            "lifestyle": ninja_chars.get("lifestyle", ""),
            "color": ninja_chars.get("color", ""),
            "skin_type": ninja_chars.get("skin_type", ""),
            "prey": ninja_chars.get("prey", ""),
            "slogan": ninja_chars.get("slogan", ""),
            "group": ninja_chars.get("group", ""),
            "number_of_species": ninja_chars.get("number_of_species", ""),
            "estimated_population_size": ninja_chars.get("estimated_population_size", ""),
            "age_of_sexual_maturity": ninja_chars.get("age_of_sexual_maturity", ""),
            "age_of_weaning": ninja_chars.get("age_of_weaning", ""),
            "most_distinctive_feature": ninja_chars.get("most_distinctive_feature", "")
        },
        
        "sources": [],
        "last_updated": datetime.now().isoformat()
    }
    
    # Add sources
    if ninja_
        data["sources"].append("API Ninjas")
    if wiki_summary and wiki_summary.get("summary"):
        data["sources"].append("Wikipedia")
    if inat_classification:
        data["sources"].append("iNaturalist")
    
    # Fill gaps with Wikipedia extraction
    if wiki_full:
        if data["physical"]["weight"] == "":
            stats = extract_stats(wiki_full, animal_type)
            if stats["weight"]:
                data["physical"]["weight"] = stats["weight"]
        if data["physical"]["height"] == "":
            stats = extract_stats(wiki_full, animal_type)
            if stats["height"]:
                data["physical"]["height"] = stats["height"]
        if data["physical"]["length"] == "":
            stats = extract_stats(wiki_full, animal_type)
            if stats["length"]:
                data["physical"]["length"] = stats["length"]
        if data["ecology"]["conservation_status"] == "":
            cons = extract_conservation(wiki_full)
            if cons:
                data["ecology"]["conservation_status"] = cons
        if data["ecology"]["group_behavior"] == "":
            behavior = extract_behavior(wiki_full)
            if behavior:
                data["ecology"]["group_behavior"] = behavior
        if not data["ecology"]["distinctive_features"]:
            features = extract_features(wiki_full, animal_type)
            if features:
                data["ecology"]["distinctive_features"] = features
        if data["ecology"]["biggest_threat"] == "":
            threats = extract_threats(wiki_full)
            if threats:
                data["ecology"]["biggest_threat"] = threats
        if data["reproduction"]["gestation_period"] == "":
            repro = extract_reproduction(wiki_full)
            if repro["gestation_period"]:
                data["reproduction"]["gestation_period"] = repro["gestation_period"]
        if data["additional_info"]["prey"] == "":
            prey = extract_prey(wiki_full)
            if prey:
                data["additional_info"]["prey"] = prey
    
    return data

# Main
def generate(animals, force=False):
    output = []
    ninja_api_key = os.environ.get("API_NINJAS_KEY", "")
    
    for i, a in enumerate(animals):
        name, sci, qid = a["name"], a["scientific_name"], a.get("qid", f"animal_{i}")
        print(f"\n{'='*60}")
        print(f"[{i+1}/{len(animals)}] {name} ({sci})")
        print(f"{'='*60}")

        print(" 🥷 Fetching from Ninja API...")
        ninja_data = fetch_animal_data(name, ninja_api_key)
        
        if ninja_data is not None:
            chars = ninja_data.get("characteristics", {})
            print(f"   📊 Got {len(chars)} fields from Ninja API")
        else:
            print(f" ⚠ No data from Ninja API for {name}")
            ninja_data = {"characteristics": {}, "taxonomy": {}, "locations": []}

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
    
    print(f"\n✅ Done! {len(output)} animals saved to {ANIMAL_STATS_DIR}/")
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
