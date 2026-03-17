# generator/modules/fetchers/__init__.py
"""
Data Fetchers - All external API/data source fetchers
"""

from .api_ninjas import fetch_animal_data
from .wikipedia import fetch_wikipedia_summary, fetch_wikipedia_full
from .inaturalist import fetch_inaturalist
from .wikidata import fetch_wikidata_properties
from .gbif_distribution import extract_gbif_all
from .eol_data import extract_eol_all
from .iucn_redlist import fetch_iucn_data

__all__ = [
    'fetch_animal_data',
    'fetch_wikipedia_summary',
    'fetch_wikipedia_full',
    'fetch_inaturalist',
    'fetch_wikidata_properties',
    'extract_gbif_all',
    'extract_eol_all',
    'fetch_iucn_data'
]
