# generator/modules/extractors/stats.py
"""Physical stats extraction module - IMPROVED"""
import re
from typing import Dict, str, Any


def extract_stats_from_sections(sections: Dict[str, str]) -> Dict[str, str]:
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
    # WEIGHT EXTRACTION
    # =============================================================================
    weight_patterns = [
        # "weighs 100 to 200 kg"
        r'weighs?\s*(?:between|about|around|approximately|up to)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|t|lbs?|pounds|grams?)',
        # "weight of 100-200 kg"
        r'weight\s*(?:of)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|t|lbs?|pounds|grams?)',
        # "100 to 200 kilograms in weight"
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|t|lbs?|pounds|grams?)\s*(?:in weight|weight|heavy)',
        # "mass of 100-200 kg"
        r'mass\s*(?:of)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|t|lbs?|pounds|grams?)',
        # Single value: "weighs 150 kg"
        r'weighs?\s*(?:about|around|approximately)?\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|t|lbs?|pounds|grams?)',
    ]
    
    for pattern in weight_patterns:
        m = re.search(pattern, clean_text, re.I)
        if m:
            if len(m.groups()) >= 3:
                stats["weight"] = f"{m.group(1)}–{m.group(2)} {m.group(3)}"
            else:
                stats["weight"] = f"{m.group(1)} {m.group(2)}"
            break
    
    # =============================================================================
    # LENGTH EXTRACTION
    # =============================================================================
    length_patterns = [
        # "100 to 200 cm long"
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)\s*(?:long|length|in length|body length|total length)',
        # "length of 100-200 cm"
        r'length\s*(?:of)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        # "grows to 100-200 cm"
        r'grows?\s*(?:to|up to)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        # "measures 100-200 cm"
        r'measures?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        # Single value: "100 cm long"
        r'(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)\s*(?:long|length)',
    ]
    
    for pattern in length_patterns:
        m = re.search(pattern, clean_text, re.I)
        if m:
            if len(m.groups()) >= 3:
                stats["length"] = f"{m.group(1)}–{m.group(2)} {m.group(3)}"
            else:
                stats["length"] = f"{m.group(1)} {m.group(2)}"
            break
    
    # =============================================================================
    # HEIGHT EXTRACTION
    # =============================================================================
    height_patterns = [
        # "stands 100 to 200 cm tall at the shoulder"
        r'stands?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)\s*(?:tall|height|at the shoulder|shoulder height)',
        # "shoulder height of 100-200 cm"
        r'shoulder\s*height\s*(?:of)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        # "height at shoulder 100-200 cm"
        r'height\s*(?:at\s*)?(?:the\s*)?shoulder\s*(?:of)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        # "100 to 200 cm at the shoulder"
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)\s*(?:at the shoulder|shoulder)',
        # Single value: "100 cm tall"
        r'(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)\s*(?:tall|height)',
    ]
    
    for pattern in height_patterns:
        m = re.search(pattern, clean_text, re.I)
        if m:
            if len(m.groups()) >= 3:
                stats["height"] = f"{m.group(1)}–{m.group(2)} {m.group(3)}"
            else:
                stats["height"] = f"{m.group(1)} {m.group(2)}"
            break
    
    # =============================================================================
    # LIFESPAN EXTRACTION
    # =============================================================================
    lifespan_patterns = [
        # "lifespan of 10 to 20 years"
        r'lifespan\s*(?:of)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)',
        # "live 10 to 20 years"
        r'live[s]?\s*(?:up to|about|around|approximately)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)',
        # "10 to 20 years in the wild"
        r'(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)\s*(?:in the wild|in captivity|old|age|lifespan)',
        # "life expectancy of 10-20 years"
        r'life\s*expectancy\s*(?:of)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)',
        # "can live up to 20 years"
        r'can\s*live\s*(?:up to)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)',
        # Single value: "20 years"
        r'(?:about|around|approximately)?\s*(\d+)\s*(years?|yrs)\s*(?:old|age|lifespan)',
    ]
    
    for pattern in lifespan_patterns:
        m = re.search(pattern, clean_text, re.I)
        if m:
            stats["lifespan"] = f"{m.group(1)} {m.group(2)}"
            break
    
    # =============================================================================
    # SPEED EXTRACTION
    # =============================================================================
    speed_patterns = [
        # "speed of 100 km/h"
        r'speed\s*(?:of)?\s*(\d+(?:[.,]\d+)?)\s*(km/h|kmph|kph|mph|mi/h|miles per hour|kilometers per hour)',
        # "can run at 100 km/h"
        r'can\s*(?:run|swim|fly|move|travel)\s*(?:at|up to)?\s*(\d+(?:[.,]\d+)?)\s*(km/h|kmph|kph|mph|mi/h|miles per hour|kilometers per hour)',
        # "100 km/h top speed"
        r'(\d+(?:[.,]\d+)?)\s*(km/h|kmph|kph|mph|mi/h|miles per hour|kilometers per hour)\s*(?:top speed|maximum speed|top speed)',
        # "reaches speeds of 100 km/h"
        r'reaches?\s*(?:speeds? of)?\s*(\d+(?:[.,]\d+)?)\s*(km/h|kmph|kph|mph|mi/h|miles per hour|kilometers per hour)',
        # "100 km/h" near speed keywords
        r'(?:speed|fast|rapid|swift)\s*(?:of)?\s*(\d+(?:[.,]\d+)?)\s*(km/h|kmph|kph|mph|mi/h|miles per hour|kilometers per hour)',
    ]
    
    for pattern in speed_patterns:
        m = re.search(pattern, clean_text, re.I)
        if m:
            stats["top_speed"] = f"{m.group(1)} {m.group(2)}"
            break
    
    return stats


def extract_stats_with_context(sections: Dict[str, str], animal_name: str = "") -> Dict[str, str]:
    """Enhanced extraction with animal-specific context"""
    stats = extract_stats_from_sections(sections)
    
    # Combine all text for context-aware extraction
    all_text = " ".join(sections.values())
    all_text = re.sub(r'\[\d+\]', '', all_text)
    
    # Animal-specific fallbacks
    if animal_name:
        name_lower = animal_name.lower()
        
        # If no weight found, try species-specific patterns
        if not stats["weight"]:
            if "elephant" in name_lower:
                m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to)\s*(\d+(?:[.,]\d+)?)\s*(tonnes?|tons|kg)', all_text, re.I)
                if m:
                    stats["weight"] = f"{m.group(1)}–{m.group(2)} {m.group(3)}"
            
            if "whale" in name_lower or "shark" in name_lower:
                m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to)\s*(\d+(?:[.,]\d+)?)\s*(tonnes?|tons|kg|pounds|lbs)', all_text, re.I)
                if m:
                    stats["weight"] = f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    return stats
