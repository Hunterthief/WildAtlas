# generator/modules/extractors/ecology/locations.py
"""
Locations Extraction Module

Extracts geographic locations from Wikipedia text.
Edit this file only for location-related changes.
"""

from pathlib import Path
import json

CONFIG_DIR = Path(__file__).parent.parent.parent.parent / "config"


def load_config(filename):
    """Load configuration from JSON file"""
    config_path = CONFIG_DIR / filename
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


LOCATIONS = load_config("locations.json")


def extract_locations(text, animal_type):
    """
    Extract geographic locations from text.
    
    Args:
        text: Wikipedia article text
        animal_type: Detected animal type for filtering
        
    Returns:
        str: Comma-separated locations or None
    """
    if not text:
        return None

    animal_locations = LOCATIONS.get("animal_specific", {}).get(animal_type, [])

    for region, locs in LOCATIONS.get("regions", {}).items():
        animal_locations.extend(locs)

    locs = []
    text_lower = text.lower()
    for loc in animal_locations:
        if loc.lower() in text_lower:
            locs.append(loc)

    # Filter out incorrect locations based on animal type
    seen = set()
    unique_locs = []
    for loc in locs:
        loc_lower = loc.lower()
        
        # Animal-specific filters
        if animal_type == 'elephant' and any(w in loc_lower for w in ['asia', 'china', 'indonesia']):
            continue
        if animal_type == 'raptor' and 'asia' in loc_lower and 'bald' in text_lower:
            continue
        if animal_type == 'penguin' and any(w in loc_lower for w in ['asia', 'africa', 'north america']):
            continue
        
        if loc_lower not in seen:
            seen.add(loc_lower)
            unique_locs.append(loc)

    return ", ".join(unique_locs[:5]) if unique_locs else None
