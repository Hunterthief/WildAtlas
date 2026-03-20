"""
Length extraction module - IMPROVED
Better filtering of temporal ranges vs actual length
"""
import re
from typing import Dict, Optional


def _is_valid_length(value: str, animal_name: str = "") -> bool:
    """Validate length value makes sense"""
    try:
        if "ma" in value.lower() or "m.y." in value.lower() or "million years" in value.lower():
            return False
        
        if re.search(r'0\.\d+.*0\s*ma', value.lower()):
            return False
        
        match = re.search(r'(\d+(?:[.,]\d+)?)', value)
        if not match:
            return False
        
        num = float(match.group(1).replace(',', ''))
        
        if num < 0.001:
            return False
        
        # FIXED: Species-specific max lengths
        animal_lower = animal_name.lower() if animal_name else ""
        max_lengths = {
            'turtle': 3.0,
            'tortoise': 1.5,
            'eagle': 1.5,
            'bee': 0.05,
            'butterfly': 0.15,
            'frog': 0.3,
            'salmon': 1.5,
            'shark': 7.0,
            'cobra': 6.0,
            'penguin': 1.5,
            'elephant': 7.5,
            'wolf': 2.0,
        }
        
        for keyword, max_len in max_lengths.items():
            if keyword in animal_lower:
                if num > max_len * 10:
                    return False
                break
        
        if num > 50:
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


def _has_negative_context(text: str) -> bool:
    """Check if length is about wrong body part or object"""
    text_lower = text.lower()
    reject_keywords = [
        'nest', 'nests', 'egg', 'tail', 'wingspan', 'wing span',
        'colony', 'hive', 'population', 'temporal', 'range',
        'smolt', 'parr', 'juvenile', 'larva', 'hatchling'
    ]
    accept_keywords = [
        'body length', 'total length', 'snout-to-vent', 'head-body',
        'measures', 'adult', 'length of'
    ]
    
    has_reject = any(kw in text_lower for kw in reject_keywords)
    has_accept = any(kw in text_lower for kw in accept_keywords)
    
    return has_reject and not has_accept


def extract_length_from_sections(sections: Dict[str, str], animal_name: str = "") -> str:
    """Extract length from Wikipedia sections"""
    all_text = " ".join(sections.values())
    
    if not all_text or len(all_text) < 50:
        return ""
    
    clean_text = re.sub(r'\[\d+\]', '', all_text)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    length_patterns = [
        r'(?:body|head-and-body|total|overall|snout-to-vent)?\s*length\s*(?:of|is|ranges from|between)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)\s*(?:long|in length|length)',
        r'grows?\s*(?:to|up to|reaching)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        r'average\s*length\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        r'reaching?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)\s*(?:in length|long)',
        r'(?:length|long|measures)\s*(\d+(?:[.,]\d+)?)\s*[–-]\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet)',
        r'(?:up to|reaching|grows to)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
    ]
    
    for pattern in length_patterns:
        m = re.search(pattern, clean_text, re.I)
        if m:
            groups = m.groups()
            match_context = clean_text[max(0, m.start()-150):m.end()+150]
            
            if _is_temporal_range(match_context):
                continue
            
            if _has_negative_context(match_context):
                continue
            
            if len(groups) >= 3 and groups[0] and groups[1] and groups[2]:
                candidate = f"{groups[0]}–{groups[1]} {groups[2]}"
                if _is_valid_length(candidate, animal_name):
                    return candidate
            elif len(groups) >= 2 and groups[0] and groups[1]:
                candidate = f"{groups[0]} {groups[1]}"
                if _is_valid_length(candidate, animal_name):
                    return candidate
    
    animal_lower = animal_name.lower() if animal_name else ""
    
    if any(x in animal_lower for x in ["snake", "cobra", "python"]):
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres|meters)', clean_text, re.I)
        if m:
            context = clean_text[max(0, m.start()-150):m.end()+150]
            if not _is_temporal_range(context) and not _has_negative_context(context):
                return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    if any(x in animal_lower for x in ["salmon", "shark", "fish"]):
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(m|metres|meters|cm)\s*(?:long|length)', clean_text, re.I)
        if m:
            context = clean_text[max(0, m.start()-150):m.end()+150]
            if not _is_temporal_range(context) and not _has_negative_context(context):
                if m.group(2):
                    return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
                else:
                    return f"{m.group(1)} {m.group(3)}"
    
    return ""
