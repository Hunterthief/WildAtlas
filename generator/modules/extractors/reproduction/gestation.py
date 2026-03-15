# generator/modules/extractors/reproduction/gestation.py
"""
Gestation Period Extraction Module

Extracts gestation/incubation period from Wikipedia text.
Edit this file only for gestation-related changes.
"""

import re

GESTATION_PATTERNS = [
    r'(?:gestation|pregnancy|incubation)\s*(?:period|lasts?|is|of)?\s*(?:around|about|approximately|over)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(months?|weeks?|days?)',
    r'(\d+(?:\s*[-–]\s*\d+)?)\s*(months?|weeks?|days?)\s*(?:gestation|pregnancy|incubation|period)',
    r'(?:pregnant|carries young)\s*(?:for)?\s*(?:around|about)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(months?|weeks?|days?)',
    r'after\s*(?:around|about)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(months?|weeks?|days?)\s*(?:of\s*)?(?:pregnancy|gestation)',
    r'lasts?\s*(?:around|about|approximately|over|up to)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(months?|weeks?|days?)',
]

# Valid gestation ranges per animal type (min_days, max_days)
GESTATION_RANGES = {
    'feline': (50, 100),
    'canine': (50, 75),
    'bear': (180, 280),
    'elephant': (600, 680),
    'whale': (300, 540),
    'deer': (180, 250),
    'bovine': (260, 300),
    'equine': (320, 370),
    'rabbit': (25, 35),
    'rodent': (15, 40),
    'primate': (150, 270),
    'bat': (30, 120),
    'bird': (10, 90),
    'raptor': (25, 50),
    'owl': (20, 40),
    'penguin': (30, 65),
    'chicken': (18, 25),
    'duck': (20, 35),
    'goose': (25, 35),
    'swan': (30, 45),
    'fish': (1, 60),
    'shark': (200, 700),
    'ray': (90, 365),
    'salmon': (1, 100),
    'frog': (1, 30),
    'salamander': (10, 60),
    'snake': (30, 120),
    'lizard': (30, 90),
    'turtle': (40, 100),
    'crocodile': (60, 100),
    'butterfly': (1, 20),
    'bee': (10, 20),
    'ant': (10, 60),
    'spider': (10, 60),
    'crab': (10, 60),
    'insect': (1, 60),
    'reptile': (30, 120),
    'amphibian': (1, 60),
    'mammal': (15, 700),
    'default': (1, 700),
}


def extract_gestation(text, animal_type):
    """
    Extract gestation period from text.
    
    Args:
        text: Wikipedia article text
        animal_type: Detected animal type for validation
        
    Returns:
        str: Gestation string (e.g., "3–4 months") or None
    """
    if not text:
        return None

    min_d, max_d = GESTATION_RANGES.get(animal_type, GESTATION_RANGES['default'])

    for pattern in GESTATION_PATTERNS:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                v = m.group(1).replace(' ', '')
                unit = m.group(2).lower()

                # Convert to days for validation
                if 'month' in unit:
                    multiplier = 30
                elif 'week' in unit:
                    multiplier = 7
                elif 'day' in unit:
                    multiplier = 1
                else:
                    continue

                if '-' in v or '–' in v:
                    p = re.split(r'[-–]', v)
                    if len(p) >= 2:
                        try:
                            v1_d = int(p[0]) * multiplier
                            v2_d = int(p[1]) * multiplier
                            if min_d * 0.5 <= v1_d <= max_d * 2 and min_d * 0.5 <= v2_d <= max_d * 2:
                                if 'month' in unit:
                                    return f"{p[0]}–{p[1]} months"
                                elif 'week' in unit:
                                    return f"{p[0]}–{p[1]} weeks"
                                elif 'day' in unit:
                                    return f"{p[0]}–{p[1]} days"
                        except:
                            pass
                else:
                    try:
                        v_d = int(v) * multiplier
                        if min_d * 0.5 <= v_d <= max_d * 2:
                            if 'month' in unit:
                                return f"{v} months"
                            elif 'week' in unit:
                                return f"{v} weeks"
                            elif 'day' in unit:
                                return f"{v} days"
                    except:
                        pass
            except Exception as e:
                print(f" ⚠ Gestation parse error: {e}")
                continue

    return None
