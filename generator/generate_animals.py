# generator/generate_animals.py
"""Main generator - orchestrates all fetchers and extractors"""
import json, time, os, sys
from datetime import datetime
from pathlib import Path

# Add generator directory to Python path (CRITICAL for GitHub Actions)
GENERATOR_DIR = Path(__file__).parent
sys.path.insert(0, str(GENERATOR_DIR))

# Import modules - use explicit paths from generator directory
from modules.api_ninjas import fetch_animal_data
from fetchers.wikipedia import fetch_wikipedia_summary, fetch_wikipedia_full
from fetchers.inaturalist import fetch_inaturalist
from extractors.sections import extract_wikipedia_sections
from extractors.stats import extract_stats_from_sections
from extractors.diet import extract_diet_from_sections
from extractors.reproduction import extract_reproduction_from_sections
from extractors.conservation import extract_conservation_from_sections
from extractors.behavior import extract_behavior_from_sections
from extractors.additional_info import extract_additional_info_from_sections

# Setup paths
REPO_ROOT = GENERATOR_DIR.parent
DATA_DIR = REPO_ROOT / "data"
ANIMAL_STATS_DIR = DATA_DIR / "animal_stats"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(ANIMAL_STATS_DIR, exist_ok=True)

CONFIG_DIR = GENERATOR_DIR / "config"

# Load configs
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

# Build animal data
def build_animal_data(ninja_data, wiki_summary, wiki_sections, inat_classification, qid, name, sci_name):
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
    
    # Extract from Wikipedia (only used as fallback)
    wiki_stats = extract_stats_from_sections(wiki_sections)
    wiki_diet, wiki_prey = extract_diet_from_sections(wiki_sections)
    wiki_repro = extract_reproduction_from_sections(wiki_sections)
    wiki_conservation_status, wiki_threats = extract_conservation_from_sections(wiki_sections)
    wiki_behavior = extract_behavior_from_sections(wiki_sections)
    wiki_additional = extract_additional_info_from_sections(wiki_sections)
    
    # Build data - Ninja API first, Wikipedia as fallback
    data = {
        "id": qid,
        "name": name,
        "scientific_name": sci_name,
        "common_names": [],
        "description": wiki_summary.get("description", "") if wiki_summary else "",
        "summary": wiki_summary.get("summary", "") if wiki_summary else "",
        "image": wiki_summary.get("image", "") if wiki_summary else "",
        "wikipedia_url": wiki_summary.get("url", "") if wiki_summary else "",
        "wikipedia_sections": wiki_sections,
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
        "physical": {
            "weight": ninja_chars.get("weight", "") or wiki_stats.get("weight", ""),
            "length": ninja_chars.get("length", "") or wiki_stats.get("length", ""),
            "height": ninja_chars.get("height", "") or wiki_stats.get("height", ""),
            "top_speed": ninja_chars.get("top_speed", "") or wiki_stats.get("top_speed", ""),
            "lifespan": ninja_chars.get("lifespan", "") or wiki_stats.get("lifespan", "")
        },
        "ecology": {
            "diet": ninja_chars.get("diet", "") or wiki_diet,
            "habitat": ninja_chars.get("habitat", "") or wiki_sections.get("habitat", ""),
            "locations": ", ".join(ninja_locations) if ninja_locations else wiki_sections.get("distribution", ""),
            "group_behavior": ninja_chars.get("group_behavior", "") or wiki_behavior,
            "conservation_status": ninja_chars.get("conservation_status", "") or wiki_conservation_status,
            "biggest_threat": ninja_chars.get("biggest_threat", "") or wiki_threats,
            "distinctive_features": [ninja_chars.get("most_distinctive_feature")] if ninja_chars.get("most_distinctive_feature") else [],
            "population_trend": ""
        },
        "reproduction": {
            "gestation_period": ninja_chars.get("gestation_period", "") or wiki_repro.get("gestation_period", ""),
            "average_litter_size": ninja_chars.get("average_litter_size", "") or wiki_repro.get("average_litter_size", ""),
            "name_of_young": ninja_chars.get("name_of_young", "") or wiki_repro.get("name_of_young", "") or young_name
        },
        "additional_info": {
            "lifestyle": ninja_chars.get("lifestyle", ""),
            "color": ninja_chars.get("color", ""),
            "skin_type": ninja_chars.get("skin_type", ""),
            "prey": ninja_chars.get("prey", "") or wiki_prey,
            "slogan": ninja_chars.get("slogan", ""),
            "group": ninja_chars.get("group", "") or wiki_additional.get("group", ""),
            "number_of_species": ninja_chars.get("number_of_species", "") or wiki_additional.get("number_of_species", ""),
            "estimated_population_size": ninja_chars.get("estimated_population_size", "") or wiki_additional.get("estimated_population_size", ""),
            "age_of_sexual_maturity": ninja_chars.get("age_of_sexual_maturity", "") or wiki_additional.get("age_of_sexual_maturity", ""),
            "age_of_weaning": ninja_chars.get("age_of_weaning", "") or wiki_additional.get("age_of_weaning", ""),
            "most_distinctive_feature": ninja_chars.get("most_distinctive_feature", "") or wiki_additional.get("most_distinctive_feature", "")
        },
        "sources": [],
        "last_updated": datetime.now().isoformat()
    }
    
    # Add sources
    if ninja_data is not None:
        data["sources"].append("API Ninjas")
    if wiki_summary and wiki_summary.get("summary"):
        data["sources"].append("Wikipedia")
    if inat_classification:
        data["sources"].append("iNaturalist")
    
    return data

# Main generation
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
        wiki_sections = extract_wikipedia_sections(wiki_full)
        
        filled_sections = sum(1 for v in wiki_sections.values() if v and len(v) > 20)
        print(f"   📋 Extracted {filled_sections}/9 Wikipedia sections")
        
        print(" 🔬 Fetching from iNaturalist...")
        inat_classification = fetch_inaturalist(sci)
        
        data = build_animal_data(ninja_data, wiki_summary, wiki_sections, inat_classification, qid, name, sci)
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
