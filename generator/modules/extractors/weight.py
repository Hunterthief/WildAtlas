# generator/modules/extractors/weight.py
"""
Weight extraction module - V2 IMPROVED
Better patterns for elephants, wolves, fish, etc.
"""
import re
from typing import Dict, Optional, Tuple


def _parse_weight_value(value: str) -> Optional[float]:
    """Parse a weight value to kg for validation"""
    try:
        match = re.search(r'(\d+(?:[.,]\d+)?)', value)
        if not match:
            return None
        num = float(match.group(1).replace(',', ''))
        
        # Convert to kg for validation
        value_lower = value.lower()
        if 'tonne' in value_lower or ' ton' in value_lower:
            num *= 1000
        elif 'lb' in value_lower or 'pound' in value_lower:
            num *= 0.453592
        elif 'g' in value_lower and 'kg' not in value_lower:
            num /= 1000
        
        return num
    except:
        return None


def _is_valid_weight(value: str, animal_name: str = "") -> bool:
    """Validate weight value makes sense for animal type"""
    kg = _parse_weight_value(value)
    if kg is None:
        return False
    
    if kg < 0.0001:  # Too small
        return False
    
    animal_lower = animal_name.lower() if animal_name else ""
    
    # Elephants should be 1000+ kg (not tusk weight 23-45kg)
    if "elephant" in animal_lower:
        return kg >= 1000  # Body weight, not tusks
    
    # Wolves should be 20-100kg range
    if "wolf" in animal_lower:
        return 15 <= kg <= 120
    
    # Bees should be in grams (0.01-1g)
    if "bee" in animal_lower:
        return 0.00001 <= kg <= 0.005
    
    # Butterflies should be in grams (0.1-3g)
    if "butterfly" in animal_lower:
        return 0.00005 <= kg <= 0.01
    
    # Frogs should be 0.1-2kg
    if "frog" in animal_lower:
        return 0.05 <= kg <= 3
    
    # Sharks can be 500-3000kg
    if "shark" in animal_lower:
        return kg >= 200
    
    # Turtles can be 50-500kg
    if "turtle" in animal_lower:
        return kg >= 30
    
    # Salmon should be 2-50kg
    if "salmon" in animal_lower:
        return 1 <= kg <= 60
    
    # Eagles/birds 1-15kg
    if "eagle" in animal_lower or "bird" in animal_lower:
        return 0.5 <= kg <= 20
    
    # Penguins 15-50kg
    if "penguin" in animal_lower:
        return 10 <= kg <= 60
    
    # Snakes 1-20kg (king cobra up to 10kg)
    if "snake" in animal_lower or "cobra" in animal_lower:
        return 0.5 <= kg <= 25
    
    # Cheetahs 20-70kg
    if "cheetah" in animal_lower:
        return 15 <= kg <= 80
    
    # Tigers 100-350kg
    if "tiger" in animal_lower:
        return 80 <= kg <= 400
    
    return True  # Default accept


def _is_tusk_weight(text: str) -> bool:
    """Check if weight is about tusks/ivory (not body weight)"""
    text_lower = text.lower()
    tusk_keywords = ["tusk", "ivory", "tooth", "trunk"]
    return any(kw in text_lower for kw in tusk_keywords)


def _is_population_number(text: str) -> bool:
    """Check if number is population (not weight)"""
    text_lower = text.lower()
    pop_keywords = [
        "individual", "population", "estimated", "wild", 
        "between 200,000", "between 250,000", "million",
        "species", "remaining", "conservation"
    ]
    return any(kw in text_lower for kw in pop_keywords)


def _is_length_not_weight(text: str) -> bool:
    """Check if measurement is about length, not weight"""
    text_lower = text.lower()
    length_keywords = [
        "length", "long", "tall", "height", "meter", "foot", 
        "inch", "cm", "mm", "span", "wing"
    ]
    return any(kw in text_lower for kw in length_keywords)


def _extract_weight_match(match, text: str, animal_name: str) -> Optional[str]:
    """Process a weight regex match and validate it"""
    groups = match.groups()
    match_context = text[max(0, match.start()-200):match.end()+200]
    
    # Skip tusk weight
    if _is_tusk_weight(match_context):
        return None
    
    # Skip population numbers
    if _is_population_number(match_context):
        return None
    
    # Skip if it's clearly about length
    if _is_length_not_weight(match_context):
        return None
    
    if len(groups) >= 3:
        candidate = f"{groups[0]}–{groups[1]} {groups[2]}"
        if _is_valid_weight(candidate, animal_name):
            return candidate
    elif len(groups) >= 2:
        candidate = f"{groups[0]} {groups[1]}"
        if _is_valid_weight(candidate, animal_name):
            return candidate
    
    return None


def extract_weight_from_sections(sections: Dict[str, str], animal_name: str = "") -> str:
    """Extract weight from Wikipedia sections with priority ordering"""
    
    if not sections:
        return ""
    
    all_text = " ".join(sections.values())
    
    if not all_text or len(all_text) < 50:
        return ""
    
    # Clean text
    clean_text = re.sub(r'\[\d+\]', '', all_text)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    # Get description section first (highest priority)
    description = sections.get("description", "")
    if description:
        description = re.sub(r'\[\d+\]', '', description)
        description = re.sub(r'\s+', ' ', description)
    
    # Priority 1: Direct weight patterns with context
    weight_patterns = [
        # "weighs between X and Y kg" (BEST - Wolf, Elephant, Cheetah)
        r'(?:adults?|males?|females?|species|it|they|average|bulls?)?\s*weighs?\s*(?:between|from|about|around|up to|typically|normally)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g)',
        
        # "weigh X to Y kg"
        r'weigh\s*(?:between|from|about|around)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "weight of X to Y kg"
        r'weight\s*(?:of|is|ranges from)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "weighing X to Y kg"
        r'weighing\s*(?:between|from|about|around)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "X to Y kilograms" with weight context nearby
        r'(?:weight|weighs|mass|body mass|body weight|heavy|weighed)\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "ranges from X to Y kg"
        r'ranges?\s*(?:from)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "mass of X to Y kg"
        r'mass\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "X–Y kg" (en-dash) with weight context
        r'(?:weighs?|weight|mass|about|around)\s*(\d+(?:[.,]\d+)?)\s*[–-]\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "up to X kg"
        r'(?:weighs?|weight|up to|reaching|maximum)\s*(?:up to|about)?\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "X kg" single value with context
        r'(?:weighs?|weight|about|around|approximately|average)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "tonnes" for large animals (elephants, sharks)
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(tonnes?|tons?|t)',
        
        # "X lbs" imperial
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(lbs?|pounds)',
    ]
    
    # Try description section first
    if description:
        for pattern in weight_patterns:
            m = re.search(pattern, description, re.I)
            if m:
                result = _extract_weight_match(m, description, animal_name)
                if result:
                    return result
    
    # Then try all sections
    for pattern in weight_patterns:
        m = re.search(pattern, clean_text, re.I)
        if m:
            result = _extract_weight_match(m, clean_text, animal_name)
            if result:
                return result
    
    # Priority 2: Animal-specific fallbacks
    animal_lower = animal_name.lower() if animal_name else ""
    
    # Elephant - look for tonne patterns, avoid tusk weight
    if "elephant" in animal_lower:
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(tonnes?|tons)', clean_text, re.I)
        if m:
            context = clean_text[max(0, m.start()-200):m.end()+200]
            if not _is_tusk_weight(context):
                return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
        
        # Also try "weighs X tonnes"
        m = re.search(r'weighs?\s*(?:up to|about|around)?\s*(\d+(?:[.,]\d+)?)\s*(tonnes?|tons)', clean_text, re.I)
        if m:
            context = clean_text[max(0, m.start()-200):m.end()+200]
            if not _is_tusk_weight(context):
                return f"{m.group(1)} {m.group(2)}"
    
    # Wolf - look for kg patterns
    if "wolf" in animal_lower:
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms)', clean_text, re.I)
        if m:
            context = clean_text[max(0, m.start()-200):m.end()+200]
            if not _is_population_number(context):
                return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    # Shark - look for tonne or large kg patterns
    if "shark" in animal_lower:
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(tonnes?|tons|kg|kilograms)', clean_text, re.I)
        if m:
            return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    # Snake - look for kg patterns
    if "snake" in animal_lower or "cobra" in animal_lower:
        m = re.search(r'weighs?\s*(?:up to|about)?\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms)', clean_text, re.I)
        if m:
            return f"{m.group(1)} {m.group(2)}"
    
    # Bee/Butterfly - look for gram patterns
    if "bee" in animal_lower or "butterfly" in animal_lower:
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(grams?|g)', clean_text, re.I)
        if m:
            if m.group(2):
                return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
            return f"{m.group(1)} {m.group(3)}"
    
    # Frog - look for gram or kg patterns
    if "frog" in animal_lower:
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(grams?|g|kg|kilograms)', clean_text, re.I)
        if m:
            if m.group(2):
                return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
            return f"{m.group(1)} {m.group(3)}"
    
    # Salmon/Fish - look for kg patterns
    if "salmon" in animal_lower or "fish" in animal_lower:
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(kg|kilograms|lbs?|pounds)', clean_text, re.I)
        if m:
            if m.group(2):
                return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
            return f"{m.group(1)} {m.group(3)}"
    
    # Turtle - look for kg patterns
    if "turtle" in animal_lower:
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms)', clean_text, re.I)
        if m:
            return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    return ""
