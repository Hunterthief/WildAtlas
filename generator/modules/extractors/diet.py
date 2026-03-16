# generator/extractors/diet.py
"""Diet and prey extraction module"""
import re


def extract_diet_from_sections(sections):
    """Extract diet type and prey from sections"""
    diet = ""
    prey = ""
    
    all_text = ""
    for section_text in sections.values():
        all_text += section_text + " "
    
    if not all_text:
        return diet, prey
    
    # Diet type
    if any(w in all_text.lower() for w in ['carnivore', 'carnivorous', 'meat-eater', 'predator', 'predatory']):
        diet = "Carnivore"
    elif any(w in all_text.lower() for w in ['herbivore', 'herbivorous', 'plant-eater', 'grazes', 'browses']):
        diet = "Herbivore"
    elif any(w in all_text.lower() for w in ['omnivore', 'omnivorous', 'both plants and animals']):
        diet = "Omnivore"
    
    # Prey items (avoid threat-related text)
    prey_patterns = [
        r'preys mainly on ([^.]{10,100})',
        r'feeds mainly on ([^.]{10,100})',
        r'hunts ([^.]{10,100})',
        r'diet consists (?:mainly)?of ([^.]{10,100})',
        r'(?:deer|wild boar|buffalo|sambar|gaur|ungulate|barasingha|wapiti|monkey|peafowl|porcupine|fish)',
    ]
    for pattern in prey_patterns:
        m = re.search(pattern, all_text, re.I)
        if m:
            prey_text = m.group(0).strip()
            if 'threat' not in prey_text.lower() and 'poach' not in prey_text.lower():
                prey = prey_text[:100]
                break
    
    return diet, prey
