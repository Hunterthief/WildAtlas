"""
Wikipedia Extractors - All text extraction from Wikipedia sections
Flat structure - all extractors at same level
"""

from .sections import extract_wikipedia_sections
from .weight import extract_weight_from_sections
from .length import extract_length_from_sections
from .height import extract_height_from_sections
from .lifespan import extract_lifespan_from_sections
from .speed import extract_speed_from_sections
from .reproduction import extract_reproduction_from_sections
from .diet import extract_diet_from_sections
from .behavior import extract_behavior_from_sections
from .conservation import extract_conservation_from_sections
from .additional_info import extract_additional_info_from_sections
from .stats import extract_stats_from_sections, extract_stats_with_context
from .wikidata_enhancer import extract_wikidata_all

__all__ = [
    'extract_wikipedia_sections',
    'extract_weight_from_sections',
    'extract_length_from_sections',
    'extract_height_from_sections',
    'extract_lifespan_from_sections',
    'extract_speed_from_sections',
    'extract_reproduction_from_sections',
    'extract_diet_from_sections',
    'extract_behavior_from_sections',
    'extract_conservation_from_sections',
    'extract_additional_info_from_sections',
    'extract_stats_from_sections',
    'extract_stats_with_context',
    'extract_wikidata_all'
]
