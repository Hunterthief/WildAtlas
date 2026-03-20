"""
Height extraction module - FIXED
Based on analysis of 13 animal Wikipedia articles
"""
import re
from typing import Dict, Any, Optional


def _is_valid_height(value: str, animal_name: str = "") -> bool:
    """Validate height value makes sense"""
    try:
        # Extract all numbers from value
        numbers = re.findall(r'(\d+(?:[.,]?\d+)?)', value)
        if not numbers:
            return False
        
        # Get the largest number (likely the max height)
        max_num = max(float(n.replace(',', '').replace('.', '')) for n in numbers if n)
        
        # Reject temporal ranges
        value_lower = value.lower()
        if "ma" in value_lower or "million years" in value_lower or "temporal" in value_lower:
            return False
        
        # Reject population numbers (too large)
        if max_num > 10000:
            return False
        
        # Reject very small values (likely not height)
        if max_num < 0.1:
            return False
        
        return True
    except:
        return False


def _has_height_context(text: str) -> bool:
    """Check if text has height-related context"""
    text_lower = text.lower()
    
    # Positive indicators
    height_keywords = [
        'height', 'tall', 'shoulder', 'stand', 'standing', 'measures',
        'at the shoulder', 'shoulder height', 'body length', 'total length'
    ]
    
    # Negative indicators (reject these)
    reject_keywords = [
        'temporal', 'range:', 'population', 'million years', 'ma ',
        'nest height', 'colony', 'elevation', 'altitude'
    ]
    
    has_height = any(kw in text_lower for kw in height_keywords)
    has_reject = any(kw in text_lower for kw in reject_keywords)
    
    return has_height and not has_reject


def extract_height_from_sections(sections: Dict[str, str], animal_name: str = "") -> str:
    """Extract height from Wikipedia sections"""
    
    # Priority sections for height data (based on log analysis)
    priority_sections = [
        'description',
        'characteristics', 
        'size',
        'anatomy',
        'appearance',
        'appearance_and_anatomy',
        'physical_description'
    ]
    
    # First, search priority sections
    for section_name in priority_sections:
        if section_name in sections and sections[section_name]:
            text = sections[section_name]
            result = _extract_height_from_text(text, animal_name)
            if result:
                return result
    
    # If not found, search all sections
    all_text = " ".join(sections.values())
    return _extract_height_from_text(all_text, animal_name)


def _extract_height_from_text(text: str, animal_name: str = "") -> str:
    """Extract height from text content"""
    
    if not text or len(text) < 50:
        return ""
    
    # Clean text
    clean_text = re.sub(r'\[\d+\]', '', text)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    # Get context window for validation
    text_lower = clean_text.lower()
    
    # IMPROVED: More flexible patterns based on actual Wikipedia formats
    height_patterns = [
        # Pattern 1: "reaches X–Y cm at the shoulder" (Tiger, Wolf format)
        r'reaches?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft|inches|in)\s*(?:at the shoulder|shoulder height|tall)?',
        
        # Pattern 2: "stands X to Y meters tall" (Elephant format)
        r'stands?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft|inches|in)\s*(?:tall|at the shoulder)?',
        
        # Pattern 3: "X–Y cm (A–B in) tall" (Common format)
        r'(\d+(?:[.,]\d+)?)\s*(cm|m)\s*(?:–|-)\s*(\d+(?:[.,]\d+)?)\s*(cm|m|in|ft)\s*(?:tall|height|standing|long)?',
        
        # Pattern 4: "measuring X to Y" (General format)
        r'measur(?:ing|es)\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft|inches|in)',
        
        # Pattern 5: "shoulder height of X–Y" (Explicit)
        r'shoulder\s*height\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft|inches|in)',
        
        # Pattern 6: "X cm tall" (Single value)
        r'(\d+(?:[.,]\d+)?)\s*(cm|m|feet|ft|inches|in)\s*(?:tall|height|standing)',
        
        # Pattern 7: "up to X meters" (Max height)
        r'up\s*to\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft|inches|in)\s*(?:tall|height)?',
        
        # Pattern 8: "between X and Y" (Range format)
        r'between\s*(\d+(?:[.,]\d+)?)\s*(?:and|-|–)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft|inches|in)\s*(?:tall|height)?',
    ]
    
    for pattern in height_patterns:
        matches = re.finditer(pattern, clean_text, re.I)
        for m in matches:
            groups = m.groups()
            
            # Get context around match for validation
            start = max(0, m.start() - 100)
            end = min(len(clean_text), m.end() + 100)
            match_context = clean_text[start:end]
            
            # Skip if context suggests this is NOT height
            if not _has_height_context(match_context):
                continue
            
            # Skip temporal ranges
            if "temporal" in match_context.lower() or "million years" in match_context.lower():
                continue
            
            # Build result based on groups
            if len(groups) >= 3 and groups[0] and groups[2]:
                # Has range: X–Y unit
                candidate = f"{groups[0]}–{groups[1]} {groups[2]}" if groups[1] else f"{groups[0]} {groups[2]}"
            elif len(groups) >= 2 and groups[0] and groups[1]:
                # Single value: X unit
                candidate = f"{groups[0]} {groups[1]}"
            else:
                continue
            
            # Validate and return
            if _is_valid_height(candidate, animal_name):
                return candidate
    
    return ""
