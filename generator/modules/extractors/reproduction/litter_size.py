# generator/modules/extractors/reproduction/litter_size.py
"""
Litter Size Extraction Module

Extracts litter/clutch size from Wikipedia text.
Edit this file only for litter size-related changes.

WIKIPEDIA PATTERNS FOUND:
- "Clutch size ranges from 7 to 43 eggs" (King Cobra)
- "Clutch size ranges between 85 and 200" (Green Sea Turtle)
- "gives live birth to two to ten pups" (Great White Shark)
- "females lay smaller eggs as they age" (Monarch Butterfly)
- "can reach 1,180" eggs (Monarch Butterfly)
"""

import re

# Valid litter size ranges per animal type (min, max)
LITTER_RANGES = {
    'feline': (1, 6),
    'canine': (1, 12),
    'bear': (1, 4),
    'elephant': (1, 1),
    'whale': (1, 1),
    'deer': (1, 3),
    'bovine': (1, 2),
    'equine': (1, 2),
    'rabbit': (1, 12),
    'rodent': (1, 20),
    'primate': (1, 3),
    'bat': (1, 2),
    'bird': (1, 12),
    'raptor': (1, 6),
    'owl': (1, 8),
    'penguin': (1, 2),
    'chicken': (1, 15),
    'duck': (1, 15),
    'goose': (1, 10),
    'swan': (1, 8),
    'fish': (10, 5000),
    'shark': (1, 300),
    'ray': (1, 50),
    'salmon': (1000, 10000),
    'frog': (100, 20000),
    'salamander': (10, 500),
    'snake': (1, 100),
    'lizard': (1, 20),
    'turtle': (50, 200),
    'crocodile': (10, 80),
    'butterfly': (50, 2000),
    'bee': (1, 5),
    'ant': (1, 100),
    'spider': (10, 1000),
    'crab': (10, 200),
    'insect': (1, 2000),
    'reptile': (1, 100),
    'amphibian': (10, 5000),
    'mammal': (1, 20),
    'default': (1, 500),
}

LITTER_PATTERNS = [
    # "Clutch size ranges from 7 to 43 eggs"
    r'(?:clutch|litter|brood)\s*(?:size)?\s*(?:ranges?\s*(?:from)?)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(?:to|and|–|-)\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(?:eggs?|young|offspring|cubs?|chicks?|pups?|eggs)?',
    # "Clutch size ranges between 85 and 200"
    r'(?:clutch|litter|brood)\s*(?:size)?\s*(?:ranges?\s*between)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(?:and|to|–|-)\s*(\d+(?:\s*[-–]\s*\d+)?)',
    # "gives live birth to two to ten pups"
    r'(?:gives?\s*(?:live\s*)?birth\s*to|bears?|produces?|lays?)\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(?:to|and|–|-)\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(?:eggs?|young|offspring|cubs?|chicks?|pups?)?',
    # "two to ten pups"
    r'(\d+(?:\s*[-–]\s*\d+)?)\s*(?:to|and|–|-)\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(?:eggs?|young|offspring|cubs?|chicks?|pups?|per\s*(?:clutch|litter|brood))',
    # "up to 1,180" eggs
    r'(?:up\s*to|as\s*many\s*as|about|around|approximately)\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(?:eggs?|young|offspring|cubs?|chicks?|pups?)?',
    # "typically 2-4 eggs"
    r'(?:typically|usually|commonly|average)\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(?:eggs?|young|offspring|cubs?|chicks?|pups?)?',
]


def extract_litter_size(text, animal_type):
    """
    Extract litter/clutch size from text.
    
    Args:
        text: Wikipedia article text
        animal_type: Detected animal type for validation
        
    Returns:
        str: Litter size string (e.g., "2–4") or None
    """
    if not text:
        return None

    min_l, max_l = LITTER_RANGES.get(animal_type, LITTER_RANGES['default'])

    for pattern in LITTER_PATTERNS:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                # Try to get both values from groups
                if m.lastindex >= 2:
                    v1_str = m.group(1).replace(' ', '')
                    v2_str = m.group(2).replace(' ', '')
                    
                    # Split if contains range
                    if '-' in v1_str or '–' in v1_str:
                        p = re.split(r'[-–]', v1_str)
                        if len(p) >= 2:
                            v1 = int(p[0])
                            v2 = int(p[1])
                        else:
                            continue
                    else:
                        v1 = int(v1_str)
                        v2 = int(v2_str)
                    
                    if min_l * 0.5 <= v1 <= max_l * 2 and min_l * 0.5 <= v2 <= max_l * 2:
                        return f"{v1}–{v2}" if v1 != v2 else str(v1)
                else:
                    v = m.group(1).replace(' ', '')
                    if '-' in v or '–' in v:
                        p = re.split(r'[-–]', v)
                        if len(p) >= 2:
                            v1 = int(p[0])
                            v2 = int(p[1])
                            if min_l * 0.5 <= v1 <= max_l * 2 and min_l * 0.5 <= v2 <= max_l * 2:
                                return f"{v1}–{v2}" if v1 != v2 else str(v1)
                    else:
                        v_int = int(v)
                        if min_l * 0.5 <= v_int <= max_l * 2:
                            return v
            except Exception as e:
                print(f" ⚠ Litter size parse error: {e}")
                continue

    return None
