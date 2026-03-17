# generator/modules/extractors/weight.py
"""
Weight extraction module
Extracts weight from Wikipedia text with validation
"""
import re
from typing import Dict, Any, Optional


def _is_valid_weight(value: str, animal_type: str = "") -> bool:
    """Validate weight value makes sense"""
    try:
        match = re.search(r'(\d+(?:[.,]\d+)?)', value)
        if not match:
            return False
        
        num = float(match.group(1).replace(',', ''))
        
        # Reject impossible values
        if num < 0.001:  # Too small (less than 1 gram)
            return False
        if num > 150000:  # Too large (more than 150 tonnes)
            return False
        
        # Animal-specific validation
        if "elephant" in animal_type.lower():
            if num < 1000:  # Elephants weigh 2000-6000+ kg
                return False
        if "mouse" in animal_type.lower() or "bat" in animal_type.lower():
            if num > 10:  # Small mammals weigh grams
                return False
        
        return True
    except:
        return False


def _has_weight_context(text: str) -> bool:
    """Check if text has weight-related context"""
    text_lower = text.lower()
    weight_keywords = ['weigh', 'weight', 'mass', 'heavy', 'tonne', 'pound', 'kg', 'lb']
    return any(kw in text_lower for kw in weight_keywords)


def _is_tusk_weight(text: str) -> bool:
    """Check if weight is about tusks/ivory (not body weight)"""
    text_lower = text.lower()
    return "tusk" in text_lower or "ivory" in text_lower


def extract_weight_from_sections(sections: Dict[str, str], animal_name: str = "") -> str:
    """Extract weight from Wikipedia sections"""
    all_text = " ".join(sections.values())
    
    if not all_text or len(all_text) < 50:
        return ""
    
    # Clean text
    clean_text = re.sub(r'\[\d+\]', '', all_text)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    weight_patterns = [
        # "weighing from 22 to 45 kg"
        r'weighing\s*(?:from|between|about|around|approximately)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "Adults weigh between 21 and 65 kg"
        r'(?:adults|males|females|species|they|it)?\s*weighs?\s*(?:between|from|about|around)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "weight of 100-200 kg"
        r'weight\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # Single value: "weighs 150 kg"
        r'weighs?\s*(?:about|around|approximately|up to)?\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "140kg - 300kg" (Tiger format)
        r'(\d+(?:[.,]\d+)?)\s*(kg|kilograms?)\s*(?:-|–|to)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?)',
        
        # "ranges from 100 to 200 kg"
        r'ranges?\s*(?:from)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "between 100 and 200 kg"
        r'between\s*(\d+(?:[.,]\d+)?)\s*(?:and|to)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "100–200 kg" (en-dash)
        r'(\d+(?:[.,]\d+)?)\s*[–-]\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
    ]
    
    for pattern in weight_patterns:
        m = re.search(pattern, clean_text, re.I)
        if m:
            groups = m.groups()
            match_context = clean_text[max(0, m.start()-100):m.end()+100]
            
            # Skip if it's about tusks/ivory
            if _is_tusk_weight(match_context):
                continue
            
            if len(groups) >= 3:
                candidate = f"{groups[0]}–{groups[1]} {groups[2]}"
                if _is_valid_weight(candidate, animal_name) and _has_weight_context(m.group(0)):
                    return candidate
            elif len(groups) >= 2:
                candidate = f"{groups[0]} {groups[1]}"
                if _is_valid_weight(candidate, animal_name) and _has_weight_context(m.group(0)):
                    return candidate
    
    # Animal-specific fallbacks
    if animal_name:
        name_lower = animal_name.lower()
        
        # Elephants - look for tonne patterns
        if "elephant" in name_lower:
            m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to)\s*(\d+(?:[.,]\d+)?)\s*(tonnes?|tons)', clean_text, re.I)
            if m:
                match_context = clean_text[max(0, m.start()-100):m.end()+100]
                if not _is_tusk_weight(match_context):
                    return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
        
        # Whales/Sharks - look for tonne patterns
        if any(x in name_lower for x in ["whale", "shark"]):
            m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to)\s*(\d+(?:[.,]\d+)?)\s*(tonnes?|tons|kg|kilograms)', clean_text, re.I)
            if m:
                return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    return ""
