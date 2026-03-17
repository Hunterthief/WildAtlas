# generator/modules/extractors/stats.py
"""
Physical stats extraction module - MAIN
Combines all individual stat extractors
"""
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
    return extract_stats_from_sections(sections, animal_name)
