# generator/modules/extractors/wikidata_enhancer.py

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
    claims = entity.get("claims", {})
    
    # P31 = instance of
    instance_of = claims.get("P31", [])
    
    # Animal QIDs (taxon, species, etc.)
    animal_qids = ["Q729", "Q16521", "Q190887", "Q14959704"]  # taxon, species, animal, etc.
    
    for claim in instance_of:
        qid = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id", "")
        if qid in animal_qids:
            return True
    
    # Check description for animal keywords
    descriptions = entity.get("descriptions", {})
    en_desc = descriptions.get("en", {}).get("value", "").lower()
    animal_keywords = ["species", "animal", "mammal", "bird", "fish", "reptile", "amphibian", "insect"]
    
    for keyword in animal_keywords:
        if keyword in en_desc:
            return True
    
    # If description mentions commune, city, person, etc. - reject
    reject_keywords = ["commune", "city", "town", "village", "person", "politician", "university", "year", "plant"]
    for keyword in reject_keywords:
        if keyword in en_desc:
            return False
    
    return True  # Default to accepting if unsure

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
            "limit": 1
        }
        headers = {
            "User-Agent": "WildAtlas/1.0 (https://github.com/Hunterthief/WildAtlas)"
        }
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("search", [])
        if results:
            # Verify it's an animal
            qid = results[0].get("id", "")
            # Fetch full entity to verify
            entity = fetch_wikidata(qid)
            if entity and _is_animal_entity(entity):
                return qid
        return None
    except Exception as e:
        print(f"   ⚠ Wikidata search failed: {e}")
        return None

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
