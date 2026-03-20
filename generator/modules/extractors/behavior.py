"""Behavior extraction module - V2 (TAXONOMY FALLBACK FIX)
WildAtlas Project

FIXES:
- Added taxonomy-based fallbacks (elephants = herd, wolves = pack)
- Better keyword matching
- Returns specific behavior types, not just "Social"
"""

from typing import Dict


def extract_behavior_from_sections(sections: Dict[str, str]) -> str:
    """Extract group behavior from sections"""
    all_text = ""
    for section_text in sections.values():
        all_text += section_text + " "
    
    if not all_text:
        return ""
    
    t = all_text.lower()
    
    # Check for specific behaviors first
    if any(w in t for w in ['solitary', 'alone', 'lives alone', 'mostly solitary', 'lives singly', 'single']):
        return "Solitary"
    elif any(w in t for w in ['pack', 'wolf pack', 'dog pack']):
        return "Pack"
    elif any(w in t for w in ['herd', 'elephant herd', 'cattle herd']):
        return "Herd"
    elif any(w in t for w in ['colony', 'bee colony', 'ant colony', 'penguin colony']):
        return "Colony"
    elif any(w in t for w in ['flock', 'bird flock']):
        return "Flock"
    elif any(w in t for w in ['school', 'fish school']):
        return "School"
    elif any(w in t for w in ['pair', 'mate', 'pairs', 'family group']):
        return "Pairs"
    elif any(w in t for w in ['social', 'group living', 'highly social', 'live in groups']):
        return "Social"
    
    return ""


def get_behavior_fallback(classification: Dict = None, animal_name: str = "") -> str:
    """Get behavior based on taxonomy when extraction fails"""
    if not classification and not animal_name:
        return "Solitary"
    
    family = classification.get("family", "").lower() if classification else ""
    cls = classification.get("class", "").lower() if classification else ""
    order = classification.get("order", "").lower() if classification else ""
    animal_lower = animal_name.lower() if animal_name else ""
    
    # Mammals - Family specific
    if "canidae" in family or "wolf" in animal_lower or "dog" in animal_lower:
        return "Pack"
    elif "elephantidae" in family or "elephant" in animal_lower:
        return "Herd"
    elif "felidae" in family and "lion" not in animal_lower:
        return "Solitary"
    elif "felidae" in family and "lion" in animal_lower:
        return "Pride"
    elif "ursidae" in family or "bear" in animal_lower:
        return "Solitary"
    elif "giraffidae" in family or "giraffe" in animal_lower:
        return "Herd"
    elif "bovidae" in family or "deer" in animal_lower or "cattle" in animal_lower:
        return "Herd"
    
    # Birds
    elif "aves" in cls:
        if "penguin" in animal_lower:
            return "Colony"
        elif "eagle" in animal_lower or "hawk" in animal_lower or "raptor" in animal_lower:
            return "Solitary"
        else:
            return "Flock"
    
    # Fish
    elif "actinopterygii" in cls or "chondrichthyes" in cls or "fish" in animal_lower:
        if "shark" in animal_lower:
            return "Solitary"
        else:
            return "School"
    
    # Reptiles
    elif "reptilia" in cls:
        if "turtle" in animal_lower or "tortoise" in animal_lower:
            return "Solitary"
        elif "snake" in animal_lower:
            return "Solitary"
        else:
            return "Solitary"
    
    # Amphibians
    elif "amphibia" in cls or "frog" in animal_lower:
        return "Solitary"
    
    # Insects - CRITICAL: Most are social
    elif "insecta" in cls or "hymenoptera" in order or "lepidoptera" in order:
        if "bee" in animal_lower or "ant" in animal_lower or "termite" in animal_lower:
            return "Colony"
        elif "butterfly" in animal_lower or "moth" in animal_lower:
            return "Solitary"
        else:
            return "Colony"
    
    return "Solitary"
