# generator/modules/detectors.py
"""
Animal Detection Module

Handles animal type detection and related metadata.
Edit this file only for detection-related changes.
"""

from pathlib import Path
import json

CONFIG_DIR = Path(__file__).parent.parent / "config"


def load_config(filename):
    """Load configuration from JSON file"""
    config_path = CONFIG_DIR / filename
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# Load all configs
ANIMAL_TYPES = load_config("animal_types.json")
YOUNG_NAMES = load_config("young_names.json")
GROUP_NAMES = load_config("group_names.json")
DIETS = load_config("diets.json")


def detect_animal_type(name, classification=None):
    """
    Detect animal type from name and classification.
    
    IMPORTANT: Check longer/more specific keywords first to avoid
    false matches (e.g., "ant" in "elephant", "ray" in "gray")
    
    Args:
        name: Animal common name
        classification: Optional taxonomic classification dict
        
    Returns:
        str: Animal type identifier
    """
    name_lower = name.lower()

    # Check name keywords - ORDER MATTERS! Check longer/more specific first
    priority_types = [
        # Mammals - specific first
        'elephant', 'feline', 'canine', 'bear', 'primate', 'whale',
        'deer', 'bovine', 'equine', 'rabbit', 'rodent', 'bat',
        # Birds - specific first
        'penguin', 'raptor', 'owl', 'chicken', 'swan', 'goose', 'duck',
        # Fish
        'shark', 'ray', 'salmon',
        # Reptiles
        'crocodile', 'turtle', 'snake', 'lizard',
        # Amphibians
        'frog', 'salamander',
        # Insects/Arthropods - specific first
        'butterfly', 'bee', 'ant', 'spider', 'crab',
    ]

    for animal_type in priority_types:
        config = ANIMAL_TYPES.get(animal_type, {})
        keywords = config.get("keywords", [])
        for keyword in keywords:
            # Use word boundary matching to avoid partial matches
            # e.g., "ant" won't match in "elephant"
            import re
            if re.search(r'\b' + re.escape(keyword) + r'\b', name_lower):
                return animal_type

    # Check classification if available
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
                return "feline"
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
            if "goose" in name_lower:
                return "goose"
            if "swan" in name_lower:
                return "swan"
            if any(w in name_lower for w in ["chicken", "rooster", "hen"]):
                return "chicken"
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
            if any(w in name_lower for w in ["snake", "serpent", "cobra", "python", "viper"]):
                return "snake"
            if any(w in name_lower for w in ["lizard", "gecko", "iguana"]):
                return "lizard"
            if any(w in name_lower for w in ["turtle", "tortoise", "terrapin"]):
                return "turtle"
            if any(w in name_lower for w in ["crocodile", "alligator", "caiman"]):
                return "crocodile"
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
    """Get the name for young/baby of this animal type"""
    return YOUNG_NAMES.get(animal_type, YOUNG_NAMES.get("default", "young"))


def get_group_name(animal_type):
    """Get the collective group name for this animal type"""
    return GROUP_NAMES.get(animal_type, GROUP_NAMES.get("default", "population"))


def get_default_diet(animal_type):
    """Get the default diet for this animal type"""
    return DIETS.get(animal_type, DIETS.get("default", "Unknown"))
