# generator/generate_animals.py
import requests, json, time, os, sys
from datetime import datetime
from pathlib import Path
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Import Ninja API module
sys.path.insert(0, str(Path(__file__).parent))
from modules.api_ninjas import fetch_animal_data

# ============================================================================
# SETUP
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

YOUNG_NAMES = load_config("young_names.json")
GROUP_NAMES = load_config("group_names.json")

def get_young_name(animal_type):
    return YOUNG_NAMES.get(animal_type, YOUNG_NAMES.get("default", "young"))

def get_group_name(animal_type):
    return GROUP_NAMES.get(animal_type, GROUP_NAMES.get("default", "population"))

# ============================================================================
# WIKIPEDIA (for summary/image only)
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
    except Exception as e:
        print(f" ⚠ Wikipedia error: {e}")
    return {"summary": "", "description": "", "image": "", "url": ""}

# ============================================================================
# INATURALIST (for classification only)
# ============================================================================

def fetch_inaturalist(sci_name):
    try:
        params = {"q": sci_name, "per_page": 1, "rank": "species"}
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

# ============================================================================
# BUILD ANIMAL DATA - DIRECT MAPPING FROM NINJA API
# ============================================================================

def build_animal_data(ninja_data, wiki_data, inat_classification, qid, name, sci_name):
    """
    Simply map Ninja API data directly to our format.
    No extraction, no complex logic.
    """
    
    # Get Ninja API data
    chars = ninja_data.get("characteristics", {}) if ninja_data else {}
    taxonomy = ninja_data.get("taxonomy", {}) if ninja_data else {}
    locations = ninja_data.get("locations", []) if ninja_data else []
    
    # Determine animal type from taxonomy
    animal_type = "default"
    if taxonomy:
        family = taxonomy.get("family", "").lower()
        order = taxonomy.get("order", "").lower()
        if "felidae" in family:
            animal_type = "feline"
        elif "canidae" in family:
            animal_type = "canine"
        elif "ursidae" in family:
            animal_type = "bear"
    
    young_name = chars.get("name_of_young") or get_young_name(animal_type)
    
    # Build data structure - DIRECT MAPPING
    data = {
        "id": qid,
        "name": name,
        "scientific_name": sci_name,
        "common_names": [],
        "description": wiki_data.get("description", "") if wiki_data else "",
        "summary": wiki_data.get("summary", "") if wiki_data else "",
        "image": wiki_data.get("image", "") if wiki_data else "",
        "wikipedia_url": wiki_data.get("url", "") if wiki_data else "",
        
        # Classification from iNaturalist or Ninja
        "classification": {
            "kingdom": inat_classification.get("kingdom") if inat_classification else taxonomy.get("kingdom", ""),
            "phylum": inat_classification.get("phylum") if inat_classification else taxonomy.get("phylum", ""),
            "class": inat_classification.get("class") if inat_classification else taxonomy.get("class", ""),
            "order": inat_classification.get("order") if inat_classification else taxonomy.get("order", ""),
            "family": inat_classification.get("family") if inat_classification else taxonomy.get("family", ""),
            "genus": inat_classification.get("genus") if inat_classification else taxonomy.get("genus", ""),
            "species": inat_classification.get("species") if inat_classification else taxonomy.get("scientific_name", sci_name)
        },
        
        "animal_type": animal_type,
        "young_name": young_name,
        "group_name": get_group_name(animal_type),
        
        # Physical - DIRECT from Ninja API
        "physical": {
            "weight": chars.get("weight", ""),
            "length": "",  # Ninja doesn't provide
            "height": chars.get("height", ""),
            "top_speed": chars.get("top_speed", ""),
            "lifespan": chars.get("lifespan", "")
        },
        
        # Ecology - DIRECT from Ninja API
        "ecology": {
            "diet": chars.get("diet", ""),
            "habitat": chars.get("habitat", ""),
            "locations": ", ".join(locations) if locations else "",
            "group_behavior": chars.get("group_behavior", ""),
            "conservation_status": "",  # Ninja doesn't provide
            "biggest_threat": chars.get("biggest_threat", ""),
            "distinctive_features": [chars.get("most_distinctive_feature")] if chars.get("most_distinctive_feature") else [],
            "population_trend": ""
        },
        
        # Reproduction - DIRECT from Ninja API
        "reproduction": {
            "gestation_period": chars.get("gestation_period", ""),
            "average_litter_size": chars.get("average_litter_size", ""),
            "name_of_young": young_name
        },
        
        # Additional Info - DIRECT from Ninja API (ALL FIELDS)
        "additional_info": {
            "lifestyle": chars.get("lifestyle", ""),
            "color": chars.get("color", ""),
            "skin_type": chars.get("skin_type", ""),
            "prey": chars.get("prey", ""),
            "slogan": chars.get("slogan", ""),
            "group": chars.get("group", ""),
            "number_of_species": chars.get("number_of_species", ""),
            "estimated_population_size": chars.get("estimated_population_size", ""),
            "age_of_sexual_maturity": chars.get("age_of_sexual_maturity", ""),
            "age_of_weaning": chars.get("age_of_weaning", ""),
            "most_distinctive_feature": chars.get("most_distinctive_feature", "")
        },
        
        "sources": ["API Ninjas"] if ninja_data else [],
        "last_updated": datetime.now().isoformat()
    }
    
    # Add Wikipedia source
    if wiki_data and wiki_data.get("summary"):
        data["sources"].append("Wikipedia")
    
    # Add iNaturalist source
    if inat_classification:
        data["sources"].append("iNaturalist")
    
    return data

# ============================================================================
# MAIN GENERATION
# ============================================================================

def generate(animals, force=False):
    output = []
    ninja_api_key = os.environ.get("API_NINJAS_KEY", "")
    
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
                    "taxonomy": {},
                    "locations": [],
                    "characteristics": {}
                }
            else:
                chars = ninja_data.get("characteristics", {})
                print(f"   📊 Got {len(chars)} fields from Ninja API")

            # 2. Fetch from Wikipedia (summary/image only)
            print(" 📖 Fetching from Wikipedia...")
            wiki_data = fetch_wikipedia_summary(name)
            
            # 3. Fetch from iNaturalist (classification only)
            print(" 🔬 Fetching from iNaturalist...")
            inat_classification = fetch_inaturalist(sci)
            
            # 4. Build data (DIRECT MAPPING)
            data = build_animal_data(ninja_data, wiki_data, inat_classification, qid, name, sci)
            save_animal_file(data, name, qid)

        output.append(data)
        print(f" ✅ {name} complete!")
        time.sleep(1)

    # Save combined file
    with open(DATA_DIR / "animals.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Done! {len(output)} animals saved")
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
