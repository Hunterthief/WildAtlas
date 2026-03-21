"""
Wikidata Extractor - No API Key Required
AGGRESSIVE MODE: Parse ALL images from Wikipedia articles
Finds distribution maps by checking image content and filenames
"""
import requests
import hashlib
import re
from typing import Dict, Any, Optional, List
from urllib.parse import unquote, urljoin
from bs4 import BeautifulSoup

# FIXED: NO TRAILING SPACES IN URLS
WIKIDATA_ENDPOINT = "https://www.wikidata.org/entity/"
WIKIDATA_SEARCH = "https://www.wikidata.org/w/api.php"
WIKIMEDIA_COMMONS = "https://commons.wikimedia.org/w/api.php"
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"

# Reject keywords for distribution maps (keep minimal)
DISTRIBUTION_REJECT_KEYWORDS = [
    'subspecies', 'historical', 'history', 'old', 'ancient', 'former',
    'cutted', 'without_borders', 'grid', 'grid_map',
    'map_2', 'map_3', 'map-2', 'map-3', 'distribution2', 'distribution3'
]

# File extensions to reject
REJECT_EXTENSIONS = ['.pdf', '.djvu', '.tiff', '.webp']


def _filename_to_direct_url(filename: str) -> str:
    """
    Convert Wikimedia filename to DIRECT image URL using MD5 hash
    
    Accepts ANY Wikimedia URL format and converts to direct URL
    """
    if not filename:
        return ""
    
    # Strip whitespace
    filename = filename.strip()
    
    # If it's already a full URL, extract the filename
    if filename.startswith('http'):
        # URL decode first (handle %28, %29, etc.)
        filename = unquote(filename)
        
        # Extract filename from thumb URL
        # https://upload.wikimedia.org/wikipedia/commons/thumb/7/7f/Tiger_distribution.png/960px-Tiger_distribution.png
        thumb_match = re.search(r'/thumb/[0-9a-fA-F]/[0-9a-fA-F]{2}/([^/]+\.(?:png|jpg|jpeg|svg|gif))', filename, re.IGNORECASE)
        if thumb_match:
            filename = thumb_match.group(1)
        else:
            # Try to extract from /wiki/File: format
            wiki_match = re.search(r'/wiki/File:([^/]+\.(?:png|jpg|jpeg|svg|gif))', filename, re.IGNORECASE)
            if wiki_match:
                filename = wiki_match.group(1)
            else:
                # Fallback: get last path component
                match = re.search(r'/([^/]+\.(?:png|jpg|jpeg|svg|gif))(?:\?|$)', filename, re.IGNORECASE)
                if match:
                    filename = match.group(1)
                else:
                    return ""
    
    # Remove "File:" prefix if present
    filename = filename.replace('File:', '').replace('file:', '')
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Strip any trailing/leading whitespace
    filename = filename.strip()
    
    if not filename:
        return ""
    
    # Calculate MD5 hash for path
    md5_hash = hashlib.md5(filename.encode('utf-8')).hexdigest()
    hash1 = md5_hash[0]
    hash2 = md5_hash[0:2]
    
    # Build direct URL
    direct_url = f"https://upload.wikimedia.org/wikipedia/commons/{hash1}/{hash2}/{filename}"
    
    return direct_url


def _is_distribution_map(filename: str, animal_name: str) -> bool:
    """
    VERY FLEXIBLE distribution map detection
    
    ACCEPTS anything with distribution/range/map in filename
    """
    filename_lower = filename.lower()
    animal_lower = animal_name.lower().replace(' ', '_')
    
    # Reject bad extensions
    for ext in REJECT_EXTENSIONS:
        if filename_lower.endswith(ext):
            return False
    
    # Must be image format
    if not any(filename_lower.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.svg', '.gif']):
        return False
    
    # Must have distribution/range/map keywords
    has_dist = 'distribution' in filename_lower
    has_range = 'range' in filename_lower
    has_map = 'map' in filename_lower
    
    if not (has_dist or (has_range and has_map)):
        return False
    
    # Reject known bad patterns
    for reject_kw in DISTRIBUTION_REJECT_KEYWORDS:
        if reject_kw in filename_lower:
            return False
    
    # Very flexible matching - just check if animal name appears with distribution
    filename_no_ext = filename_lower.rsplit('.', 1)[0]
    
    # Clean up common suffixes
    filename_clean = re.sub(r'_\(.*?\)', '', filename_no_ext)
    filename_clean = re.sub(r'_map$', '', filename_clean)
    filename_clean = re.sub(r'_range$', '', filename_clean)
    
    # Check if animal name appears in filename
    animal_parts = animal_lower.split('_')
    animal_in_filename = any(part in filename_clean for part in animal_parts if len(part) > 2)
    
    # If animal name found with distribution = ACCEPT
    if animal_in_filename and has_dist:
        return True
    
    # If just "distribution" without animal name but has range/map = ACCEPT
    if has_dist or (has_range and has_map):
        return True
    
    return False


def _get_all_images_from_wikipedia_html(animal_name: str) -> List[str]:
    """
    AGGRESSIVE: Parse Wikipedia HTML and extract ALL image URLs
    
    This finds images in:
    - Infoboxes
    - Article content
    - Galleries
    - Thumbnails
    """
    images = []
    
    try:
        wiki_title = animal_name.replace(' ', '_')
        url = f"https://en.wikipedia.org/wiki/{wiki_title}"
        
        headers = {
            "User-Agent": "WildAtlas/1.0 (https://github.com/Hunterthief/WildAtlas)"
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return images
        
        html = response.text
        
        # Parse with BeautifulSoup for better HTML handling
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find ALL img tags
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            # Try multiple attributes for image URL
            src = img.get('src', '')
            data_src = img.get('data-src', '')
            original = img.get('data-original', '')
            
            img_url = original or data_src or src
            
            if not img_url:
                continue
            
            # Make absolute URL if relative
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            elif img_url.startswith('/'):
                img_url = 'https://en.wikipedia.org' + img_url
            
            images.append(img_url)
        
        # Also find images in href links (for file pages)
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            if 'File:' in href and any(ext in href.lower() for ext in ['.png', '.jpg', '.jpeg', '.svg']):
                # Convert wiki file link to direct URL
                if href.startswith('/wiki/'):
                    filename = href.replace('/wiki/File:', '').replace('/wiki/file:', '')
                    if filename:
                        direct = _filename_to_direct_url(filename)
                        if direct:
                            images.append(direct)
        
        # Remove duplicates
        images = list(dict.fromkeys(images))
        
        print(f"   📖 Found {len(images)} total images in Wikipedia HTML")
        
        return images
    
    except Exception as e:
        print(f"   ⚠️  Wikipedia HTML parse failed: {e}")
        return images


def _get_all_images_from_wikipedia_api(animal_name: str) -> List[str]:
    """
    Get all images from Wikipedia API (backup method)
    """
    images = []
    
    try:
        params = {
            "action": "query",
            "format": "json",
            "titles": animal_name,
            "prop": "images",
            "imlimit": "500"  # Get more images
        }
        headers = {
            "User-Agent": "WildAtlas/1.0 (https://github.com/Hunterthief/WildAtlas)"
        }
        
        response = requests.get(WIKIPEDIA_API, params=params, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return images
        
        data = response.json()
        pages = data.get("query", {}).get("pages", {})
        
        page_data = None
        for page_id, page_info in pages.items():
            if page_id != "-1":
                page_data = page_info
                break
        
        if not page_data:
            return images
        
        images_list = page_data.get("images", [])
        
        for img in images_list:
            filename = img.get("title", "")
            if filename:
                direct_url = _filename_to_direct_url(filename)
                if direct_url:
                    images.append(direct_url)
        
        print(f"   📖 Found {len(images)} images from Wikipedia API")
        
        return images
    
    except Exception as e:
        print(f"   ⚠️  Wikipedia API failed: {e}")
        return images


def _get_distribution_from_wikipedia(animal_name: str) -> Optional[str]:
    """
    AGGRESSIVE: Find distribution map by checking ALL images
    
    Priority:
    1. HTML parsing (finds embedded images)
    2. API (gets all image titles)
    """
    distribution_images = []
    
    # STEP 1: Parse HTML for all images
    all_images = _get_all_images_from_wikipedia_html(animal_name)
    
    # STEP 2: Also get API images
    api_images = _get_all_images_from_wikipedia_api(animal_name)
    all_images.extend(api_images)
    
    # Remove duplicates
    all_images = list(dict.fromkeys(all_images))
    
    print(f"   🔍 Checking {len(all_images)} images for distribution maps...")
    
    # STEP 3: Check each image for distribution pattern
    for img_url in all_images:
        if not img_url:
            continue
        
        # Extract filename from URL
        filename_match = re.search(r'/([^/]+\.(?:png|jpg|jpeg|svg|gif))', img_url, re.IGNORECASE)
        if not filename_match:
            continue
        
        filename = unquote(filename_match.group(1))
        
        # Check if it's a distribution map
        if _is_distribution_map(filename, animal_name):
            direct_url = _filename_to_direct_url(img_url)
            if direct_url:
                distribution_images.append(direct_url)
                print(f"   ✅ Distribution candidate: {filename}")
    
    # Return first valid distribution image
    if distribution_images:
        # Prefer images with animal name in filename
        for img in distribution_images:
            if animal_name.lower().replace(' ', '_') in img.lower():
                print(f"   🗺️  Selected distribution map: {img}")
                return img
        
        # Otherwise return first one
        print(f"   🗺️  Selected distribution map: {distribution_images[0]}")
        return distribution_images[0]
    
    return None


def _search_distribution_on_commons(animal_name: str) -> Optional[str]:
    """
    Search Wikimedia Commons for distribution map
    """
    try:
        search_queries = [
            f"{animal_name} distribution",
            f"{animal_name.replace(' ', '_')}_distribution",
            f"{animal_name} range map",
            f"{animal_name.replace(' ', '_')}_range",
            f"{animal_name} distribution map",
        ]
        
        for query in search_queries:
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": f"{query}",
                "srnamespace": 6,
                "srlimit": 50
            }
            headers = {
                "User-Agent": "WildAtlas/1.0 (https://github.com/Hunterthief/WildAtlas)"
            }
            
            response = requests.get(WIKIMEDIA_COMMONS, params=params, headers=headers, timeout=10)
            
            if response.status_code != 200:
                continue
            
            data = response.json()
            results = data.get("query", {}).get("search", [])
            
            for result in results:
                filename = result.get("title", "")
                if filename and _is_distribution_map(filename, animal_name):
                    direct_url = _filename_to_direct_url(filename)
                    print(f"   ✅ Found distribution map on Commons: {filename}")
                    return direct_url
        
        return None
    
    except Exception as e:
        print(f"   ⚠️  Commons search failed: {e}")
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
    Extract DIRECT image URLs from Wikidata AND Wikipedia
    AGGRESSIVE MODE: Check ALL images
    """
    result = {
        "photos": [],
        "distribution": []
    }
    
    # Get images from Wikidata P18 claims
    claims = wikidata.get("claims", {})
    image_claims = claims.get("P18", [])
    
    for claim in image_claims[:10]:  # Get more images
        filename = claim.get("mainsnak", {}).get("datavalue", {}).get("value", "")
        if filename:
            filename_clean = filename.replace('File:', '').strip()
            direct_url = _filename_to_direct_url(filename).strip()
            
            if direct_url:
                if "distribution" in filename_clean.lower() or "range" in filename_clean.lower():
                    result["distribution"].append(direct_url)
                    print(f"   🗺️  Distribution from Wikidata: {filename_clean}")
                else:
                    result["photos"].append(direct_url)
    
    # PRIORITY 1: AGGRESSIVE Wikipedia HTML parsing
    if not result["distribution"] and animal_name:
        print(f"   📖 AGGRESSIVE: Parsing Wikipedia HTML for ALL images...")
        dist_map = _get_distribution_from_wikipedia(animal_name)
        if dist_map:
            result["distribution"].append(dist_map)
    
    # PRIORITY 2: Wikimedia Commons search
    if not result["distribution"] and animal_name:
        print(f"   🔍 Searching Wikimedia Commons for distribution map...")
        dist_map = _search_distribution_on_commons(animal_name)
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
