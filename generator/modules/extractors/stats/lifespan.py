# generator/modules/extractors/stats/lifespan.py
"""
Lifespan Extraction Module

Extracts lifespan from Wikipedia text with validation.
Edit this file only for lifespan-related changes.
"""

import re

# Valid lifespan ranges per animal type (min_years, max_years)
LIFESPAN_RANGES = {
    'feline': (5, 30),
    'canine': (5, 20),
    'bear': (15, 50),
    'elephant': (40, 80),
    'whale': (20, 200),
    'deer': (5, 25),
    'bovine': (10, 30),
    'equine': (20, 40),
    'rabbit': (3, 15),
    'rodent': (1, 15),
    'primate': (10, 60),
    'bat': (5, 40),
    'bird': (2, 80),
    'raptor': (10, 40),
    'owl': (5, 30),
    'penguin': (10, 30),
    'chicken': (3, 15),
    'duck': (3, 15),
    'goose': (10, 30),
    'swan': (15, 40),
    'fish': (1, 100),
    'shark': (10, 400),
    'ray': (5, 50),
    'salmon': (2, 10),
    'frog': (2, 30),
    'salamander': (5, 30),
    'snake': (5, 40),
    'lizard': (3, 30),
    'turtle': (20, 200),
    'crocodile': (30, 100),
    'butterfly': (0.02, 1),
    'bee': (0.01, 5),
    'ant': (0.01, 30),
    'spider': (0.5, 30),
    'crab': (1, 20),
    'insect': (0.01, 20),
    'reptile': (3, 200),
    'amphibian': (2, 50),
    'mammal': (1, 200),
    'default': (0.1, 200),
}

LIFESPAN_PATTERNS = [
    r'(?:lifespan|life expectancy|live|lives|live up to)\s*(?:of|is|up to|about|around)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs?|months?|weeks?|days?)',
    r'(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs?|months?|weeks?|days?)\s*(?:lifespan|life|in wild|in captivity|old|age)',
    r'(?:up to|about|around|approximately)\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs?)\s*(?:old|age|lifespan)',
]


def extract_lifespan(text, animal_type):
    """
    Extract lifespan from text with animal-type validation.
    
    Args:
        text: Wikipedia article text
        animal_type: Detected animal type for validation
        
    Returns:
        str: Lifespan string (e.g., "10–20 years") or None
    """
    if not text:
        return None

    min_y, max_y = LIFESPAN_RANGES.get(animal_type, LIFESPAN_RANGES['default'])

    for pattern in LIFESPAN_PATTERNS:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                v = m.group(1).replace(' ', '')
                unit = m.group(2).lower()

                # Convert to years for validation
                if 'year' in unit:
                    multiplier = 1
                elif 'month' in unit:
                    multiplier = 1/12
                elif 'week' in unit:
                    multiplier = 1/52
                elif 'day' in unit:
                    multiplier = 1/365
                else:
                    continue

                if '-' in v or '–' in v:
                    p = re.split(r'[-–]', v)
                    if len(p) >= 2:
                        try:
                            v1 = int(p[0]) * multiplier
                            v2 = int(p[1]) * multiplier
                            if min_y * 0.5 <= v1 <= max_y * 2 and min_y * 0.5 <= v2 <= max_y * 2:
                                if unit in ['year', 'years', 'yr', 'yrs']:
                                    return f"{p[0]}–{p[1]} years"
                                elif 'month' in unit:
                                    return f"{p[0]}–{p[1]} months"
                                elif 'week' in unit:
                                    return f"{p[0]}–{p[1]} weeks"
                                elif 'day' in unit:
                                    return f"{p[0]}–{p[1]} days"
                        except:
                            pass
                else:
                    try:
                        v_years = int(v) * multiplier
                        if min_y * 0.5 <= v_years <= max_y * 2:
                            if unit in ['year', 'years', 'yr', 'yrs']:
                                return f"{v} years"
                            elif 'month' in unit:
                                return f"{v} months"
                            elif 'week' in unit:
                                return f"{v} weeks"
                            elif 'day' in unit:
                                return f"{v} days"
                    except:
                        pass
            except Exception as e:
                print(f" ⚠ Lifespan parse error: {e}")
                continue

    return None
