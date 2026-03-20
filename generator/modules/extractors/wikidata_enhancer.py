"""
Wikidata Extractor - No API Key Required
Enhances taxonomy, conservation status, images, and more
CRITICAL FIX: Direct image URLs ✅
"""
import requests
from typing import Dict, Any, Optional

# FIXED: No trailing spaces
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
        
        if not _is_animal_entity(entity):
            print(f"   ⚠ QID {qid} is not an animal, searching by name...")
            return None
        
        return entity
    except Exception as e:
        print(f"   ⚠ Wikidata fetch failed: {e}")
        return None


def _is_animal_entity(entity: Dict[str, Any]) -> bool:
    """Check if Wikidata entity is actually an animal"""
    if not entity:
        return False
    
    claims = entity.get("claims", {})
    instance_of = claims.get("P31", [])
    
    animal_qids = [
        "Q729", "Q16521", "Q190887", "Q14959704", "Q7432",
        "Q10878", "Q25313", "Q25306", "Q25303", "Q25308", "Q25311",
    ]
    
    for claim in instance_of:
        qid = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id", "")
        if qid in animal_qids:
            return True
    
    descriptions = entity.get("descriptions", {})
    en_desc = descriptions.get("en", {}).get("value", "").lower()
    
    animal_keywords = [
        "species of", "animal", "mammal", "bird", "fish", "reptile", 
        "amphibian", "insect", "cat", "dog", "elephant", "wolf", 
        "tiger", "shark", "turtle", "snake", "frog", "butterfly", 
        "bee", "penguin", "eagle", "cheetah", "salmon", "cobra",
    ]
    
    reject_keywords = [
        "commune", "city", "town", "village", "person", "politician", 
        "university", "year", "plant", "emperor of", "dynasty",
    ]
    
    has_animal_keyword = any(kw in en_desc for kw in animal_keywords)
    has_reject_keyword = any(kw in en_desc for kw in reject_keywords)
    
    return has_animal_keyword and not has_reject_keyword


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
            entity = fetch_wikidata(qid)
            if entity and _is_animal_entity(entity):
                return qid
        
        return None
    except Exception as e:
        print(f"   ⚠ Wikidata search failed: {e}")
        return None


def _convert_filename_to_direct_url(filename: str) -> str:
    """
    CRITICAL FIX: Convert Wikimedia filename to DIRECT image URL
    
    Input:  "Adult_male_Royal_Bengal_tiger.jpg"
    Output: "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Adult_male_Royal_Bengal_tiger.jpg/800px-Adult_male_Royal_Bengal_tiger.jpg"
    """
    if not filename:
        return ""
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Get hash path (first char and first two chars of filename)
    clean_name = filename.split('.')[0]
    if len(clean_name) >= 2:
        hash1 = clean_name[0]
        hash2 = clean_name[:2]
        
        # Build DIRECT image URL (800px width for good quality)
        direct_url = f"https://upload.wikimedia.org/wikipedia/commons/thumb/{hash1}/{hash2}/{filename}/800px-{filename}"
        return direct_url
    
    # Fallback
    return f"https://upload.wikimedia.org/wikipedia/commons/{filename}"


def extract_taxonomy(wikidata: Dict[str, Any]) -> Dict[str, str]:
    """Extract taxonomic classification from Wikidata"""
    taxonomy = {
        "kingdom": "", "phylum": "", "class": "", "order": "", 
        "family": "", "genus": "", "species": ""
    }
    
    if not wikidata:
        return taxonomy
    
    claims = wikidata.get("claims", {})
    taxon_name = claims.get("P225", [])
    if taxon_name:
        taxonomy["species"] = taxon_name[0].get("mainsnak", {}).get("datavalue", {}).get("value", "")
    
    return taxonomy


def extract_conservation_status(wikidata: Dict[str, Any]) -> Dict[str, str]:
    """Extract IUCN conservation status from Wikidata"""
    if not wikidata:
        return {"status": None, "status_id": None}
    
    claims = wikidata.get("claims", {})
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
        status = status_map.get(status_id)
        if status:
            return {"status": status, "status_id": status_id}
    
    return {"status": None, "status_id": None}


def extract_images(wikidata: Dict[str, Any]) -> list:
    """
    CRITICAL FIX: Extract DIRECT image URLs from Wikidata
    
    Returns upload.wikimedia.org URLs (actual images), NOT commons.wikimedia.org page URLs
    """
    images = []
    claims = wikidata.get("claims", {})
    
    # P18 = image
    image_claims = claims.get("P18", [])
    for claim in image_claims[:3]:  # Max 3 images
        filename = claim.get("mainsnak", {}).get("datavalue", {}).get("value", "")
        if filename:
            # CRITICAL FIX: Convert to DIRECT image URL
            direct_url = _convert_filename_to_direct_url(filename)
            images.append(direct_url)
    
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
    pop_claims = claims.get("P1082", [])
    if pop_claims:
        amount = pop_claims[0].get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("amount", "")
        if amount:
            return amount.lstrip("+")
    return ""


def extract_wikidata_all(qid: str, scientific_name: str = "") -> Dict[str, Any]:
    """Main function - fetch all Wikidata enhancements with fallback search"""
    wikidata = fetch_wikidata(qid)
    
    if not wikidata and scientific_name:
        print(f"   🔍 Searching Wikidata for: {scientific_name}")
        new_qid = search_wikidata_by_name(scientific_name)
        if new_qid:
            print(f"   ✅ Found QID: {new_qid}")
            wikidata = fetch_wikidata(new_qid)
    
    if not wikidata:
        return {}
    
    wiki_title = scientific_name.replace(' ', '_') if scientific_name else qid
    
    return {
        "taxonomy": extract_taxonomy(wikidata),
        "conservation": extract_conservation_status(wikidata),
        "images": extract_images(wikidata),  # Now returns DIRECT URLs
        "common_names": extract_common_names(wikidata),
        "population": extract_population(wikidata),
        "description": wikidata.get("descriptions", {}).get("en", {}).get("value", ""),
        "wikipedia_url": f"https://en.wikipedia.org/wiki/{wiki_title}"
    }
