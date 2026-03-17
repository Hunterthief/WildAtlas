# generator/modules/extractors/stats.py
"""
Physical stats extraction module - MAIN
Combines all individual stat extractors with animal_name parameter
"""
import re  # ← Keep this at the top
from typing import Dict, Any

from .weight import extract_weight_from_sections
from .length import extract_length_from_sections
from .height import extract_height_from_sections
from .lifespan import extract_lifespan_from_sections
from .speed import extract_speed_from_sections


def extract_stats_from_sections(sections: Dict[str, str], animal_name: str = "") -> Dict[str, str]:
    """Extract all physical stats from Wikipedia sections"""
    return {
        "weight": extract_weight_from_sections(sections, animal_name),
        "length": extract_length_from_sections(sections, animal_name),
        "height": extract_height_from_sections(sections, animal_name),
        "lifespan": extract_lifespan_from_sections(sections, animal_name),
        "top_speed": extract_speed_from_sections(sections, animal_name),
    }


def extract_stats_with_context(sections: Dict[str, str], animal_name: str = "", scientific_name: str = "") -> Dict[str, str]:
    """Enhanced extraction with animal-specific context and fallbacks"""
    stats = extract_stats_from_sections(sections, animal_name)
    
    # Combine all text for context-aware extraction
    all_text = " ".join(sections.values())
    all_text = re.sub(r'\[\d+\]', '', all_text)  # ← Now this works!
    
    # Animal-specific fallbacks for large animals
    if animal_name:
        name_lower = animal_name.lower()
        
        # Elephants - look for tonne patterns (body weight, not tusks)
        if "elephant" in name_lower and not stats["weight"]:
            # import re  ← REMOVE THIS!
            m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to)\s*(\d+(?:[.,]\d+)?)\s*(tonnes?|tons)', all_text, re.I)
            if m:
                match_context = all_text[max(0, m.start()-150):m.end()+150]
                if "tusk" not in match_context.lower() and "ivory" not in match_context.lower():
                    stats["weight"] = f"{m.group(1)}–{m.group(2)} {m.group(3)}"
        
        # Whales/Sharks - look for tonne patterns
        if any(x in name_lower for x in ["whale", "shark"]) and not stats["weight"]:
            # import re  ← REMOVE THIS!
            m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to)\s*(\d+(?:[.,]\d+)?)\s*(tonnes?|tons|kg|kilograms)', all_text, re.I)
            if m:
                stats["weight"] = f"{m.group(1)}–{m.group(2)} {m.group(3)}"
        
        # Snakes - look for meter length patterns
        if any(x in name_lower for x in ["snake", "cobra", "python"]) and not stats["length"]:
            # import re  ← REMOVE THIS!
            m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to)\s*(\d+(?:[.,]\d+)?)\s*(m|metres|meters)', all_text, re.I)
            if m:
                match_context = all_text[max(0, m.start()-150):m.end()+150]
                if "temporal" not in match_context.lower() and "ma" not in match_context.lower():
                    stats["length"] = f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    return stats
