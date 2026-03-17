# generator/modules/extractors/length.py
"""
Length extraction module - IMPROVED
Better filtering of temporal ranges vs actual length
"""
import re
from typing import Dict, Optional


def _is_valid_length(value: str, animal_name: str = "") -> bool:
    """Validate length value makes sense"""
    try:
        # Reject temporal ranges (Ma = million years)
        if "ma" in value.lower() or "m.y." in value.lower() or "million years" in value.lower():
            return False
        
        # Reject "0.21–0 Ma" patterns
        if re.search(r'0\.\d+.*0\s*ma', value.lower()):
            return False
        
        match = re.search(r'(\d+(?:[.,]\d+)?)', value)
        if not match:
            return False
        
        num = float(match.group(1).replace(',', ''))
        
        # Reject impossible lengths
        if num < 0.001:  # Too small
            return False
        if num > 50:  # No animal is 50m+ (except whales)
            animal_lower = animal_name.lower() if animal_name else ""
            if "whale" not in animal_lower and "shark" not in animal_lower:
                return False
        
        return True
    except:
        return False


def _is_temporal_range(text: str) -> bool:
    """Check if value is a temporal range (not length)"""
    text_lower = text.lower()
    temporal_keywords = [
        "temporal range", "ma ", "million years", "mya", 
        "pleistocene", "miocene", "pilocene", "fossil",
        "0.21–0", "7–0", "5–0"
    ]
    return any(kw in text_lower for kw in temporal_keywords)


def extract_length_from_sections(sections: Dict[str, str], animal_name: str = "") -> str:
    """Extract length from Wikipedia sections"""
    all_text = " ".join(sections.values())
    
    if not all_text or len(all_text) < 50:
        return ""
    
    # Clean text
    clean_text = re.sub(r'\[\d+\]', '', all_text)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    # Priority 1: Direct length patterns with context
    length_patterns = [
        # "length of X to Y m"
        r'(?:body|head-and-body|total|overall|snout-to-vent)?\s*length\s*(?:of|is|ranges from|between)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        
        # "X to Y meters long"
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)\s*(?:long|in length|length)',
        
        # "grows to X-Y m"
        r'grows?\s*(?:to|up to|reaching)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        
        # "average length of X to Y m"
        r'average\s*length\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        
        # "reaching X m in length"
        r'reaching?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)\s*(?:in length|long)',
        
        # "X–Y m" (en-dash) with length context
        r'(?:length|long|measures)\s*(\d+(?:[.,]\d+)?)\s*[–-]\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet)',
        
        # "up to X m"
        r'(?:up to|reaching|grows to)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        
        # Snake specific - "average length of X to Y m"
        r'(?:snake|cobra|python|serpent)\s*(?:average)?\s*length\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?)',
    ]
    
    for pattern in length_patterns:
        m = re.search(pattern, clean_text, re.I)
        if m:
            groups = m.groups()
            match_context = clean_text[max(0, m.start()-150):m.end()+150]
            
            # Skip temporal ranges
            if _is_temporal_range(match_context):
                continue
            
            if len(groups) >= 3 and groups[0] and groups[1] and groups[2]:
                candidate = f"{groups[0]}–{groups[1]} {groups[2]}"
                if _is_valid_length(candidate, animal_name):
                    return candidate
            elif len(groups) >= 2 and groups[0] and groups[1]:
                candidate = f"{groups[0]} {groups[1]}"
                if _is_valid_length(candidate, animal_name):
                    return candidate
    
    # Priority 2: Animal-specific patterns
    animal_lower = animal_name.lower() if animal_name else ""
    
    # Snake specific
    if any(x in animal_lower for x in ["snake", "cobra", "python"]):
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres|meters)', clean_text,
