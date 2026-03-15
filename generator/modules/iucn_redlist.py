# generator/modules/iucn_redlist.py
"""
IUCN Red List API Module (v4)

Fetches official conservation status and threat data.
Documentation: https://apiv4.iucnredlist.org/api/v4/docs

API Key: Store in GitHub Secrets as IUCN_API_KEY
Free tier: 10,000 requests/month

v4 API Changes from v3:
- Base URL: https://apiv4.iucnredlist.org/api/v4/
- Endpoint structure changed
- Response format slightly different
"""

import requests
from typing import Optional, Dict, Any

IUCN_API_BASE = "https://apiv4.iucnredlist.org/api/v4"


def fetch_iucn_data(scientific_name: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Fetch conservation data from IUCN Red List API v4.
    
    Args:
        scientific_name: Species scientific name (e.g., "Panthera tigris")
        api_key: IUCN API key from GitHub Secrets
    
    Returns:
        dict: Conservation data or None
    """
    
    if not api_key:
        print(" ⚠ IUCN: No API key provided")
        return None
    
    try:
        # v4 API: Get species by scientific name
        # Endpoint: /species/getSpecies/{scientific_name}
        response = requests.get(
            f"{IUCN_API_BASE}/species/getSpecies/{scientific_name.replace(' ', '%20')}",
            params={"key": api_key},
            timeout=30
        )
        
        print(f" 📡 IUCN API v4 Status: {response.status_code}")
        
        if response.status_code == 403:
            print(" ⚠ IUCN: Authentication failed - check API key in GitHub Secrets")
            return None
        elif response.status_code == 404:
            print(f" ⚠ IUCN: Species not found: {scientific_name}")
            return None
        elif response.status_code == 429:
            print(" ⚠ IUCN: Rate limit exceeded (10,000 requests/month)")
            return None
        elif response.status_code != 200:
            print(f" ⚠ IUCN API error: {response.status_code} - {response.text[:200]}")
            return None
        
        species_data = response.json()
        
        # v4 API response structure: {"result": [...]}
        results = species_data.get("result", [])
        
        if not results:
            print(f" ⚠ IUCN: No results for {scientific_name}, trying common name fallback")
            return fetch_iucn_by_common_name(scientific_name.split()[0], api_key)
        
        # Get the taxon ID from first result
        taxon_id = results[0].get("taxonid")
        if not taxon_id:
            print(" ⚠ IUCN: No taxon ID in response")
            return None
        
        print(f" ✓ IUCN: Found taxon ID {taxon_id} for {scientific_name}")
        
        # Get detailed conservation data
        conservation_data = fetch_taxon_details(taxon_id, api_key)
        
        if conservation_data:
            conservation_data["sources"] = ["IUCN Red List"]
        
        return conservation_data
        
    except requests.exceptions.Timeout:
        print(" ⚠ IUCN: Request timeout")
        return None
    except requests.exceptions.RequestException as e:
        print(f" ⚠ IUCN API error: {e}")
        return None
    except Exception as e:
        print(f" ⚠ IUCN unexpected error: {e}")
        return None


def fetch_iucn_by_common_name(common_name: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Fallback: Search by common name if scientific name fails.
    v4 API: /species/getSpeciesByCommonName/{common_name}
    """
    try:
        response = requests.get(
            f"{IUCN_API_BASE}/species/getSpeciesByCommonName/{common_name.replace(' ', '%20')}",
            params={"key": api_key},
            timeout=30
        )
        
        if response.status_code == 200:
            results = response.json().get("result", [])
            if results:
                taxon_id = results[0].get("taxonid")
                if taxon_id:
                    print(f" ✓ IUCN: Found via common name, taxon ID {taxon_id}")
                    return fetch_taxon_details(taxon_id, api_key)
    except Exception as e:
        print(f" ⚠ IUCN common name search failed: {e}")
    return None


def fetch_taxon_details(taxon_id: int, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Fetch detailed conservation data for a taxon ID.
    v4 API: /assessment/getAssessment/{taxonid}
    """
    
    try:
        # Get latest assessment
        assessment_response = requests.get(
            f"{IUCN_API_BASE}/assessment/getAssessment/{taxon_id}",
            params={"key": api_key},
            timeout=30
        )
        
        if assessment_response.status_code != 200:
            print(f" ⚠ IUCN assessment lookup failed: {assessment_response.status_code}")
            return None
        
        assessment = assessment_response.json().get("result", {})
        
        # Get threats
        threats = fetch_threats(taxon_id, api_key)
        
        # Get population data
        population = fetch_population(taxon_id, api_key)
        
        # Get conservation actions
        actions = fetch_actions(taxon_id, api_key)
        
        return {
            "ecology": {
                "conservation_status": parse_conservation_status(assessment.get("category")),
                "biggest_threat": threats,
                "population_trend": population.get("trend"),
                "population_size": population.get("size"),
            },
            "conservation": {
                "category": assessment.get("category"),
                "published_year": assessment.get("published_year"),
                "rationale": assessment.get("rationale"),
                "geographic_range": assessment.get("geographic_range"),
                "conservation_actions": actions,
            },
            "sources": ["IUCN Red List"],
        }
        
    except Exception as e:
        print(f" ⚠ IUCN details error: {e}")
        return None


def fetch_threats(taxon_id: int, api_key: str) -> Optional[str]:
    """
    Fetch threat information for a species.
    v4 API: /threats/getThreats/{taxonid}
    """
    try:
        response = requests.get(
            f"{IUCN_API_BASE}/threats/getThreats/{taxon_id}",
            params={"key": api_key},
            timeout=30
        )
        
        if response.status_code == 200:
            threats = response.json().get("result", [])
            if threats:
                threat_list = []
                for t in threats[:3]:
                    # v4 API: threat data structure
                    scope = t.get("scope", "")
                    threat_type = t.get("threat_type", "")
                    if scope:
                        threat_list.append(scope)
                    elif threat_type:
                        threat_list.append(threat_type)
                return ", ".join(threat_list) if threat_list else None
    except Exception as e:
        print(f" ⚠ IUCN threats error: {e}")
    return None


def fetch_population(taxon_id: int, api_key: str) -> Dict[str, Optional[str]]:
    """
    Fetch population data for a species.
    v4 API: /population/getPopulation/{taxonid}
    """
    try:
        response = requests.get(
            f"{IUCN_API_BASE}/population/getPopulation/{taxon_id}",
            params={"key": api_key},
            timeout=30
        )
        
        if response.status_code == 200:
            pop = response.json().get("result", {})
            return {
                "trend": pop.get("trend"),
                "size": pop.get("description") or pop.get("size"),
            }
    except Exception as e:
        print(f" ⚠ IUCN population error: {e}")
    return {"trend": None, "size": None}


def fetch_actions(taxon_id: int, api_key: str) -> Optional[str]:
    """
    Fetch conservation actions for a species.
    v4 API: /actions/getActions/{taxonid}
    """
    try:
        response = requests.get(
            f"{IUCN_API_BASE}/actions/getActions/{taxon_id}",
            params={"key": api_key},
            timeout=30
        )
        
        if response.status_code == 200:
            actions = response.json().get("result", [])
            if actions:
                action_list = []
                for a in actions[:3]:
                    desc = a.get("action_description") or a.get("description")
                    if desc:
                        action_list.append(desc)
                return ", ".join(action_list) if action_list else None
    except Exception as e:
        print(f" ⚠ IUCN actions error: {e}")
    return None


def parse_conservation_status(category: Optional[str]) -> Optional[str]:
    """
    Parse IUCN category to standardized status string.
    
    IUCN Red List Categories:
    - EX: Extinct
    - EW: Extinct in the Wild
    - CR: Critically Endangered
    - EN: Endangered
    - VU: Vulnerable
    - NT: Near Threatened
    - LC: Least Concern
    - DD: Data Deficient
    - NE: Not Evaluated
    """
    
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
    
    # Handle full category names too
    full_name_map = {
        "Critically Endangered": "Critically Endangered",
        "Endangered": "Endangered",
        "Vulnerable": "Vulnerable",
        "Near Threatened": "Near Threatened",
        "Least Concern": "Least Concern",
        "Data Deficient": "Data Deficient",
        "Not Evaluated": "Not Evaluated",
        "Extinct": "Extinct",
        "Extinct in the Wild": "Extinct in the Wild",
    }
    
    return status_map.get(category.upper()) or full_name_map.get(category)


# Test function
if __name__ == "__main__":
    import os
    api_key = os.environ.get("IUCN_API_KEY", "")
    
    # Test with Tiger
    print("Testing IUCN API v4 with Panthera tigris...")
    result = fetch_iucn_data("Panthera tigris", api_key)
    print(result)
