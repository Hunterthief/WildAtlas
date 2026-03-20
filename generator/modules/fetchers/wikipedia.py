"""
Wikipedia data fetcher - PROFESSIONAL VERSION ✅
Uses Wikidata API for structured data (not regex scraping)
Sources: Wikidata, DBPedia, Wikipedia API
"""
import re
import requests
from typing import Dict, Optional, List, Any
from bs4 import BeautifulSoup


# =============================================================================
# WIKIDATA PROPERTY MAPPINGS FOR ANIMALS
# =============================================================================
WIKIDATA_PROPERTIES = {
    'weight': ['P2067'],      # mass
    'length': ['P2048'],      # height/length
    'height': ['P2048'],      # height
    'lifespan': ['P2250'],    # longevity
    'top_speed': ['P6137'],   # maximum speed
    'diet': ['P1009'],        # diet
    'habitat': ['P1009'],     # habitat
}


def fetch_wikidata_properties(qid: str) -> Dict[str, str]:
    """
    Fetch structured physical stats from Wikidata API
    This is RELIABLE - no regex parsing needed!
    """
    if not qid or not qid.startswith('Q'):
        print(f"⚠️ Invalid QID: {qid}")
        return {}
    
    try:
        url = f'https://www.wikidata.org/wiki/Special:EntityData/{qid}.json'
        print(f"🔗 Fetching Wikidata: {url}")
        
        response = requests.get(
            url,
            headers={'User-Agent': 'WildAtlas/1.0 (contact: wildatlas@example.com)'},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"⚠️ HTTP {response.status_code} from Wikidata")
            return {}
        
        data = response.json()
        entity = data.get('entities', {}).get(qid, {})
        claims = entity.get('claims', {})
        
        wikidata_stats = {}
        
        # Extract mass (weight) - P2067
        if 'P2067' in claims:
            for claim in claims['P2067']:
                mainsnak = claim.get('mainsnak', {})
                datavalue = mainsnak.get('datavalue', {})
                value = datavalue.get('value', {})
                amount = value.get('amount', '')
                unit = value.get('unit', '')
                
                if amount:
                    amount = amount.lstrip('+')
                    if 'kilogram' in unit:
                        wikidata_stats['weight'] = f"{amount} kg"
                    elif 'gram' in unit:
                        wikidata_stats['weight'] = f"{float(amount)/1000} kg"
                    elif 'pound' in unit:
                        wikidata_stats['weight'] = f"{amount} lb"
                    else:
                        wikidata_stats['weight'] = f"{amount}"
                    print(f"   ✅ Wikidata weight: {wikidata_stats['weight']}")
                    break
        
        # Extract height/length - P2048
        if 'P2048' in claims:
            for claim in claims['P2048']:
                mainsnak = claim.get('mainsnak', {})
                datavalue = mainsnak.get('datavalue', {})
                value = datavalue.get('value', {})
                amount = value.get('amount', '').lstrip('+')
                unit = value.get('unit', '')
                
                if amount:
                    if 'meter' in unit:
                        wikidata_stats['length'] = f"{amount} m"
                    elif 'centimeter' in unit:
                        wikidata_stats['length'] = f"{float(amount)/100} m"
                    elif 'foot' in unit:
                        wikidata_stats['length'] = f"{amount} ft"
                    else:
                        wikidata_stats['length'] = f"{amount}"
                    print(f"   ✅ Wikidata length: {wikidata_stats['length']}")
                    break
        
        # Extract lifespan - P2250
        if 'P2250' in claims:
            for claim in claims['P2250']:
                mainsnak = claim.get('mainsnak', {})
                datavalue = mainsnak.get('datavalue', {})
                value = datavalue.get('value', {})
                amount = value.get('amount', '').lstrip('+')
                unit = value.get('unit', '')
                
                if amount:
                    if 'year' in unit:
                        wikidata_stats['lifespan'] = f"{amount} years"
                    else:
                        wikidata_stats['lifespan'] = f"{amount}"
                    print(f"   ✅ Wikidata lifespan: {wikidata_stats['lifespan']}")
                    break
        
        # Extract speed - P6137
        if 'P6137' in claims:
            for claim in claims['P6137']:
                mainsnak = claim.get('mainsnak', {})
                datavalue = mainsnak.get('datavalue', {})
                value = datavalue.get('value', {})
                amount = value.get('amount', '').lstrip('+')
                unit = value.get('unit', '')
                
                if amount:
                    if 'kilometre' in unit:
                        wikidata_stats['top_speed'] = f"{amount} km/h"
                    elif 'mile' in unit:
                        wikidata_stats['top_speed'] = f"{amount} mph"
                    else:
                        wikidata_stats['top_speed'] = f"{amount}"
                    print(f"   ✅ Wikidata speed: {wikidata_stats['top_speed']}")
                    break
        
        print(f"✅ Wikidata: Found {len(wikidata_stats)} physical stats")
        return wikidata_stats
    
    except Exception as e:
        print(f"❌ Error fetching Wikidata: {e}")
        return {}


def fetch_dbpedia_properties(name: str) -> Dict[str, str]:
    """
    Fetch physical stats from DBPedia (structured Wikipedia data)
    DBPedia extracts infobox data into a queryable database
    """
    try:
        resource_name = name.replace(' ', '_')
        url = f'http://dbpedia.org/data/{resource_name}.json'
        print(f"🔗 Fetching DBPedia: {url}")
        
        response = requests.get(
            url,
            headers={'User-Agent': 'WildAtlas/1.0 (contact: wildatlas@example.com)'},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"⚠️ HTTP {response.status_code} from DBPedia")
            return {}
        
        data = response.json()
        resource_key = f'http://dbpedia.org/resource/{resource_name}'
        resource_data = data.get(resource_key, {})
        
        dbpedia_stats = {}
        
        property_mappings = {
            'http://dbpedia.org/ontology/mass': 'weight',
            'http://dbpedia.org/ontology/length': 'length',
            'http://dbpedia.org/ontology/height': 'height',
            'http://dbpedia.org/ontology/lifespan': 'lifespan',
            'http://dbpedia.org/ontology/speed': 'top_speed',
        }
        
        for dbpedia_prop, our_key in property_mappings.items():
            if dbpedia_prop in resource_data:
                values = resource_data[dbpedia_prop]
                if values:
                    value = values[0].get('value', '')
                    if value:
                        dbpedia_stats[our_key] = str(value)
                        print(f"   ✅ DBPedia {our_key}: {value}")
        
        print(f"✅ DBPedia: Found {len(dbpedia_stats)} physical stats")
        return dbpedia_stats
    
    except Exception as e:
        print(f"❌ Error fetching DBPedia: {e}")
        return {}


def fetch_wikipedia_sections(name: str) -> Dict[str, str]:
    """Fetch Wikipedia article sections"""
    try:
        response = requests.get(
            'https://en.wikipedia.org/w/api.php',
            params={
                'action': 'parse',
                'page': name,
                'format': 'json',
                'prop': 'sections|text',
                'redirects': 1
            },
            headers={'User-Agent': 'WildAtlas/1.0 (contact: wildatlas@example.com)'},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"⚠️ HTTP {response.status_code} for sections of {name}")
            return {}
        
        data = response.json()
        if 'error' in data:
            print(f"⚠️ API Error: {data['error']}")
            return {}
        
        sections = {}
        parse_data = data.get('parse', {})
        
        sections_list = parse_data.get('sections', [])
        for section in sections_list:
            section_title = section.get('anchor', '').lower().replace(' ', '_')
            sections[section_title] = ""
        
        html_content = parse_data.get('text', {}).get('*', '')
        if html_content:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            current_section = 'description'
            for element in soup.find_all(['h2', 'h3', 'p', 'ul', 'ol']):
                if element.name in ['h2', 'h3']:
                    section_title = element.get_text().strip().lower().replace(' ', '_')
                    section_title = re.sub(r'[\[\]\d]', '', section_title)
                    current_section = section_title
                else:
                    text = element.get_text().strip()
                    if text:
                        if current_section not in sections:
                            sections[current_section] = text
                        else:
                            sections[current_section] += ' ' + text
        
        cleaned_sections = {}
        for key, value in sections.items():
            key = re.sub(r'[\[\]\d]', '', key)
            key = key.replace(' ', '_').lower()
            
            section_mapping = {
                'description': ['description', 'summary', 'intro', 'introduction'],
                'size': ['size', 'dimensions', 'physical_description', 'physical_characteristics'],
                'behavior': ['behavior', 'behaviour', 'habits'],
                'habitat': ['habitat', 'distribution_and_habitat', 'range_and_habitat'],
                'diet': ['diet', 'feeding', 'hunting_diet', 'food'],
                'reproduction': ['reproduction', 'breeding', 'life_cycle'],
                'conservation': ['conservation', 'conservation_status', 'threats'],
            }
            
            for standard_name, variations in section_mapping.items():
                if key in variations or any(v in key for v in variations):
                    cleaned_sections[standard_name] = value
                    break
            else:
                cleaned_sections[key] = value
        
        print(f"✅ Found {len(cleaned_sections)} Wikipedia sections for {name}")
        return cleaned_sections
    
    except Exception as e:
        print(f"❌ Error fetching Wikipedia sections: {e}")
        return {}


def fetch_wikipedia_infobox(name: str, qid: str = None) -> Dict[str, str]:
    """
    PROFESSIONAL VERSION: Uses Wikidata + DBPedia instead of regex scraping
    Priority: Wikidata > DBPedia > Wikipedia text (fallback only)
    """
    print(f"\n📊 Fetching structured physical stats for: {name}")
    
    infobox_data = {}
    
    # ===== PRIORITY 1: Wikidata (Most Reliable) =====
    print("\n🔍 PRIORITY 1: Wikidata API...")
    if qid:
        wikidata_stats = fetch_wikidata_properties(qid)
        infobox_data.update(wikidata_stats)
    
    # ===== PRIORITY 2: DBPedia (Structured Wikipedia) =====
    if not infobox_data:
        print("\n🔍 PRIORITY 2: DBPedia...")
        dbpedia_stats = fetch_dbpedia_properties(name)
        infobox_data.update(dbpedia_stats)
    
    # ===== PRIORITY 3: Wikipedia sections (Fallback only) =====
    if not infobox_data:
        print("\n🔍 PRIORITY 3: Wikipedia sections (fallback)...")
        sections = fetch_wikipedia_sections(name)
        
        if 'physical_characteristics' in sections:
            text = sections['physical_characteristics']
            conservative_patterns = {
                'weight': r'(?:weighs?|weight|mass)[:\s]+([0-9]+\s*(?:kg|lb))',
                'length': r'(?:length|measures?)[:\s]+([0-9]+\s*(?:m|cm|ft))',
                'lifespan': r'(?:lifespan|longevity)[:\s]+([0-9]+\s*years?)',
            }
            
            for stat_name, pattern in conservative_patterns.items():
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    infobox_data[stat_name] = match.group(1).strip()
                    print(f"   ✅ From text: {stat_name} = {infobox_data[stat_name]}")
    
    print(f"\n✅ TOTAL: Found {len(infobox_data)} physical stats")
    print(f"📦 Keys: {list(infobox_data.keys())}")
    print(f"🎯 Data: {infobox_data}")
    
    return infobox_data


def fetch_wikipedia_data(name: str, qid: str = None) -> Dict[str, Any]:
    """
    Main fetcher - uses structured data sources
    """
    print(f"\n{'='*80}")
    print(f"📚 Fetching data for: {name} (QID: {qid})")
    print(f"{'='*80}")
    
    sections = fetch_wikipedia_sections(name)
    infobox = fetch_wikipedia_infobox(name, qid)
    
    result = {
        'sections': sections,
        'infobox': infobox,
        'has_infobox': bool(infobox),
        'has_sections': bool(sections)
    }
    
    print(f"\n📋 FINAL Infobox: {type(infobox).__name__} with {len(infobox)} keys")
    print(f"📦 Final Keys: {list(infobox.keys())}")
    print(f"{'='*80}\n")
    
    return result


if __name__ == "__main__":
    test_animals = [
        {"name": "Tiger", "qid": "Q132186"},
        {"name": "Lion", "qid": "Q140"},
        {"name": "African Bush Elephant", "qid": "Q7372"},
    ]
    
    for animal in test_animals:
        data = fetch_wikipedia_data(animal["name"], animal["qid"])
        print(f"\n🎯 FINAL RESULT for {animal['name']}:")
        print(f"   Infobox: {data['infobox']}")
        print(f"\n\n")
