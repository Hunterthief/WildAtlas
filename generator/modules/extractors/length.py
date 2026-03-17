# generator/modules/extractors/length.py
"""
Length extraction module
Extracts length from Wikipedia text with validation
"""
import re
from typing import Dict, Any, Optional


def _is_valid_length(value: str, animal_type: str = "") -> bool:
    """Validate length value makes sense"""
    try:
        match = re.search(r'(\d+(?:[.,]\d+)?)', value)
        if not match:
            return False
        
        num = float(match.group(1).replace(',', ''))
        
        # Reject temporal ranges (Ma = million years)
        if "ma" in value.lower() or "m.y." in value.lower():
            return False
        
        # Reject population numbers
        if num > 10000:  # No animal is 10km+ long
            return False
        
        # Reject very small values
        if num < 0.01:
            return False
        
        return True
    except:
        return False


def _has_length_context(text: str) -> bool:
    """Check if text has length-related context"""
    text_lower = text.lower()
    length_keywords = ['length', 'long', 'measure', 'size', 'body', 'total', 'head-and-body']
    reject_keywords = ['temporal', 'range', 'population', 'individual', 'ma ', 'million years', 'fossil']
    
    has_length = any(kw in text_lower for kw in length_keywords)
    has_reject = any(kw in text_lower for kw in reject_keywords)
    
    return has_length and not has_reject


def _is_temporal_range(text: str) -> bool:
    """Check if value is a temporal range (not length)"""
    text_lower = text.lower()
    return "temporal" in text_lower or "range" in text_lower or "ma" in text_lower


def extract_length_from_sections(sections: Dict[str, str], animal_name: str = "") -> str:
    """Extract length from Wikipedia sections"""
    all_text = " ".join(sections.values())
    
    if not all_text or len(all_text) < 50:
        return ""
    
    # Clean text
    clean_text = re.sub(r'\[\d+\]', '', all_text)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    length_patterns = [
        # "head-and-body length is between 1.1 and 1.5 m"
        r'(?:body|head-and-body|total|overall)?\s*length\s*(?:is|of)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        
        # "100 to 200 cm long"
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)\s*(?:long|in length|length)',
        
        # "average length of 3.18 to 4 m"
        r'average\s*length\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        
        # "reaching 100 cm in length"
        r'reaching?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)\s*(?:in length|long)',
        
        # "grows to 100-200 cm"
        r'grows?\s*(?:to|up to)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        
        # "2.4m - 3.3m" (Tiger format)
        r'(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?)\s*(?:-|–|to)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?)',
    ]
    
    for pattern in length_patterns:
        m = re.search(pattern, clean_text, re.I)
        if m:
            groups = m.groups()
            match_context = clean_text[max(0, m.start()-100):m.end()+100]
            
            # Skip temporal ranges
            if _is_temporal_range(match_context):
                continue
            
            if len(groups) >= 3 and groups[0] and groups[1] and groups[2]:
                candidate = f"{groups[0]}–{groups[1]} {groups[2]}"
                if _is_valid_length(candidate, animal_name) and _has_length_context(m.group(0)):
                    return candidate
            elif len(groups) >= 2 and groups[0] and groups[1]:
                candidate = f"{groups[0]} {groups[1]}"
                if _is_valid_length(candidate, animal_name) and _has_length_context(m.group(0)):
                    return candidate
    
    # Animal-specific fallbacks
    if animal_name:
        name_lower = animal_name.lower()
        
        # Snakes - look for meter length patterns
        if any(x in name_lower for x in ["snake", "cobra", "python"]):
            m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to)\s*(\d+(?:[.,]\d+)?)\s*(m|metres|meters)', clean_text, re.I)
            if m:
                match_context = clean_text[max(0, m.start()-100):m.end()+100]
                if not _is_temporal_range(match_context):
                    return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    return ""
