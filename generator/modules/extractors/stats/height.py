# generator/modules/extractors/stats/height.py
"""
Height Extraction Module

Extracts height from Wikipedia text with animal-type validation.
Edit this file only for height-related changes.
"""

import re

# Valid height ranges per animal type (min_m, max_m)
HEIGHT_RANGES = {
    'feline': (0.3, 1.5),
    'canine': (0.2, 1),
    'bear': (0.6, 3.5),
    'elephant': (2, 4.5),
    'whale': (2, 10),
    'deer': (0.5, 2.5),
    'bovine': (1, 2.2),
    'equine': (1, 2),
    'rabbit': (0.1, 0.3),
    'rodent': (0.05, 0.5),
    'primate': (0.3, 2),
    'bat': (0.03, 0.2),
    'bird': (0.1, 2.5),
    'raptor': (0.3, 1.2),
    'owl': (0.15, 0.8),
    'penguin': (0.3, 1.3),
    'chicken': (0.2, 0.6),
    'duck': (0.2, 0.5),
    'goose': (0.4, 1),
    'swan': (0.8, 1.5),
    'fish': (0.01, 3),
    'shark': (0.5, 6),
    'ray': (0.1, 3),
    'salmon': (0.1, 0.5),
    'frog': (0.02, 0.3),
    'salamander': (0.05, 0.5),
    'snake': (0.05, 0.5),
    'lizard': (0.02, 0.5),
    'turtle': (0.1, 1.5),
    'crocodile': (0.3, 1),
    'butterfly': (0.01, 0.3),
    'bee': (0.005, 0.03),
    'ant': (0.001, 0.02),
    'spider': (0.001, 0.2),
    'crab': (0.01, 0.5),
    'insect': (0.001, 0.2),
    'reptile': (0.05, 2),
    'amphibian': (0.02, 0.5),
    'mammal': (0.1, 5),
    'default': (0.05, 5),
}

HEIGHT_PATTERNS = [
    r'(?:stands?|stand|height|tall|at the shoulder)\s*(?:about|around|up to|of)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet)',
    r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet)\s*(?:tall|height|shoulder|at the shoulder)',
]

UNIT_TO_M = {
    'm': 1, 'metre': 1, 'metres': 1, 'meter': 1, 'meters': 1,
    'cm': 0.01, 'centimetre': 0.01, 'centimetres': 0.01, 'centimeter': 0.01, 'centimeters': 0.01,
    'ft': 0.3048, 'foot': 0.3048, 'feet': 0.3048,
}


def extract_height(text, animal_type):
    """
    Extract height from text with animal-type validation.
    
    Args:
        text: Wikipedia article text
        animal_type: Detected animal type for validation
        
    Returns:
        str: Height string (e.g., "1.5–2.5 m") or None
    """
    if not text:
        return None

    # Only check for height if relevant keywords exist
    text_lower = text.lower()
    if not any(w in text_lower for w in ['shoulder', 'stands', 'tall', 'height', 'at the shoulder']):
        return None

    min_m, max_m = HEIGHT_RANGES.get(animal_type, HEIGHT_RANGES['default'])

    for pattern in HEIGHT_PATTERNS:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                groups = m.groups()
                v1 = float(groups[0].replace(',', '.'))
                
                if len(groups) >= 3 and groups[1]:
                    try:
                        v2 = float(groups[1].replace(',', '.'))
                    except:
                        v2 = v1
                else:
                    v2 = v1
                
                unit = groups[-1].lower().strip()
                multiplier = UNIT_TO_M.get(unit, 1)
                v1_m = v1 * multiplier
                v2_m = v2 * multiplier

                # Validate against animal type range
                tolerance = 0.5
                if (min_m * (1 - tolerance) <= v1_m <= max_m * (1 + tolerance) or
                    min_m * (1 - tolerance) <= v2_m <= max_m * (1 + tolerance)):
                    
                    if v1 > v2:
                        v1, v2 = v2, v1
                    
                    if unit in ['cm', 'centimetre', 'centimetres', 'centimeter', 'centimeters']:
                        return f"{v1}–{v2} cm" if v1 != v2 else f"{v1} cm"
                    elif unit in ['ft', 'foot', 'feet']:
                        return f"{v1}–{v2} ft" if v1 != v2 else f"{v1} ft"
                    else:
                        return f"{v1}–{v2} m" if v1 != v2 else f"{v1} m"
            except Exception as e:
                print(f" ⚠ Height parse error: {e}")
                continue

    return None
