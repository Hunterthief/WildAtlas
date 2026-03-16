# generator/modules/extractors/gbif_distribution.py
"""
GBIF Distribution Extractor - No API Key Required
Gets clean location and distribution data
"""
import requests
from typing import Dict, Any, Optional, List

GBIF_API = "https://api.gbif.org/v1"

def fetch_gbif_occurrences(scientific_name: str, limit: int = 100) -> Optional[Dict[str, Any]]:
    """Fetch occurrence data from GBIF"""
    try:
        url = f"{GBIF_API}/occurrence/search"
        params = {
            "scientificName": scientific_name,
            "limit": limit,
            "hasCoordinate": "true"
        }
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"   ⚠ GBIF fetch failed: {e}")
        return None

def fetch_gbif_species(scientific_name: str) -> Optional[Dict[str, Any]]:
    """Fetch species info from GBIF"""
    try:
        url = f"{GBIF_API}/species/search"
        params = {
            "q": scientific_name,
            "limit": 1
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("results"):
            return data["results"][0]
        return None
    except Exception as e:
        print(f"   ⚠ GBIF species fetch failed: {e}")
        return None

def extract_countries(occurrences: Dict[str, Any]) -> List[str]:
    """Extract unique countries from occurrence data"""
    countries = set()
    
    for result in occurrences.get("results", []):
        country = result.get("country", "")
        if country:
            countries.add(country)
    
    return sorted(list(countries))

def extract_coordinates(occurrences: Dict[str, Any]) -> Dict[str, Any]:
    """Extract coordinate bounds for distribution map"""
    lats = []
    lons = []  # ← FIXED: Removed extra indent
    
    for result in occurrences.get("results", [])[:50]:  # Sample first 50
        lat = result.get("decimalLatitude")
        lon = result.get("decimalLongitude")
        if lat and lon:
            lats.append(lat)
            lons.append(lon)
    
    if lats and lons:
        return {
            "min_lat": min(lats),
            "max_lat": max(lats),
            "min_lon": min(lons),
            "max_lon": max(lons),
            "count": len(lats)
        }
    
    return {}

def extract_habitat_from_gbif(species_data: Dict[str, Any]) -> str:
    """Extract habitat information from GBIF species data"""
    if not species_data:
        return ""
    
    # GBIF doesn't have structured habitat, but we can use description
    description = species_data.get("description", "")
    
    # Common habitat keywords
    habitat_keywords = [
        "forest", "grassland", "savanna", "desert", "wetland",
        "marine", "freshwater", "mountain", "coastal", "tropical"
    ]
    
    habitats = []
    desc_lower = description.lower()
    for keyword in habitat_keywords:
        if keyword in desc_lower:
            habitats.append(keyword)
    
    return ", ".join(habitats) if habitats else ""

def extract_gbif_all(scientific_name: str) -> Dict[str, Any]:
    """Main function - fetch all GBIF data"""
    occurrences = fetch_gbif_occurrences(scientific_name)
    species_data = fetch_gbif_species(scientific_name)
    
    result = {
        "countries": [],
        "coordinates": {},
        "habitat": "",
        "occurrence_count": 0,
        "gbif_key": ""
    }
    
    if occurrences:
        result["countries"] = extract_countries(occurrences)
        result["coordinates"] = extract_coordinates(occurrences)
        result["occurrence_count"] = occurrences.get("count", 0)
    
    if species_data:
        result["habitat"] = extract_habitat_from_gbif(species_data)
        result["gbif_key"] = species_data.get("key", "")
    
    return result
