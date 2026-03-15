# generator/generate_animals.py
"""
WildAtlas Animal Data Generator

Main entry point that orchestrates the data generation process.
All data collection and extraction is handled by modular components.
"""

import json
import time
import os
import sys
from datetime import datetime
from pathlib import Path

# Import modular components
from modules.fetchers import fetch_wikipedia_summary, fetch_wikipedia_full, fetch_inaturalist
from modules.detectors import detect_animal_type, get_young_name, get_group_name
from modules.extractors import (
    extract_stats, extract_diet, extract_conservation,
    extract_locations, extract_habitat, extract_features,
    extract_behavior, extract_reproduction, extract_threats
)
from modules.cache import load_cache, save_cache

# Setup
os.makedirs("data", exist_ok=True)
CONFIG_DIR = Path(__file__).parent / "config"
CLASSIFICATION_FIELDS = ["kingdom", "phylum", "class", "order", "family", "genus", "species"]


def load_config(filename):
    """Load configuration from JSON file"""
    config_path = CONFIG_DIR / filename
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def initialize_animal_data(qid, name, sci):
    """Initialize empty animal data structure"""
    return {
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


def update_from_wikipedia(data, wiki):
    """Update data structure with Wikipedia info"""
    if wiki["summary"]:
        data["summary"] = wiki["summary"]
        data["description"] = wiki["description"]
        data["image"] = wiki["image"]
        data["wikipedia_url"] = wiki["url"]
        if "Wikipedia" not in data["sources"]:
            data["sources"].append("Wikipedia")


def extract_all_data(data, text, animal_type):
    """Run all extraction functions and update data"""
    # Physical stats
    stats = extract_stats(text, animal_type)
    for k, v in stats.items():
        if v:
            data["physical"][k] = v

    # Ecology data
    data["ecology"]["diet"] = extract_diet(text, animal_type)
    data["ecology"]["conservation_status"] = extract_conservation(text)
    data["ecology"]["locations"] = extract_locations(text, animal_type)
    data["ecology"]["habitat"] = extract_habitat(text, animal_type)
    data["ecology"]["distinctive_features"] = extract_features(text, animal_type)
    data["ecology"]["group_behavior"] = extract_behavior(text, animal_type)
    data["ecology"]["biggest_threat"] = extract_threats(text)

    # Reproduction data
    repro = extract_reproduction(text, animal_type)
    for k, v in repro.items():
        if v:
            data["reproduction"][k] = v


def generate(animals, force=False):
    """
    Main generation orchestration function.
    
    Args:
        animals: List of animal dicts with name, scientific_name, qid
        force: If True, regenerate even if cached
    """
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
            print(" 📦 Using cached data")
        else:
            data = initialize_animal_data(qid, name, sci)
            
            # Fetch Wikipedia data
            print(" 📖 Wikipedia...")
            wiki = fetch_wikipedia_summary(name)
            full = fetch_wikipedia_full(name)
            all_text = wiki["summary"] + " " + full
            
            # Update data with Wikipedia info
            update_from_wikipedia(data, wiki)
            
            # Detect animal type
            animal_type = detect_animal_type(name, data["classification"])
            data["animal_type"] = animal_type
            data["young_name"] = get_young_name(animal_type)
            data["group_name"] = get_group_name(animal_type)
            print(f" ✓ Type: {animal_type}")

            # Extract all data using dedicated extractors
            extract_all_data(data, all_text, animal_type)

            # Fetch classification from iNaturalist
            if not data["classification"]["kingdom"] or force:
                print(" 🔬 iNaturalist...")
                cl = fetch_inaturalist(sci)
                if cl:
                    data["classification"] = cl
                    if "iNaturalist" not in data["sources"]:
                        data["sources"].append("iNaturalist")

                # Re-detect with classification
                animal_type = detect_animal_type(name, cl)
                data["animal_type"] = animal_type
                data["young_name"] = get_young_name(animal_type)
                data["group_name"] = get_group_name(animal_type)
                print(f" ✓ Classification complete")

            data["last_updated"] = datetime.now().isoformat()
            save_cache(qid, data)
        
        output.append(data)
        print(f" ✅ {name} complete!")
        time.sleep(1)

    # Save final output
    with open("data/animals.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Done! {len(output)} animals saved to data/animals.json")
    return output


# Test animals
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
    force = "--force" in sys.argv
    generate(TEST_ANIMALS, force)
