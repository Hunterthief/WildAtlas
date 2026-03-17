# generator/modules/extractors/wikidata_enhancer.py

def extract_conservation_status(wikidata: Dict[str, Any]) -> Dict[str, str]:
    """Extract IUCN conservation status from Wikidata"""
    if not wikidata:
        return {"status": "", "status_id": ""}
    
    claims = wikidata.get("claims", {})
    
    # P141 = IUCN conservation status
    status_claims = claims.get("P141", [])
    
    # EXPANDED status mapping with more QIDs
    status_map = {
        # Least Concern
        "Q75807": "Least Concern",
        "Q13478884": "Least Concern",
        
        # Near Threatened
        "Q192072": "Near Threatened",
        "Q13478882": "Near Threatened",
        
        # Vulnerable
        "Q192076": "Vulnerable",
        "Q13478880": "Vulnerable",
        
        # Endangered
        "Q192078": "Endangered",
        "Q13478878": "Endangered",
        
        # Critically Endangered
        "Q192082": "Critically Endangered",
        "Q13478876": "Critically Endangered",
        
        # Extinct in the Wild
        "Q23037168": "Extinct in the Wild",
        
        # Extinct
        "Q192086": "Extinct",
        "Q13478874": "Extinct",
        
        # Data Deficient
        "Q873109": "Data Deficient",
        "Q13478886": "Data Deficient",
        
        # Not Evaluated
        "Q873116": "Not Evaluated",
        "Q13478888": "Not Evaluated"
    }
    
    if status_claims:
        status_id = status_claims[0].get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id", "")
        return {
            "status": status_map.get(status_id, "Unknown"),
            "status_id": status_id
        }
    
    return {"status": "", "status_id": ""}
