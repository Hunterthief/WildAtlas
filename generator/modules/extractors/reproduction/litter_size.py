# generator/modules/extractors/reproduction/litter_size.py
"""
Litter Size Extraction Module

Extracts litter/clutch size from Wikipedia text.
Edit this file only for litter size-related changes.
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
    'butterfly': (50, 500),
    'bee': (1, 5),
    'ant': (1, 100),
    'spider': (10, 1000),
    'crab': (10, 200),
    'insect': (1, 500),
    'reptile': (1, 100),
    'amphibian': (10, 5000),
    'mammal': (1, 20),
    'default': (1, 100),
}

LITTER_PATTERNS = [
    r'(?:litter|clutch|brood|cubs?|young|offspring|chicks?|pups?)?\s*(?:size|consists?|of|contains|are|is)?\s*(?:of|up to|typically|average|more)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(?:eggs?|young|offspring|cubs?|chicks?|pups?)?',
    r'(?:as many as|up to|about|around|typically|usually)\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(?:eggs?|young|offspring|cubs?|chicks?|pups?)?',
    r'(\d+(?:\s*[-–]\s*\d+)?)\s*(?:eggs?|young|offspring|cubs?|chicks?|pups?)?\s*(?:per\s*)?(?:litter|clutch|brood)',
    r'(?:gives birth|lays|produces)\s*(?:to|up to|about)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(?:eggs?|young|offspring|cubs?|chicks?|pups?)?',
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
                v = m.group(1).replace(' ', '')

                if '-' in v or '–' in v:
                    p = re.split(r'[-–]', v)
                    if len(p) >= 2:
                        try:
                            v1 = int(p[0])
                            v2 = int(p[1])
                            if min_l * 0.5 <= v1 <= max_l * 2 and min_l * 0.5 <= v2 <= max_l * 2:
                                return p[0] if v1 == v2 else f"{p[0]}–{p[1]}"
                        except:
                            pass
                else:
                    try:
                        v_int = int(v)
                        if min_l * 0.5 <= v_int <= max_l * 2:
                            return v
                    except:
                        pass
            except Exception as e:
                print(f" ⚠ Litter size parse error: {e}")
                continue

    return None
