# generator/modules/wikidata_query.py
"""
Wikidata SPARQL Query Module

Fetches structured animal data from Wikidata.
This is MORE RELIABLE than parsing Wikipedia text with regex.

Documentation: https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service
"""

import requests
from typing import Optional, Dict, Any

WIKIDATA_SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
HEADERS = {"User-Agent": "WildAtlas/1.0"}


def query_wikidata_animal(qid: str) -> Dict[str, Any]:
    """
    Query Wikidata for structured animal data using SPARQL.
    
    Properties used:
    - P225: taxon name
    - P1843: common name
    - P2043: length
    - P2048: height
    - P2067: mass
    - P2250: life expectancy
    - P1082: population
    - P1412: spoken language (for diet hints)
    - P31: instance of
    - P17: country (for locations)
    
    Based on: https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/queries/examples
    """
    
    sparql_query = f"""
    SELECT DISTINCT 
      ?common_name 
      ?length ?lengthUnit 
      ?height ?heightUnit 
      ?mass ?massUnit 
      ?life_expectancy ?life_expectancyUnit
      ?population
      ?image
      ?description
    WHERE {{
      wd:{qid} wdt:P1843 ?common_name .
      FILTER(LANG(?common_name) = "en")
      
      OPTIONAL {{ ?wd:{qid} wdt:P2043 ?length . }}
      OPTIONAL {{ ?wd:{qid} wdt:P2048 ?height . }}
      OPTIONAL {{ ?wd:{qid} p:P2067 [ps:P2067 ?mass] . }}
      OPTIONAL {{ ?wd:{qid} wdt:P2250 ?life_expectancy . }}
      OPTIONAL {{ ?wd:{qid} wdt:P1082 ?population . }}
      OPTIONAL {{ ?wd:{qid} wdt:P18 ?image . }}
      
      # Get description
      SERVICE wikibase:label {{ 
        bd:serviceParam wikibase:language "en" .
        wd:{qid} schema:description ?description .
      }}
    }}
    LIMIT 1
    """
    
    try:
        response = requests.get(
            WIKIDATA_SPARQL_ENDPOINT,
            params={"query": sparql_query, "format": "json"},
            headers=HEADERS,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", {}).get("bindings", [])
            
            if results:
                return parse_wikidata_result(results[0], qid)
    except Exception as e:
        print(f" ⚠ Wikidata query error: {e}")
    
    return {}


def parse_wikidata_result(result: Dict, qid: str) -> Dict[str, Any]:
    """Parse Wikidata SPARQL result into standardized format"""
    
    def get_value(key: str) -> Optional[str]:
        if key in result:
            return result[key].get("value")
        return None
    
    def format_quantity(value: Optional[str], unit: Optional[str]) -> Optional[str]:
        if not value:
            return None
        # Wikidata returns quantities as strings like "100" 
        # Unit would need separate lookup from Wikidata
        try:
            num = float(value)
            return f"{num:g}"
        except:
            return value
    
    return {
        "id": qid,
        "common_names": [get_value("common_name")] if get_value("common_name") else [],
        "description": get_value("description"),
        "image": get_value("image"),
        "physical": {
            "length": format_quantity(get_value("length"), get_value("lengthUnit")),
            "height": format_quantity(get_value("height"), get_value("heightUnit")),
            "weight": format_quantity(get_value("mass"), get_value("massUnit")),
            "lifespan": format_quantity(get_value("life_expectancy"), get_value("life_expectancyUnit")),
        },
        "ecology": {
            "population": get_value("population"),
        }
    }


# Example usage
if __name__ == "__main__":
    # Test with Tiger
    result = query_wikidata_animal("Q132186")
    print(result)
