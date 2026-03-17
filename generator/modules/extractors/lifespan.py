# generator/modules/extractors/lifespan.py
"""
Lifespan extraction module
Extracts lifespan from Wikipedia text with validation
"""
import re
from typing import Dict, Any, Optional


def _is_valid_lifespan(value: str) -> bool:
    """Validate lifespan value makes sense"""
    try:
        match = re.search(r'(\d+(?:\s*[-–]\s*\d+)?)', value)
        if not match:
            return False
        
        # Check for reasonable year values
        if "years" not in value.lower() and "yrs" not in value.lower():
            return False
        
        return True
    except:
        return False


def _has_lifespan_context(text: str) -> bool:
    """Check if text has lifespan-related context"""
    text_lower = text.lower()
    lifespan_keywords = ['lifespan', 'life', 'years', 'live', 'longevity', 'age', 'expectancy']
    return any(kw in text_lower for kw in lifespan_keywords)


def extract_lifespan_from_sections(sections: Dict[str, str], animal_name: str = "") -> str:
    """Extract lifespan from Wikipedia sections"""
    all_text = " ".join(sections.values())
    
    if not all_text or len(all_text) < 50:
        return ""
    
    # Clean text
    clean_text = re.sub(r'\[\d+\]', '', all_text)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    lifespan_patterns = [
        # "lifespan of 10 to 20 years"
        r'lifespan\s*(?:of|is)?\s*(?:typically|usually|about|around)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)',
        
        # "15-20 years in the wild"
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
                if _is_valid_lifespan(candidate) and _has_lifespan_context(m.group(0)):
                    return candidate
    
    return ""
