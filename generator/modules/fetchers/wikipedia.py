"""
Wikipedia data fetcher - CLEAN VERSION ✅
Focuses on Wikipedia sections ONLY
Wikidata properties handled by separate wikidata.py module
"""
import re
import requests
from typing import Dict, Optional, List, Any
from bs4 import BeautifulSoup


def fetch_wikipedia_sections(name: str) -> Dict[str, str]:
    """
    Fetch Wikipedia article sections via API
    Returns cleaned sections mapped to standard keys
    """
    try:
        # FIXED: No trailing spaces in URL
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
        
        # Get section list
        sections_list = parse_data.get('sections', [])
        for section in sections_list:
            section_title = section.get('anchor', '').lower().replace(' ', '_')
            sections[section_title] = ""
        
        # Parse HTML content
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
        
        # Clean and map sections to standard keys
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


def fetch_wikipedia_infobox(name: str) -> Dict[str, str]:
    """
    Fetch physical stats from Wikipedia infobox (simple parsing)
    Returns empty dict if not found - Wikidata is primary source for stats
    """
    try:
        # FIXED: No trailing spaces in URL
        url = f'https://en.wikipedia.org/wiki/{name.replace(" ", "_")}'
        
        response = requests.get(
            url,
            headers={
                'User-Agent': 'WildAtlas/1.0 (contact: wildatlas@example.com)'
            },
            timeout=10
        )
        
        if response.status_code != 200:
            return {}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        infobox_data = {}
        
        # Find infobox table
        infobox_table = soup.find('table', class_=lambda x: x and 'infobox' in str(x).lower())
        
        if not infobox_table:
            return {}
        
        # Get all text from infobox
        all_text = infobox_table.get_text()
        
        # Simple patterns for physical stats (fallback only)
        patterns = {
            'weight': r'(?:mass|weight)[:\s]+([0-9][0-9,\s.\-–]*\s*(?:kg|lb))',
            'length': r'(?:length)[:\s]+([0-9][0-9,\s.\-–]*\s*(?:m|cm|ft))',
            'lifespan': r'(?:lifespan|longevity)[:\s]+([0-9][0-9,\s.\-–]*\s*(?:years?))',
        }
        
        for stat_name, pattern in patterns.items():
            match = re.search(pattern, all_text, re.IGNORECASE)
            if match:
                infobox_data[stat_name] = match.group(1).strip()
        
        return infobox_data
    
    except Exception as e:
        print(f"❌ Error fetching Wikipedia infobox: {e}")
        return {}


def fetch_wikipedia_data(name: str) -> Dict[str, Any]:
    """
    Main Wikipedia fetcher - returns sections and infobox data
    Note: For physical stats, use fetch_wikidata_properties() from wikidata.py
    """
    print(f"\n{'='*80}")
    print(f"📚 Fetching Wikipedia data for: {name}")
    print(f"{'='*80}")
    
    sections = fetch_wikipedia_sections(name)
    infobox = fetch_wikipedia_infobox(name)
    
    result = {
        'sections': sections,
        'infobox': infobox,
        'has_infobox': bool(infobox),
        'has_sections': bool(sections)
    }
    
    print(f"\n📋 Wikipedia Infobox: {type(infobox).__name__} with {len(infobox)} keys")
    print(f"📦 Keys: {list(infobox.keys())}")
    print(f"{'='*80}\n")
    
    return result


if __name__ == "__main__":
    # Test the fetcher
    test_animals = ["Tiger", "Lion", "African Bush Elephant"]
    
    for animal in test_animals:
        print(f"\n{'='*80}")
        print(f"Testing: {animal}")
        print('='*80)
        data = fetch_wikipedia_data(animal)
        print(f"\n🎯 FINAL RESULT for {animal}:")
        print(f"   Infobox: {data['infobox']}")
        print(f"   Sections: {list(data['sections'].keys())}")
        print(f"\n\n")
