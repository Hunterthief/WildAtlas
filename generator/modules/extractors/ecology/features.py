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

# Features that are ONLY valid for these animal types
# (if animal_type is NOT in this list, block the feature)
FEATURE_ALLOWED_TYPES = {
    'fin': ['fish', 'shark', 'ray', 'turtle', 'whale'],
    'wing': ['bird', 'raptor', 'owl', 'penguin', 'butterfly', 'bee', 'bat', 'insect'],
    'shell': ['turtle', 'crab'],
    'trunk': ['elephant'],
    'tusk': ['elephant', 'bovine', 'deer', 'walrus'],
    'stripe': ['feline', 'zebra', 'tiger'],
    'mane': ['feline', 'canine', 'equine', 'lion'],
    'horn': ['bovine', 'deer', 'rhino'],
    'antler': ['deer', 'bovine'],
    'venom': ['snake', 'spider', 'frog', 'insect'],
    'fang': ['feline', 'canine', 'snake', 'bat'],
    'beak': ['bird', 'raptor', 'owl', 'penguin', 'chicken', 'duck', 'turtle'],
    'feather': ['bird', 'raptor', 'owl', 'penguin', 'chicken'],
    'scale': ['fish', 'shark', 'ray', 'snake', 'lizard', 'turtle', 'crocodile'],
    'fur': ['feline', 'canine', 'bear', 'elephant', 'deer', 'bovine', 'equine', 
            'rabbit', 'rodent', 'primate', 'bat', 'whale', 'mammal'],
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

    # First add features from config
    for feature in positive:
        if feature in text_lower:
            display_feature = feature.replace('_', ' ').title()
            if display_feature not in features:
                features.append(display_feature)

    # Then add common features with proper validation
    for keyword, feature in COMMON_FEATURES.items():
        if keyword in text_lower and feature not in features:
            blocked = False
            
            # Check negative list from config
            for neg in negative:
                if neg in keyword or keyword in neg:
                    blocked = True
                    break
            
            # Check if this feature is allowed for this animal type
            if keyword in FEATURE_ALLOWED_TYPES:
                if animal_type not in FEATURE_ALLOWED_TYPES[keyword]:
                    blocked = True
            
            # Special cases
            if 'tail' in keyword and animal_type in ['frog', 'butterfly', 'bee']:
                blocked = True
            if 'mane' in keyword and animal_type not in ['feline', 'canine', 'equine', 'lion']:
                blocked = True
            if 'horn' in keyword and animal_type not in ['bovine', 'deer', 'rhino', 'elephant']:
                blocked = True
            if 'antler' in keyword and animal_type not in ['deer', 'bovine']:
                blocked = True

            if not blocked:
                features.append(feature)

    return features[:3] if features else None
