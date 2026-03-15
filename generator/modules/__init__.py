# generator/modules/__init__.py
"""
WildAtlas Generator Modules

This package contains modular components for animal data generation:
- fetchers: API calls (Wikipedia, iNaturalist)
- detectors: Animal type detection and classification
- extractors: Data extraction from text (organized by category)
- cache: Cache load/save operations
"""

from .fetchers import fetch_wikipedia_summary, fetch_wikipedia_full, fetch_inaturalist
from .detectors import detect_animal_type, get_young_name, get_group_name, get_default_diet
from .cache import load_cache, save_cache

# Note: Extractors are now organized in sub-packages
# Import them directly from their sub-packages in generate_animals.py

__all__ = [
    'fetch_wikipedia_summary', 'fetch_wikipedia_full', 'fetch_inaturalist',
    'detect_animal_type', 'get_young_name', 'get_group_name', 'get_default_diet',
    'load_cache', 'save_cache'
]
