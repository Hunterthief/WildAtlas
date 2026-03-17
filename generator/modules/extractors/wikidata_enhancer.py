# generator/modules/extractors/wikidata_enhancer.py
"""
Wikidata Extractor - No API Key Required
Enhances taxonomy, conservation status, images, and more
"""
import requests
from typing import Dict, Any, Optional

WIKIDATA_ENDPOINT = "https://www.wikidata.org/entity/"
WIKIDATA_SEARCH = "https://www.wikidata.org/w/api.php"

def fetch_wikidata(qid: str) -> Optional[Dict[str, Any]]:
    """Fetch data from Wikidata using QID"""
    try:
        url = f"{WIKIDATA_ENDPOINT}{qid}.json"
        headers = {
            "User-Agent": "WildAtlas/1.0 (https://github.com/Hunterthief/WildAtlas)",
            "Accept": "application/json"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        entity = data.get("entities", {}).get(qid, {})
        
        # Verify this is actually an animal (not a place/person)
        if not _is_animal_entity(entity):
            print(f"   ⚠ QID {qid} is not an animal, searching by name...")
            return None
        
        return entity
    except Exception as e:
        print(f"   ⚠ Wikidata fetch failed: {e}")
        return None

def _is_animal_entity(entity: Dict[str, Any]) -> bool:
    """Check if Wikidata entity is an animal (not place, person, etc.)"""
    if not entity:
        return False
    
    claims = entity.get("claims", {})
    
    # P31 = instance of
    instance_of = claims.get("P31", [])
    
    # Animal QIDs (taxon, species, etc.)
    animal_qids = ["Q729", "Q16521", "Q190887", "Q14959704", "Q7432", "Q10878"]
    
    for claim in instance_of:
        qid = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id", "")
        if qid in animal_qids:
            return True
    
    # Check description for animal keywords
    descriptions = entity.get("descriptions", {})
    en_desc = descriptions.get("en", {}).get("value", "").lower()
    
    animal_keywords = ["species", "animal", "mammal", "bird", "fish", "reptile", "amphibian", "insect", "cat", "dog", "elephant", "wolf", "tiger", "shark", "turtle", "snake", "frog", "butterfly", "bee", "penguin", "eagle", "cheetah", "salmon", "cobra"]
    
    for keyword in animal_keywords:
        if keyword in en_desc:
            return True
    
    # If description mentions commune, city, person, etc. - reject
    reject_keywords = ["commune", "city", "town", "village", "person", "politician", "university", "year", "plant", "emperor of", "dynasty"]
    for keyword in reject_keywords:
        if keyword in en_desc:
            return False
    
    return True

def search_wikidata_by_name(scientific_name: str) -> Optional[str]:
    """Search Wikidata for QID by scientific name"""
    try:
        url = WIKIDATA_SEARCH
        params = {
            "action": "wbsearchentities",
            "format": "json",
            "language": "en",
            "search": scientific_name,
            "type": "item",
            "limit": 5
        }
        headers = {
            "User-Agent": "WildAtlas/1.0 (https://github.com/Hunterthief/WildAtlas)"
        }
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("search", [])
        for result in results:
            qid = result.get("id", "")
            # Fetch full entity to verify it's an animal
            entity = fetch_wikidata(qid)
            if entity and _is_animal_entity(entity):
                return qid
        
        return None
    except Exception as e:
        print(f"   ⚠ Wikidata search failed: {e}")
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
    
    if not wikidata:
        return taxonomy
    
    claims = wikidata.get("claims", {})
    
    # P225 = taxon name
    taxon_name = claims.get("P225", [])
    if taxon_name:
        taxonomy["species"] = taxon_name[0].get("mainsnak", {}).get("datavalue", {}).get("value", "")
    
    # P171 = parent taxon (would need to resolve each QID to get full chain)
    # For now, we rely on iNaturalist for detailed taxonomy
    
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
            url = f"https://commons.wikimedia.org/wiki/File:{filename}"
            images.append(url)
    
    return images

def extract_common_names(wikidata: Dict[str, Any]) -> list:
    """Extract common names from Wikidata labels"""
    names = []
    labels = wikidata.get("labels", {})
    
    for lang, label_data in labels.items():
        name = label_data.get("value", "")
        if lang != "en" and name:
            names.append({"name": name, "language": lang})
    
    return names[:10]

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

def extract_wikidata_all(qid: str, scientific_name: str = "") -> Dict[str, Any]:
    """Main function - fetch all Wikidata enhancements with fallback search"""
    wikidata = fetch_wikidata(qid)
    
    # If QID failed or returned non-animal, try searching by scientific name
    if not wikidata and scientific_name:
        print(f"   🔍 Searching Wikidata for: {scientific_name}")
        new_qid = search_wikidata_by_name(scientific_name)
        if new_qid:
            print(f"   ✅ Found QID: {new_qid}")
            wikidata = fetch_wikidata(new_qid)
    
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
