# generator/modules/iucn_redlist.py
"""
IUCN Red List API Module

Fetches official conservation status and threat data.
Documentation: https://apiv3.iucnredlist.org/api/v3/docs

API Key: Store in GitHub Secrets as IUCN_API_KEY
Free tier: 10,000 requests/month
"""

import requests
from typing import Optional, Dict, Any

IUCN_API_BASE = "https://apiv3.iucnredlist.org/api/v3"


def fetch_iucn_data(scientific_name: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Fetch conservation data from IUCN Red List API.
    
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
        # Step 1: Get species ID by scientific name
        # Using the taxa endpoint which is more reliable
        response = requests.get(
            f"{IUCN_API_BASE}/taxonname/gettaxonname/{scientific_name.replace(' ', '%20')}",
            params={"key": api_key},
            timeout=30
        )
        
        print(f" 📡 IUCN API Status: {response.status_code}")
        
        if response.status_code == 403:
            print(" ⚠ IUCN: Authentication failed - check API key")
            return None
        elif response.status_code != 200:
            print(f" ⚠ IUCN species lookup failed: {response.status_code}")
            return None
        
        species_data = response.json()
        results = species_data.get("result", [])
        
        if not results:
            # Try alternative: search by common name
            print(f" ⚠ IUCN: No results for {scientific_name}, trying fallback")
            return fetch_iucn_by_common_name(scientific_name.split()[0], api_key)
        
        # Get the taxon ID
        taxon_id = results[0].get("taxonid")
        if not taxon_id:
            return None
        
        # Step 2: Get detailed conservation data
        conservation_data = fetch_taxon_details(taxon_id, api_key)
        
        if conservation_data:
            conservation_data["sources"] = ["IUCN Red List"]
        
        return conservation_data
        
    except Exception as e:
        print(f" ⚠ IUCN API error: {e}")
        return None


def fetch_iucn_by_common_name(common_name: str, api_key: str) -> Optional[Dict[str, Any]]:
    """Fallback: Search by common name if scientific name fails"""
    try:
        response = requests.get(
            f"{IUCN_API_BASE}/speciesname/{common_name.replace(' ', '%20')}",
            params={"key": api_key},
            timeout=30
        )
        
        if response.status_code == 200:
            results = response.json().get("result", [])
            if results:
                taxon_id = results[0].get("taxonid")
                if taxon_id:
                    return fetch_taxon_details(taxon_id, api_key)
    except:
        pass
    return None


def fetch_taxon_details(taxon_id: int, api_key: str) -> Optional[Dict[str, Any]]:
    """Fetch detailed conservation data for a taxon ID"""
    
    try:
        # Get latest assessment
        assessment_response = requests.get(
            f"{IUCN_API_BASE}/speciesassessment/{taxon_id}",
            params={"key": api_key},
            timeout=30
        )
        
        if assessment_response.status_code != 200:
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
    """Fetch threat information for a species"""
    try:
        response = requests.get(
            f"{IUCN_API_BASE}/speciesthreats/{taxon_id}",
            params={"key": api_key},
            timeout=30
        )
        
        if response.status_code == 200:
            threats = response.json().get("result", [])
            if threats:
                threat_list = []
                for t in threats[:3]:
                    scope = t.get("scope", "")
                    if scope:
                        threat_list.append(scope)
                return ", ".join(threat_list) if threat_list else None
    except:
        pass
    return None


def fetch_population(taxon_id: int, api_key: str) -> Dict[str, Optional[str]]:
    """Fetch population data for a species"""
    try:
        response = requests.get(
            f"{IUCN_API_BASE}/speciespopulation/{taxon_id}",
            params={"key": api_key},
            timeout=30
        )
        
        if response.status_code == 200:
            pop = response.json().get("result", {})
            return {
                "trend": pop.get("trend"),
                "size": pop.get("description"),
            }
    except:
        pass
    return {"trend": None, "size": None}


def fetch_actions(taxon_id: int, api_key: str) -> Optional[str]:
    """Fetch conservation actions for a species"""
    try:
        response = requests.get(
            f"{IUCN_API_BASE}/speciesactions/{taxon_id}",
            params={"key": api_key},
            timeout=30
        )
        
        if response.status_code == 200:
            actions = response.json().get("result", [])
            if actions:
                action_list = [a.get("action_description", "") for a in actions[:3] if a.get("action_description")]
                return ", ".join(action_list) if action_list else None
    except:
        pass
    return None


def parse_conservation_status(category: Optional[str]) -> Optional[str]:
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
    
    return status_map.get(category.upper())
