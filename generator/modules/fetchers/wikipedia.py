"""
Wikipedia data fetcher - FIXED ROW PARSING ✅
Handles Wikipedia's split header/data row structure
"""
import re
import requests
from typing import Dict, Optional, List, Any
from bs4 import BeautifulSoup


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


def fetch_wikipedia_infobox(name: str) -> Dict[str, str]:
    """
    FIXED: Properly parses Wikipedia infobox with split header/data rows
    """
    try:
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
        
        page_title = soup.find('h1', id='firstHeading')
        if page_title:
            print(f"📄 Page Title: {page_title.get_text()}")
        
        # Find infobox table
        infobox_table = soup.find('table', class_=lambda x: x and 'infobox' in str(x).lower())
        
        if not infobox_table:
            print(f"⚠️ NO infobox table found for {name}")
            return {}
        
        print(f"✅ Found infobox table for {name}")
        
        # KEY FIX: Get ALL cells from the infobox, not just row-by-row
        infobox_data = {}
        all_text = infobox_table.get_text()
        
        # Debug: Print raw infobox text
        print("\n📋 RAW INFOBOX TEXT (first 2000 chars):")
        print("=" * 80)
        print(all_text[:2000])
        print("=" * 80)
        
        # Now search for physical stats in the raw text
        stat_patterns = {
            'weight': [
                r'(?:mass|weight)[\s:]+([0-9.,\s\-]+(?:kg|lb|pounds?|kilograms?))',
                r'([0-9.,\s\-]+(?:kg|lb|pounds?|kilograms?)).*?(?:mass|weight)',
            ],
            'length': [
                r'(?:length|body length)[\s:]+([0-9.,\s\-]+(?:m|cm|ft|in|feet|inches|metres?|meters?))',
                r'([0-9.,\s\-]+(?:m|cm|ft|in|feet|inches|metres?|meters?)).*?(?:length)',
            ],
            'height': [
                r'(?:height|shoulder height)[\s:]+([0-9.,\s\-]+(?:m|cm|ft|in|feet|inches|metres?|meters?))',
                r'([0-9.,\s\-]+(?:m|cm|ft|in|feet|inches|metres?|meters?)).*?(?:height)',
            ],
            'lifespan': [
                r'(?:lifespan|longevity|life span)[\s:]+([0-9.,\s\-]+(?:years?|yrs?|months?|days?))',
                r'([0-9.,\s\-]+(?:years?|yrs?|months?|days?)).*?(?:lifespan|longevity)',
            ],
            'top_speed': [
                r'(?:speed|top speed|maximum speed)[\s:]+([0-9.,\s\-]+(?:km/h|mph|km|mi))',
                r'([0-9.,\s\-]+(?:km/h|mph|km|mi)).*?(?:speed)',
            ],
        }
        
        print("\n🔍 Searching for physical stats in infobox text:")
        
        for stat_name, patterns in stat_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, all_text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    # Clean up the value
                    value = re.sub(r'\s+', ' ', value)
                    infobox_data[stat_name] = value
                    print(f"   ✅ {stat_name}: {value}")
                    break
        
        if not infobox_data:
            print("   ⚠️ No physical stats found with regex patterns")
            
            # Fallback: Parse rows more carefully
            print("\n🔍 Fallback: Parsing rows with better logic...")
            rows = infobox_table.find_all('tr')
            
            current_header = ""
            for i, row in enumerate(rows):
                cells = row.find_all(['th', 'td'])
                row_text = ' '.join(cell.get_text().strip() for cell in cells)
                
                # Check if this row has a header
                th = row.find('th')
                td = row.find('td')
                
                if th and not td:
                    # This is a header row
                    current_header = th.get_text().strip().lower()
                    print(f"   Header row {i}: {current_header[:50]}")
                elif td and not th:
                    # This is a data row - associate with previous header
                    data_text = td.get_text().strip()
                    data_text = re.sub(r'\[\d+\]', '', data_text)
                    print(f"   Data row {i}: {current_header[:30]} -> {data_text[:50]}")
                    
                    # Check if current header matches our stats
                    for stat_name, keywords in {
                        'weight': ['mass', 'weight'],
                        'length': ['length', 'body length', 'size'],
                        'height': ['height', 'shoulder height'],
                        'lifespan': ['lifespan', 'longevity', 'life span'],
                        'top_speed': ['speed', 'top speed'],
                    }.items():
                        if any(kw in current_header for kw in keywords) and data_text:
                            if stat_name not in infobox_data:
                                infobox_data[stat_name] = data_text
                                print(f"      📊 Captured {stat_name}: {data_text[:50]}")
                            break
                elif th and td:
                    # Both in same row
                    header_text = th.get_text().strip().lower()
                    data_text = td.get_text().strip()
                    data_text = re.sub(r'\[\d+\]', '', data_text)
                    print(f"   Combined row {i}: {header_text[:30]} -> {data_text[:50]}")
                    
                    for stat_name, keywords in {
                        'weight': ['mass', 'weight'],
                        'length': ['length', 'body length', 'size'],
                        'height': ['height', 'shoulder height'],
                        'lifespan': ['lifespan', 'longevity', 'life span'],
                        'top_speed': ['speed', 'top speed'],
                    }.items():
                        if any(kw in header_text for kw in keywords) and data_text:
                            if stat_name not in infobox_data:
                                infobox_data[stat_name] = data_text
                                print(f"      📊 Captured {stat_name}: {data_text[:50]}")
                            break
        
        print(f"\n✅ Total physical stats captured: {len(infobox_data)}")
        print(f"📦 Keys: {list(infobox_data.keys())}")
        
        return infobox_data
    
    except Exception as e:
        print(f"❌ Error fetching Wikipedia infobox: {e}")
        import traceback
        traceback.print_exc()
        return {}


def fetch_wikipedia_data(name: str) -> Dict[str, Any]:
    """Main Wikipedia fetcher"""
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
    test_animals = ["Tiger", "Lion", "African Bush Elephant"]
    
    for animal in test_animals:
        data = fetch_wikipedia_data(animal)
        print(f"\n🎯 FINAL RESULT for {animal}:")
        print(f"   Infobox: {data['infobox']}")
        print(f"\n\n")
