# generator/modules/extractors/speed.py
"""
Speed extraction module
Extracts speed from Wikipedia text with validation
"""
import re
from typing import Dict, Any, Optional


def _is_valid_speed(value: str) -> bool:
    """Validate speed value makes sense"""
    try:
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


def _has_speed_context(text: str) -> bool:
    """Check if text has speed-related context"""
    text_lower = text.lower()
    speed_keywords = ['speed', 'fast', 'run', 'swim', 'fly', 'km/h', 'mph', 'kph', 'sprint']
    return any(kw in text_lower for kw in speed_keywords)


def extract_speed_from_sections(sections: Dict[str, str], animal_name: str = "") -> str:
    """Extract speed from Wikipedia sections"""
    all_text = " ".join(sections.values())
    
    if not all_text or len(all_text) < 50:
        return ""
    
    # Clean text
    clean_text = re.sub(r'\[\d+\]', '', all_text)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    speed_patterns = [
        # "capable of running at 93 to 104 km/h"
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
                if _is_valid_speed(candidate) and _has_speed_context(m.group(0)):
                    return candidate
    
    return ""
