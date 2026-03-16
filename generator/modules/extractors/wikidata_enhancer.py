# generator/modules/extractors/wikidata_enhancer.py
"""
Wikidata Extractor - No API Key Required
Enhances taxonomy, conservation status, images, and more
"""
import requests
from typing import Dict, Any, Optional

WIKIDATA_ENDPOINT = "https://www.wikidata.org/wiki/Special:EntityData/"

def fetch_wikidata(qid: str) -> Optional[Dict[str, Any]]:
    """Fetch data from Wikidata using QID"""
    try:
        url = f"{WIKIDATA_ENDPOINT}{qid}.json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("entities", {}).get(qid, {})
    except Exception as e:
        print(f"   ⚠ Wikidata fetch failed: {e}")
        return None

def extract_taxonomy(wikidata: Dict[str, Any]) -> Dict[str, str]:
    """Extract taxonomic classification from Wikidata"""
    taxonomy = {
        "kingdom": "",
        "phylum": "",
        "class": "",
        "order": "",
        "family": "",
        "genus": "",
        "species": ""
    }
    
    claims = wikidata.get("claims", {})
    
    # Taxon name mappings (P225 = taxon name, P171 = parent taxon)
    taxon_name = claims.get("P225", [])
    if taxon_name:
        taxonomy["species"] = taxon_name[0].get("mainsnak", {}).get("datavalue", {}).get("value", "")
    
    # Parent taxon chain
    parent_taxon = claims.get("P171", [])
    for claim in parent_taxon[:7]:  # Max 7 levels
        value = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {})
        if isinstance(value, dict):
            name = value.get("id", "")
            # Could fetch each parent's name, but for now use ID
            # In production, you'd resolve each QID to name
    
    return taxonomy

def extract_conservation_status(wikidata: Dict[str, Any]) -> Dict[str, str]:
    """Extract IUCN conservation status from Wikidata"""
    claims = wikidata.get("claims", {})
    
    # P141 = IUCN conservation status
    status_claims = claims.get("P141", [])
    
    status_map = {
        "Q75807": "Least Concern",
        "Q192072": "Near Threatened",
        "Q192076": "Vulnerable",
        "Q192078": "Endangered",
        "Q192082": "Critically Endangered",
        "Q23037168": "Extinct in the Wild",
        "Q192086": "Extinct",
        "Q873109": "Data Deficient",
        "Q873116": "Not Evaluated"
    }
    
    if status_claims:
        status_id = status_claims[0].get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id", "")
        return {
            "status": status_map.get(status_id, "Unknown"),
            "status_id": status_id
        }
    
    return {"status": "", "status_id": ""}

def extract_images(wikidata: Dict[str, Any]) -> list:
    """Extract image URLs from Wikidata"""
    images = []
    claims = wikidata.get("claims", {})
    
    # P18 = image
    image_claims = claims.get("P18", [])
    for claim in image_claims[:3]:  # Max 3 images
        filename = claim.get("mainsnak", {}).get("datavalue", {}).get("value", "")
        if filename:
            # Convert to Wikimedia Commons URL
            url = f"https://commons.wikimedia.org/wiki/File:{filename}"
            images.append(url)
    
    return images

def extract_common_names(wikidata: Dict[str, Any]) -> list:
    """Extract common names from Wikidata labels"""
    names = []
    
    # Get labels in different languages
    labels = wikidata.get("labels", {})
    for lang, label_data in labels.items():
        name = label_data.get("value", "")
        if lang != "en" and name:  # Exclude English (already have main name)
            names.append({"name": name, "language": lang})
    
    return names[:10]  # Max 10 common names

def extract_population(wikidata: Dict[str, Any]) -> str:
    """Extract population estimate from Wikidata"""
    claims = wikidata.get("claims", {})
    
    # P1082 = population
    pop_claims = claims.get("P1082", [])
    if pop_claims:
        amount = pop_claims[0].get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("amount", "")
        if amount:
            return amount.lstrip("+")
    
    return ""

def extract_wikidata_all(qid: str) -> Dict[str, Any]:
    """Main function - fetch all Wikidata enhancements"""
    wikidata = fetch_wikidata(qid)
    
    if not wikidata:
        return {}
    
    return {
        "taxonomy": extract_taxonomy(wikidata),
        "conservation": extract_conservation_status(wikidata),
        "images": extract_images(wikidata),
        "common_names": extract_common_names(wikidata),
        "population": extract_population(wikidata),
        "description": wikidata.get("descriptions", {}).get("en", {}).get("value", ""),
        "wikipedia_url": f"https://en.wikipedia.org/wiki/{qid}"
    }
