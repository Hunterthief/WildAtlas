# generator/modules/fetchers/api_ninjas.py
"""
API Ninjas Animals API Module

Free API with pre-extracted animal facts.
Documentation: https://api-ninjas.com/api/animals  
Free tier: 100 requests/month
"""

import requests
from typing import Optional, Dict, Any

# ✅ FIXED: Removed trailing spaces from URL
API_NINJAS_ENDPOINT = "https://api.api-ninjas.com/v1/animals"


def fetch_animal_data(name: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Fetch animal data from API Ninjas.
    
    Args:
        name: Animal common name
        api_key: API Ninjas API key
    
    Returns:
        dict: Animal data or None
    """
    
    if not api_key:
        print(" ⚠ API Ninjas: No API key provided")
        return None
    
    try:
        print(f"   🔍 Searching Ninja API for: {name}")
        response = requests.get(
            API_NINJAS_ENDPOINT,
            params={"name": name},
            headers={"X-Api-Key": api_key},
            timeout=30
        )
        
        print(f"   📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            if results:
                print(f"   ✓ Found {len(results)} result(s) for {name}")
                return results[0]
            else:
                print(f"   ⚠ No results for {name}")
        elif response.status_code == 429:
            print(" ⚠ API Ninjas: Rate limit exceeded (100/month free tier)")
        elif response.status_code == 401:
            print(" ⚠ API Ninjas: Invalid API key")
        elif response.status_code == 403:
            print(" ⚠ API Ninjas: API key forbidden - check your plan")
        else:
            print(f" ⚠ API Ninjas: HTTP {response.status_code}")
    except Exception as e:
        print(f" ⚠ API Ninjas error: {type(e).__name__}: {e}")
    
    return None
