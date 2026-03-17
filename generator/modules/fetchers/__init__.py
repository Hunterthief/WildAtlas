# generator/modules/fetchers/__init__.py
"""
Data Fetchers - All external API/data source fetchers
"""

from .api_ninjas import fetch_animal_data
from .wikipedia import fetch_wikipedia_data, fetch_wikipedia_sections, fetch_wikipedia_infobox
from .inaturalist import fetch_inaturalist
from .wikidata import fetch_wikidata_properties
from .gbif_distribution import fetch_gbif_distribution
from .eol_data import fetch_eol_data
from .iucn_redlist import fetch_iucn_status

__all__ = [
    'fetch_animal_data',
    'fetch_wikipedia_data',
    'fetch_wikipedia_sections',
    'fetch_wikipedia_infobox',
    'fetch_inaturalist',
    'fetch_wikidata_properties',
    'fetch_gbif_distribution',
    'fetch_eol_data',
    'fetch_iucn_status'
]
