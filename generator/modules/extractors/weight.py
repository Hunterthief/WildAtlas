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
    
    validation_rules = {
        'elephant': (500, 12000),
        'wolf': (10, 120),
        'bee': (0.00001, 0.5),
        'butterfly': (0.00001, 0.05),
        'frog': (0.01, 5),
        'shark': (50, 15000),
        'turtle': (10, 900),
        'salmon': (0.5, 60),
        'eagle': (0.5, 20),
        'penguin': (5, 60),
        'snake': (0.1, 25),
        'cobra': (0.1, 25),
        'cheetah': (10, 80),
        'tiger': (50, 400),
        'cat': (1, 300),
        'bird': (0.001, 20),
        'fish': (0.001, 5000),
        'reptile': (0.001, 1000),
        'amphibian': (0.0001, 10),
        'insect': (0.000001, 0.5),
        'feline': (1, 400),
        'canine': (1, 120),
    }
    
    for keyword, (min_kg, max_kg) in validation_rules.items():
        if keyword in animal_lower:
            return min_kg <= kg <= max_kg
    
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
        "workers", "colony of", "hive of", "per colony",
        "392", "hundreds of grams"
    ]
    return any(kw in text_lower for kw in colony_keywords)


def _extract_and_validate(match, text: str, animal_name: str) -> Optional[str]:
    """Process a regex match and validate it"""
    groups = match.groups()
    match_context = text[max(0, match.start()-400):match.end()+400]
    
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
    priority_order = [
        "size",
        "description",
        "summary",
        "hunting_diet",
        "behavior",
        "habitat",
        "reproduction",
        "distribution",
        "etymology",
        "threats",
        "conservation",
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
    
    all_text = " ".join(sections.values())
    if not all_text or len(all_text) < 50:
        return ""
    
    clean_all = re.sub(r'\[\d+\]', '', all_text)
    clean_all = re.sub(r'\s+', ' ', clean_all)
    
    prioritized_sections = _get_section_priority(sections)
    
    weight_patterns = [
        r'(?:females?|cows?|adults?|males?|bulls?|species|it|they|average)\s*(?:are|is)?\s*(?:.*?)(?:weigh|weight|weighing)\s*(?:between|from|about|around|up to|typically|normally|approximately)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g)\b',
        r'(?:females?|cows?|adults?|males?|bulls?|species|it|they|average)?\s*weigh\s*(?:between|from|about|around|up to|typically|normally|approximately)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g)\b',
        r'(?:females?|cows?|adults?|males?|bulls?|species|it|they|average)?\s*weighs?\s*(?:between|from|about|around|up to|typically|normally|approximately)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g)\b',
        r'weighing\s*(?:from|between|about|around)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)\b',
        r'weight\s*(?:of|is|ranges from|between)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)\b',
        r'weight\s*ranges?\s*(?:from)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)\b',
        r'(?:body\s*)?(?:mass|weight)\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)\b',
        r'ranges?\s*(?:from)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)\b',
        r'(?:weighs?|weight|mass|about|around|approximately)\s*(\d+(?:[.,]\d+)?)\s*[–-]\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)\b',
        r'(?:weighs?|weight|up to|reaching|maximum|can reach)\s*(?:up to|about|around)?\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)\b',
        r'weighed\s*(?:up to|about|around)?\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)\b',
        r'(?:average|averages?|typically)\s*(?:weighs?|weight|of|is)?\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)\b',
        r'(?:weighs?|weight|about|around|approximately|average)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)\b',
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(tonnes?|tons?|t)\b',
        r'(\d{3,4})\s*(?:–|-|to|and)\s*(\d{3,4})\s*(kg|kilograms)\b',
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms)\s*in\s*weight\b',
    ]
    
    for section_name, section_text in prioritized_sections:
        clean_section = re.sub(r'\[\d+\]', '', section_text)
        clean_section = re.sub(r'\s+', ' ', clean_section)
        
        for pattern in weight_patterns:
            m = re.search(pattern, clean_section, re.I)
            if m:
                result = _extract_and_validate(m, clean_section, animal_name)
                if result:
                    return result
    
    for pattern in weight_patterns:
        m = re.search(pattern, clean_all, re.I)
        if m:
            result = _extract_and_validate(m, clean_all, animal_name)
            if result:
                return result
    
    animal_lower = animal_name.lower() if animal_name else ""
    
    if "elephant" in animal_lower:
        patterns = [
            r'(?:females?|cows?|adults?)\s*(?:are|is)?\s*(?:.*?)(?:weigh|weight|weighing)\s*(?:between|from|about)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms|tonnes?|tons)',
            r'(?:bulls?|males?|adults?)\s*(?:are|is)?\s*(?:.*?)(?:weigh|weight|weighing)\s*(?:between|from|about)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms|tonnes?|tons)',
            r'(\d{3,4})\s*(?:–|-|to|and)\s*(\d{3,4})\s*(kg|kilograms)\s*in\s*weight',
            r'weigh\s*(?:between|from|about)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms|tonnes?|tons)',
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
    
    if "shark" in animal_lower:
        patterns = [
            r'(?:sharks?|adults?|females?|males?)\s*(?:weigh|weight|weighing)\s*(?:between|from)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(tonnes?|tons|kg|kilograms)',
            r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(tonnes?|tons|kg|kilograms)',
        ]
        for pattern in patterns:
            m = re.search(pattern, clean_all, re.I)
            if m:
                return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
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
    
    if "bee" in animal_lower or "butterfly" in animal_lower:
        patterns = [
            r'(?:individual|worker|single)\s*(?:bee|butterfly)\s*(?:weighs?|weight|weighing)\s*(?:between|from|about)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(grams?|g)',
            r'(?:bee|butterfly)\s*(?:weighs?|weight|weighing)\s*(?:about|approximately|around)?\s*(\d+(?:[.,]\d+)?)\s*(grams?|g)',
        ]
        for pattern in patterns:
            m = re.search(pattern, clean_all, re.I)
            if m:
                context = clean_all[max(0, m.start()-200):m.end()+200]
                if not _is_colony_weight(context):
                    if m.group(2) and m.group(2) != m.group(1):
                        return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
                    return f"{m.group(1)} {m.group(2) if m.group(2) else m.group(1)}"
    
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
    
    if "turtle" in animal_lower or "tortoise" in animal_lower:
        patterns = [
            r'(?:turtles?|tortoises?|adults?)\s*(?:weigh|weight|weighing)\s*(?:between|from|about)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms)',
            r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms)',
        ]
        for pattern in patterns:
            m = re.search(pattern, clean_all, re.I)
            if m:
                return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    if "penguin" in animal_lower or "eagle" in animal_lower or "bird" in animal_lower:
        patterns = [
            r'(?:penguins?|eagles?|birds?|adults?)\s*(?:weigh|weight|weighing|averaging)\s*(?:between|from|about)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms|lbs?|pounds|grams?|g)',
            r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms|lbs?|pounds|grams?|g)',
        ]
        for pattern in patterns:
            m = re.search(pattern, clean_all, re.I)
            if m:
                return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
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
