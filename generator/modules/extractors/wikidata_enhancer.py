"""
Wikidata Extractor - No API Key Required
CRITICAL FIX: Direct upload.wikimedia.org URLs + Distribution Images
STRICT PATTERN: Only {animal_name}_distribution.png accepted
"""
import requests
import hashlib
import re
from typing import Dict, Any, Optional, List

# FIXED: NO TRAILING SPACES ANYWHERE
WIKIDATA_ENDPOINT = "https://www.wikidata.org/entity/"
WIKIDATA_SEARCH = "https://www.wikidata.org/w/api.php"
WIKIMEDIA_COMMONS = "https://commons.wikimedia.org/w/api.php"
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"

# Language suffixes to reject (e.g., -ar.png, -he.png, -fr.png)
LANGUAGE_SUFFIXES = [
    '-ar', '-fr', '-de', '-es', '-pt', '-ru', '-zh', '-ja', '-ko',
    '-he', '-it', '-nl', '-pl', '-tr', '-hi', '-bn', '-ta', '-te',
    '-th', '-vi', '-id', '-ms', '-tl', '-uk', '-cs', '-sk', '-hu',
    '-ro', '-bg', '-hr', '-sr', '-sl', '-et', '-lv', '-lt', '-fi',
    '-sv', '-no', '-da', '-is', '-ga', '-cy', '-mt', '-eu', '-ca',
    '-gl', '-ast', '-oc', '-br', '-gd', '-gv', '-kw', '-lb', '-rm',
    '-cz', '-cn', '-tw', '-hk', '-sg'
]

# Reject keywords for distribution maps
DISTRIBUTION_REJECT_KEYWORDS = [
    'historical', 'history', 'old', 'ancient', 'former',
    'plo', 'early', 'late', 'century', 'past', 'previous',
    'grid_map', 'grid', 'cutted', 'without_borders',
    'subspecies', 'range', 'map', '202', '201', '200', '199', '198'
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
    
    # FIXED: NO SPACES IN URL
    direct_url = f"https://upload.wikimedia.org/wikipedia/commons/{hash1}/{hash2}/{filename}"
    
    return direct_url


def _is_valid_distribution_map(filename: str, animal_name: str) -> bool:
    """
    Check if this is a valid distribution map
    
    ACCEPT ONLY:
    - Tiger_distribution.png
    - Tiger_distribution.svg
    - Tiger_distribution.jpg
    
    REJECT:
    - Panthera_tigris_distribution.png (scientific name)
    - Panthera_tigris_tigris_distribution.png (subspecies)
    - Tiger_distribution_2022.png (has year)
    - Tiger_distribution_map-ar.png (language suffix)
    - Distribution_Canis_Lupus_Italicus.png (multi-name)
    """
    filename_lower = filename.lower()
    animal_lower = animal_name.lower().replace(' ', '_')
    
    # Must contain "distribution"
    if 'distribution' not in filename_lower:
        return False
    
    # Get file extension
    if not (filename_lower.endswith('.png') or filename_lower.endswith('.svg') or 
            filename_lower.endswith('.jpg') or filename_lower.endswith('.jpeg')):
        return False
    
    # Remove extension for pattern matching
    filename_no_ext = filename_lower.rsplit('.', 1)[0]
    
    # STRICT PATTERN: Must be exactly "{animal_name}_distribution"
    # Example: "tiger_distribution" for animal_name "Tiger"
    expected_pattern = f"{animal_lower}_distribution"
    
    # Check if filename matches the exact pattern
    if filename_no_ext == expected_pattern:
        return True
    
    # Also accept "{animal_lower}_distribution_map" (without numbers/suffixes)
    if filename_no_ext == f"{animal_lower}_distribution_map":
        # But reject if it has language suffixes or numbers
        for lang_suffix in LANGUAGE_SUFFIXES:
            if filename_lower.endswith(lang_suffix + '.png') or \
               filename_lower.endswith(lang_suffix + '.svg'):
                return False
        return True
    
    # REJECT everything else (scientific names, multi-names, etc.)
    print(f"   ⚠️  Rejecting distribution map (wrong pattern): {filename}")
    print(f"      Expected: {expected_pattern}")
    print(f"      Got: {filename_no_ext}")
    return False


def _get_wikipedia_images(animal_name: str) -> List[str]:
    """
    Get all images from Wikipedia article including distribution maps
    
    Example: https://en.wikipedia.org/wiki/Tiger
    Returns list of direct image URLs
    """
    images = []
    
    try:
        # Get page images from Wikipedia API
        params = {
            "action": "query",
            "format": "json",
            "titles": animal_name,
            "prop": "images",
            "imlimit": "50"
        }
        headers = {
            "User-Agent": "WildAtlas/1.0 (https://github.com/Hunterthief/WildAtlas)"
        }
        
        response = requests.get(WIKIPEDIA_API, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            
            for page_id, page_data in pages.items():
                if page_id == "-1":
                    continue
                    
                images_list = page_data.get("images", [])
                for img in images_list:
                    filename = img.get("title", "")
                    if filename:
                        # Convert to direct URL
                        direct_url = _filename_to_direct_url(filename)
                        images.append(direct_url)
    
    except Exception as e:
        print(f"   ⚠️  Wikipedia image fetch failed: {e}")
    
    return images


def _search_distribution_map(animal_name: str, scientific_name: str) -> Optional[str]:
    """
    Search Wikimedia Commons AND Wikipedia for distribution map images
    
    Priority:
    1. Wikipedia article images (most likely to have correct distribution map)
    2. Wikimedia Commons search
    
    Example: https://upload.wikimedia.org/wikipedia/commons/7/7f/Tiger_distribution.png
    """
    # PRIORITY 1: Get images from Wikipedia article
    print(f"   📖 Searching Wikipedia article for distribution map...")
    wiki_images = _get_wikipedia_images(animal_name)
    
    for img_url in wiki_images:
        # Extract filename from URL
        filename = img_url.split('/')[-1]
        filename_clean = filename.replace('File:', '').strip()
        
        if 'distribution' in filename_clean.lower():
            if _is_valid_distribution_map(filename_clean, animal_name):
                print(f"   ✅ Found distribution map in Wikipedia: {filename_clean}")
                return img_url
    
    # PRIORITY 2: Search Wikimedia Commons
    print(f"   🔍 Searching Wikimedia Commons for distribution map...")
    search_queries = [
        f"{animal_name} distribution",
    ]
    
    for query in search_queries:
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": f"{query}",
            "srnamespace": 6,  # File namespace
            "srlimit": 20
        }
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
                
                if filename_clean and "distribution" in filename_clean.lower():
                    if _is_valid_distribution_map(filename_clean, animal_name):
                        direct_url = _filename_to_direct_url(filename)
                        print(f"   ✅ Found distribution map: {filename_clean}")
                        return direct_url
    
    return None


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


def extract_taxonomy(wiki Dict[str, Any]) -> Dict[str, str]:
    """Extract taxonomic classification from Wikidata"""
    taxonomy = {
        "kingdom": "", "phylum": "", "class": "", "order": "", 
        "family": "", "genus": "", "species": ""
    }
    
    if not wiki
        return taxonomy
    
    claims = wikidata.get("claims", {})
    taxon_name = claims.get("P225", [])
    if taxon_name:
        taxonomy["species"] = taxon_name[0].get("mainsnak", {}).get("datavalue", {}).get("value", "")
    
    return taxonomy


def extract_conservation_status(wiki Dict[str, Any]) -> Dict[str, str]:
    """Extract IUCN conservation status from Wikidata"""
    if not wiki
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


def extract_images(wiki Dict[str, Any], animal_name: str = "", scientific_name: str = "") -> Dict[str, List[str]]:
    """
    Extract DIRECT image URLs from Wikidata AND Wikipedia
    Separates regular photos from distribution maps
    """
    result = {
        "photos": [],
        "distribution": []
    }
    
    # Get images from Wikidata P18 claims
    claims = wikidata.get("claims", {})
    image_claims = claims.get("P18", [])
    
    for claim in image_claims[:5]:
        filename = claim.get("mainsnak", {}).get("datavalue", {}).get("value", "")
        if filename:
            filename_clean = filename.replace('File:', '').strip()
            direct_url = _filename_to_direct_url(filename).strip()
            
            if "distribution" in filename_clean.lower():
                if _is_valid_distribution_map(filename_clean, animal_name):
                    result["distribution"].append(direct_url)
                    print(f"   🗺️  Distribution image from Wikidata: {filename_clean}")
            else:
                result["photos"].append(direct_url)
    
    # If no distribution image from Wikidata, search Wikipedia and Commons
    if not result["distribution"] and animal_name:
        dist_map = _search_distribution_map(animal_name, scientific_name)
        if dist_map:
            result["distribution"].append(dist_map)
    
    return result


def extract_common_names(wiki Dict[str, Any]) -> list:
    """Extract common names from Wikidata labels"""
    names = []
    labels = wikidata.get("labels", {})
    
    for lang, label_data in labels.items():
        name = label_data.get("value", "")
        if lang != "en" and name:
            names.append({"name": name, "language": lang})
    
    return names[:10]


def extract_population(wiki Dict[str, Any]) -> str:
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
    
    if not wiki
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
