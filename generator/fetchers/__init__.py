# generator/fetchers/__init__.py
from .wikipedia import fetch_wikipedia_summary, fetch_wikipedia_full
from .inaturalist import fetch_inaturalist

__all__ = [
    'fetch_wikipedia_summary',
    'fetch_wikipedia_full',
    'fetch_inaturalist'
]
