# generator/modules/iucn_redlist.py
"""
IUCN Red List API Module

Fetches official conservation status and threat data.
Documentation: https://apiv4.iucnredlist.org/api/v4/docs

API Key: Store in GitHub Secrets as IUCN_API_KEY
Free tier: 10,000 requests/month

Note: IUCN API may not be accessible from all environments.
This module gracefully falls back if the API is unreachable.
"""

import requests
from typing import Optional, Dict, Any

# Try v4 first, fallback to v3 if DNS fails
IUCN_API_BASE_V4 = "https://apiv4.iucnredlist.org/api/v4"
IUCN_API_BASE_V3 = "https://apiv3.iucnredlist.org/api/v3"


def fetch_iucn_data(scientific_name: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Fetch conservation data from IUCN Red List API.
    Tries v4 first, then v3, then returns None if both fail.
    """
    
    if not api_key:
        print(" ⚠ IUCN: No API key provided")
        return None
    
    # Try v4 first
    result = _fetch_iucn_with_base(scientific_name, api_key, IUCN_API_BASE_V4)
    if result:
        return result
    
    # Fallback to v3
    print(" 🔄 IUCN: Trying v3 API as fallback...")
    result = _fetch_iucn_with_base(scientific_name, api_key, IUCN_API_BASE_V3)
    if result:
        return result
    
    # Both failed - return None gracefully
    print(" ℹ️ IUCN: API unavailable, using Wikipedia conservation data instead")
    return None


def _fetch_iucn_with_base(scientific_name: str, api_key: str, base_url: str) -> Optional[Dict[str, Any]]:
    """Internal: Fetch from specific API base URL"""
    
    try:
        # Get species by scientific name
        response = requests.get(
            f"{base_url}/species/getSpecies/{scientific_name.replace(' ', '%20')}",
            params={"key": api_key},
            timeout=15  # Shorter timeout for faster fallback
        )
        
        if response.status_code == 200:
            species_data = response.json()
            results = species_data.get("result", [])
            
            if results:
                taxon_id = results[0].get("taxonid")
                if taxon_id:
                    conservation_data = _fetch_taxon_details(taxon_id, api_key, base_url)
                    if conservation_data:
                        conservation_data["sources"] = ["IUCN Red List"]
                        return conservation_data
        
        return None
        
    except requests.exceptions.DNSResolutionError:
        print(f" ⚠ IUCN: DNS resolution failed for {base_url}")
        return None
    except requests.exceptions.ConnectionError:
        print(f" ⚠ IUCN: Connection failed for {base_url}")
        return None
    except requests.exceptions.Timeout:
        print(f" ⚠ IUCN: Timeout for {base_url}")
        return None
    except Exception as e:
        print(f" ⚠ IUCN API error ({base_url}): {e}")
        return None


def _fetch_taxon_details(taxon_id: int, api_key: str, base_url: str) -> Optional[Dict[str, Any]]:
    """Fetch detailed conservation data for a taxon ID"""
    
    try:
        # Get assessment
        assessment_response = requests.get(
            f"{base_url}/assessment/getAssessment/{taxon_id}",
            params={"key": api_key},
            timeout=15
        )
        
        if assessment_response.status_code != 200:
            return None
        
        assessment = assessment_response.json().get("result", {})
        
        # Get threats
        threats = _fetch_threats(taxon_id, api_key, base_url)
        
        # Get population data
        population = _fetch_population(taxon_id, api_key, base_url)
        
        return {
            "ecology": {
                "conservation_status": _parse_conservation_status(assessment.get("category")),
                "biggest_threat": threats,
                "population_trend": population.get("trend"),
            },
            "conservation": {
                "category": assessment.get("category"),
                "published_year": assessment.get("published_year"),
            },
            "sources": ["IUCN Red List"],
        }
        
    except Exception as e:
        print(f" ⚠ IUCN details error: {e}")
        return None


def _fetch_threats(taxon_id: int, api_key: str, base_url: str) -> Optional[str]:
    """Fetch threat information for a species"""
    try:
        response = requests.get(
            f"{base_url}/threats/getThreats/{taxon_id}",
            params={"key": api_key},
            timeout=15
        )
        
        if response.status_code == 200:
            threats = response.json().get("result", [])
            if threats:
                threat_list = [t.get("scope", "") for t in threats[:3] if t.get("scope")]
                return ", ".join(threat_list) if threat_list else None
    except:
        pass
    return None


def _fetch_population(taxon_id: int, api_key: str, base_url: str) -> Dict[str, Optional[str]]:
    """Fetch population data for a species"""
    try:
        response = requests.get(
            f"{base_url}/population/getPopulation/{taxon_id}",
            params={"key": api_key},
            timeout=15
        )
        
        if response.status_code == 200:
            pop = response.json().get("result", {})
            return {"trend": pop.get("trend"), "size": pop.get("description")}
    except:
        pass
    return {"trend": None, "size": None}


def _parse_conservation_status(category: Optional[str]) -> Optional[str]:
    """Parse IUCN category to standardized status string"""
    
    if not category:
        return None
    
    status_map = {
        "EX": "Extinct",
        "EW": "Extinct in the Wild",
        "CR": "Critically Endangered",
        "EN": "Endangered",
        "VU": "Vulnerable",
        "NT": "Near Threatened",
        "LC": "Least Concern",
        "DD": "Data Deficient",
        "NE": "Not Evaluated",
    }
    
    return status_map.get(category.upper()) or category
