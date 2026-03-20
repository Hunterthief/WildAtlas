"""
Wikipedia data fetcher - MAXIMUM DEBUG 🔍
Shows EXACTLY what text is in the infobox
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
    MAXIMUM DEBUG - Shows EXACTLY what's in the infobox
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
        
        infobox_data = {}
        
        # Find ALL tables
        all_tables = soup.find_all('table')
        print(f"\n📊 Total tables on page: {len(all_tables)}")
        
        # Find infobox tables
        infobox_tables = []
        for i, table in enumerate(all_tables):
            class_attr = table.get('class', [])
            class_str = ' '.join(class_attr) if isinstance(class_attr, list) else str(class_attr)
            if 'infobox' in class_str.lower():
                infobox_tables.append((i, table, class_str))
                print(f"   ✅ Table #{i} is infobox: '{class_str}'")
        
        if not infobox_tables:
            print("   ⚠️ NO infobox tables found!")
            # Save HTML for inspection
            with open(f'debug_{name.replace(" ", "_")}.html', 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            print(f"   💾 Saved full HTML to debug_{name.replace(' ', '_')}.html")
            return {}
        
        # Process each infobox
        for idx, (table_num, infobox_table, class_str) in enumerate(infobox_tables):
            print(f"\n{'='*80}")
            print(f"   INFOBOX #{idx + 1} (Table #{table_num})")
            print(f"{'='*80}")
            
            # Get ALL text
            all_text = infobox_table.get_text(separator=' | ')
            print(f"\n📋 FULL INFOBOX TEXT ({len(all_text)} chars):")
            print("-" * 80)
            print(all_text)
            print("-" * 80)
            
            # Save infobox HTML for inspection
            with open(f'debug_infobox_{name.replace(" ", "_")}_{idx}.html', 'w', encoding='utf-8') as f:
                f.write(str(infobox_table))
            print(f"\n💾 Saved infobox HTML to debug_infobox_{name.replace(' ', '_')}_{idx}.html")
            
            # Search for physical stats
            print("\n🔍 Searching for physical stats...")
            
            # Look for specific keywords followed by numbers
            keywords_to_find = ['mass', 'weight', 'length', 'height', 'lifespan', 'longevity', 'speed']
            
            for keyword in keywords_to_find:
                # Find the keyword in text
                pattern = rf'{keyword}.*?([0-9][0-9,\s.\-–]*\s*[a-z/]+)'
                match = re.search(pattern, all_text, re.IGNORECASE | re.DOTALL)
                if match:
                    value = match.group(1).strip()
                    print(f"   Found '{keyword}': {value}")
                    
                    # Map to our standard keys
                    if any(k in keyword for k in ['mass', 'weight']):
                        infobox_data['weight'] = value
                    elif 'length' in keyword:
                        infobox_data['length'] = value
                    elif 'height' in keyword:
                        infobox_data['height'] = value
                    elif any(k in keyword for k in ['lifespan', 'longevity']):
                        infobox_data['lifespan'] = value
                    elif 'speed' in keyword:
                        infobox_data['top_speed'] = value
            
            # Also try row-by-row parsing
            print("\n📊 Parsing rows:")
            rows = infobox_table.find_all('tr')
            print(f"   Total rows: {len(rows)}")
            
            for i, row in enumerate(rows):
                cells = row.find_all(['th', 'td'])
                cell_texts = [cell.get_text().strip() for cell in cells]
                
                # Only show rows with numbers (likely physical stats)
                row_text = ' '.join(cell_texts)
                if re.search(r'[0-9]', row_text) and len(row_text) > 5:
                    print(f"   Row {i:2d}: {cell_texts}")
                    
                    # Try to extract stats from this row
                    for cell in cell_texts:
                        # Weight patterns
                        if re.search(r'(?:mass|weight)', cell, re.IGNORECASE):
                            match = re.search(r'([0-9][0-9,\s.\-–]*\s*(?:kg|lb|pounds?))', cell, re.IGNORECASE)
                            if match and 'weight' not in infobox_data:
                                infobox_data['weight'] = match.group(1).strip()
                                print(f"      → Captured weight: {infobox_data['weight']}")
                        
                        # Length patterns
                        if re.search(r'(?:length)', cell, re.IGNORECASE):
                            match = re.search(r'([0-9][0-9,\s.\-–]*\s*(?:m|cm|ft|in|metres?))', cell, re.IGNORECASE)
                            if match and 'length' not in infobox_data:
                                infobox_data['length'] = match.group(1).strip()
                                print(f"      → Captured length: {infobox_data['length']}")
                        
                        # Lifespan patterns
                        if re.search(r'(?:lifespan|longevity)', cell, re.IGNORECASE):
                            match = re.search(r'([0-9][0-9,\s.\-–]*\s*(?:years?|yrs?))', cell, re.IGNORECASE)
                            if match and 'lifespan' not in infobox_data:
                                infobox_data['lifespan'] = match.group(1).strip()
                                print(f"      → Captured lifespan: {infobox_data['lifespan']}")
        
        print(f"\n{'='*80}")
        print(f"✅ Total physical stats captured: {len(infobox_data)}")
        print(f"📦 Keys: {list(infobox_data.keys())}")
        print(f"🎯 Data: {infobox_data}")
        print(f"{'='*80}")
        
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
    test_animals = ["Tiger"]
    
    for animal in test_animals:
        data = fetch_wikipedia_data(animal)
        print(f"\n🎯 FINAL RESULT for {animal}:")
        print(f"   Infobox: {data['infobox']}")
