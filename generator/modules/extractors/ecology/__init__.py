# generator/modules/extractors/ecology/__init__.py
"""Ecology extraction functions"""

from .diet import extract_diet
from .conservation import extract_conservation
from .locations import extract_locations
from .habitat import extract_habitat
from .features import extract_features
from .behavior import extract_behavior
from .threats import extract_threats

__all__ = [
    'extract_diet', 'extract_conservation', 'extract_locations',
    'extract_habitat', 'extract_features', 'extract_behavior', 'extract_threats'
]
