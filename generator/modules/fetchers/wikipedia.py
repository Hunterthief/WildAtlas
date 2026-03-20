"""
Wikipedia data fetcher - FIXED ✅
Properly extracts infobox data from rendered HTML
"""
import re
import requests
from typing import Dict, Optional, List, Any
from bs4 import BeautifulSoup


def fetch_wikipedia_sections(name: str) -> Dict[str, str]:
    """Fetch Wikipedia article sections"""
    try:
        response = requests.get(
            'https://en.wikipedia.org/w/api.php',  # FIXED: removed trailing spaces
            params={
                'action': 'parse',
                'page': name,
                'format': 'json',
                'prop': 'sections|text',
                'redirects': 1
            },
            headers={'User-Agent': 'WildAtlas/1.0'}
        )
        
        if response.status_code != 200:
            return {}
        
        data = response.json()
        if 'error' in data:
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
        
        return cleaned_sections
    
    except Exception as e:
        print(f"❌ Error fetching Wikipedia sections: {e}")
        return {}


def fetch_wikipedia_infobox(name: str) -> Dict[str, str]:
    """
    Extract data from Wikipedia infobox - FIXED VERSION ✅
    Fetches rendered HTML and parses the infobox table directly
    Returns dict with weight, length, height, lifespan, speed if found
    """
    try:
        # FIXED: Fetch the actual article HTML to parse infobox table
        response = requests.get(
            f'https://en.wikipedia.org/wiki/{name}',
            headers={
                'User-Agent': 'WildAtlas/1.0 (contact: wildatlas@example.com)'
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"⚠️ HTTP {response.status_code} for {name}")
            return {}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the infobox table - multiple possible class names
        infobox_table = soup.find('table', class_=lambda x: x and 'infobox' in x.lower())
        
        if not infobox_table:
            print(f"⚠️ No infobox found for {name}")
            return {}
        
        infobox_data = {}
        
        # Extract all rows from infobox
        rows = infobox_table.find_all('tr')
        
        # Keywords mapping for physical stats
        stat_keywords = {
            'weight': ['mass', 'weight', 'body mass'],
            'length': ['length', 'body length', 'total length', 'size'],
            'height': ['height', 'shoulder height', 'standing height'],
            'lifespan': ['lifespan', 'longevity', 'life span'],
            'top_speed': ['speed', 'top speed', 'maximum speed'],
        }
        
        for row in rows:
            header_cell = row.find('th')
            data_cell = row.find('td')
            
            if not header_cell or not data_cell:
                continue
            
            header_text = header_cell.get_text().strip().lower()
            data_text = data_cell.get_text().strip()
            
            # Clean the data text - remove citations, references, etc.
            data_text = re.sub(r'\[\d+\]', '', data_text)
            data_text = re.sub(r'\[\^\d+\]', '', data_text)
            data_text = ' '.join(data_text.split())
            
            # Match against our stat keywords
            for stat_name, keywords in stat_keywords.items():
                if any(keyword in header_text for keyword in keywords):
                    if stat_name not in infobox_data:  # Don't overwrite if already found
                        infobox_data[stat_name] = data_text
                    break
        
        if infobox_data:
            print(f"✅ Found infobox data for {name}: {list(infobox_data.keys())}")
        else:
            print(f"⚠️ Infobox found but no matching stats for {name}")
        
        return infobox_data
    
    except Exception as e:
        print(f"❌ Error fetching Wikipedia infobox: {e}")
        return {}


def fetch_wikipedia_data(name: str) -> Dict[str, Any]:
    """
    Main Wikipedia fetcher - combines sections and infobox
    Returns combined data structure
    """
    print(f"📚 Fetching Wikipedia data for: {name}")
    
    sections = fetch_wikipedia_sections(name)
    infobox = fetch_wikipedia_infobox(name)
    
    result = {
        'sections': sections,
        'infobox': infobox,
        'has_infobox': bool(infobox),
        'has_sections': bool(sections)
    }
    
    print(f"📋 Infobox: {type(infobox).__name__} with {len(infobox)} keys")
    print(f"📦 Keys: {list(infobox.keys())}")
    
    return result
