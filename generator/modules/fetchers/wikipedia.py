"""
Wikipedia data fetcher - DEBUG VERSION 🔍
Dumps ALL infobox data without filtering to verify fetching works
"""
import re
import requests
from typing import Dict, Optional, List, Any
from bs4 import BeautifulSoup


def fetch_wikipedia_sections(name: str) -> Dict[str, str]:
    """Fetch Wikipedia article sections"""
    try:
        # FIXED: NO trailing spaces!
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
    DEBUG VERSION - Dumps ALL infobox data without filtering 🔍
    """
    try:
        # FIXED: NO trailing spaces! Clean URL construction
        url = f'https://en.wikipedia.org/wiki/{name.replace(" ", "_")}'
        print(f"🔗 Requesting URL: {url}")
        
        response = requests.get(
            url,
            headers={
                'User-Agent': 'WildAtlas/1.0 (contact: wildatlas@example.com)'
            },
            timeout=10
        )
        
        print(f"📡 HTTP Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"⚠️ HTTP {response.status_code} for {name}")
            return {}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Debug: Check page title to verify we got the right page
        page_title = soup.find('h1', id='firstHeading')
        if page_title:
            print(f"📄 Page Title: {page_title.get_text()}")
        
        # Find ALL tables with infobox in class name
        print("\n🔍 Searching for infobox tables...")
        all_tables = soup.find_all('table')
        print(f"   Total tables on page: {len(all_tables)}")
        
        infobox_tables = []
        for i, table in enumerate(all_tables):
            class_attr = table.get('class', [])
            class_str = ' '.join(class_attr) if isinstance(class_attr, list) else str(class_attr)
            if 'infobox' in class_str.lower():
                infobox_tables.append(table)
                print(f"   ✅ Found infobox table #{len(infobox_tables)} with class: '{class_str}'")
        
        if not infobox_tables:
            print(f"⚠️ NO infobox tables found for {name}")
            print("   Searching for ANY table...")
            for i, table in enumerate(all_tables[:5]):
                class_attr = table.get('class', [])
                print(f"   Table #{i}: class='{class_attr}'")
            return {}
        
        # Use the first infobox table
        infobox_table = infobox_tables[0]
        print(f"\n✅ Using infobox table for {name}")
        
        # DUMP ALL ROWS - NO FILTERING
        infobox_data = {}
        rows = infobox_table.find_all('tr')
        print(f"📊 Total rows in infobox: {len(rows)}")
        
        print("\n📋 DUMPING ALL INFOBOX ROWS:")
        print("=" * 80)
        
        for i, row in enumerate(rows):
            header_cell = row.find('th')
            data_cell = row.find('td')
            
            header_text = header_cell.get_text().strip() if header_cell else ""
            data_text = data_cell.get_text().strip() if data_cell else ""
            
            # Clean citations from data
            data_text = re.sub(r'\[\d+\]', '', data_text)
            data_text = ' '.join(data_text.split())
            
            print(f"   Row {i:2d} | Header: {header_text[:40]:<40} | Data: {data_text[:60]}")
            
            # Store ALL data (not just physical stats)
            if header_text and data_text:
                # Create clean key from header
                key = header_text.lower().replace(' ', '_').replace('-', '_')
                key = re.sub(r'[^\w]', '', key)
                infobox_data[key] = data_text
        
        print("=" * 80)
        print(f"\n✅ Total infobox fields captured: {len(infobox_data)}")
        print(f"📦 All keys: {list(infobox_data.keys())}")
        
        # Also return the standard physical stats
        physical_stats = {}
        stat_keywords = {
            'weight': ['mass', 'weight', 'body_mass'],
            'length': ['length', 'body_length', 'total_length', 'size'],
            'height': ['height', 'shoulder_height', 'standing_height'],
            'lifespan': ['lifespan', 'longevity', 'life_span'],
            'top_speed': ['speed', 'top_speed', 'maximum_speed', 'max_speed'],
        }
        
        for key, value in infobox_data.items():
            for stat_name, keywords in stat_keywords.items():
                if any(kw in key for kw in keywords):
                    if stat_name not in physical_stats:
                        physical_stats[stat_name] = value
                    break
        
        print(f"\n🎯 Physical stats extracted: {physical_stats}")
        
        return physical_stats
    
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
    
    print(f"\n📋 FINAL Infobox: {type(infobox).__name__} with {len(infobox)} keys")
    print(f"📦 Final Keys: {list(infobox.keys())}")
    print(f"{'='*80}\n")
    
    return result


if __name__ == "__main__":
    # Test the fetcher with detailed debug output
    test_animals = ["Tiger", "Lion"]
    
    for animal in test_animals:
        data = fetch_wikipedia_data(animal)
        print(f"\n🎯 FINAL RESULT for {animal}:")
        print(f"   Infobox: {data['infobox']}")
        print(f"\n\n")
