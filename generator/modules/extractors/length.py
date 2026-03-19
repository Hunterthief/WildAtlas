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
        
        # Species-specific max lengths (in meters)
        animal_lower = animal_name.lower() if animal_name else ""
        max_lengths = {
            'turtle': 3.0,  # Green sea turtle max ~1.5m
            'eagle': 1.5,  # Bald eagle ~1m
            'wolf': 2.0,  # Gray wolf ~1.6m
            'salmon': 1.5,  # Atlantic salmon ~1m
            'bee': 0.05,  # Honey bee ~2.5cm
            'butterfly': 0.15,  # Monarch ~10cm
            'frog': 0.3,  # Bullfrog ~20cm
            'cobra': 6.0,  # King cobra ~5.5m
            'shark': 7.0,  # Great white ~6m
            'elephant': 7.0,  # African elephant ~6-7m total
            'penguin': 1.5,  # Emperor ~1.2m
            'cheetah': 2.0,  # Cheetah ~1.5m
            'tiger': 4.0,  # Tiger ~3.3m
        }
        
        for keyword, max_len in max_lengths.items():
            if keyword in animal_lower:
                if num > max_len:
                    return False
                break
        
        # Default max for non-whale/shark animals
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
    # Reject these contexts
    reject_keywords = [
        'nest', 'nests', 'egg', 'tail', 'wingspan', 'wing span',
        'colony', 'hive', 'population', 'temporal', 'range',
        'smolt', 'parr', 'juvenile', 'larva', 'hatchling'
    ]
    # Accept these contexts
    accept_keywords = [
        'body length', 'total length', 'snout-to-vent', 'head-body',
        'measures', 'adult', 'length of'
    ]
    
    has_reject = any(kw in text_lower for kw in reject_keywords)
    has_accept = any(kw in text_lower for kw in accept_keywords)
    
    # Reject if has negative context without positive context
    return has_reject and not has_accept


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
            
            # Skip negative contexts (nests, tails, etc.)
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
    
    # Priority 2: Animal-specific patterns
    animal_lower = animal_name.lower() if animal_name else ""
    
    # Snake specific
    if any(x in animal_lower for x in ["snake", "cobra", "python"]):
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres|meters)', clean_text, re.I)
        if m:
            context = clean_text[max(0, m.start()-150):m.end()+150]
            if not _is_temporal_range(context) and not _has_negative_context(context):
                return f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    # Fish specific
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
