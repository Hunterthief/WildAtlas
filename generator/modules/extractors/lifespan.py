# generator/modules/extractors/lifespan.py
"""
Lifespan extraction module - IMPROVED
Better patterns for various animals
"""
import re
from typing import Dict, Optional


def _is_valid_lifespan(value: str) -> bool:
    """Validate lifespan value makes sense"""
    try:
        # Must have years
        if "years" not in value.lower() and "yrs" not in value.lower():
            return False
        
        match = re.search(r'(\d+(?:\s*[-–]\s*\d+)?)', value)
        if not match:
            return False
        
        # Extract years
        years_match = re.search(r'(\d+)', match.group(1))
        if years_match:
            num = int(years_match.group(1))
            # Reasonable lifespan range: 1-200 years
            if num < 1 or num > 200:
                return False
        
        return True
    except:
        return False


def extract_lifespan_from_sections(sections: Dict[str, str], animal_name: str = "") -> str:
    """Extract lifespan from Wikipedia sections"""
    all_text = " ".join(sections.values())
    
    if not all_text or len(all_text) < 50:
        return ""
    
    # Clean text
    clean_text = re.sub(r'\[\d+\]', '', all_text)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    # Priority 1: Direct lifespan patterns
    lifespan_patterns = [
        # "lifespan of X to Y years"
        r'lifespan\s*(?:of|is|for)?\s*(?:typically|usually|about|around|average|in the wild)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)',
        
        # "average lifespan of X years"
        r'average\s*lifespan\s*(?:of|is)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)',
        
        # "X years in the wild"
        r'(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)\s*(?:in the wild|in captivity|typically|usually|average)',
        
        # "can live up to X years"
        r'(?:can\s*)?live[s]?\s*(?:up to|about|around|typically)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)',
        
        # "life expectancy of X years"
        r'life\s*expectancy\s*(?:of|is)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)',
        
        # "typically X years"
        r'typically\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)',
        
        # "about X years" with lifespan context
        r'(?:lifespan|life|live|longevity|age)\s*(?:of|is)?\s*(?:about|around|approximately)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)',
        
        # "X–Y years" (en-dash)
        r'(\d+)\s*[–-]\s*(\d+)\s*(years?|yrs)',
        
        # "longevity of X years"
        r'longevity\s*(?:of|is)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)',
    ]
    
    for pattern in lifespan_patterns:
        m = re.search(pattern, clean_text, re.I)
        if m:
            groups = m.groups()
            if len(groups) >= 2:
                candidate = f"{groups[0]} {groups[1]}"
                if _is_valid_lifespan(candidate):
                    return candidate
    
    # Priority 2: Animal-specific patterns
    animal_lower = animal_name.lower() if animal_name else ""
    
    # Snake specific - "average lifespan of about X years"
    if any(x in animal_lower for x in ["snake", "cobra", "python"]):
        m = re.search(r'average\s*lifespan\s*(?:of|is)?\s*(?:a\s+wild\s+)?(?:about|around)?\s*(\d+)\s*(years?)', clean_text, re.I)
        if m:
            return f"{m.group(1)} {m.group(2)}"
    
    return ""
