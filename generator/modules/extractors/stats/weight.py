# generator/modules/extractors/stats/weight.py
"""
Weight Extraction Module

Extracts weight from Wikipedia text with animal-type validation.
Edit this file only for weight-related changes.

WIKIPEDIA PATTERNS FOUND:
- "weigh 1,000–1,900 kg" (Great White Shark)
- "average weight of mature individuals is 68–190 kg" (Green Sea Turtle)
- "weighed up to 10 kg" (King Cobra)
- "weighing from 22 to 45 kg" (Emperor Penguin)
- "mass is normally between 3 and 6.3 kg" (Bald Eagle)
- "females... averaging as much as 5.6 kg" (Bald Eagle)
"""

import re

# Valid weight ranges per animal type (min_kg, max_kg)
WEIGHT_RANGES = {
    'feline': (2, 400),
    'canine': (1, 100),
    'bear': (25, 800),
    'elephant': (2000, 12000),
    'whale': (500, 200000),
    'deer': (10, 800),
    'bovine': (200, 1400),
    'equine': (150, 1200),
    'rabbit': (0.5, 8),
    'rodent': (0.01, 80),
    'primate': (0.1, 200),
    'bat': (0.002, 1.5),
    'bird': (0.002, 20),
    'raptor': (0.1, 15),
    'owl': (0.05, 4),
    'penguin': (1, 45),
    'chicken': (0.5, 5),
    'duck': (0.5, 5),
    'goose': (2, 12),
    'swan': (5, 15),
    'fish': (0.001, 2000),
    'shark': (1, 20000),
    'ray': (1, 3000),
    'salmon': (0.5, 60),
    'frog': (0.001, 3),
    'salamander': (0.001, 2),
    'snake': (0.01, 250),
    'lizard': (0.001, 10),
    'turtle': (1, 900),
    'crocodile': (10, 1000),
    'butterfly': (0.0001, 0.003),
    'bee': (0.00005, 0.0003),
    'ant': (0.000001, 0.0001),
    'spider': (0.00001, 0.0002),
    'crab': (0.01, 20),
    'insect': (0.00001, 0.1),
    'reptile': (0.01, 500),
    'amphibian': (0.001, 5),
    'mammal': (0.001, 20000),
    'default': (0.001, 20000),
}

WEIGHT_PATTERNS = [
    # "average weight of mature individuals is 68–190 kg"
    r'(?:average\s*)?(?:weight|mass)\s*(?:of\s*)?(?:mature\s*)?(?:individuals?|adults?)?\s*(?:is|of|ranges?|between)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|t|lbs?|pounds?|g|grams?)',
    # "weigh 1,000–1,900 kg"
    r'(?:males?|females?|adults?|individuals?|they|it)\s*(?:weigh|weighs)\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|t|lbs?|pounds?)',
    # "weighs up to 10 kg"
    r'weighs?\s*(?:up\s*to|about|around|approximately)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)?\s*(\d+(?:[.,]\d+)?)?\s*(kg|kilograms?|tonnes?|t|lbs?|pounds?)',
    # "weighing from 22 to 45 kg"
    r'weighing\s*(?:from)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|t|lbs?|pounds?)',
    # "mass is normally between 3 and 6.3 kg"
    r'mass\s*(?:is)?\s*(?:normally|typically|usually)?\s*(?:between)?\s*(\d+(?:[.,]\d+)?)\s*(?:and|to|–|-)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|t|lbs?|pounds?)',
    # "averaging as much as 5.6 kg"
    r'averaging\s*(?:as\s*much\s*as)?\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|t|lbs?|pounds?)',
    # "weighed 2,530 kg"
    r'weighed\s*(?:up\s*to)?\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|t|lbs?|pounds?)',
]

UNIT_TO_KG = {
    'kg': 1, 'kilogram': 1, 'kilograms': 1,
    't': 1000, 'tonne': 1000, 'tonnes': 1000, 'ton': 1000,
    'lb': 0.453592, 'lbs': 0.453592, 'pound': 0.453592, 'pounds': 0.453592,
    'g': 0.001, 'gram': 0.001, 'grams': 0.001,
}


def extract_weight(text, animal_type):
    """
    Extract weight from text with animal-type validation.
    
    Args:
        text: Wikipedia article text
        animal_type: Detected animal type for validation
        
    Returns:
        str: Weight string (e.g., "100–200 kg") or None
    """
    if not text:
        return None

    min_kg, max_kg = WEIGHT_RANGES.get(animal_type, WEIGHT_RANGES['default'])

    for pattern in WEIGHT_PATTERNS:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                groups = m.groups()
                v1 = float(groups[0].replace(',', '.'))
                
                # Determine v2 (range end or same as v1)
                if len(groups) >= 3 and groups[1]:
                    try:
                        v2 = float(groups[1].replace(',', '.'))
                    except:
                        v2 = v1
                else:
                    v2 = v1
                
                # Get unit and convert to kg
                unit = groups[-1].lower().strip()
                multiplier = UNIT_TO_KG.get(unit, 1)
                v1_kg = v1 * multiplier
                v2_kg = v2 * multiplier

                # Validate against animal type range (with tolerance)
                tolerance = 0.5
                if (min_kg * (1 - tolerance) <= v1_kg <= max_kg * (1 + tolerance) or
                    min_kg * (1 - tolerance) <= v2_kg <= max_kg * (1 + tolerance)):
                    
                    # Ensure v1 <= v2
                    if v1 > v2:
                        v1, v2 = v2, v1
                    
                    # Return in original unit
                    if unit in ['t', 'tonne', 'tonnes', 'ton']:
                        return f"{v1}–{v2} t" if v1 != v2 else f"{v1} t"
                    elif unit in ['lb', 'lbs', 'pound', 'pounds']:
                        return f"{v1}–{v2} lbs" if v1 != v2 else f"{v1} lbs"
                    elif unit in ['g', 'gram', 'grams']:
                        return f"{v1}–{v2} g" if v1 != v2 else f"{v1} g"
                    else:
                        return f"{v1}–{v2} kg" if v1 != v2 else f"{v1} kg"
            except Exception as e:
                print(f" ⚠ Weight parse error: {e}")
                continue

    return None
