# generator/extractors/diet.py
"""Diet and prey extraction module"""
import re


def extract_diet_from_sections(sections, animal_name=""):
    """Extract diet type and prey from sections"""
    diet = ""
    prey = ""
    
    all_text = ""
    for section_text in sections.values():
        all_text += section_text + " "
    
    if not all_text:
        return diet, prey
    
    animal_lower = animal_name.lower() if animal_name else ""
    
    # Diet type - check specific animals first
    if "turtle" in animal_lower and "sea" in animal_lower:
        # Green sea turtles are herbivores as adults
        if "adult" in all_text.lower() and ("seagrass" in all_text.lower() or "algae" in all_text.lower()):
            diet = "Herbivore"
        else:
            diet = "Herbivore"  # Default for adult green sea turtles
    elif "butterfly" in animal_lower or "moth" in animal_lower:
        diet = "Herbivore"
    elif "bee" in animal_lower:
        diet = "Herbivore"
    elif any(w in all_text.lower() for w in ['carnivore', 'carnivorous', 'meat-eater', 'predator', 'predatory']):
        diet = "Carnivore"
    elif any(w in all_text.lower() for w in ['herbivore', 'herbivorous', 'plant-eater', 'grazes', 'browses', 'seagrass', 'algae']):
        diet = "Herbivore"
    elif any(w in all_text.lower() for w in ['omnivore', 'omnivorous', 'both plants and animals']):
        diet = "Omnivore"
    
    # Prey items (avoid threat-related text and herbivore food)
    if diet == "Herbivore":
        # For herbivores, extract food plants instead of prey
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
        # For carnivores/omnivores, extract prey
        prey_patterns = [
            r'preys\s+mainly\s+on\s+([^.]{10,100})',
            r'feeds\s+mainly\s+on\s+([^.]{10,100})',
            r'hunts\s+([^.]{10,100})',
            r'diet\s+consists\s+(?:mainly)?\s+(?:of)?\s+([^.]{10,100})',
            r'(?:deer|wild\s+boar|buffalo|sambar|gaur|ungulate|barasingha|wapiti|monkey|peafowl|porcupine|fish|seal|sea\s+lion|dolphin|snake|lizard|bird|rodent)',
        ]
        for pattern in prey_patterns:
            m = re.search(pattern, all_text, re.I)
            if m:
                prey_text = m.group(0).strip()
                # Avoid threat-related text and herbivore food
                if 'threat' not in prey_text.lower() and 'poach' not in prey_text.lower() and 'seagrass' not in prey_text.lower() and 'algae' not in prey_text.lower():
                    prey = prey_text[:100]
                    break
    
    return diet, prey
