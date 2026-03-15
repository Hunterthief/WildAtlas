# generator/modules/extractors/ecology/habitat.py
"""
Habitat Extraction Module

Extracts habitat types from Wikipedia text.
Edit this file only for habitat-related changes.
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


HABITATS = load_config("habitats.json")

COMMON_HABITATS = [
    'forest', 'jungle', 'savanna', 'grassland', 'desert',
    'mountain', 'ocean', 'sea', 'river', 'lake', 'wetland',
    'swamp', 'marsh', 'tundra', 'rainforest', 'woodland',
    'coastal', 'coral reef', 'mangrove', 'temperate', 'tropical'
]


def extract_habitat(text, animal_type):
    """
    Extract habitat types from text.
    
    Args:
        text: Wikipedia article text
        animal_type: Detected animal type
        
    Returns:
        str: Comma-separated habitats or None
    """
    if not text:
        return None

    habitat_keywords = HABITATS.get(animal_type, HABITATS.get("default", []))
    habitat_keywords.extend(COMMON_HABITATS)

    found = []
    text_lower = text.lower()

    for keyword in habitat_keywords:
        if keyword.lower() in text_lower:
            found.append(keyword)

    return ", ".join(list(set(found))[:4]) if found else None
