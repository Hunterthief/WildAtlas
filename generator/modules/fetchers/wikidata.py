"""
Wikidata fetcher - ENHANCED
Now includes P2067 (mass) property extraction with animal verification
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
    if any(key in claims for key in ['P2067', 'P2048', 'P2283', 'P1347']):
        return True
    
    return False


def fetch_wikidata_mass(qid: str) -> Optional[str]:
    """Fetch mass from Wikidata property P2067"""
    try:
        response = requests.get(
            f'https://www.wikidata.org/wiki/Special:EntityData/{qid}.json',
            headers={'User-Agent': 'WildAtlas/1.0'}
        )
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        entities = data.get('entities', {})
        if not entities:
            return None
        
        entity = list(entities.values())[0]
        
        # FIXED: Verify this is actually an animal
        if not _verify_animal_entity(entity):
            print(f"⚠️  Wikidata QID {qid} does not appear to be an animal")
            return None
        
        claims = entity.get('claims', {})
        
        if 'P2067' not in claims:
            return None
        
        mass_claims = claims['P2067']
        if not mass_claims:
            return None
        
        for claim in mass_claims:
            if 'mainsnak' not in claim:
                continue
            
            mainsnak = claim['mainsnak']
            if mainsnak.get('snaktype') != 'value':
                continue
            
            if 'datavalue' not in mainsnak:
                continue
            
            datavalue = mainsnak['datavalue']
            value = datavalue.get('value', {})
            
            amount = value.get('amount', '')
            unit = value.get('unit', '')
            
            amount = amount.lstrip('+')
            
            unit_map = {
                'http://www.wikidata.org/entity/Q11573': 'kg',
                'http://www.wikidata.org/entity/Q191118': 'g',
                'http://www.wikidata.org/entity/Q1009905': 'tonnes',
                'http://www.wikidata.org/entity/Q103207': 'lbs',
            }
            
            unit_short = unit_map.get(unit, 'kg')
            
            return f"{amount} {unit_short}"
        
        return None
    
    except Exception as e:
        print(f"❌ Error fetching Wikidata mass: {e}")
        return None


def fetch_wikidata_length(qid: str) -> Optional[str]:
    """Fetch length from Wikidata property P2048"""
    try:
        response = requests.get(
            f'https://www.wikidata.org/wiki/Special:EntityData/{qid}.json',
            headers={'User-Agent': 'WildAtlas/1.0'}
        )
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        entities = data.get('entities', {})
        if not entities:
            return None
        
        entity = list(entities.values())[0]
        
        if not _verify_animal_entity(entity):
            return None
        
        claims = entity.get('claims', {})
        
        if 'P2048' not in claims:
            return None
        
        length_claims = claims['P2048']
        if not length_claims:
            return None
        
        for claim in length_claims:
            if 'mainsnak' not in claim:
                continue
            
            mainsnak = claim['mainsnak']
            if mainsnak.get('snaktype') != 'value':
                continue
            
            if 'datavalue' not in mainsnak:
                continue
            
            datavalue = mainsnak['datavalue']
            value = datavalue.get('value', {})
            
            amount = value.get('amount', '').lstrip('+')
            unit = value.get('unit', '')
            
            unit_map = {
                'http://www.wikidata.org/entity/Q828224': 'm',
                'http://www.wikidata.org/entity/Q174728': 'cm',
                'http://www.wikidata.org/entity/Q2112654': 'mm',
                'http://www.wikidata.org/entity/Q3710': 'ft',
            }
            
            unit_short = unit_map.get(unit, 'm')
            
            return f"{amount} {unit_short}"
        
        return None
    
    except Exception as e:
        print(f"❌ Error fetching Wikidata length: {e}")
        return None


def fetch_wikidata_lifespan(qid: str) -> Optional[str]:
    """Fetch lifespan from Wikidata property P2283"""
    try:
        response = requests.get(
            f'https://www.wikidata.org/wiki/Special:EntityData/{qid}.json',
            headers={'User-Agent': 'WildAtlas/1.0'}
        )
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        entities = data.get('entities', {})
        if not entities:
            return None
        
        entity = list(entities.values())[0]
        
        if not _verify_animal_entity(entity):
            return None
        
        claims = entity.get('claims', {})
        
        if 'P2283' not in claims:
            return None
        
        lifespan_claims = claims['P2283']
        if not lifespan_claims:
            return None
        
        for claim in lifespan_claims:
            if 'mainsnak' not in claim:
                continue
            
            mainsnak = claim['mainsnak']
            if mainsnak.get('snaktype') != 'value':
                continue
            
            if 'datavalue' not in mainsnak:
                continue
            
            datavalue = mainsnak['datavalue']
            value = datavalue.get('value', {})
            
            amount = value.get('amount', '').lstrip('+')
            unit = value.get('unit', '')
            
            unit_map = {
                'http://www.wikidata.org/entity/Q573': 'years',
                'http://www.wikidata.org/entity/Q5151': 'months',
            }
            
            unit_short = unit_map.get(unit, 'years')
            
            return f"{amount} {unit_short}"
        
        return None
    
    except Exception as e:
        print(f"❌ Error fetching Wikidata lifespan: {e}")
        return None


def fetch_wikidata_speed(qid: str) -> Optional[str]:
    """Fetch top speed from Wikidata property P1347"""
    try:
        response = requests.get(
            f'https://www.wikidata.org/wiki/Special:EntityData/{qid}.json',
            headers={'User-Agent': 'WildAtlas/1.0'}
        )
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        entities = data.get('entities', {})
        if not entities:
            return None
        
        entity = list(entities.values())[0]
        
        if not _verify_animal_entity(entity):
            return None
        
        claims = entity.get('claims', {})
        
        if 'P1347' not in claims:
            return None
        
        speed_claims = claims['P1347']
        if not speed_claims:
            return None
        
        for claim in speed_claims:
            if 'mainsnak' not in claim:
                continue
            
            mainsnak = claim['mainsnak']
            if mainsnak.get('snaktype') != 'value':
                continue
            
            if 'datavalue' not in mainsnak:
                continue
            
            datavalue = mainsnak['datavalue']
            value = datavalue.get('value', {})
            
            amount = value.get('amount', '').lstrip('+')
            unit = value.get('unit', '')
            
            unit_map = {
                'http://www.wikidata.org/entity/Q828224': 'm/s',
                'http://www.wikidata.org/entity/Q484640': 'km/h',
                'http://www.wikidata.org/entity/Q827583': 'mph',
            }
            
            unit_short = unit_map.get(unit, 'km/h')
            
            return f"{amount} {unit_short}"
        
        return None
    
    except Exception as e:
        print(f"❌ Error fetching Wikidata speed: {e}")
        return None


def fetch_wikidata_properties(qid: str) -> Dict[str, Optional[str]]:
    """Fetch all physical properties from Wikidata"""
    return {
        'weight': fetch_wikidata_mass(qid),
        'length': fetch_wikidata_length(qid),
        'height': None,
        'lifespan': fetch_wikidata_lifespan(qid),
        'top_speed': fetch_wikidata_speed(qid),
    }
