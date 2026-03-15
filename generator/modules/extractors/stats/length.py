# generator/modules/extractors/stats/length.py
"""
Length Extraction Module

Extracts length from Wikipedia text with animal-type validation.
Edit this file only for length-related changes.
"""

import re

# Valid length ranges per animal type (min_m, max_m)
LENGTH_RANGES = {
    'feline': (0.5, 4),
    'canine': (0.3, 2.5),
    'bear': (1, 3.5),
    'elephant': (4, 10),
    'whale': (2, 35),
    'deer': (0.8, 3),
    'bovine': (1.5, 4),
    'equine': (1.5, 3),
    'rabbit': (0.15, 0.8),
    'rodent': (0.05, 1.5),
    'primate': (0.3, 2),
    'bat': (0.03, 0.5),
    'bird': (0.05, 2),
    'raptor': (0.3, 1.5),
    'owl': (0.15, 0.8),
    'penguin': (0.3, 1.3),
    'chicken': (0.3, 0.8),
    'duck': (0.3, 0.8),
    'goose': (0.5, 1.2),
    'swan': (1, 1.8),
    'fish': (0.02, 12),
    'shark': (1, 12),
    'ray': (0.3, 9),
    'salmon': (0.3, 1.5),
    'frog': (0.02, 0.35),
    'salamander': (0.05, 1.8),
    'snake': (0.2, 10),
    'lizard': (0.05, 4),
    'turtle': (0.1, 2.5),
    'crocodile': (1, 7),
    'butterfly': (0.02, 0.3),
    'bee': (0.005, 0.05),
    'ant': (0.001, 0.05),
    'spider': (0.001, 0.3),
    'crab': (0.01, 4),
    'insect': (0.001, 0.5),
    'reptile': (0.1, 10),
    'amphibian': (0.02, 2),
    'mammal': (0.05, 35),
    'default': (0.01, 50),
}

LENGTH_PATTERNS = [
    r'(?:head[- ]?body|body|total)?\s*(?:length|long)\s*(?:of|is|ranges from|between)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|mm|ft|feet|in|inches?)',
    r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet)\s*(?:long|length|in length)?',
    r'(?:grows|reaches|measures)\s*(?:up to|to|about)?\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet)',
    r'wingspan\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet)',
]

UNIT_TO_M = {
    'm': 1, 'metre': 1, 'metres': 1, 'meter': 1, 'meters': 1,
    'cm': 0.01, 'centimetre': 0.01, 'centimetres': 0.01, 'centimeter': 0.01, 'centimeters': 0.01,
    'mm': 0.001,
    'ft': 0.3048, 'foot': 0.3048, 'feet': 0.3048,
    'in': 0.0254, 'inch': 0.0254, 'inches': 0.0254,
}


def extract_length(text, animal_type):
    """
    Extract length from text with animal-type validation.
    
    Args:
        text: Wikipedia article text
        animal_type: Detected animal type for validation
        
    Returns:
        str: Length string (e.g., "2.5–3.5 m") or None
    """
    if not text:
        return None

    min_m, max_m = LENGTH_RANGES.get(animal_type, LENGTH_RANGES['default'])

    for pattern in LENGTH_PATTERNS:
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

                # Validate against animal type range (with 50% tolerance)
                tolerance = 0.5
                if (min_m * (1 - tolerance) <= v1_m <= max_m * (1 + tolerance) or
                    min_m * (1 - tolerance) <= v2_m <= max_m * (1 + tolerance)):
                    
                    # Ensure v1 <= v2
                    if v1 > v2:
                        v1, v2 = v2, v1
                    
                    # Return in original unit
                    if unit in ['cm', 'centimetre', 'centimetres', 'centimeter', 'centimeters']:
                        return f"{v1}–{v2} cm" if v1 != v2 else f"{v1} cm"
                    elif unit in ['ft', 'foot', 'feet']:
                        return f"{v1}–{v2} ft" if v1 != v2 else f"{v1} ft"
                    else:
                        return f"{v1}–{v2} m" if v1 != v2 else f"{v1} m"
            except Exception as e:
                print(f" ⚠ Length parse error: {e}")
                continue

    return None
