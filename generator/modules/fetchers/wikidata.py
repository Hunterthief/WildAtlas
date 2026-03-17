# generator/modules/fetchers/wikidata.py
"""
Wikidata fetcher - ENHANCED
Now includes P2067 (mass) property extraction
"""
import requests
from typing import Dict, Optional, Any


def fetch_wikidata_mass(qid: str) -> Optional[str]:
    """
    Fetch mass from Wikidata property P2067
    Returns formatted weight string or None
    """
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
        claims = entity.get('claims', {})
        
        # P2067 = mass
        if 'P2067' not in claims:
            return None
        
        mass_claims = claims['P2067']
        if not mass_claims:
            return None
        
        # Get first valid mass claim
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
            
            # Extract amount and unit
            amount = value.get('amount', '')
            unit = value.get('unit', '')
            
            # Clean amount (remove + sign)
            amount = amount.lstrip('+')
            
            # Convert unit to readable format
            unit_map = {
                'http://www.wikidata.org/entity/Q11573': 'kg',  # kilogram
                'http://www.wikidata.org/entity/Q191118': 'g',   # gram
                'http://www.wikidata.org/entity/Q1009905': 'tonnes',  # tonne
                'http://www.wikidata.org/entity/Q103207': 'lbs',  # pound
            }
            
            unit_short = unit_map.get(unit, 'kg')
            
            # Check for qualifiers (min/max values)
            qualifiers = claim.get('qualifiers', {})
            
            # P1545 = series ordinal (sometimes indicates min/max)
            # P1311 = point in time
            
            # For now, return single value
            return f"{amount} {unit_short}"
        
        return None
    
    except Exception as e:
        print(f"❌ Error fetching Wikidata mass: {e}")
        return None


def fetch_wikidata_length(qid: str) -> Optional[str]:
    """
    Fetch length from Wikidata property P2048
    Returns formatted length string or None
    """
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
        claims = entity.get('claims', {})
        
        # P2048 = height/length
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
                'http://www.wikidata.org/entity/Q828224': 'm',  # metre
                'http://www.wikidata.org/entity/Q174728': 'cm',  # centimetre
                'http://www.wikidata.org/entity/Q2112654': 'mm',  # millimetre
                'http://www.wikidata.org/entity/Q3710': 'ft',  # foot
            }
            
            unit_short = unit_map.get(unit, 'm')
            
            return f"{amount} {unit_short}"
        
        return None
    
    except Exception as e:
        print(f"❌ Error fetching Wikidata length: {e}")
        return None


def fetch_wikidata_lifespan(qid: str) -> Optional[str]:
    """
    Fetch lifespan from Wikidata property P2283
    Returns formatted lifespan string or None
    """
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
        claims = entity.get('claims', {})
        
        # P2283 = lifespan
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
                'http://www.wikidata.org/entity/Q573': 'years',  # year
                'http://www.wikidata.org/entity/Q5151': 'months',  # month
            }
            
            unit_short = unit_map.get(unit, 'years')
            
            return f"{amount} {unit_short}"
        
        return None
    
    except Exception as e:
        print(f"❌ Error fetching Wikidata lifespan: {e}")
        return None


def fetch_wikidata_speed(qid: str) -> Optional[str]:
    """
    Fetch top speed from Wikidata property P1347
    Returns formatted speed string or None
    """
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
        claims = entity.get('claims', {})
        
        # P1347 = top speed
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
                'http://www.wikidata.org/entity/Q828224': 'm/s',  # metre per second
                'http://www.wikidata.org/entity/Q484640': 'km/h',  # kilometre per hour
                'http://www.wikidata.org/entity/Q827583': 'mph',  # mile per hour
            }
            
            unit_short = unit_map.get(unit, 'km/h')
            
            return f"{amount} {unit_short}"
        
        return None
    
    except Exception as e:
        print(f"❌ Error fetching Wikidata speed: {e}")
        return None


def fetch_wikidata_properties(qid: str) -> Dict[str, Optional[str]]:
    """
    Fetch all physical properties from Wikidata
    Returns dict with mass, length, lifespan, speed
    """
    return {
        'weight': fetch_wikidata_mass(qid),
        'length': fetch_wikidata_length(qid),
        'height': None,  # No specific height property, use length
        'lifespan': fetch_wikidata_lifespan(qid),
        'top_speed': fetch_wikidata_speed(qid),
    }
