# generator/modules/extractors/weight.py
"""
Weight extraction module - IMPROVED
Better patterns for elephants, wolves, fish, etc.
"""
import re
from typing import Dict, Optional


def _is_valid_weight(value: str, animal_name: str = "") -> bool:
    """Validate weight value makes sense for animal type"""
    try:
        match = re.search(r'(\d+(?:[.,]\d+)?)', value)
        if not match:
            return False
        
        num = float(match.group(1).replace(',', ''))
        
        # Reject impossible values
        if num < 0.001:  # Too small
            return False
        
        # Animal-specific validation
        animal_lower = animal_name.lower() if animal_name else ""
        
        # Elephants should be 1000+ kg (not tusk weight 23-45kg)
        if "elephant" in animal_lower and num < 500:
            return False
        
        # Wolves should be 20-100kg range
        if "wolf" in animal_lower and (num < 10 or num > 150):
            return False
        
        # Bees should be in grams (0.01-1g)
        if "bee" in animal_lower and num > 10:
            return False
        
        # Butterflies should be in grams (0.1-3g)
        if "butterfly" in animal_lower and num > 10:
            return False
        
        # Frogs should be 0.1-2kg
        if "frog" in animal_lower and num > 5:
            return False
        
        # Sharks can be 500-3000kg
        if "shark" in animal_lower and num < 100:
            return False
        
        # Turtles can be 50-500kg
        if "turtle" in animal_lower and num < 10:
            return False
        
        # Salmon should be 2-50kg
        if "salmon" in animal_lower and (num < 0.5 or num > 100):
            return False
        
        return True
    except:
        return False


def _is_tusk_weight(text: str) -> bool:
    """Check if weight is about tusks/ivory (not body weight)"""
    text_lower = text.lower()
    return "tusk" in text_lower or "ivory" in text_lower


def _is_population_number(text: str) -> bool:
    """Check if number is population (not weight)"""
    text_lower = text.lower()
    pop_keywords = [
        "individual", "population", "estimated", "wild", 
        "between 200,000", "between 250,000"
    ]
    return any(kw in text_lower for kw in pop_keywords)


def extract_weight_from_sections(sections: Dict[str, str], animal_name: str = "") -> str:
    """Extract weight from Wikipedia sections"""
    all_text = " ".join(sections.values())
    
    if not all_text or len(all_text) < 50:
        return ""
    
    # Clean text
    clean_text = re.sub(r'\[\d+\]', '', all_text)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    # Priority 1: Direct weight patterns with context
    weight_patterns = [
        # "weighs between X and Y kg" (Wolf, Elephant)
        r'(?:adults?|males?|females?|species|it|they|average)?\s*weighs?\s*(?:between|from|about|around|up to|typically)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g)',
        
        # "weight of X to Y kg"
        r'weight\s*(?:of|is|ranges from)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "X to Y kilograms" with weight context nearby
        r'(?:weighing|weight|weighs|mass|heavy|weighed)\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "ranges from X to Y kg"
        r'ranges?\s*(?:from)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "X–Y kg" (en-dash)
        r'(\d+(?:[.,]\d+)?)\s*[–-]\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "up to X kg"
        r'(?:weighs?|weight|up to|reaching)\s*(?:up to|about)?\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "X kg" single value with context
        r'(?:weighs?|weight|about|around|approximately)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "tonnes" for large animals (elephants, sharks)
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(tonnes?|tons?|t)',
        
        # "X lbs" imperial
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(lbs?|pounds)',
    ]
    
    for pattern in weight_patterns:
        m = re.search(pattern, clean_text, re.I)
        if m:
            groups = m.groups()
            match_context = clean_text[max(0, m.start()-150):m.end()+150]
            
            # Skip tusk weight
            if _is_tusk_weight(match_context):
                continue
            
            # Skip population numbers
            if _is_population_number(match_context):
                continue
            
            if len(groups) >= 3:
                candidate = f"{groups[0]}–{groups[1]} {groups[2]}"
                if _is_valid_weight(candidate, animal_name):
                    return candidate
            elif len(groups) >= 2:
                candidate = f"{groups[0]} {groups[1]}"
                if _is_valid_weight(candidate, animal_name):
                    return candidate
    
    # Priority 2: Look for specific animal patterns
    animal_lower = animal_name.lower() if animal_name else ""
    
    # Elephant specific - look for tonne patterns
    if "elephant" in animal_lower:
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(tonnes?|tons)', clean_text, re.I)
        if m:
            context = clean_text[max(0, m.start()-150):m.end()+150]
            if not _is_tusk_weight(context):
                return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    # Wolf specific - look for kg patterns
    if "wolf" in animal_lower:
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms)', clean_text, re.I)
        if m:
            context = clean_text[max(0, m.start()-150):m.end()+150]
            if not _is_population_number(context):
                return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    return ""
