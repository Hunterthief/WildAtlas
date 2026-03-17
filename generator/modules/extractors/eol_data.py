# generator/modules/extractors/eol_data.py
"""
Encyclopedia of Life Extractor - No API Key Required
Gets additional biological data
"""
import requests
from typing import Dict, Any, Optional

EOL_API = "https://eol.org/api"

def search_eol(scientific_name: str) -> Optional[str]:
    """Search for species on EOL, return page ID"""
    try:
        url = f"{EOL_API}/search/1.0.json"
        params = {"q": scientific_name, "page": 1}
        
        # FIXED: Add User-Agent header (required by EOL)
        headers = {
            "User-Agent": "WildAtlas/1.0 (https://github.com/Hunterthief/WildAtlas)",
            "Accept": "application/json"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("results"):
            # Find exact match first
            for result in data["results"]:
                if result.get("scientificName", "").lower() == scientific_name.lower():
                    return str(result.get("id"))
            # Return first result if no exact match
            return str(data["results"][0].get("id"))
        return None
    except Exception as e:
        print(f"   ⚠ EOL search failed: {e}")
        return None

def fetch_eol_data(page_id: str) -> Optional[Dict[str, Any]]:
    """Fetch detailed data from EOL page"""
    try:
        url = f"{EOL_API}/pages/{page_id}.json"
        params = {"images": 1, "subjects": 1}
        
        headers = {
            "User-Agent": "WildAtlas/1.0 (https://github.com/Hunterthief/WildAtlas)",
            "Accept": "application/json"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"   ⚠ EOL data fetch failed: {e}")
        return None

def extract_trophic_level(eol_data: Dict[str, Any]) -> str:
    """Extract trophic level (diet category) from EOL"""
    subjects = eol_data.get("subjects", [])
    
    for subject in subjects:
        if subject.get("subject") == "TrophicLevel":
            return subject.get("literal", "")
    
    return ""

def extract_life_expectancy(eol_data: Dict[str, Any]) -> str:
    """Extract life expectancy from EOL"""
    subjects = eol_data.get("subjects", [])
    
    for subject in subjects:
        if subject.get("subject") == "LifeExpectancy":
            return subject.get("literal", "")
    
    return ""

def extract_migration(eol_data: Dict[str, Any]) -> str:
    """Extract migration behavior from EOL"""
    subjects = eol_data.get("subjects", [])
    
    for subject in subjects:
        if subject.get("subject") == "Migration":
            return subject.get("literal", "")
    
    return ""

def extract_images_eol(eol_data: Dict[str, Any]) -> list:
    """Extract image URLs from EOL"""
    images = []
    data_objects = eol_data.get("dataObjects", [])
    
    for obj in data_objects[:5]:
        if obj.get("dataType") == "http://purl.org/dc/dcmitype/StillImage":
            url = obj.get("dataURL", "")
            if url:
                images.append(url)
    
    return images

def extract_eol_all(scientific_name: str) -> Dict[str, Any]:
    """Main function - fetch all EOL data"""
    page_id = search_eol(scientific_name)
    
    if not page_id:
        return {}
    
    eol_data = fetch_eol_data(page_id)
    
    if not eol_data:
        return {}
    
    return {
        "page_id": page_id,
        "eol_url": f"https://eol.org/pages/{page_id}",
        "trophic_level": extract_trophic_level(eol_data),
        "life_expectancy": extract_life_expectancy(eol_data),
        "migration": extract_migration(eol_data),
        "images": extract_images_eol(eol_data),
        "description": eol_data.get("description", "")
    }
