"""
Wikipedia data fetcher - FULLY FIXED ✅
Properly extracts infobox data from rendered HTML
"""
import re
import requests
from typing import Dict, Optional, List, Any
from bs4 import BeautifulSoup


def fetch_wikipedia_sections(name: str) -> Dict[str, str]:
    """Fetch Wikipedia article sections"""
    try:
        # FIXED: Removed trailing spaces from URL
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


def fetch_wikipedia_infobox(name: str) -> Dict[str, str]:
    """
    Extract data from Wikipedia infobox - FIXED VERSION ✅
    Fetches rendered HTML and parses the infobox table directly
    Returns dict with weight, length, height, lifespan, speed if found
    """
    try:
        # FIXED: Removed trailing spaces from URL
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
        
        print(f"✅ Found infobox table for {name}")
        
        infobox_data = {}
        
        # Extract all rows from infobox
        rows = infobox_table.find_all('tr')
        
        # Keywords mapping for physical stats - EXPANDED
        stat_keywords = {
            'weight': ['mass', 'weight', 'body mass', 'avg mass', 'average mass'],
            'length': ['length', 'body length', 'total length', 'size', 'avg length'],
            'height': ['height', 'shoulder height', 'standing height', 'avg height'],
            'lifespan': ['lifespan', 'longevity', 'life span', 'average lifespan'],
            'top_speed': ['speed', 'top speed', 'maximum speed', 'max speed'],
        }
        
        for row in rows:
            header_cell = row.find('th')
            data_cell = row.find('td')
            
            if not header_cell or not data_cell:
                continue
            
            header_text = header_cell.get_text().strip().lower()
            data_text = data_cell.get_text().strip()
            
            # Skip empty or very short values
            if len(data_text) < 2:
                continue
            
            # Clean the data text - remove citations, references, etc.
            data_text = re.sub(r'\[\d+\]', '', data_text)
            data_text = re.sub(r'\[\^\d+\]', '', data_text)
            data_text = re.sub(r'\s+', ' ', data_text)
            data_text = data_text.strip()
            
            # Match against our stat keywords
            for stat_name, keywords in stat_keywords.items():
                if any(keyword in header_text for keyword in keywords):
                    if stat_name not in infobox_data:  # Don't overwrite if already found
                        infobox_data[stat_name] = data_text
                        print(f"   📊 {stat_name}: {data_text}")
                    break
        
        if infobox_data:
            print(f"✅ Found infobox data for {name}: {list(infobox_data.keys())}")
        else:
            print(f"⚠️ Infobox found but no matching stats for {name}")
            # Debug: print all row headers to see what's available
            print("   Available infobox fields:")
            for row in rows[:10]:
                th = row.find('th')
                td = row.find('td')
                if th and td:
                    print(f"      - {th.get_text().strip()}: {td.get_text().strip()[:50]}")
        
        return infobox_data
    
    except Exception as e:
        print(f"❌ Error fetching Wikipedia infobox: {e}")
        import traceback
        traceback.print_exc()
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


if __name__ == "__main__":
    # Test the fetcher
    test_animals = ["Tiger", "African Bush Elephant", "Lion", "Giraffe"]
    
    for animal in test_animals:
        print(f"\n{'='*60}")
        print(f"Testing: {animal}")
        print('='*60)
        data = fetch_wikipedia_data(animal)
        print(f"\nFinal Result: {data['infobox']}")
