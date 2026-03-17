# generator/modules/fetchers/__init__.py
"""
Data Fetchers - All external API/data source fetchers
"""

from .api_ninjas import fetch_animal_data
from .wikipedia import fetch_wikipedia_data, fetch_wikipedia_sections, fetch_wikipedia_infobox
from .inaturalist import fetch_inaturalist
from .wikidata import fetch_wikidata_properties
from .gbif_distribution import extract_gbif_all
from .eol_data import extract_eol_all
from .iucn_redlist import fetch_iucn_status

__all__ = [
    'fetch_animal_data',
    'fetch_wikipedia_data',
    'fetch_wikipedia_sections',
    'fetch_wikipedia_infobox',
    'fetch_inaturalist',
    'fetch_wikidata_properties',
    'extract_gbif_all',
    'extract_eol_all',
    'fetch_iucn_status'
]
