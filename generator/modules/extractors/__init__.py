# generator/modules/extractors/__init__.py
"""
Extractors Package

All data extraction functions organized by category.
Each sub-module can be edited independently without affecting others.
"""

from .stats import extract_weight, extract_length, extract_height, extract_lifespan, extract_speed
from .ecology import (
    extract_diet, extract_conservation, extract_locations,
    extract_habitat, extract_features, extract_behavior, extract_threats
)
from .reproduction import extract_gestation, extract_litter_size

__all__ = [
    'extract_weight', 'extract_length', 'extract_height', 'extract_lifespan', 'extract_speed',
    'extract_diet', 'extract_conservation', 'extract_locations',
    'extract_habitat', 'extract_features', 'extract_behavior', 'extract_threats',
    'extract_gestation', 'extract_litter_size'
]
