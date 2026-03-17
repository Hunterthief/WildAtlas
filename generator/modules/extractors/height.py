# generator/modules/extractors/height.py
"""
Height extraction module
Extracts height from Wikipedia text with validation
"""
import re
from typing import Dict, Any, Optional


def _is_valid_height(value: str, animal_type: str = "") -> bool:
    """Validate height value makes sense"""
    try:
        match = re.search(r'(\d+(?:[.,]\d+)?)', value)
        if not match:
            return False
        
        num = float(match.group(1).replace(',', ''))
        
        # Reject temporal ranges
        if "ma" in value.lower() or "m.y." in value.lower():
            return False
        
        # Reject population numbers
        if num > 10000:
            return False
        
        # Reject very small values
        if num < 0.01:
            return False
        
        return True
    except:
        return False


def _has_height_context(text: str) -> bool:
    """Check if text has height-related context"""
    text_lower = text.lower()
    height_keywords = ['height', 'tall', 'shoulder', 'stand', 'at the']
    reject_keywords = ['temporal', 'range', 'population', 'ma ', 'million years']
    
    has_height = any(kw in text_lower for kw in height_keywords)
    has_reject = any(kw in text_lower for kw in reject_keywords)
    
    return has_height and not has_reject


def _is_temporal_range(text: str) -> bool:
    """Check if value is a temporal range (not height)"""
    text_lower = text.lower()
    return "temporal" in text_lower or "range" in text_lower


def extract_height_from_sections(sections: Dict[str, str], animal_name: str = "") -> str:
    """Extract height from Wikipedia sections"""
    all_text = " ".join(sections.values())
    
    if not all_text or len(all_text) < 50:
        return ""
    
    # Clean text
    clean_text = re.sub(r'\[\d+\]', '', all_text)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    height_patterns = [
        # "reaches 67–94 cm at the shoulder"
        r'reaches?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)\s*(?:at the shoulder|shoulder height|at shoulder)',
        
        # "stands 100 to 200 cm tall at the shoulder"
        r'stands?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)\s*(?:tall|at the shoulder|shoulder height)',
        
        # "shoulder height of 100-200 cm"
        r'shoulder\s*height\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        
        # "28-38 inches" (Bald Eagle)
        r'(\d+(?:[.,]\d+)?)\s*(?:-|–|to)\s*(\d+(?:[.,]\d+)?)\s*(in|inches|ft|feet)\s*(?:tall|height|long)?',
        
        # "100cm - 120cm" (Emperor Penguin format)
        r'(\d+(?:[.,]\d+)?)\s*(cm|m)\s*(?:-|–|to)\s*(\d+(?:[.,]\d+)?)\s*(cm|m|in|ft)',
    ]
    
    for pattern in height_patterns:
        m = re.search(pattern, clean_text, re.I)
        if m:
            groups = m.groups()
            match_context = clean_text[max(0, m.start()-100):m.end()+100]
            
            # Skip temporal ranges
            if _is_temporal_range(match_context):
                continue
            
            if len(groups) >= 3 and groups[0] and groups[1] and groups[2]:
                candidate = f"{groups[0]}–{groups[1]} {groups[2]}"
                if _is_valid_height(candidate, animal_name) and _has_height_context(m.group(0)):
                    return candidate
            elif len(groups) >= 2 and groups[0] and groups[1]:
                candidate = f"{groups[0]} {groups[1]}"
                if _is_valid_height(candidate, animal_name) and _has_height_context(m.group(0)):
                    return candidate
    
    return ""
