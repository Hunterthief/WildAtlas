# generator/modules/extractors/__init__.py
from .sections import extract_wikipedia_sections
from .stats import extract_stats_from_sections
from .diet import extract_diet_from_sections
from .reproduction import extract_reproduction_from_sections
from .conservation import extract_conservation_from_sections
from .behavior import extract_behavior_from_sections
from .additional_info import extract_additional_info_from_sections
from .wikidata_enhancer import extract_wikidata_all
from .gbif_distribution import extract_gbif_all
from .eol_data import extract_eol_all

__all__ = [
    "extract_wikipedia_sections",
    "extract_stats_from_sections",
    "extract_diet_from_sections",
    "extract_reproduction_from_sections",
    "extract_conservation_from_sections",
    "extract_behavior_from_sections",
    "extract_additional_info_from_sections",
    "extract_wikidata_all",
    "extract_gbif_all",
    "extract_eol_all"
]
