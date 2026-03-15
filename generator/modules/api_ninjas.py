# generator/modules/api_ninjas.py
"""
API Ninjas Animals API Module

Free API with pre-extracted animal facts.
Documentation: https://api-ninjas.com/api/animals
Free tier: 100 requests/month
"""

import requests
import re
from typing import Optional, Dict, Any, List

API_NINJAS_ENDPOINT = "https://api.api-ninjas.com/v1/animals"
DEFAULT_API_KEY = ""


def fetch_animal_data(name: str, api_key: str = None) -> Optional[Dict[str, Any]]:
    """Fetch animal data from API Ninjas."""
    
    if not api_key:
        api_key = DEFAULT_API_KEY
    
    if not api_key:
        print(" ⚠ API Ninjas: No API key provided")
        return None
    
    try:
        response = requests.get(
            API_NINJAS_ENDPOINT,
            params={"name": name},
            headers={"X-Api-Key": api_key},
            timeout=30
        )
        
        if response.status_code == 200:
            results = response.json()
            if results:
                return parse_api_ninjas_result(results[0])
        elif response.status_code == 429:
            print(" ⚠ API Ninjas: Rate limit exceeded")
        elif response.status_code == 401:
            print(" ⚠ API Ninjas: Invalid API key")
    except Exception as e:
        print(f" ⚠ API Ninjas error: {e}")
    
    return None


def parse_api_ninjas_result(data: Dict) -> Dict[str, Any]:
    """Parse API Ninjas result into WildAtlas standardized format."""
    
    chars = data.get("characteristics", {})
    locations = data.get("locations", [])
    
    # Parse weight string
    weight = parse_weight(chars.get("weight", ""))
    
    # Parse height string
    height = parse_height(chars.get("height", ""))
    
    # Parse length
    length = parse_length(chars)
    
    return {
        "name": data.get("name"),
        "scientific_name": None,
        "common_names": [data.get("name")] if data.get("name") else [],
        "description": chars.get("slogan", ""),
        "image": None,
        "classification": {
            "kingdom": data.get("taxonomy", {}).get("kingdom"),
            "phylum": data.get("taxonomy", {}).get("phylum"),
            "class": data.get("taxonomy", {}).get("class"),
            "order": data.get("taxonomy", {}).get("order"),
            "family": data.get("taxonomy", {}).get("family"),
            "genus": data.get("taxonomy", {}).get("genus"),
            "species": data.get("taxonomy", {}).get("scientific_name"),
        },
        "physical": {
            "weight": weight,
            "length": length,
            "height": height,
            "top_speed": chars.get("top_speed"),
            "lifespan": chars.get("lifespan"),
        },
        "ecology": {
            "diet": chars.get("diet"),
            "habitat": chars.get("habitat"),
            # FIX: Convert locations array to comma-separated string
            "locations": ", ".join(locations) if isinstance(locations, list) else locations,
            "group_behavior": chars.get("group_behavior"),
            "biggest_threat": chars.get("biggest_threat"),
            "distinctive_features": [chars.get("most_distinctive_feature")] if chars.get("most_distinctive_feature") else None,
        },
        "reproduction": {
            "gestation_period": chars.get("gestation_period"),
            "average_litter_size": chars.get("average_litter_size"),
            "name_of_young": chars.get("name_of_young"),
        },
        "sources": ["API Ninjas"],
    }


def parse_weight(weight_str: str) -> Optional[str]:
    """Parse weight string like '40kg - 65kg (88lbs - 140lbs)'"""
    if not weight_str:
        return None
    
    kg_match = re.search(r'(\d+(?:\.\d+)?)\s*kg\s*-\s*(\d+(?:\.\d+)?)\s*kg', weight_str, re.I)
    if kg_match:
        return f"{kg_match.group(1)}–{kg_match.group(2)} kg"
    
    kg_single = re.search(r'(\d+(?:\.\d+)?)\s*kg', weight_str, re.I)
    if kg_single:
        return f"{kg_single.group(1)} kg"
    
    return weight_str


def parse_height(height_str: str) -> Optional[str]:
    """Parse height string like '115cm - 136cm (45in - 53in)'"""
    if not height_str:
        return None
    
    cm_match = re.search(r'(\d+(?:\.\d+)?)\s*cm\s*-\s*(\d+(?:\.\d+)?)\s*cm', height_str, re.I)
    if cm_match:
        return f"{cm_match.group(1)}–{cm_match.group(2)} cm"
    
    cm_single = re.search(r'(\d+(?:\.\d+)?)\s*cm', height_str, re.I)
    if cm_single:
        return f"{cm_single.group(1)} cm"
    
    return height_str


def parse_length(chars: Dict) -> Optional[str]:
    """Try to get length from various characteristic fields"""
    return None
