"""
Wikidata Extractor - No API Key Required
CRITICAL FIX: Direct upload.wikimedia.org URLs + Distribution Images
ALL TRAILING SPACES REMOVED + Subspecies Filter + Historical/Language Filter
"""
import requests
import hashlib
from typing import Dict, Any, Optional, List

# FIXED: No trailing spaces
WIKIDATA_ENDPOINT = "https://www.wikidata.org/entity/"
WIKIDATA_SEARCH = "https://www.wikidata.org/w/api.php"
WIKIMEDIA_COMMONS = "https://commons.wikimedia.org/w/api.php"

# Subspecies keywords to filter out (we want general species maps only)
SUBSPECIES_KEYWORDS = [
    'sumatrae', 'altaica', 'amoyensis', 'corbetti', 'jacksoni',
    'virgata', 'sondaica', 'balica', 'tigris', 'leo', 'persica',
    'africanus', 'asiaticus', 'bengalensis', 'indicus'
]

# FIXED: Reject keywords for distribution maps
DISTRIBUTION_REJECT_KEYWORDS = [
    'historical',  # Reject historical distribution maps
    '-ar',         # Reject Arabic language versions
    '-fr',         # Reject French language versions
    '-de',         # Reject German language versions
    '-es',         # Reject Spanish language versions
    '-pt',         # Reject Portuguese language versions
    '-ru',         # Reject Russian language versions
    '-zh',         # Reject Chinese language versions
    '-ja',         # Reject Japanese language versions
    'plo',         # Reject PLoS journal maps (often historical)
    'old',         # Reject old distribution maps
    'ancient',     # Reject ancient distribution maps
    'former',      # Reject former range maps
]


def _filename_to_direct_url(filename: str) -> str:
    """
    Convert Wikimedia filename to DIRECT image URL using MD5 hash
    
    Input:  "Tiger_distribution.png"
    Output: "https://upload.wikimedia.org/wikipedia/commons/7/7f/Tiger_distribution.png"
    """
    if not filename:
        return ""
    
    # Remove "File:" prefix if present
    filename = filename.replace('File:', '')
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Strip any trailing/leading whitespace
    filename = filename.strip()
    
    # Calculate MD5 hash for path
    md5_hash = hashlib.md5(filename.encode('utf-8')).hexdigest()
    hash1 = md5_hash[0]
    hash2 = md5_hash[0:2]
    
    # Build direct URL (NO SPACES ANYWHERE)
    direct_url = f"https://upload.wikimedia.org/wikipedia/commons/{hash1}/{hash2}/{filename}"
    
    return direct_url


def _is_valid_distribution_map(filename: str, animal_name: str) -> bool:
    """
    Check if this is a valid general species distribution map
    
    Accept: Tiger_distribution.png
    Reject: Panthera_tigris_sumatrae_distribution_map-ar.png
    Reject: Historical_tiger_distribution_PLoS_2009-ar.png
    """
    filename_lower = filename.lower()
    animal_lower = animal_name.lower().replace(' ', '_')
    
    # FIXED: Check for reject keywords first (historical, language suffixes, etc.)
    for reject_kw in DISTRIBUTION_REJECT_KEYWORDS:
        if reject_kw in filename_lower:
            print(f"   ⚠️  Rejecting distribution map (contains '{reject_kw}'): {filename}")
            return False
    
    # Check if filename contains subspecies keywords
    for subspecies in SUBSPECIES_KEYWORDS:
        if subspecies in filename_lower:
            print(f"   ⚠️  Rejecting distribution map (subspecies '{subspecies}'): {filename}")
            return False
    
    # Prefer filenames that match the common animal name
    if animal_lower in filename_lower:
        return True
    
    # Accept if it has "distribution" but no reject/subspecies keywords
    if 'distribution' in filename_lower:
        return True
    
    return False


def _search_distribution_map(animal_name: str, scientific_name: str) -> Optional[str]:
    """
    Search Wikimedia Commons for distribution map images
    Prefers general species maps over subspecies-specific ones
    Rejects historical and language-specific versions
    
    Example: https://upload.wikimedia.org/wikipedia/commons/7/7f/Tiger_distribution.png
    """
    try:
        # Try multiple search queries - general name first
        search_queries = [
            f"{animal_name} distribution",
            f"{animal_name} range",
            f"{scientific_name} distribution",
        ]
        
        best_match = None
        
        for query in search_queries:
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": f"{query}",
                "srnamespace": 6,  # File namespace
                "srlimit": 20
            }
            # FIXED: No trailing spaces in User-Agent
            headers = {
                "User-Agent": "WildAtlas/1.0 (https://github.com/Hunterthief/WildAtlas)"
            }
            
            response = requests.get(WIKIMEDIA_COMMONS, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("query", {}).get("search", [])
                
                for result in results:
                    filename = result.get("title", "")
                    filename_clean = filename.replace('File:', '').strip()
                    
                    # Must have "distribution" in name
                    if filename_clean and "distribution" in filename_clean.lower():
                        # FIXED: Check if it's a valid general map
                        if _is_valid_distribution_map(filename_clean, animal_name):
                            direct_url = _filename_to_direct_url(filename)
                            direct_url = direct_url.strip()
                            print(f"   ✅ Found distribution map: {filename_clean}")
                            return direct_url
                        elif best_match is None:
                            # Keep as fallback if no valid map found
                            best_match = _filename_to_direct_url(filename).strip()
        
        # Return fallback if no valid map found
        if best_match:
            print(f"   ⚠️  Using fallback map (no ideal map found): {best_match}")
            return best_match
    
    except Exception as e:
        print(f"   Distribution map search failed: {e}")
    
    return None


def fetch_wikidata(qid: str) -> Optional[Dict[str, Any]]:
    """Fetch data from Wikidata using QID"""
    try:
        url = f"{WIKIDATA_ENDPOINT}{qid}.json"
        # FIXED: No trailing spaces in User-Agent
        headers = {
            "User-Agent": "WildAtlas/1.0 (https://github.com/Hunterthief/WildAtlas)",
            "Accept": "application/json"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        entity = data.get("entities", {}).get(qid, {})
        
        if not _is_animal_entity(entity):
            print(f"   ⚠️  QID {qid} is not an animal, searching by name...")
            return None
        
        return entity
    except Exception as e:
        print(f"   ⚠️  Wikidata fetch failed: {e}")
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
        # FIXED: No trailing spaces in User-Agent
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
        print(f"   ⚠️  Wikidata search failed: {e}")
        return None


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


def extract_images(wikidata: Dict[str, Any], animal_name: str = "", scientific_name: str = "") -> Dict[str, List[str]]:
    """
    Extract DIRECT image URLs from Wikidata
    Separates regular photos from distribution maps
    Filters out subspecies-specific, historical, and language-specific distribution maps
    """
    result = {
        "photos": [],
        "distribution": []
    }
    
    claims = wikidata.get("claims", {})
    
    # P18 = image
    image_claims = claims.get("P18", [])
    for claim in image_claims[:5]:
        filename = claim.get("mainsnak", {}).get("datavalue", {}).get("value", "")
        if filename:
            filename_clean = filename.replace('File:', '').strip()
            direct_url = _filename_to_direct_url(filename).strip()
            
            # Check if it's a distribution map
            if "distribution" in filename_clean.lower() or "range_map" in filename_clean.lower():
                # FIXED: Only add if it's a valid general species map
                if _is_valid_distribution_map(filename_clean, animal_name):
                    result["distribution"].append(direct_url)
                    print(f"   🗺️  Distribution image: {filename_clean}")
                else:
                    print(f"   ⚠️  Skipping invalid distribution map: {filename_clean}")
            else:
                result["photos"].append(direct_url)
    
    # If no distribution image found in Wikidata, search Wikimedia Commons
    if not result["distribution"] and animal_name:
        dist_map = _search_distribution_map(animal_name, scientific_name)
        if dist_map:
            result["distribution"].append(dist_map)
    
    return result


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
    
    # Extract images with distribution filtering
    image_data = extract_images(wikidata, scientific_name, scientific_name)
    
    # Combine photos and distribution for "images" array
    all_images = image_data["photos"] + image_data["distribution"]
    
    # Primary image is first photo (not distribution map)
    primary_image = image_data["photos"][0] if image_data["photos"] else (image_data["distribution"][0] if image_data["distribution"] else "")
    
    # Strip trailing spaces
    primary_image = primary_image.strip()
    all_images = [img.strip() for img in all_images if img.strip()]
    
    # FIXED: No spaces in Wikipedia URL
    wiki_title = scientific_name.replace(' ', '_') if scientific_name else qid
    
    return {
        "taxonomy": extract_taxonomy(wikidata),
        "conservation": extract_conservation_status(wikidata),
        "images": all_images,
        "distribution_image": image_data["distribution"][0].strip() if image_data["distribution"] else "",
        "common_names": extract_common_names(wikidata),
        "population": extract_population(wikidata),
        "description": wikidata.get("descriptions", {}).get("en", {}).get("value", ""),
        "wikipedia_url": f"https://en.wikipedia.org/wiki/{wiki_title}"
    }
