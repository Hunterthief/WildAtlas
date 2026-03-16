# generator/modules/api_ninjas.py
"""
API Ninjas Animals API Module

Free API with pre-extracted animal facts.
Documentation: https://api-ninjas.com/api/animals
Free tier: 100 requests/month

API returns structured data like:
{
  "name": "Cheetah",
  "taxonomy": {...},
  "locations": [...],
  "characteristics": {...}
}
"""

import requests
import re
from typing import Optional, Dict, Any, List

API_NINJAS_ENDPOINT = "https://api.api-ninjas.com/v1/animals"
DEFAULT_API_KEY = ""


def fetch_animal_data(name: str, api_key: str = None) -> Optional[Dict[str, Any]]:
    """
    Fetch animal data from API Ninjas.
    
    Args:
        name: Animal common name
        api_key: API Ninjas API key (free at api-ninjas.com)
    
    Returns:
        dict: Animal data or None
    """
    
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
            print(" ⚠ API Ninjas: Rate limit exceeded (100/month)")
        elif response.status_code == 401:
            print(" ⚠ API Ninjas: Invalid API key")
    except Exception as e:
        print(f" ⚠ API Ninjas error: {e}")
    
    return None


def parse_api_ninjas_result(data: Dict) -> Dict[str, Any]:
    """
    Parse API Ninjas result into WildAtlas standardized format.
    Maps ALL API Ninjas fields to our data structure.
    """
    
    chars = data.get("characteristics", {})
    taxonomy = data.get("taxonomy", {})
    locations = data.get("locations", [])
    
    # Parse weight string like "40kg - 65kg (88lbs - 140lbs)"
    weight = parse_weight(chars.get("weight", ""))
    
    # Parse height string like "115cm - 136cm (45in - 53in)"
    height = parse_height(chars.get("height", ""))
    
    # Parse length from various fields
    length = parse_length(chars)
    
    # Build comprehensive data structure
    return {
        "name": data.get("name"),
        "scientific_name": taxonomy.get("scientific_name"),
        "common_names": [chars.get("common_name")] if chars.get("common_name") else [],
        "description": chars.get("slogan", ""),
        "image": None,  # API Ninjas doesn't provide images
        "wikipedia_url": None,
        "classification": {
            "kingdom": taxonomy.get("kingdom"),
            "phylum": taxonomy.get("phylum"),
            "class": taxonomy.get("class"),
            "order": taxonomy.get("order"),
            "family": taxonomy.get("family"),
            "genus": taxonomy.get("genus"),
            "species": taxonomy.get("scientific_name"),
        },
        "animal_type": get_animal_type_from_taxonomy(taxonomy),
        "young_name": chars.get("name_of_young"),
        "group_name": get_group_name_from_behavior(chars.get("group_behavior")),
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
            "locations": ", ".join(locations) if locations else None,
            "group_behavior": chars.get("group_behavior"),
            "biggest_threat": chars.get("biggest_threat"),
            "distinctive_features": [chars.get("most_distinctive_feature")] if chars.get("most_distinctive_feature") else None,
            "population_trend": None,
            "conservation_status": None,  # API Ninjas doesn't provide this
        },
        "reproduction": {
            "gestation_period": chars.get("gestation_period"),
            "average_litter_size": chars.get("average_litter_size"),
            "name_of_young": chars.get("name_of_young"),
        },
        "additional_info": {
            "prey": chars.get("prey"),
            "lifestyle": chars.get("lifestyle"),
            "color": chars.get("color"),
            "skin_type": chars.get("skin_type"),
            "estimated_population": chars.get("estimated_population_size"),
            "number_of_species": chars.get("number_of_species"),
            "age_of_sexual_maturity": chars.get("age_of_sexual_maturity"),
            "age_of_weaning": chars.get("age_of_weaning"),
        },
        "sources": ["API Ninjas"],
    }


def get_animal_type_from_taxonomy(taxonomy: Dict) -> str:
    """Determine animal type from taxonomy classification"""
    class_name = taxonomy.get("class", "").lower()
    order_name = taxonomy.get("order", "").lower()
    family_name = taxonomy.get("family", "").lower()
    
    if "mammalia" in class_name:
        if "carnivora" in order_name:
            if "felidae" in family_name:
                return "feline"
            elif "canidae" in family_name:
                return "canine"
            elif "ursidae" in family_name:
                return "bear"
        return "mammal"
    elif "aves" in class_name:
        return "bird"
    elif "reptilia" in class_name:
        return "reptile"
    elif "amphibia" in class_name:
        return "amphibian"
    elif "insecta" in class_name:
        return "insect"
    
    return "default"


def get_group_name_from_behavior(behavior: str) -> str:
    """Map group behavior to group name"""
    if not behavior:
        return "population"
    
    behavior_lower = behavior.lower()
    
    if "solitary" in behavior_lower:
        return "solitary"
    elif "pair" in behavior_lower:
        return "pair"
    elif "herd" in behavior_lower:
        return "herd"
    elif "pack" in behavior_lower:
        return "pack"
    elif "colony" in behavior_lower:
        return "colony"
    elif "flock" in behavior_lower:
        return "flock"
    elif "school" in behavior_lower:
        return "school"
    
    return "population"


def parse_weight(weight_str: str) -> Optional[str]:
    """Parse weight string like '40kg - 65kg (88lbs - 140lbs)'"""
    if not weight_str:
        return None
    
    # Extract kg values
    kg_match = re.search(r'(\d+(?:\.\d+)?)\s*kg\s*-\s*(\d+(?:\.\d+)?)\s*kg', weight_str, re.I)
    if kg_match:
        return f"{kg_match.group(1)}–{kg_match.group(2)} kg"
    
    # Single kg value
    kg_single = re.search(r'(\d+(?:\.\d+)?)\s*kg', weight_str, re.I)
    if kg_single:
        return f"{kg_single.group(1)} kg"
    
    return weight_str


def parse_height(height_str: str) -> Optional[str]:
    """Parse height string like '115cm - 136cm (45in - 53in)'"""
    if not height_str:
        return None
    
    # Extract cm values
    cm_match = re.search(r'(\d+(?:\.\d+)?)\s*cm\s*-\s*(\d+(?:\.\d+)?)\s*cm', height_str, re.I)
    if cm_match:
        return f"{cm_match.group(1)}–{cm_match.group(2)} cm"
    
    # Single cm value
    cm_single = re.search(r'(\d+(?:\.\d+)?)\s*cm', height_str, re.I)
    if cm_single:
        return f"{cm_single.group(1)} cm"
    
    return height_str


def parse_length(chars: Dict) -> Optional[str]:
    """Try to get length from various characteristic fields"""
    # API Ninjas doesn't have explicit length field
    # Could potentially extract from other fields if available
    return None
