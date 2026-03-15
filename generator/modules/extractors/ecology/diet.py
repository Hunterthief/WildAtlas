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
    
    IMPORTANT ORDER:
    1. Check for explicit diet statements FIRST
    2. Check for feeding behavior
    3. Fall back to animal type default
    
    Args:
        text: Wikipedia article text
        animal_type: Detected animal type for fallback
        
    Returns:
        str: Diet type (Carnivore, Herbivore, Omnivore, etc.)
    """
    if not text:
        return get_default_diet(animal_type)

    t = text.lower()

    # ========== EXPLICIT DIET STATEMENTS (Highest Priority) ==========
    
    # Herbivore - explicit statements
    if any(w in t for w in ['herbivore', 'herbivorous', 'plant-eater', 'plant eater']):
        return "Herbivore"
    if any(w in t for w in ['strictly herbivorous', 'exclusively herbivorous', 
                            'feeds on plants', 'feeds on vegetation', 'feeds on seagrass',
                            'grazes on', 'browses on', 'foliage', 'seagrass', 'sea grasses']):
        return "Herbivore"
    
    # Omnivore - explicit statements
    if any(w in t for w in ['omnivore', 'omnivorous', 'both plants and animals', 
                            'varied diet', 'eats both', 'generalist']):
        return "Omnivore"
    
    # Insectivore
    if any(w in t for w in ['insectivore', 'insectivorous', 'eats insects', 'feeds on insects']):
        return "Insectivore"
    
    # Piscivore (fish-eater)
    if any(w in t for w in ['piscivore', 'piscivorous', 'feeds mainly on fish', 
                            'diet consists mainly of fish', 'fish comprise']):
        return "Piscivore"
    
    # ========== CARNIVORE (Check AFTER herbivore/omnivore) ==========
    
    # Carnivore - explicit statements
    if any(w in t for w in ['carnivore', 'carnivorous', 'meat-eater', 'meat eater']):
        return "Carnivore"
    
    # Predator/prey language (but be careful - some herbivores are called prey)
    if any(w in t for w in ['predator', 'predatory', 'preys on', 'hunts']):
        # Make sure it's not talking about being prey
        if 'prey on' in t or 'preys on' in t or 'hunts' in t:
            return "Carnivore"
    
    # ========== FALLBACK TO ANIMAL TYPE DEFAULT ==========
    # This is important - feline should default to Carnivore
    return get_default_diet(animal_type)
