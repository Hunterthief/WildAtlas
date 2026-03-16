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

# ============================================================================
# FILE NAMING
# ============================================================================

def get_animal_filename(name, qid):
    clean_name = name.lower().replace(' ', '_').replace('-', '_').replace("'", "")
    return f"{clean_name}_{{QID={qid}}}.json"

def save_animal_file(data, name, qid):
    filename = get_animal_filename(name, qid)
    filepath = ANIMAL_STATS_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f" 💾 Saved: {filename}")

# ============================================================================
# FORMAT NINJA API DATA
# ============================================================================

def format_ninja_data(ninja_data, qid, name, sci_name):
    """Format Ninja API data into our structure"""
    
    if not ninja_data:
        return {
            "id": qid,
            "name": name,
            "scientific_name": sci_name,
            "error": "No data from Ninja API"
        }
    
    chars = ninja_data.get("characteristics", {})
    taxonomy = ninja_data.get("taxonomy", {})
    locations = ninja_data.get("locations", [])
    
    # Determine animal type
    animal_type = "default"
    if taxonomy:
        family = taxonomy.get("family", "").lower()
        if "felidae" in family:
            animal_type = "feline"
        elif "canidae" in family:
            animal_type = "canine"
        elif "ursidae" in family:
            animal_type = "bear"
        elif "elephantidae" in family:
            animal_type = "elephant"
    
    # Map to our format
    data = {
        "id": qid,
        "name": name,
        "scientific_name": sci_name,
        "common_names": [],
        "description": "",
        "summary": "",
        "image": "",
        "wikipedia_url": "",
        "classification": {
            "kingdom": taxonomy.get("kingdom", ""),
            "phylum": taxonomy.get("phylum", ""),
            "class": taxonomy.get("class", ""),
            "order": taxonomy.get("order", ""),
            "family": taxonomy.get("family", ""),
            "genus": taxonomy.get("genus", ""),
            "species": taxonomy.get("scientific_name", sci_name)
        },
        "animal_type": animal_type,
        "young_name": chars.get("name_of_young", ""),
        "group_name": chars.get("group", ""),
        "physical": {
            "weight": chars.get("weight", ""),
            "length": "",
            "height": chars.get("height", ""),
            "top_speed": chars.get("top_speed", ""),
            "lifespan": chars.get("lifespan", "")
        },
        "ecology": {
            "diet": chars.get("diet", ""),
            "habitat": chars.get("habitat", ""),
            "locations": ", ".join(locations) if locations else "",
            "group_behavior": chars.get("group_behavior", ""),
            "conservation_status": "",
            "biggest_threat": chars.get("biggest_threat", ""),
            "distinctive_features": [chars.get("most_distinctive_feature")] if chars.get("most_distinctive_feature") else [],
            "population_trend": ""
        },
        "reproduction": {
            "gestation_period": chars.get("gestation_period", ""),
            "average_litter_size": chars.get("average_litter_size", ""),
            "name_of_young": chars.get("name_of_young", "")
        },
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
        "sources": ["API Ninjas"],
        "last_updated": datetime.now().isoformat()
    }
    
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

        print(" 🥷 Fetching from Ninja API...")
        ninja_data = fetch_animal_data(name, ninja_api_key)
        
        if ninja_
            chars = ninja_data.get("characteristics", {})
            print(f"   📊 Got {len(chars)} fields from Ninja API")
        else:
            print(f" ⚠ No data from Ninja API for {name}")
        
        # Format and save
        data = format_ninja_data(ninja_data, qid, name, sci)
        save_animal_file(data, name, qid)
        
        output.append(data)
        print(f" ✅ {name} complete!")
        time.sleep(1)

    # Save combined file
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
