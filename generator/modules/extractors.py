# generator/modules/extractors.py
"""
Data Extractors Module

Handles all data extraction from Wikipedia text:
- Physical stats (weight, length, height, lifespan, speed)
- Diet, conservation status, locations, habitat
- Features, behavior, reproduction, threats
"""

import re
from pathlib import Path
import json
from .detectors import get_default_diet, get_young_name

CONFIG_DIR = Path(__file__).parent.parent / "config"


def load_config(filename):
    """Load configuration from JSON file"""
    config_path = CONFIG_DIR / filename
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# Load configs
LOCATIONS = load_config("locations.json")
HABITATS = load_config("habitats.json")
FEATURES = load_config("features.json")


def extract_stats(text, animal_type):
    """
    Extract physical stats from text.
    
    Args:
        text: Wikipedia article text
        animal_type: Detected animal type for validation
        
    Returns:
        dict with weight, length, height, lifespan, top_speed
    """
    stats = {"weight": None, "length": None, "height": None, "lifespan": None, "top_speed": None}
    if not text:
        print(" ⚠ No text for stats extraction")
        return stats

    text_lower = text.lower()

    # ========== WEIGHT ==========
    weight_patterns = [
        r'(?:males?|females?|adults?|individuals?|they|it)\s*(?:weigh|weighs|weight)\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|t|lbs?|pounds?|g|grams?)',
        r'weighs?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|t|lbs?|pounds?)',
        r'(?:weigh|weight|weighing|up to|over|about|around)\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|t|lbs?|pounds?)',
        r'weighs?\s*(?:around|about|approximately|up to)?\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|t|lbs?|pounds?)',
    ]

    for pattern in weight_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                groups = m.groups()
                if len(groups) >= 2:
                    v1 = float(groups[0].replace(',', '.'))
                    v2 = float(groups[1].replace(',', '.')) if len(groups) > 2 and groups[1] and groups[1].replace(',','').replace('.','').isdigit() else v1
                    u = groups[-1].lower().strip()

                    if u in ['kg', 'kilogram', 'kilograms']:
                        if animal_type in ['feline', 'canine', 'bear'] and 10 < v1 < 500:
                            stats["weight"] = f"{v1}–{v2} kg" if v1 != v2 else f"{v1} kg"
                            print(f" ✓ Weight found: {stats['weight']}")
                            break
                        elif animal_type in ['elephant', 'whale'] and 100 < v1 < 10000:
                            stats["weight"] = f"{v1}–{v2} kg" if v1 != v2 else f"{v1} kg"
                            print(f" ✓ Weight found: {stats['weight']}")
                            break
                        elif 0.1 < v1 < 10000:
                            stats["weight"] = f"{v1}–{v2} kg" if v1 != v2 else f"{v1} kg"
                            print(f" ✓ Weight found: {stats['weight']}")
                            break
                    elif u in ['t', 'tonne', 'tonnes', 'ton'] and 0.1 < v1 < 200:
                        stats["weight"] = f"{v1}–{v2} t" if v1 != v2 else f"{v1} t"
                        print(f" ✓ Weight found: {stats['weight']}")
                        break
                    elif u in ['lb', 'lbs', 'pound', 'pounds'] and 1 < v1 < 22000:
                        stats["weight"] = f"{v1}–{v2} lbs" if v1 != v2 else f"{v1} lbs"
                        print(f" ✓ Weight found: {stats['weight']}")
                        break
            except Exception as e:
                print(f" ⚠ Weight parse error: {e}")

    # ========== LENGTH ==========
    length_patterns = [
        r'(?:head[- ]?body|body|total)?\s*(?:length|long)\s*(?:of|is|ranges from|between)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|mm|ft|feet|in|inches?)',
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet)\s*(?:long|length|in length)?',
        r'(?:grows|reaches|measures)\s*(?:up to|to|about)?\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet)',
        r'wingspan\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet)',
    ]

    for pattern in length_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                groups = m.groups()
                v1 = float(groups[0].replace(',', '.'))
                v2 = float(groups[1].replace(',', '.')) if len(groups) > 2 and groups[1] else v1
                u = groups[-1].lower().strip()

                if u in ['m', 'metre', 'metres', 'meter', 'meters'] and 0.1 < v1 < 100:
                    stats["length"] = f"{v1}–{v2} m" if v1 != v2 else f"{v1} m"
                    print(f" ✓ Length found: {stats['length']}")
                    break
                elif u in ['cm', 'centimetre', 'centimetres', 'centimeter', 'centimeters'] and 1 < v1 < 10000:
                    stats["length"] = f"{v1}–{v2} cm" if v1 != v2 else f"{v1} cm"
                    print(f" ✓ Length found: {stats['length']}")
                    break
                elif u in ['ft', 'foot', 'feet'] and 0.5 < v1 < 300:
                    stats["length"] = f"{v1}–{v2} ft" if v1 != v2 else f"{v1} ft"
                    print(f" ✓ Length found: {stats['length']}")
                    break
            except Exception as e:
                print(f" ⚠ Length parse error: {e}")

    # ========== HEIGHT ==========
    if any(w in text_lower for w in ['shoulder', 'stands', 'tall', 'height', 'at the shoulder']):
        height_patterns = [
            r'(?:stands?|stand|height|tall|at the shoulder)\s*(?:about|around|up to|of)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet)',
            r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet)\s*(?:tall|height|shoulder|at the shoulder)',
        ]
        for pattern in height_patterns:
            m = re.search(pattern, text, re.I)
            if m:
                try:
                    groups = m.groups()
                    v1 = float(groups[0].replace(',', '.'))
                    v2 = float(groups[1].replace(',', '.')) if len(groups) > 2 else v1
                    u = groups[-1].lower().strip()

                    if u in ['m', 'metre', 'metres', 'meter', 'meters'] and 0.1 < v1 < 10:
                        stats["height"] = f"{v1}–{v2} m" if v1 != v2 else f"{v1} m"
                        print(f" ✓ Height found: {stats['height']}")
                        break
                    elif u in ['cm', 'centimetre', 'centimetres'] and 10 < v1 < 1000:
                        stats["height"] = f"{v1}–{v2} cm" if v1 != v2 else f"{v1} cm"
                        print(f" ✓ Height found: {stats['height']}")
                        break
                    elif u in ['ft', 'foot', 'feet'] and 0.5 < v1 < 30:
                        stats["height"] = f"{v1}–{v2} ft" if v1 != v2 else f"{v1} ft"
                        print(f" ✓ Height found: {stats['height']}")
                        break
                except Exception as e:
                    print(f" ⚠ Height parse error: {e}")

    # ========== LIFESPAN ==========
    lifespan_patterns = [
        r'(?:lifespan|life expectancy|live|lives|live up to)\s*(?:of|is|up to|about|around)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs?|months?|weeks?|days?)',
        r'(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs?|months?|weeks?|days?)\s*(?:lifespan|life|in wild|in captivity|old|age)',
        r'(?:up to|about|around|approximately)\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs?)\s*(?:old|age|lifespan)',
    ]

    for pattern in lifespan_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                v = m.group(1).replace(' ', '')
                unit = m.group(2).lower()

                if 'year' in unit:
                    if '-' in v or '–' in v:
                        p = re.split(r'[-–]', v)
                        if len(p) >= 2 and 0 < int(p[0]) < int(p[1]) < 200:
                            stats["lifespan"] = f"{p[0]}–{p[1]} years"
                            print(f" ✓ Lifespan found: {stats['lifespan']}")
                            break
                    elif 0 < int(v) < 200:
                        stats["lifespan"] = f"{v} years"
                        print(f" ✓ Lifespan found: {stats['lifespan']}")
                        break
                elif 'month' in unit and 1 < int(v) < 120:
                    stats["lifespan"] = f"{v} months"
                    print(f" ✓ Lifespan found: {stats['lifespan']}")
                    break
            except Exception as e:
                print(f" ⚠ Lifespan parse error: {e}")

    # ========== SPEED ==========
    if any(w in text_lower for w in ['speed', 'sprint', 'run', 'fly', 'swim', 'fast', 'km/h', 'mph', 'kilometers per hour']):
        speed_patterns = [
            r'(?:speed|sprint|run|swim|fly|can|capable of)\s*(?:of|up to|about|around)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−)?\s*(\d+(?:[.,]\d+)?)?\s*(km/h|kmph|mph|mi/h|m/s|kilometers? per hour|miles? per hour)',
            r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−)?\s*(\d+(?:[.,]\d+)?)?\s*(km/h|kmph|mph|mi/h|m/s)\s*(?:speed|top speed|maximum)?',
            r'(?:up to|about|around|approximately|can)\s*(\d+(?:[.,]\d+)?)\s*(km/h|kmph|mph|mi/h|m/s)',
        ]

        for pattern in speed_patterns:
            m = re.search(pattern, text, re.I)
            if m:
                try:
                    v = float(m.group(1).replace(',', '.'))
                    if 1 < v < 500:
                        stats["top_speed"] = f"{v} {m.group(3).lower()}"
                        print(f" ✓ Speed found: {stats['top_speed']}")
                        break
                except Exception as e:
                    print(f" ⚠ Speed parse error: {e}")

    return stats


def extract_diet(text, animal_type):
    """Extract diet type from text"""
    if not text:
        return get_default_diet(animal_type)

    t = text.lower()

    if any(w in t for w in ['carnivore', 'carnivorous', 'meat-eater', 'predator', 'preys on', 'hunts', 'feeds on animals']):
        return "Carnivore"
    elif any(w in t for w in ['herbivore', 'herbivorous', 'plant-eater', 'grazes', 'browses', 'foliage', 'vegetation', 'feeds on plants']):
        return "Herbivore"
    elif any(w in t for w in ['omnivore', 'omnivorous', 'both plants and animals', 'varied diet', 'eats both']):
        return "Omnivore"
    elif any(w in t for w in ['insectivore', 'insectivorous', 'eats insects', 'insects']):
        return "Insectivore"
    elif any(w in t for w in ['piscivore', 'piscivorous', 'eats fish', 'fish']):
        return "Piscivore"

    return get_default_diet(animal_type)


def extract_conservation(text):
    """Extract conservation status from text"""
    if not text: return None
    statuses = ["Critically Endangered", "Endangered", "Vulnerable", "Near Threatened",
                "Least Concern", "Data Deficient", "Extinct in the Wild", "Extinct"]
    for s in statuses:
        if s.lower() in text.lower():
            return s
    return None


def extract_locations(text, animal_type):
    """Extract geographic locations from text"""
    if not text:
        return None

    animal_locations = LOCATIONS.get("animal_specific", {}).get(animal_type, [])

    for region, locs in LOCATIONS.get("regions", {}).items():
        animal_locations.extend(locs)

    locs = []
    text_lower = text.lower()
    for loc in animal_locations:
        if loc.lower() in text_lower:
            locs.append(loc)

    seen = set()
    unique_locs = []
    for loc in locs:
        loc_lower = loc.lower()
        if animal_type == 'elephant' and any(w in loc_lower for w in ['asia', 'china', 'indonesia']):
            continue
        if animal_type == 'raptor' and 'asia' in loc_lower and 'bald' in text_lower:
            continue
        if animal_type == 'penguin' and any(w in loc_lower for w in ['asia', 'africa', 'north america']):
            continue
        if loc_lower not in seen:
            seen.add(loc_lower)
            unique_locs.append(loc)

    return ", ".join(unique_locs[:5]) if unique_locs else None


def extract_habitat(text, animal_type):
    """Extract habitat types from text"""
    if not text:
        return None

    habitat_keywords = HABITATS.get(animal_type, HABITATS.get("default", []))

    common_habitats = ['forest', 'jungle', 'savanna', 'grassland', 'desert',
                       'mountain', 'ocean', 'sea', 'river', 'lake', 'wetland',
                       'swamp', 'marsh', 'tundra', 'rainforest', 'woodland',
                       'coastal', 'coral reef', 'mangrove', 'temperate', 'tropical']
    habitat_keywords.extend(common_habitats)

    found = []
    text_lower = text.lower()

    for keyword in habitat_keywords:
        if keyword.lower() in text_lower:
            found.append(keyword)

    return ", ".join(list(set(found))[:4]) if found else None


def extract_features(text, animal_type):
    """Extract distinctive features from text"""
    if not text:
        return None

    type_features = FEATURES.get(animal_type, FEATURES.get("default", {}))
    positive = type_features.get("positive", [])
    negative = type_features.get("negative", [])

    features = []
    text_lower = text.lower()

    for feature in positive:
        if feature in text_lower:
            display_feature = feature.replace('_', ' ').title()
            if display_feature not in features:
                features.append(display_feature)

    common_features = {
        "striped": "Striped coat", "stripe": "Striped coat",
        "spotted": "Spotted coat", "spot": "Spotted coat",
        "mane": "Distinctive mane", "trunk": "Long trunk",
        "tusk": "Large tusks", "horn": "Prominent horns",
        "antler": "Large antlers", "wing": "Distinctive wings",
        "tail": "Long tail", "fin": "Distinctive fins",
        "shell": "Protective shell", "venom": "Venomous",
        "claw": "Sharp claws", "fang": "Large fangs",
        "beak": "Distinctive beak", "feather": "Distinctive plumage",
        "scale": "Scaled skin", "fur": "Thick fur"
    }

    for keyword, feature in common_features.items():
        if keyword in text_lower and feature not in features:
            blocked = False
            for neg in negative:
                if neg in keyword or keyword in neg:
                    blocked = True
                    break

            if animal_type not in ['fish', 'shark', 'ray'] and 'fin' in keyword:
                blocked = True
            if animal_type not in ['bird', 'raptor', 'penguin', 'butterfly', 'bee', 'bat'] and 'wing' in keyword:
                blocked = True
            if animal_type not in ['turtle'] and 'shell' in keyword:
                blocked = True
            if animal_type not in ['elephant'] and 'trunk' in keyword:
                blocked = True
            if animal_type not in ['elephant', 'bovine', 'deer'] and 'tusk' in keyword:
                blocked = True
            if animal_type not in ['feline'] and 'stripe' in keyword:
                blocked = True
            if animal_type not in ['frog', 'fish', 'salmon', 'shark', 'ray'] and 'tail' in keyword and 'long' in text_lower:
                if animal_type == 'frog':
                    blocked = True

            if not blocked:
                features.append(feature)

    return features[:3] if features else None


def extract_behavior(text, animal_type):
    """Extract social behavior from text"""
    if not text:
        return None

    t = text.lower()

    social_indicators = {
        'elephant': ['herd', 'family', 'matriarch', 'social', 'group'],
        'bee': ['colony', 'hive', 'social', 'eusocial', 'worker', 'queen'],
        'penguin': ['colony', 'rookery', 'huddle', 'group', 'social'],
        'canine': ['pack', 'social', 'group', 'hunting together'],
        'ant': ['colony', 'social', 'eusocial', 'worker', 'queen']
    }

    if animal_type in social_indicators:
        for indicator in social_indicators[animal_type]:
            if indicator in t:
                return "Social"

    if any(w in t for w in ['solitary', 'alone', 'lives alone', 'mostly solitary', 'lives singly', 'lone', 'territorial']):
        return "Solitary"
    elif any(w in t for w in ['pack', 'herd', 'flock', 'school', 'swarm', 'colony', 'social', 'group living', 'highly social', 'live in groups']):
        return "Social"
    elif any(w in t for w in ['pair', 'mate', 'family group', 'monogamous', 'nuclear family', 'pairs']):
        return "Family groups"

    social_types = ['elephant', 'bee', 'ant', 'penguin', 'canine', 'whale']
    if animal_type in social_types:
        return "Social"

    return "Solitary"


def extract_reproduction(text, animal_type):
    """Extract reproduction data from text"""
    repro = {
        "gestation_period": None,
        "average_litter_size": None,
        "name_of_young": get_young_name(animal_type)
    }

    if not text:
        return repro

    text_lower = text.lower()

    gestation_patterns = [
        r'(?:gestation|pregnancy|incubation)\s*(?:period|lasts?|is|of)?\s*(?:around|about|approximately|over)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(months?|weeks?|days?)',
        r'(\d+(?:\s*[-–]\s*\d+)?)\s*(months?|weeks?|days?)\s*(?:gestation|pregnancy|incubation|period)',
        r'(?:pregnant|carries young)\s*(?:for)?\s*(?:around|about)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(months?|weeks?|days?)',
        r'after\s*(?:around|about)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(months?|weeks?|days?)\s*(?:of\s*)?(?:pregnancy|gestation)',
        r'lasts?\s*(?:around|about|approximately|over|up to)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(months?|weeks?|days?)',
    ]

    for pattern in gestation_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                v = m.group(1).replace(' ', '')
                unit = m.group(2).lower()

                if 'month' in unit:
                    if '-' in v or '–' in v:
                        p = re.split(r'[-–]', v)
                        if len(p) >= 2 and 1 <= int(p[0]) <= int(p[1]) <= 24:
                            repro["gestation_period"] = f"{p[0]}–{p[1]} months"
                            print(f" ✓ Gestation found: {repro['gestation_period']}")
                            break
                    elif 1 <= int(v) <= 24:
                        repro["gestation_period"] = f"{v} months"
                        print(f" ✓ Gestation found: {repro['gestation_period']}")
                        break
                elif 'week' in unit and 1 <= int(v) <= 100:
                    repro["gestation_period"] = f"{v} weeks"
                    print(f" ✓ Gestation found: {repro['gestation_period']}")
                    break
                elif 'day' in unit and 1 <= int(v) <= 365:
                    repro["gestation_period"] = f"{v} days"
                    print(f" ✓ Gestation found: {repro['gestation_period']}")
                    break
            except Exception as e:
                print(f" ⚠ Gestation parse error: {e}")

    litter_patterns = [
        r'(?:litter|clutch|brood|cubs?|young|offspring|chicks?|pups?)?\s*(?:size|consists?|of|contains|are|is)?\s*(?:of|up to|typically|average|more)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(?:eggs?|young|offspring|cubs?|chicks?|pups?)?',
        r'(?:as many as|up to|about|around|typically|usually)\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(?:eggs?|young|offspring|cubs?|chicks?|pups?)?',
        r'(\d+(?:\s*[-–]\s*\d+)?)\s*(?:eggs?|young|offspring|cubs?|chicks?|pups?)?\s*(?:per\s*)?(?:litter|clutch|brood)',
        r'(?:gives birth|lays|produces)\s*(?:to|up to|about)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(?:eggs?|young|offspring|cubs?|chicks?|pups?)?',
    ]

    for pattern in litter_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                v = m.group(1).replace(' ', '')

                if '-' in v or '–' in v:
                    p = re.split(r'[-–]', v)
                    if len(p) >= 2 and 1 <= int(p[0]) <= int(p[1]) <= 50:
                        repro["average_litter_size"] = p[0] if p[0] == p[1] else f"{p[0]}–{p[1]}"
                        print(f" ✓ Litter size found: {repro['average_litter_size']}")
                        break
                elif 1 <= int(v) <= 50:
                    repro["average_litter_size"] = v
                    print(f" ✓ Litter size found: {repro['average_litter_size']}")
                    break
            except Exception as e:
                print(f" ⚠ Litter size parse error: {e}")

    return repro


def extract_threats(text):
    """Extract threats from text"""
    threats = []
    t = text.lower()
    if any(w in t for w in ['poach', 'illegal trade', 'body parts', 'fur trade', 'ivory', 'horn trade']):
        threats.append('Poaching')
    if any(w in t for w in ['habitat loss', 'deforestation', 'habitat destruction', 'habitat fragmentation', 'loss of habitat']):
        threats.append('Habitat loss')
    if any(w in t for w in ['human-wildlife conflict', 'livestock', 'retaliation', 'persecution', 'killed by humans']):
        threats.append('Human-wildlife conflict')
    if any(w in t for w in ['climate change', 'global warming', 'ocean acidification', 'rising temperatures']):
        threats.append('Climate change')
    if any(w in t for w in ['pollution', 'pesticide', 'contamination', 'pollutants']):
        threats.append('Pollution')
    if any(w in t for w in ['overfishing', 'bycatch', 'fishing', 'overhunting', 'hunting']):
        threats.append('Overfishing')
    return ', '.join(threats[:3]) if threats else None
