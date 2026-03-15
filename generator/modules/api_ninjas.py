# generator/modules/api_ninjas.py
"""
API Ninjas Animals API Module

Free API with pre-extracted animal facts.
Documentation: https://api-ninjas.com/api/animals
Free tier: 100 requests/month

Based on: https://api-ninjas.com/category/animals [[9]]
"""

import requests
from typing import Optional, Dict, Any

API_NINJAS_ENDPOINT = "https://api.api-ninjas.com/v1/animals"


def fetch_animal_data(name: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Fetch animal data from API Ninjas.
    
    Returns structured data including:
    - name, locations, characteristics
    - diet, length, weight, lifespan
    - top_speed, gestation_period
    
    Args:
        name: Animal common name
        api_key: API Ninjas API key (free at api-ninjas.com)
    
    Returns:
        dict: Animal data or None
    """
    
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
    except Exception as e:
        print(f" ⚠ API Ninjas error: {e}")
    
    return None


def parse_api_ninjas_result(data: Dict) -> Dict[str, Any]:
    """Parse API Ninjas result into standardized format"""
    
    return {
        "name": data.get("name"),
        "physical": {
            "length": data.get("length"),
            "weight": data.get("weight"),
            "lifespan": data.get("lifespan"),
            "top_speed": data.get("top_speed"),
        },
        "ecology": {
            "diet": data.get("diet"),
            "locations": data.get("locations"),
            "habitat": data.get("habitat"),
        },
        "reproduction": {
            "gestation_period": data.get("gestation_period"),
        },
        "characteristics": {
            "sexuality": data.get("sexuality"),
            "lifestyle": data.get("lifestyle"),
            "favorite_food": data.get("favorite_food"),
            "distinctive_features": data.get("distinctive_features"),
        }
    }
