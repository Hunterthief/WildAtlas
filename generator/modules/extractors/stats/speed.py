# generator/modules/extractors/stats/speed.py
"""
Speed Extraction Module

Extracts top speed from Wikipedia text with validation.
Edit this file only for speed-related changes.
"""

import re

# Valid speed ranges per animal type (min_kmh, max_kmh)
SPEED_RANGES = {
    'feline': (10, 120),
    'canine': (10, 80),
    'bear': (10, 65),
    'elephant': (10, 50),
    'whale': (5, 60),
    'deer': (10, 100),
    'bovine': (10, 65),
    'equine': (10, 90),
    'rabbit': (10, 80),
    'rodent': (1, 20),
    'primate': (5, 60),
    'bat': (5, 60),
    'bird': (10, 390),
    'raptor': (50, 390),
    'owl': (30, 130),
    'penguin': (5, 40),
    'chicken': (5, 15),
    'duck': (10, 120),
    'goose': (10, 100),
    'swan': (10, 90),
    'fish': (1, 110),
    'shark': (5, 80),
    'ray': (5, 40),
    'salmon': (5, 50),
    'frog': (1, 20),
    'salamander': (0.1, 5),
    'snake': (1, 25),
    'lizard': (1, 35),
    'turtle': (0.5, 35),
    'crocodile': (5, 50),
    'butterfly': (1, 50),
    'bee': (5, 30),
    'ant': (0.01, 1),
    'spider': (0.1, 2),
    'crab': (0.5, 10),
    'insect': (0.1, 60),
    'reptile': (1, 50),
    'amphibian': (0.1, 20),
    'mammal': (1, 120),
    'default': (0.1, 400),
}

SPEED_PATTERNS = [
    r'(?:speed|sprint|run|swim|fly|can|capable of)\s*(?:of|up to|about|around)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−)?\s*(\d+(?:[.,]\d+)?)?\s*(km/h|kmph|mph|mi/h|m/s|kilometers? per hour|miles? per hour)',
    r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−)?\s*(\d+(?:[.,]\d+)?)?\s*(km/h|kmph|mph|mi/h|m/s)\s*(?:speed|top speed|maximum)?',
    r'(?:up to|about|around|approximately|can)\s*(\d+(?:[.,]\d+)?)\s*(km/h|kmph|mph|mi/h|m/s)',
]

UNIT_TO_KMH = {
    'km/h': 1, 'kmph': 1, 'kilometers per hour': 1, 'kilometer per hour': 1,
    'mph': 1.60934, 'mi/h': 1.60934, 'miles per hour': 1.60934, 'mile per hour': 1.60934,
    'm/s': 3.6,
}


def extract_speed(text, animal_type):
    """
    Extract top speed from text with animal-type validation.
    
    Args:
        text: Wikipedia article text
        animal_type: Detected animal type for validation
        
    Returns:
        str: Speed string (e.g., "65 km/h") or None
    """
    if not text:
        return None

    # Only check for speed if relevant keywords exist
    text_lower = text.lower()
    if not any(w in text_lower for w in ['speed', 'sprint', 'run', 'fly', 'swim', 'fast', 'km/h', 'mph', 'kilometers per hour']):
        return None

    min_kmh, max_kmh = SPEED_RANGES.get(animal_type, SPEED_RANGES['default'])

    for pattern in SPEED_PATTERNS:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                v = float(m.group(1).replace(',', '.'))
                unit = m.group(3).lower().strip()
                
                multiplier = UNIT_TO_KMH.get(unit, 1)
                v_kmh = v * multiplier

                # Validate against animal type range
                if min_kmh * 0.5 <= v_kmh <= max_kmh * 1.5:
                    return f"{v} {unit}"
            except Exception as e:
                print(f" ⚠ Speed parse error: {e}")
                continue

    return None
