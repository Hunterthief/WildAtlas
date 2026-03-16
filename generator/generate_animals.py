# generator/generate_animals.py
import requests, json, time, os, re
from datetime import datetime
from pathlib import Path
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

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
NINJA_API = "https://api.api-ninjas.com/v1/animals"

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
# NINJA API FETCHING
# ============================================================================

def fetch_ninja_animal(name):
    try:
        ninja_headers = {"X-Api-Key": os.environ.get("NINJA_API_KEY", "")}
        r = session.get(f"{NINJA_API}?name={name.replace(' ', '%20')}", 
                       headers={**headers, **ninja_headers}, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if data and len(data) > 0:
                return data[0]
    except Exception as e:
        print(f" ⚠ Ninja API error: {e}")
    return None

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
            if any(w in name_lower for w in ["salmon", "trout", "tuna"]):
                return "salmon"
            return "fish"
        elif "amphibia" in class_name:
            if any(w in name_lower for w in ["frog", "toad"]):
                return "frog"
            return "salamander"
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

# ============================================================================
# FILE NAMING & CACHING
# ============================================================================

def get_animal_filename(name, qid):
    clean_name = name.lower().replace(' ', '_').replace('-', '_').replace("'", "")
    return f"{clean_name}_{{QID={qid}}}.json"

def load_cache(qid, name=None):
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
    filename = get_animal_filename(name, qid)
    filepath = f"data/animal_stats/{filename}"
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f" 💾 Saved: {filename}")
    return filepath

# ============================================================================
# BUILD ANIMAL DATA (NO NULLS - ALL NINJA API FIELDS INCLUDED)
# ============================================================================

def build_animal_data(ninja_data, wiki_data, qid, animal_type):
    data = {
        "id": qid,
        "name": ninja_data.get("name", "Unknown"),
        "scientific_name": "Unknown",
        "common_names": [],
        "description": wiki_data.get("description", "Unknown"),
        "summary": wiki_data.get("summary", "Unknown"),
        "image": wiki_data.get("image", ""),
        "wikipedia_url": wiki_data.get("url", "Unknown"),
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
        "young_name": get_young_name(animal_type),
        "group_name": get_group_name(animal_type),
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
            "name_of_young": get_young_name(animal_type)
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

    # ========== MERGE NINJA API DATA (ALL FIELDS) ==========
    if ninja_data:
        taxonomy = ninja_data.get("taxonomy", {})
        if taxonomy:
            data["classification"]["kingdom"] = taxonomy.get("kingdom", "Unknown")
            data["classification"]["phylum"] = taxonomy.get("phylum", "Unknown")
            data["classification"]["class"] = taxonomy.get("class", "Unknown")
            data["classification"]["order"] = taxonomy.get("order", "Unknown")
            data["classification"]["family"] = taxonomy.get("family", "Unknown")
            data["classification"]["genus"] = taxonomy.get("genus", "Unknown")
            data["scientific_name"] = taxonomy.get("scientific_name", data["scientific_name"])
            data["classification"]["species"] = taxonomy.get("scientific_name", "Unknown")

        locations = ninja_data.get("locations", [])
        if locations and len(locations) > 0:
            data["ecology"]["locations"] = ", ".join(locations)
        
        single_location = ninja_data.get("characteristics", {}).get("location", "")
        if single_location and single_location != data["ecology"]["locations"]:
            if data["ecology"]["locations"] == "Unknown":
                data["ecology"]["locations"] = single_location

        chars = ninja_data.get("characteristics", {})
        if chars:
            data["physical"]["weight"] = chars.get("weight", "Unknown")
            data["physical"]["height"] = chars.get("height", "Unknown")
            data["physical"]["top_speed"] = chars.get("top_speed", "Unknown")
            data["physical"]["lifespan"] = chars.get("lifespan", "Unknown")

            data["ecology"]["diet"] = chars.get("diet", "Unknown")
            data["ecology"]["habitat"] = chars.get("habitat", "Unknown")
            data["ecology"]["group_behavior"] = chars.get("group_behavior", "Unknown")
            data["ecology"]["biggest_threat"] = chars.get("biggest_threat", "Unknown")
            data["ecology"]["estimated_population_size"] = chars.get("estimated_population_size", "Unknown")

            data["reproduction"]["gestation_period"] = chars.get("gestation_period", "Unknown")
            data["reproduction"]["average_litter_size"] = chars.get("average_litter_size", "Unknown")
            data["reproduction"]["name_of_young"] = chars.get("name_of_young", get_young_name(animal_type))

            data["additional_info"]["lifestyle"] = chars.get("lifestyle", "Unknown")
            data["additional_info"]["color"] = chars.get("color", "Unknown")
            data["additional_info"]["skin_type"] = chars.get("skin_type", "Unknown")
            data["additional_info"]["prey"] = chars.get("prey", "Unknown")
            data["additional_info"]["slogan"] = chars.get("slogan", "Unknown")
            data["additional_info"]["group"] = chars.get("group", "Unknown")
            data["additional_info"]["number_of_species"] = chars.get("number_of_species", "Unknown")
            data["additional_info"]["age_of_sexual_maturity"] = chars.get("age_of_sexual_maturity", "Unknown")
            data["additional_info"]["age_of_weaning"] = chars.get("age_of_weaning", "Unknown")
            data["additional_info"]["most_distinctive_feature"] = chars.get("most_distinctive_feature", "Unknown")

            distinct_feature = chars.get("most_distinctive_feature", "")
            if distinct_feature and distinct_feature != "Unknown":
                data["ecology"]["distinctive_features"] = [distinct_feature]

    if ninja_data:
        data["sources"].append("API Ninjas")
    if wiki_data.get("summary") and wiki_data.get("summary") != "Unknown":
        data["sources"].append("Wikipedia")

    return data

# ============================================================================
# MAIN GENERATION
# ============================================================================

def generate(animals, force=False):
    output = []
    
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
            ninja_data = fetch_ninja_animal(name)
            
            if not ninja_data:
                print(f" ⚠ No data from Ninja API for {name}, creating basic entry")
                ninja_data = {
                    "name": name,
                    "taxonomy": {"scientific_name": sci},
                    "locations": [],
                    "characteristics": {}
                }

            print(" 📖 Fetching from Wikipedia...")
            wiki_data = fetch_wikipedia_summary(name)
            
            animal_type = detect_animal_type(name, ninja_data.get("taxonomy", {}))
            print(f" ✓ Type: {animal_type}")

            data = build_animal_data(ninja_data, wiki_data, qid, animal_type)
            save_animal_file(data, name, qid)

        output.append(data)
        print(f" ✅ {name} complete!")
        time.sleep(1)

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
    force = "--force" in os.sys.argv
    generate(TEST_ANIMALS, force)
