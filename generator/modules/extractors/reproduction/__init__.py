# generator/modules/extractors/reproduction/__init__.py
"""Reproduction extraction functions"""

from .gestation import extract_gestation
from .litter_size import extract_litter_size

__all__ = ['extract_gestation', 'extract_litter_size']
