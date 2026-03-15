# generator/modules/extractors/ecology/diet.py
"""
Diet Extraction Module

Extracts diet type from Wikipedia text.
Edit this file only for diet-related changes.

WIKIPEDIA PATTERNS FOUND:
- "diet consists primarily of other snakes" (King Cobra)
- "strictly herbivorous" (Green Sea Turtle)
- "juveniles are carnivorous, but as they mature they become omnivorous" (Green Sea Turtle)
- "opportunistic carnivore" (Bald Eagle)
- "feeds mainly on fish" (many animals)
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
    
    IMPORTANT: Check specific diet terms FIRST, then general terms.
    Order matters to avoid false positives.
    
    Args:
        text: Wikipedia article text
        animal_type: Detected animal type for fallback
        
    Returns:
        str: Diet type (Carnivore, Herbivore, Omnivore, etc.)
    """
    if not text:
        return get_default_diet(animal_type)

    t = text.lower()

    # ========== CHECK SPECIFIC DIET TERMS FIRST ==========
    
    # Herbivore - check before carnivore to avoid false positives
    if any(w in t for w in ['herbivore', 'herbivorous', 'plant-eater', 'plant eater']):
        return "Herbivore"
    
    # Strictly/primarily herbivore indicators
    if any(w in t for w in ['strictly herbivorous', 'exclusively herbivorous', 
                            'feeds on plants', 'feeds on vegetation', 'feeds on seagrass',
                            'grazes on', 'browses on', 'foliage', 'seagrass', 'sea grasses']):
        return "Herbivore"
    
    # Omnivore - check before carnivore
    if any(w in t for w in ['omnivore', 'omnivorous', 'both plants and animals', 
                            'varied diet', 'eats both', 'generalist carnivore']):
        return "Omnivore"
    
    # Insectivore
    if any(w in t for w in ['insectivore', 'insectivorous', 'eats insects', 'feeds on insects']):
        return "Insectivore"
    
    # Piscivore (fish-eater) - specific term
    if any(w in t for w in ['piscivore', 'piscivorous', 'feeds mainly on fish', 
                            'diet consists mainly of fish', 'fish comprise']):
        return "Piscivore"
    
    # ========== THEN CHECK CARNIVORE ==========
    
    # Carnivore - specific terms first
    if any(w in t for w in ['carnivore', 'carnivorous', 'meat-eater', 'meat eater']):
        return "Carnivore"
    
    # Apex predator doesn't always mean carnivore (some are omnivores)
    # Only use if no herbivore/omnivore indicators found
    if any(w in t for w in ['apex predator', 'predatory', 'preys on', 'hunts']):
        # But check if it's specifically about hunting animals
        if any(w in t for w in ['preys on mammals', 'preys on fish', 'preys on birds',
                                'hunts mammals', 'hunts fish', 'hunts birds',
                                'feeds on animals', 'feeds on mammals']):
            return "Carnivore"
    
    # ========== FALLBACK TO ANIMAL TYPE DEFAULT ==========
    return get_default_diet(animal_type)
