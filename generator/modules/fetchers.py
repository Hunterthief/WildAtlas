# generator/modules/fetchers.py
"""
API Fetchers Module

Handles all external API calls:
- Wikipedia (summary and full page)
- iNaturalist (taxonomic classification)
"""

import requests
import re
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Setup session with retry logic
session = requests.Session()
retry = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retry))
headers = {"User-Agent": "WildAtlasBot/1.0 (contact@example.com)", "Accept": "application/json"}

WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
WIKI_MOBILE = "https://en.m.wikipedia.org/wiki/"
INAT_API = "https://api.inaturalist.org/v1/taxa"

CLASSIFICATION_FIELDS = ["kingdom", "phylum", "class", "order", "family", "genus", "species"]


def fetch_wikipedia_summary(name):
    """
    Fetch Wikipedia page summary for an animal.
    
    Args:
        name: Animal common name
        
    Returns:
        dict with summary, description, image, and url
    """
    try:
        r = session.get(f"{WIKI_API}{name.replace(' ', '_')}", headers=headers, timeout=15)
        if r.status_code == 200:
            d = r.json()
            return {
                "summary": d.get("extract", ""),
                "description": d.get("description", ""),
                "image": d.get("thumbnail", {}).get("source", "").strip(),
                "url": d.get("content_urls", {}).get("desktop", {}).get("page", "").strip()
            }
    except Exception as e:
        print(f" ⚠ Wikipedia summary error: {e}")
    return {"summary": "", "description": "", "image": "", "url": ""}


def fetch_wikipedia_full(name):
    """
    Fetch full Wikipedia page content for detailed text extraction.
    
    Args:
        name: Animal common name
        
    Returns:
        str: Cleaned HTML text content
    """
    try:
        r = session.get(f"{WIKI_MOBILE}{name.replace(' ', '_')}", headers=headers, timeout=15)
        if r.status_code == 200:
            text = re.sub(r'<[^>]+>', ' ', r.text)
            text = re.sub(r'\s+', ' ', text).strip()
            text = re.sub(r'\[\d+\]', '', text)
            return text
    except Exception as e:
        print(f" ⚠ Wikipedia full error: {e}")
    return ""


def fetch_inaturalist(sci_name):
    """
    Fetch taxonomic classification from iNaturalist API.
    
    Args:
        sci_name: Scientific name of the animal
        
    Returns:
        dict: Classification with kingdom, phylum, class, order, family, genus, species
    """
    try:
        params = {"q": sci_name, "per_page": 1, "rank": "species"}
        r = session.get(INAT_API, params=params, headers=headers, timeout=30)
        if r.status_code != 200:
            params = {"q": sci_name, "per_page": 1}
            r = session.get(INAT_API, params=params, headers=headers, timeout=30)
        
        if r.status_code == 200:
            results = r.json().get("results", [])
            if results:
                taxon = results[0]
                time.sleep(0.5)
                anc_ids = taxon.get("ancestor_ids", [])
                if anc_ids:
                    r = session.get(f"{INAT_API}/{','.join(map(str, anc_ids))}", headers=headers, timeout=30)
                    if r.status_code == 200:
                        classification = {f: None for f in CLASSIFICATION_FIELDS}
                        classification["species"] = taxon.get("name", sci_name)
                        for a in r.json().get("results", []):
                            rank = a.get("rank", "").lower()
                            name = a.get("name")
                            if rank == "kingdom": classification["kingdom"] = name
                            elif rank == "phylum": classification["phylum"] = name
                            elif rank == "class": classification["class"] = name
                            elif rank == "order": classification["order"] = name
                            elif rank == "family": classification["family"] = name
                            elif rank == "genus": classification["genus"] = name
                        return classification
    except Exception as e:
        print(f" ⚠ iNaturalist error: {e}")
    return None
