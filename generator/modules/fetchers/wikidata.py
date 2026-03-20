"""
Wikidata fetcher - OPTIMIZED ✅
Single API call for all properties
ALL URL SPACES FIXED + Spaces replaced with underscores
"""
import requests
from typing import Dict, Optional, Any


def _verify_animal_entity(entity: Dict[str, Any]) -> bool:
    """Verify this Wikidata entity is actually an animal"""
    claims = entity.get('claims', {})
    
    # Check P31 (instance of) for animal-related values
    p31_claims = claims.get('P31', [])
    animal_qids = ['Q729', 'Q16521', 'Q11968521', 'Q1088412']
    
    for claim in p31_claims:
        if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
            value = claim['mainsnak']['datavalue'].get('value', {})
            if isinstance(value, dict):
                entity_id = value.get('id', '')
                if any(aqid in entity_id for aqid in animal_qids):
                    return True
    
    # Check if taxonomy claims exist
    if any(key in claims for key in ['P171', 'P175', 'P105', 'P1076']):
        return True
    
    # Check for common animal properties
    if any(key in claims for key in ['P2067', 'P2048', 'P2283', 'P6137']):
        return True
    
    return False


def _extract_quantity_value(claim: Dict[str, Any], unit_map: Dict[str, str], default_unit: str) -> Optional[str]:
    """Extract quantity value from a Wikidata claim"""
    mainsnak = claim.get('mainsnak', {})
    if mainsnak.get('snaktype') != 'value':
        return None
    
    datavalue = mainsnak.get('datavalue', {})
    value = datavalue.get('value', {})
    
    amount = value.get('amount', '').lstrip('+')
    unit = value.get('unit', '')
    
    unit_short = unit_map.get(unit, default_unit)
    
    return f"{amount} {unit_short}" if amount else None


def fetch_wikidata_properties(qid: str) -> Dict[str, Optional[str]]:
    """
    Fetch ALL physical properties from Wikidata in ONE API call ✅
    Returns dict with weight, length, lifespan, top_speed
    """
    if not qid or not qid.startswith('Q'):
        print(f"⚠️ Invalid QID: {qid}")
        return {}
    
    try:
        print(f"🔗 Fetching Wikidata: {qid}")
        
        # FIXED: No spaces in URL
        response = requests.get(
            f'https://www.wikidata.org/wiki/Special:EntityData/{qid}.json',
            headers={'User-Agent': 'WildAtlas/1.0 (contact: wildatlas@example.com)'},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"⚠️ HTTP {response.status_code} from Wikidata")
            return {}
        
        data = response.json()
        entities = data.get('entities', {})
        if not entities:
            return {}
        
        entity = list(entities.values())[0]
        
        # Verify this is an animal
        if not _verify_animal_entity(entity):
            print(f"⚠️ Wikidata QID {qid} does not appear to be an animal")
            return {}
        
        claims = entity.get('claims', {})
        result = {}
        
        # ===== Weight (P2067 - mass) =====
        if 'P2067' in claims:
            unit_map = {
                'http://www.wikidata.org/entity/Q11573': 'kg',
                'http://www.wikidata.org/entity/Q191118': 'g',
                'http://www.wikidata.org/entity/Q1009905': 'tonnes',
                'http://www.wikidata.org/entity/Q103207': 'lb',
            }
            for claim in claims['P2067']:
                value = _extract_quantity_value(claim, unit_map, 'kg')
                if value:
                    result['weight'] = value
                    print(f"   ✅ Weight: {value}")
                    break
        
        # ===== Length (P2048 - height/length) =====
        if 'P2048' in claims:
            unit_map = {
                'http://www.wikidata.org/entity/Q828224': 'm',
                'http://www.wikidata.org/entity/Q174728': 'cm',
                'http://www.wikidata.org/entity/Q2112654': 'mm',
                'http://www.wikidata.org/entity/Q3710': 'ft',
            }
            for claim in claims['P2048']:
                value = _extract_quantity_value(claim, unit_map, 'm')
                if value:
                    result['length'] = value
                    print(f"   ✅ Length: {value}")
                    break
        
        # ===== Lifespan (P2283 - life expectancy) =====
        if 'P2283' in claims:
            unit_map = {
                'http://www.wikidata.org/entity/Q573': 'years',
                'http://www.wikidata.org/entity/Q5151': 'months',
            }
            for claim in claims['P2283']:
                value = _extract_quantity_value(claim, unit_map, 'years')
                if value:
                    result['lifespan'] = value
                    print(f"   ✅ Lifespan: {value}")
                    break
        
        # ===== Top Speed (P6137 - maximum speed) =====
        if 'P6137' in claims:
            unit_map = {
                'http://www.wikidata.org/entity/Q828224': 'm/s',
                'http://www.wikidata.org/entity/Q484640': 'km/h',
                'http://www.wikidata.org/entity/Q827583': 'mph',
            }
            for claim in claims['P6137']:
                value = _extract_quantity_value(claim, unit_map, 'km/h')
                if value:
                    result['top_speed'] = value
                    print(f"   ✅ Speed: {value}")
                    break
        
        print(f"✅ Wikidata: Found {len(result)} physical stats")
        return result
    
    except Exception as e:
        print(f"❌ Error fetching Wikidata: {e}")
        return {}


# Keep individual functions for backward compatibility
def fetch_wikidata_mass(qid: str) -> Optional[str]:
    """Fetch mass from Wikidata property P2067"""
    result = fetch_wikidata_properties(qid)
    return result.get('weight')


def fetch_wikidata_length(qid: str) -> Optional[str]:
    """Fetch length from Wikidata property P2048"""
    result = fetch_wikidata_properties(qid)
    return result.get('length')


def fetch_wikidata_lifespan(qid: str) -> Optional[str]:
    """Fetch lifespan from Wikidata property P2283"""
    result = fetch_wikidata_properties(qid)
    return result.get('lifespan')


def fetch_wikidata_speed(qid: str) -> Optional[str]:
    """Fetch top speed from Wikidata property P6137"""
    result = fetch_wikidata_properties(qid)
    return result.get('top_speed')
