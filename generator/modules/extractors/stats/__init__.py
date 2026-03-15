# generator/modules/extractors/stats/__init__.py
"""Stats extraction functions"""

from .weight import extract_weight
from .length import extract_length
from .height import extract_height
from .lifespan import extract_lifespan
from .speed import extract_speed

__all__ = ['extract_weight', 'extract_length', 'extract_height', 'extract_lifespan', 'extract_speed']
