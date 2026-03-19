# generator/modules/extractors/weight.py
"""
Weight extraction module - V6 ELEPHANT-OPTIMIZED
Based on actual Wikipedia article analysis
"""
import re
from typing import Dict, Optional, List, Tuple


def _parse_weight_to_kg(value: str) -> Optional[float]:
    """Parse a weight value and convert to kg for validation"""
    try:
        match = re.search(r'(\d+(?:[.,]\d+)?)', value)
        if not match:
            return None
        num = float(match.group(1).replace(',', ''))
        
        value_lower = value.lower()
        if 'tonne' in value_lower or re.search(r'\bton\b', value_lower):
            num *= 1000
        elif 'lb' in value_lower or 'pound' in value_lower:
            num *= 0.453592
        elif re.search(r'\bg\b', value_lower) and 'kg' not in value_lower:
            num /= 1000
        
        return num
    except:
        return None


def _is_valid_weight(value: str, animal_name: str = "") -> bool:
    """Validate weight value makes sense for animal type"""
    kg = _parse_weight_to_kg(value)
    if kg is None or kg < 0.00001:
        return False
    
    animal_lower = animal_name.lower() if animal_name else ""
    
    # Animal-specific validation ranges (kg) - EXPANDED based on actual data
    validation_rules = {
        'elephant': (500, 12000),       # African elephant 2-6 tonnes (forest elephants smaller)
        'wolf': (10, 120),               # Gray wolf 30-80 kg
        'bee': (0.00001, 0.5),           # Honey bee ~0.1g
        'butterfly': (0.00001, 0.05),    # Monarch ~0.5g
        'frog': (0.01, 5),               # Bullfrog 0.1-0.8 kg
        'shark': (50, 15000),            # Great white 1-2 tonnes
        'turtle': (10, 900),             # Sea turtle 68-190 kg
        'salmon': (0.5, 60),             # Atlantic salmon 3-15 kg
        'eagle': (0.5, 20),              # Bald eagle 3-6 kg
        'penguin': (5, 60),              # Emperor 22-45 kg
        'snake': (0.1, 25),              # King cobra up to 10 kg
        'cobra': (0.1, 25),
        'cheetah': (10, 80),             # Cheetah 21-65 kg
        'tiger': (50, 400),              # Tiger 140-300 kg
        'cat': (1, 300),                 # General feline
        'bird': (0.001, 20),             # General bird
        'fish': (0.001, 5000),           # General fish
        'reptile': (0.001, 1000),        # General reptile
        'amphibian': (0.0001, 10),       # General amphibian
        'insect': (0.000001, 0.5),       # General insect
        'feline': (1, 400),              # All cats
        'canine': (1, 120),              # All dogs/wolves
    }
    
    for keyword, (min_kg, max_kg) in validation_rules.items():
        if keyword in animal_lower:
            return min_kg <= kg <= max_kg
    
    # Default: accept reasonable animal weights (0.1g to 10 tonnes)
    return 0.0001 <= kg <= 10000


def _is_tusk_or_trunk_weight(text: str) -> bool:
    """Check if weight is about tusks/ivory/trunk (not body weight)"""
    text_lower = text.lower()
    tusk_keywords = ["tusk", "ivory", "tooth", "trunk weigh", "trunk weight", "molar", "teeth"]
    return any(kw in text_lower for kw in tusk_keywords)


def _is_population_or_count(text: str) -> bool:
    """Check if number is population count (not weight)"""
    text_lower = text.lower()
    pop_keywords = [
        "individual", "population", "estimated", "wild population",
        "million", "thousand", "species", "remaining", "conservation",
        "between 200,000", "between 250,000"
    ]
    return any(kw in text_lower for kw in pop_keywords)


def _is_length_measurement(text: str) -> bool:
    """Check if measurement is about length, not weight"""
    text_lower = text.lower()
    weight_keywords = ["weigh", "weight", "mass", "heavy", "kg", "kilogram", "tonne", "ton", "lb", "pound", "gram", "g"]
    length_keywords = ["length", "long", "tall", "height", "meter", "foot", "inch", "cm", "mm", "span", "wing"]
    
    has_weight = any(kw in text_lower for kw in weight_keywords)
    has_length = any(kw in text_lower for kw in length_keywords)
    
    return has_length and not has_weight


def _is_nest_or_object_weight(text: str) -> bool:
    """Check if weight is about nest/object (not animal body)"""
    text_lower = text.lower()
    object_keywords = [
        "nest", "egg", "liver", "heart", "brain", "bone", "skeleton",
        "carapace", "shell", "wing", "tail", "head"
    ]
    return any(kw in text_lower for kw in object_keywords)


def _is_colony_weight(text: str) -> bool:
    """Check if weight is about colony/hive (not individual bee)"""
    text_lower = text.lower()
    colony_keywords = [
        "colony", "hive", "colony weight", "hive weight",
        "workers", "colony of", "hive of", "per colony"
    ]
    return any(kw in text_lower for kw in colony_keywords)


def _extract_and_validate(match, text: str, animal_name: str) -> Optional[str]:
    """Process a regex match and validate it"""
    groups = match.groups()
    match_context = text[max(0, match.start()-400):match.end()+400]  # Expanded context
    
    # Skip invalid contexts
    if _is_tusk_or_trunk_weight(match_context):
        return None
    if _is_population_or_count(match_context):
        return None
    if _is_length_measurement(match_context):
        return None
    if _is_nest_or_object_weight(match_context):
        return None
    if _is_colony_weight(match_context):
        return None
    
    # Build candidate string
    if len(groups) >= 3:
        candidate = f"{groups[0]}–{groups[1]} {groups[2]}"
    elif len(groups) >= 2:
        candidate = f"{groups[0]} {groups[1]}"
    else:
        return None
    
    if _is_valid_weight(candidate, animal_name):
        return candidate
    
    return None


def _get_section_priority(sections: Dict[str, str]) -> List[Tuple[str, str]]:
    """Get sections in priority order for weight extraction"""
    # Based on actual Wikipedia structure - Size section has weight for elephants!
    priority_order = [
        "size",             # MOST IMPORTANT for elephants - has "weigh 2600-3500 kg"
        "description",      # Often has weight summary
        "summary",          # Often has key stats
        "hunting_diet",     # Diet sections often mention prey/weight
        "behavior",         # Can include size/weight info
        "habitat",          # Sometimes has size info
        "reproduction",     # Can have weight info
        "distribution",     # Less likely but possible
        "etymology",        # Rare but possible
        "threats",          # Rare but possible
        "conservation",     # Least likely
    ]
    
    result = []
    for section_name in priority_order:
        if section_name in sections and sections[section_name]:
            result.append((section_name, sections[section_name]))
    
    return result


def extract_weight_from_sections(sections: Dict[str, str], animal_name: str = "") -> str:
    """Extract weight from Wikipedia sections with comprehensive pattern matching"""
    
    if not sections:
        return ""
    
    # Get all text for fallback
    all_text = " ".join(sections.values())
    if not all_text or len(all_text) < 50:
        return ""
    
    # Clean text (remove citations)
    clean_all = re.sub(r'\[\d+\]', '', all_text)
    clean_all = re.sub(r'\s+', ' ', clean_all)
    
    # Get sections in priority order
    prioritized_sections = _get_section_priority(sections)
    
    # Comprehensive weight patterns (ordered by specificity)
    # Based on actual Wikipedia patterns found in WildAtlas data
    weight_patterns = [
        # Pattern 1: "females... weigh 2600–3500 kg" (Elephant pattern from Size section)
        r'(?:females?|cows?|adults?|males?|bulls?|species|it|they|average)\s*(?:are|is)?\s*(?:.*?)(?:weigh|weight|weighing)\s*(?:between|from|about|around|up to|typically|normally|approximately)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g)\b',
        
        # Pattern 2: "weigh 2600–3500 kg" (Simple weigh pattern)
        r'(?:females?|cows?|adults?|males?|bulls?|species|it|they|average)?\s*weigh\s*(?:between|from|about|around|up to|typically|normally|approximately)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g)\b',
        
        # Pattern 3: "weighs 2600–3500 kg" (Most common)
        r'(?:females?|cows?|adults?|males?|bulls?|species|it|they|average)?\s*weighs?\s*(?:between|from|about|around|up to|typically|normally|approximately)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g)\b',
        
        # Pattern 4: "weighing from 22 to 45 kg" (Penguin uses this)
        r'weighing\s*(?:from|between|about|around)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)\b',
        
        # Pattern 5: "weight of X to Y kg"
        r'weight\s*(?:of|is|ranges from|between)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)\b',
        
        # Pattern 6: "weight ranges from X to Y kg"
        r'weight\s*ranges?\s*(?:from)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)\b',
        
        # Pattern 7: "body mass/weight X to Y kg"
        r'(?:body\s*)?(?:mass|weight)\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)\b',
        
        # Pattern 8: "ranges from X to Y kg"
        r'ranges?\s*(?:from)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)\b',
        
        # Pattern 9: "X-Y kg" with weight context before
        r'(?:weighs?|weight|mass|about|around|approximately)\s*(\d+(?:[.,]\d+)?)\s*[–-]\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)\b',
        
        # Pattern 10: "up to X kg"
        r'(?:weighs?|weight|up to|reaching|maximum|can reach)\s*(?:up to|about|around)?\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)\b',
        
        # Pattern 11: "weighed up to X kg" (King Cobra uses this)
        r'weighed\s*(?:up to|about|around)?\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)\b',
        
        # Pattern 12: "average X kg"
        r'(?:average|averages?|typically)\s*(?:weighs?|weight|of|is)?\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)\b',
        
        # Pattern 13: "X kg" single value with weight context
        r'(?:weighs?|weight|about|around|approximately|average)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)\b',
        
        # Pattern 14: Standalone "X to Y tonnes" (for elephants, sharks)
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(tonnes?|tons?|t)\b',
        
        # Pattern 15: Standalone "X to Y kg" with large numbers (elephants)
        r'(\d{3,4})\s*(?:–|-|to|and)\s*(\d{3,4})\s*(kg|kilograms)\b',
        
        # Pattern 16: "X to Y kg in weight" (Elephant forest pattern)
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms)\s*in\s*weight\b',
    ]
    
    # Try each section in priority order
    for section_name, section_text in prioritized_sections:
        clean_section = re.sub(r'\[\d+\]', '', section_text)
        clean_section = re.sub(r'\s+', ' ', clean_section)
        
        for pattern in weight_patterns:
            m = re.search(pattern, clean_section, re.I)
            if m:
                result = _extract_and_validate(m, clean_section, animal_name)
                if result:
                    return result
    
    # Fallback: Try all text combined
    for pattern in weight_patterns:
        m = re.search(pattern, clean_all, re.I)
        if m:
            result = _extract_and_validate(m, clean_all, animal_name)
            if result:
                return result
    
    # Priority 2: Animal-specific fallback patterns
    animal_lower = animal_name.lower() if animal_name else ""
    
    # Elephant - specifically look for body weight in kg/tonnes, avoid tusks
    if "elephant" in animal_lower:
        patterns = [
            # "females... weigh 2600–3500 kg"
            r'(?:females?|cows?|adults?)\s*(?:are|is)?\s*(?:.*?)(?:weigh|weight|weighing)\s*(?:between|from|about)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms|tonnes?|tons)',
            # "bulls... weigh 5200–6900 kg"
            r'(?:bulls?|males?|adults?)\s*(?:are|is)?\s*(?:.*?)(?:weigh|weight|weighing)\s*(?:between|from|about)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms|tonnes?|tons)',
            # "1700-2300 kg in weight" (forest elephant pattern)
            r'(\d{3,4})\s*(?:–|-|to|and)\s*(\d{3,4})\s*(kg|kilograms)\s*in\s*weight',
            # "weigh 2600-3500 kg"
            r'weigh\s*(?:between|from|about)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms|tonnes?|tons)',
            # Standalone large kg values (2000-10000 range for elephants)
            r'(\d{4})\s*(?:–|-|to|and)\s*(\d{4})\s*(kg|kilograms)',
        ]
        for pattern in patterns:
            m = re.search(pattern, clean_all, re.I)
            if m:
                context = clean_all[max(0, m.start()-500):m.end()+500]
                if not _is_tusk_or_trunk_weight(context):
                    if m.lastindex >= 3:
                        return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
                    elif m.lastindex == 2:
                        return f"{m.group(1)} {m.group(2)}"
    
    # Wolf - look for kg patterns, avoid population numbers
    if "wolf" in animal_lower:
        patterns = [
            r'(?:wolves?|adults?|packs?)\s*(?:weigh|weight|weighing)\s*(?:between|from)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms)',
            r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms)\s*(?:each|per)?',
        ]
        for pattern in patterns:
            m = re.search(pattern, clean_all, re.I)
            if m:
                context = clean_all[max(0, m.start()-300):m.end()+300]
                if not _is_population_or_count(context):
                    return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    # Shark - look for tonne or large kg patterns
    if "shark" in animal_lower:
        patterns = [
            r'(?:sharks?|adults?|females?|males?)\s*(?:weigh|weight|weighing)\s*(?:between|from)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(tonnes?|tons|kg|kilograms)',
            r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(tonnes?|tons|kg|kilograms)',
        ]
        for pattern in patterns:
            m = re.search(pattern, clean_all, re.I)
            if m:
                return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    # Snake/Cobra - look for kg patterns
    if "snake" in animal_lower or "cobra" in animal_lower:
        patterns = [
            r'(?:snakes?|cobras?|adults?)\s*(?:weigh|weight|weighing)\s*(?:up to|about|around)?\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms)',
            r'weighs?\s*(?:up to|about)?\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms)',
            r'weighed\s*(?:up to|about)?\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms)',
        ]
        for pattern in patterns:
            m = re.search(pattern, clean_all, re.I)
            if m:
                return f"{m.group(1)} {m.group(2)}"
    
    # Bee/Butterfly - look for gram patterns
    if "bee" in animal_lower or "butterfly" in animal_lower:
        patterns = [
            r'(?:bees?|butterflies?|adults?|workers?)\s*(?:weigh|weight|weighing)\s*(?:between|from|about)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(grams?|g)',
            r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(grams?|g)',
        ]
        for pattern in patterns:
            m = re.search(pattern, clean_all, re.I)
            if m:
                if m.group(2) and m.group(2) != m.group(1):
                    return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
                return f"{m.group(1)} {m.group(3)}"
    
    # Frog/Amphibian - look for gram or kg patterns
    if "frog" in animal_lower or "toad" in animal_lower:
        patterns = [
            r'(?:frogs?|toads?|adults?)\s*(?:weigh|weight|weighing)\s*(?:between|from|about)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(grams?|g|kg|kilograms)',
            r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(grams?|g|kg|kilograms)',
        ]
        for pattern in patterns:
            m = re.search(pattern, clean_all, re.I)
            if m:
                if m.group(2) and m.group(2) != m.group(1):
                    return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
                return f"{m.group(1)} {m.group(3)}"
    
    # Fish/Salmon - look for kg or lb patterns
    if "salmon" in animal_lower or "fish" in animal_lower:
        patterns = [
            r'(?:salmon|fish|adults?)\s*(?:weigh|weight|weighing|growing)\s*(?:up to|between|from|about)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(kg|kilograms|lbs?|pounds)',
            r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(kg|kilograms|lbs?|pounds)',
        ]
        for pattern in patterns:
            m = re.search(pattern, clean_all, re.I)
            if m:
                if m.group(2) and m.group(2) != m.group(1):
                    return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
                return f"{m.group(1)} {m.group(3)}"
    
    # Turtle - look for kg patterns
    if "turtle" in animal_lower or "tortoise" in animal_lower:
        patterns = [
            r'(?:turtles?|tortoises?|adults?)\s*(?:weigh|weight|weighing)\s*(?:between|from|about)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms)',
            r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms)',
        ]
        for pattern in patterns:
            m = re.search(pattern, clean_all, re.I)
            if m:
                return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    # Penguin/Bird - look for kg patterns
    if "penguin" in animal_lower or "eagle" in animal_lower or "bird" in animal_lower:
        patterns = [
            r'(?:penguins?|eagles?|birds?|adults?)\s*(?:weigh|weight|weighing|averaging)\s*(?:between|from|about)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms|lbs?|pounds|grams?|g)',
            r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms|lbs?|pounds|grams?|g)',
        ]
        for pattern in patterns:
            m = re.search(pattern, clean_all, re.I)
            if m:
                return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    # Cheetah/Cat/Feline - look for kg patterns
    if "cheetah" in animal_lower or "tiger" in animal_lower or "cat" in animal_lower or "feline" in animal_lower:
        patterns = [
            r'(?:cheetahs?|tigers?|cats?|adults?|males?|females?)\s*(?:weigh|weight|weighing)\s*(?:between|from|about)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms|lbs?|pounds)',
            r'adults?\s*weigh\s*(?:between|from)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms)',
        ]
        for pattern in patterns:
            m = re.search(pattern, clean_all, re.I)
            if m:
                return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    return ""
