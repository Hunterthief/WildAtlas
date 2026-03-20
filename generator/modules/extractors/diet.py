"""Diet and prey extraction module"""
import re


def extract_diet_from_sections(sections, animal_name="", classification=None):
    """Extract diet type and prey from sections"""
    diet = ""
    prey = ""
    
    all_text = ""
    for section_text in sections.values():
        all_text += section_text + " "
    
    if not all_text:
        return diet, prey
    
    animal_lower = animal_name.lower() if animal_name else ""
    
    # FIXED: Check taxonomy first for known herbivores
    if classification:
        family = classification.get('family', '').lower()
        order = classification.get('order', '').lower()
        
        # Green sea turtles are herbivores as adults
        if 'cheloniidae' in family and 'turtle' in animal_lower:
            if 'adult' in all_text.lower() and ('seagrass' in all_text.lower() or 'algae' in all_text.lower()):
                diet = "Herbivore"
                return diet, prey
        
        # Butterflies are herbivores
        if 'butterfly' in animal_lower or 'moth' in animal_lower:
            diet = "Herbivore"
            return diet, prey
        
        # Bees are herbivores
        if 'bee' in animal_lower:
            diet = "Herbivore"
            return diet, prey
    
    # Original text-based extraction
    if any(w in all_text.lower() for w in ['carnivore', 'carnivorous', 'meat-eater', 'predator', 'predatory']):
        diet = "Carnivore"
    elif any(w in all_text.lower() for w in ['herbivore', 'herbivorous', 'plant-eater', 'grazes', 'browses', 'seagrass', 'algae']):
        diet = "Herbivore"
    elif any(w in all_text.lower() for w in ['omnivore', 'omnivorous', 'both plants and animals']):
        diet = "Omnivore"
    
    # Prey extraction
    if diet == "Herbivore":
        food_patterns = [
            r'(?:feeds?|eats?|consumes?|grazes?)\s+(?:mainly|primarily)?\s+(?:on)?\s+([^.]{10,150}(?:seagrass|algae|plants?|leaves?|flowers?|nectar|pollen))',
            r'(?:diet|food)\s+(?:consists|composed)\s+(?:mainly)?\s+(?:of)?\s+([^.]{10,150}(?:seagrass|algae|plants?|leaves?|flowers?))',
        ]
        for pattern in food_patterns:
            m = re.search(pattern, all_text, re.I)
            if m:
                prey_text = m.group(1).strip()
                prey = prey_text[:150]
                break
    else:
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
