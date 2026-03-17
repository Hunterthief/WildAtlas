"""
Data Fetchers - All external API/data source fetchers
"""

from .api_ninjas import fetch_animal_data
from .wikipedia import fetch_wikipedia_summary, fetch_wikipedia_full
from .inaturalist import fetch_inaturalist
from .wikidata import fetch_wikidata_properties
from .gbif_distribution import fetch_gbif_distribution
from .eol_data import fetch_eol_data
from .iucn_redlist import fetch_iucn_status

__all__ = [
    'fetch_animal_data',
    'fetch_wikipedia_summary',
    'fetch_wikipedia_full',
    'fetch_inaturalist',
    'fetch_wikidata_properties',
    'fetch_gbif_distribution',
    'fetch_eol_data',
    'fetch_iucn_status'
]
