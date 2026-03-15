# generator/modules/__init__.py
"""
WildAtlas Generator Modules

This package contains modular components for animal data generation:
- fetchers: API calls (Wikipedia, iNaturalist)
- detectors: Animal type detection and classification
- extractors: Data extraction from text
- cache: Cache load/save operations
"""

from .fetchers import fetch_wikipedia_summary, fetch_wikipedia_full, fetch_inaturalist
from .detectors import detect_animal_type, get_young_name, get_group_name, get_default_diet
from .extractors import (
    extract_stats, extract_diet, extract_conservation,
    extract_locations, extract_habitat, extract_features,
    extract_behavior, extract_reproduction, extract_threats
)
from .cache import load_cache, save_cache

__all__ = [
    'fetch_wikipedia_summary', 'fetch_wikipedia_full', 'fetch_inaturalist',
    'detect_animal_type', 'get_young_name', 'get_group_name', 'get_default_diet',
    'extract_stats', 'extract_diet', 'extract_conservation',
    'extract_locations', 'extract_habitat', 'extract_features',
    'extract_behavior', 'extract_reproduction', 'extract_threats',
    'load_cache', 'save_cache'
]
