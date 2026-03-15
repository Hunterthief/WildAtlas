# generator/modules/extractors/ecology/features.py
"""
Features Extraction Module

Extracts distinctive features from Wikipedia text.
Edit this file only for features-related changes.
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


FEATURES = load_config("features.json")

COMMON_FEATURES = {
    "striped": "Striped coat", "stripe": "Striped coat",
    "spotted": "Spotted coat", "spot": "Spotted coat",
    "mane": "Distinctive mane", "trunk": "Long trunk",
    "tusk": "Large tusks", "horn": "Prominent horns",
    "antler": "Large antlers", "wing": "Distinctive wings",
    "tail": "Long tail", "fin": "Distinctive fins",
    "shell": "Protective shell", "venom": "Venomous",
    "claw": "Sharp claws", "fang": "Large fangs",
    "beak": "Distinctive beak", "feather": "Distinctive plumage",
    "scale": "Scaled skin", "fur": "Thick fur"
}

# Features to block for certain animal types
FEATURE_BLOCKS = {
    'fin': ['fish', 'shark', 'ray'],
    'wing': ['bird', 'raptor', 'penguin', 'butterfly', 'bee', 'bat'],
    'shell': ['turtle'],
    'trunk': ['elephant'],
    'tusk': ['elephant', 'bovine', 'deer'],
    'stripe': ['feline'],
}


def extract_features(text, animal_type):
    """
    Extract distinctive features from text.
    
    Args:
        text: Wikipedia article text
        animal_type: Detected animal type
        
    Returns:
        list: List of feature strings or None
    """
    if not text:
        return None

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

    for keyword, feature in COMMON_FEATURES.items():
        if keyword in text_lower and feature not in features:
            blocked = False
            
            # Check negative list
            for neg in negative:
                if neg in keyword or keyword in neg:
                    blocked = True
                    break

            # Check animal type blocks
            if keyword in FEATURE_BLOCKS:
                if animal_type not in FEATURE_BLOCKS[keyword]:
                    blocked = True

            # Special case: tail for frogs
            if 'tail' in keyword and animal_type == 'frog':
                blocked = True

            if not blocked:
                features.append(feature)

    return features[:3] if features else None
