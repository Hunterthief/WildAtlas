# generator/modules/extractors/stats.py
"""
Physical stats extraction module - FIXED
Extracts weight, length, height, lifespan, speed from Wikipedia text
With validation to reject impossible values
"""
import re
from typing import Dict, Any, List, Tuple, Optional


def _is_valid_weight(value: str, animal_type: str = "") -> bool:
    """Validate weight value makes sense"""
    try:
        # Extract numeric value
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


def _is_valid_length(value: str, animal_type: str = "") -> bool:
    """Validate length value makes sense"""
    try:
        # Extract numeric value
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
        
        # Reject very small values (likely not length)
        if num < 0.01:
            return False
        
        return True
    except:
        return False


def _is_valid_height(value: str, animal_type: str = "") -> bool:
    """Validate height value makes sense"""
    try:
        # Extract numeric value
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


def _is_valid_lifespan(value: str) -> bool:
    """Validate lifespan value makes sense"""
    try:
        # Extract numeric value
        match = re.search(r'(\d+(?:\s*[-–]\s*\d+)?)', value)
        if not match:
            return False
        
        # Check for reasonable year values
        if "years" not in value.lower() and "yrs" not in value.lower():
            return False
        
        return True
    except:
        return False


def _is_valid_speed(value: str) -> bool:
    """Validate speed value makes sense"""
    try:
        # Extract numeric value
        match = re.search(r'(\d+(?:[.,]\d+)?)', value)
        if not match:
            return False
        
        num = float(match.group(1).replace(',', ''))
        
        # Reject impossible speeds
        if num < 0.1:  # Too slow
            return False
        if num > 1000:  # Too fast (nothing goes 1000+ km/h)
            return False
        
        # Must have speed units
        if not any(unit in value.lower() for unit in ['km/h', 'mph', 'kph', 'mi/h']):
            return False
        
        return True
    except:
        return False


def _has_stat_context(text: str, stat_type: str) -> bool:
    """Check if text has appropriate context for stat type"""
    text_lower = text.lower()
    
    if stat_type == "weight":
        # Must have weight-related keywords nearby
        weight_keywords = ['weigh', 'weight', 'mass', 'heavy', 'tonne', 'pound', 'kg', 'lb']
        return any(kw in text_lower for kw in weight_keywords)
    
    elif stat_type == "length":
        # Must have length-related keywords, NOT temporal/population
        length_keywords = ['length', 'long', 'measure', 'size', 'body', 'total', 'head-and-body']
        reject_keywords = ['temporal', 'range', 'population', 'individual', 'ma ', 'million years', 'fossil']
        
        has_length = any(kw in text_lower for kw in length_keywords)
        has_reject = any(kw in text_lower for kw in reject_keywords)
        
        return has_length and not has_reject
    
    elif stat_type == "height":
        # Must have height-related keywords
        height_keywords = ['height', 'tall', 'shoulder', 'stand', 'at the']
        reject_keywords = ['temporal', 'range', 'population', 'ma ', 'million years']
        
        has_height = any(kw in text_lower for kw in height_keywords)
        has_reject = any(kw in text_lower for kw in reject_keywords)
        
        return has_height and not has_reject
    
    elif stat_type == "lifespan":
        # Must have lifespan-related keywords
        lifespan_keywords = ['lifespan', 'life', 'years', 'live', 'longevity', 'age', 'expectancy']
        return any(kw in text_lower for kw in lifespan_keywords)
    
    elif stat_type == "speed":
        # Must have speed-related keywords
        speed_keywords = ['speed', 'fast', 'run', 'swim', 'fly', 'km/h', 'mph', 'kph', 'sprint']
        return any(kw in text_lower for kw in speed_keywords)
    
    return True


def extract_stats_from_sections(sections: Dict[str, str], animal_name: str = "") -> Dict[str, str]:
    """Extract weight, length, height, lifespan, speed from sections"""
    stats = {
        "weight": "",
        "length": "",
        "height": "",
        "lifespan": "",
        "top_speed": ""
    }
    
    # Combine all section text
    all_text = " ".join(sections.values())
    
    if not all_text or len(all_text) < 50:
        return stats
    
    # Clean text for better matching
    clean_text = re.sub(r'\[\d+\]', '', all_text)  # Remove citations
    clean_text = re.sub(r'\s+', ' ', clean_text)  # Normalize whitespace
    
    # =============================================================================
    # WEIGHT EXTRACTION - With validation
    # =============================================================================
    weight_patterns = [
        # "weighing from 22 to 45 kg" (Emperor Penguin)
        r'weighing\s*(?:from|between|about|around|approximately)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "Adults weigh between 21 and 65 kg" (Cheetah)
        r'(?:adults|males|females|species|they|it)?\s*weighs?\s*(?:between|from|about|around)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "weight of 100-200 kg"
        r'weight\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # Single value: "weighs 150 kg"
        r'weighs?\s*(?:about|around|approximately|up to)?\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "140kg - 300kg (309lbs - 660lbs)" (Tiger format)
        r'(\d+(?:[.,]\d+)?)\s*(kg|kilograms?)\s*(?:-|–|to)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?)',
        
        # "ranges from 100 to 200 kg"
        r'ranges?\s*(?:from)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "between 100 and 200 kg"
        r'between\s*(\d+(?:[.,]\d+)?)\s*(?:and|to)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "100–200 kg" (en-dash without spaces)
        r'(\d+(?:[.,]\d+)?)\s*[–-]\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
    ]
    
    for pattern in weight_patterns:
        m = re.search(pattern, clean_text, re.I)
        if m:
            groups = m.groups()
            if len(groups) >= 3:
                candidate = f"{groups[0]}–{groups[1]} {groups[2]}"
                if _is_valid_weight(candidate, animal_name) and _has_stat_context(m.group(0), "weight"):
                    # Additional check: reject if near "tusk" or "ivory"
                    match_context = clean_text[max(0, m.start()-100):m.end()+100]
                    if "tusk" not in match_context.lower() and "ivory" not in match_context.lower():
                        stats["weight"] = candidate
                        break
            elif len(groups) >= 2:
                candidate = f"{groups[0]} {groups[1]}"
                if _is_valid_weight(candidate, animal_name) and _has_stat_context(m.group(0), "weight"):
                    match_context = clean_text[max(0, m.start()-100):m.end()+100]
                    if "tusk" not in match_context.lower() and "ivory" not in match_context.lower():
                        stats["weight"] = candidate
                        break
    
    # =============================================================================
    # LENGTH EXTRACTION - With validation
    # =============================================================================
    length_patterns = [
        # "head-and-body length is between 1.1 and 1.5 m" (Cheetah)
        r'(?:body|head-and-body|total|overall)?\s*length\s*(?:is|of)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        
        # "100 to 200 cm long"
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)\s*(?:long|in length|length)',
        
        # "average length of 3.18 to 4 m" (King Cobra)
        r'average\s*length\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        
        # "reaching 100 cm in length"
        r'reaching?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)\s*(?:in length|long)',
        
        # "grows to 100-200 cm"
        r'grows?\s*(?:to|up to)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        
        # "2.4m - 3.3m (6.8ft - 11ft)" (Tiger format)
        r'(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?)\s*(?:-|–|to)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?)',
    ]
    
    for pattern in length_patterns:
        m = re.search(pattern, clean_text, re.I)
        if m:
            groups = m.groups()
            if len(groups) >= 3 and groups[0] and groups[1] and groups[2]:
                candidate = f"{groups[0]}–{groups[1]} {groups[2]}"
                if _is_valid_length(candidate, animal_name) and _has_stat_context(m.group(0), "length"):
                    # Reject temporal ranges
                    match_context = clean_text[max(0, m.start()-100):m.end()+100]
                    if "temporal" not in match_context.lower() and "range" not in match_context.lower() and "ma" not in match_context.lower():
                        stats["length"] = candidate
                        break
            elif len(groups) >= 2 and groups[0] and groups[1]:
                candidate = f"{groups[0]} {groups[1]}"
                if _is_valid_length(candidate, animal_name) and _has_stat_context(m.group(0), "length"):
                    match_context = clean_text[max(0, m.start()-100):m.end()+100]
                    if "temporal" not in match_context.lower() and "range" not in match_context.lower() and "ma" not in match_context.lower():
                        stats["length"] = candidate
                        break
    
    # =============================================================================
    # HEIGHT EXTRACTION - With validation
    # =============================================================================
    height_patterns = [
        # "reaches 67–94 cm at the shoulder" (Cheetah)
        r'reaches?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)\s*(?:at the shoulder|shoulder height|at shoulder)',
        
        # "stands 100 to 200 cm tall at the shoulder"
        r'stands?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)\s*(?:tall|at the shoulder|shoulder height)',
        
        # "shoulder height of 100-200 cm"
        r'shoulder\s*height\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        
        # "28-38 inches" (Bald Eagle)
        r'(\d+(?:[.,]\d+)?)\s*(?:-|–|to)\s*(\d+(?:[.,]\d+)?)\s*(in|inches|ft|feet)\s*(?:tall|height|long)?',
        
        # "100cm - 120cm (39in - 47in)" (Emperor Penguin format)
        r'(\d+(?:[.,]\d+)?)\s*(cm|m)\s*(?:-|–|to)\s*(\d+(?:[.,]\d+)?)\s*(cm|m|in|ft)',
    ]
    
    for pattern in height_patterns:
        m = re.search(pattern, clean_text, re.I)
        if m:
            groups = m.groups()
            if len(groups) >= 3 and groups[0] and groups[1] and groups[2]:
                candidate = f"{groups[0]}–{groups[1]} {groups[2]}"
                if _is_valid_height(candidate, animal_name) and _has_stat_context(m.group(0), "height"):
                    # Reject temporal ranges
                    match_context = clean_text[max(0, m.start()-100):m.end()+100]
                    if "temporal" not in match_context.lower() and "range" not in match_context.lower():
                        stats["height"] = candidate
                        break
            elif len(groups) >= 2 and groups[0] and groups[1]:
                candidate = f"{groups[0]} {groups[1]}"
                if _is_valid_height(candidate, animal_name) and _has_stat_context(m.group(0), "height"):
                    match_context = clean_text[max(0, m.start()-100):m.end()+100]
                    if "temporal" not in match_context.lower() and "range" not in match_context.lower():
                        stats["height"] = candidate
                        break
    
    # =============================================================================
    # LIFESPAN EXTRACTION - With validation
    # =============================================================================
    lifespan_patterns = [
        # "lifespan of 10 to 20 years"
        r'lifespan\s*(?:of|is)?\s*(?:typically|usually|about|around)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)',
        
        # "15-20 years in the wild" (Bald Eagle)
        r'(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)\s*(?:in the wild|in captivity|typically|usually|average)',
        
        # "can live up to 20 years"
        r'(?:can\s*)?live[s]?\s*(?:up to|about|around)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)',
        
        # "typically 20 years"
        r'typically\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)',
        
        # "20 years" near lifespan context
        r'(?:lifespan|life|live|longevity)\s*(?:of|is)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)',
    ]
    
    for pattern in lifespan_patterns:
        m = re.search(pattern, clean_text, re.I)
        if m:
            groups = m.groups()
            if len(groups) >= 2:
                candidate = f"{groups[0]} {groups[1]}"
                if _is_valid_lifespan(candidate) and _has_stat_context(m.group(0), "lifespan"):
                    stats["lifespan"] = candidate
                    break
    
    # =============================================================================
    # SPEED EXTRACTION - With validation
    # =============================================================================
    speed_patterns = [
        # "capable of running at 93 to 104 km/h" (Cheetah)
        r'capable\s*of\s*(?:running|swimming|flying)?\s*(?:at)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(km/h|kmph|kph|mph|mi/h)',
        
        # "can run at 100 km/h"
        r'can\s*(?:run|swim|fly|sprint)\s*(?:at|up to)?\s*(\d+(?:[.,]\d+)?)\s*(km/h|kmph|kph|mph|mi/h)',
        
        # "speed of 100 km/h"
        r'speed\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(km/h|kmph|kph|mph|mi/h)',
        
        # "60 mph" (Tiger format - single value)
        r'(\d+(?:[.,]\d+)?)\s*(mph|km/h|kmph|kph)',
        
        # "reaches speeds of 100 km/h"
        r'reaches?\s*(?:speeds? of|up to)?\s*(\d+(?:[.,]\d+)?)\s*(km/h|kmph|kph|mph|mi/h)',
    ]
    
    for pattern in speed_patterns:
        m = re.search(pattern, clean_text, re.I)
        if m:
            groups = m.groups()
            if len(groups) >= 2 and groups[0] and groups[1]:
                if len(groups) >= 3 and groups[1]:
                    candidate = f"{groups[0]}–{groups[1]} {groups[2]}"
                else:
                    candidate = f"{groups[0]} {groups[1]}"
                if _is_valid_speed(candidate) and _has_stat_context(m.group(0), "speed"):
                    stats["top_speed"] = candidate
                    break
    
    return stats


def extract_stats_with_context(sections: Dict[str, str], animal_name: str = "", scientific_name: str = "") -> Dict[str, str]:
    """
    Enhanced extraction with animal-specific context and fallbacks
    """
    stats = extract_stats_from_sections(sections, animal_name)
    
    # Combine all text for context-aware extraction
    all_text = " ".join(sections.values())
    all_text = re.sub(r'\[\d+\]', '', all_text)
    
    # Animal-specific fallbacks for large animals
    if animal_name:
        name_lower = animal_name.lower()
        
        # Elephants - look for tonne patterns (body weight, not tusks)
        if "elephant" in name_lower and not stats["weight"]:
            m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to)\s*(\d+(?:[.,]\d+)?)\s*(tonnes?|tons)', all_text, re.I)
            if m:
                # Verify it's not about tusks
                match_context = all_text[max(0, m.start()-100):m.end()+100]
                if "tusk" not in match_context.lower() and "ivory" not in match_context.lower():
                    stats["weight"] = f"{m.group(1)}–{m.group(2)} {m.group(3)}"
        
        # Whales/Sharks - look for tonne patterns
        if any(x in name_lower for x in ["whale", "shark"]) and not stats["weight"]:
            m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to)\s*(\d+(?:[.,]\d+)?)\s*(tonnes?|tons|kg|kilograms)', all_text, re.I)
            if m:
                stats["weight"] = f"{m.group(1)}–{m.group(2)} {m.group(3)}"
        
        # Snakes - look for meter length patterns
        if any(x in name_lower for x in ["snake", "cobra", "python"]) and not stats["length"]:
            m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to)\s*(\d+(?:[.,]\d+)?)\s*(m|metres|meters)', all_text, re.I)
            if m:
                # Verify it's not temporal range
                match_context = all_text[max(0, m.start()-100):m.end()+100]
                if "temporal" not in match_context.lower() and "range" not in match_context.lower():
                    stats["length"] = f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    return stats
