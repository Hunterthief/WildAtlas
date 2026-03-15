# generator/modules/extractors/ecology/diet.py
"""
Diet Extraction Module

Extracts diet type from Wikipedia text.
Edit this file only for diet-related changes.
"""


def get_default_diet(animal_type):
    """Get default diet from config"""
    from pathlib import Path
    import json
    
    config_dir = Path(__file__).parent.parent.parent.parent / "config"
    diets_path = config_dir / "diets.json"
    
    if diets_path.exists():
        with open(diets_path, "r", encoding="utf-8") as f:
            diets = json.load(f)
            return diets.get(animal_type, diets.get("default", "Unknown"))
    return "Unknown"


def extract_diet(text, animal_type):
    """
    Extract diet type from text.
    
    Args:
        text: Wikipedia article text
        animal_type: Detected animal type for fallback
        
    Returns:
        str: Diet type (Carnivore, Herbivore, Omnivore, etc.)
    """
    if not text:
        return get_default_diet(animal_type)

    t = text.lower()

    # Check in order of specificity
    if any(w in t for w in ['carnivore', 'carnivorous', 'meat-eater', 'predator', 'preys on', 'hunts', 'feeds on animals']):
        return "Carnivore"
    elif any(w in t for w in ['herbivore', 'herbivorous', 'plant-eater', 'grazes', 'browses', 'foliage', 'vegetation', 'feeds on plants']):
        return "Herbivore"
    elif any(w in t for w in ['omnivore', 'omnivorous', 'both plants and animals', 'varied diet', 'eats both']):
        return "Omnivore"
    elif any(w in t for w in ['insectivore', 'insectivorous', 'eats insects', 'insects']):
        return "Insectivore"
    elif any(w in t for w in ['piscivore', 'piscivorous', 'eats fish', 'fish']):
        return "Piscivore"

    return get_default_diet(animal_type)
