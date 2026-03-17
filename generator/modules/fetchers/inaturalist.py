# generator/modules/fetchers/inaturalist.py
"""iNaturalist fetching module"""
import requests
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

INAT_API = "https://api.inaturalist.org/v1/taxa"

CLASSIFICATION_FIELDS = ["kingdom", "phylum", "class", "order", "family", "genus", "species"]

session = requests.Session()
retry = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retry))
headers = {"User-Agent": "WildAtlasBot/1.0 (contact@example.com)", "Accept": "application/json"}


def fetch_inaturalist(sci_name):
    """Fetch classification from iNaturalist"""
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
                        classification = {f: "" for f in CLASSIFICATION_FIELDS}
                        classification["species"] = taxon.get("name", sci_name)
                        for a in r.json().get("results", []):
                            rank = a.get("rank", "").lower()
                            name = a.get("name")
                            if rank == "kingdom":
                                classification["kingdom"] = name
                            elif rank == "phylum":
                                classification["phylum"] = name
                            elif rank == "class":
                                classification["class"] = name
                            elif rank == "order":
                                classification["order"] = name
                            elif rank == "family":
                                classification["family"] = name
                            elif rank == "genus":
                                classification["genus"] = name
                        return classification
    except Exception as e:
        print(f" ⚠ iNaturalist error: {e}")
    return None
