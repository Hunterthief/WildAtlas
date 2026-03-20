"""
Wikipedia data fetcher - COMPREHENSIVE FIX ✅
Searches ALL infoboxes and full page content for physical stats
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
    COMPREHENSIVE: Searches ALL infoboxes and full page for physical stats
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
        
        # ===== STRATEGY 1: Find ALL infobox tables =====
        print("\n🔍 STRATEGY 1: Searching ALL infobox tables...")
        all_tables = soup.find_all('table', class_=lambda x: x and 'infobox' in str(x).lower())
        print(f"   Found {len(all_tables)} infobox table(s)")
        
        for idx, infobox_table in enumerate(all_tables):
            print(f"\n   --- Infobox #{idx + 1} ---")
            
            # Get ALL text from this infobox
            all_text = infobox_table.get_text()
            
            # Search for physical stats with flexible patterns
            stat_patterns = {
                'weight': [
                    r'(?:mass|weight)\s*[:\s]\s*([0-9.,\s\-–]+(?:\s*[kmglb]+)?(?:\s*\(.*?\))?)',
                    r'([0-9.,\s\-–]+\s*(?:kg|lb|pounds?|kilograms?|grams?|tonnes?|tons?))',
                ],
                'length': [
                    r'(?:length|body\s*length|total\s*length)\s*[:\s]\s*([0-9.,\s\-–]+(?:\s*[kcmftin]+)?(?:\s*\(.*?\))?)',
                    r'([0-9.,\s\-–]+\s*(?:m|cm|mm|ft|in|feet|inches|metres?|meters?))',
                ],
                'height': [
                    r'(?:height|shoulder\s*height|standing\s*height)\s*[:\s]\s*([0-9.,\s\-–]+(?:\s*[kcmftin]+)?(?:\s*\(.*?\))?)',
                    r'([0-9.,\s\-–]+\s*(?:m|cm|mm|ft|in|feet|inches|metres?|meters?)).*?(?:height)',
                ],
                'lifespan': [
                    r'(?:lifespan|longevity|life\s*span)\s*[:\s]\s*([0-9.,\s\-–]+(?:\s*[a-z]+)?(?:\s*\(.*?\))?)',
                    r'([0-9.,\s\-–]+\s*(?:years?|yrs?|months?|weeks?|days?)).*?(?:lifespan|longevity|life)',
                ],
                'top_speed': [
                    r'(?:speed|top\s*speed|maximum\s*speed)\s*[:\s]\s*([0-9.,\s\-–]+(?:\s*[a-z/]+)?(?:\s*\(.*?\))?)',
                    r'([0-9.,\s\-–]+\s*(?:km/h|mph|km|mi|m/s)).*?(?:speed)',
                ],
            }
            
            for stat_name, patterns in stat_patterns.items():
                if stat_name in infobox_data:
                    continue  # Already found
                    
                for pattern in patterns:
                    match = re.search(pattern, all_text, re.IGNORECASE)
                    if match:
                        value = match.group(1).strip()
                        value = re.sub(r'\s+', ' ', value)
                        # Validate it looks like a measurement
                        if re.search(r'[0-9]', value):
                            infobox_data[stat_name] = value
                            print(f"      ✅ {stat_name}: {value}")
                        break
        
        # ===== STRATEGY 2: Parse infobox rows more carefully =====
        if not infobox_data:
            print("\n🔍 STRATEGY 2: Parsing infobox rows with state machine...")
            
            for idx, infobox_table in enumerate(all_tables):
                rows = infobox_table.find_all('tr')
                current_label = ""
                
                for row in rows:
                    # Get all cells in this row
                    cells = row.find_all(['th', 'td'])
                    
                    for cell in cells:
                        cell_text = cell.get_text().strip()
                        cell_text = re.sub(r'\[\d+\]', '', cell_text)
                        
                        if not cell_text:
                            continue
                        
                        # Check if this looks like a label (short, ends with colon, or is a known stat)
                        is_label = (
                            cell.name == 'th' or
                            cell_text.endswith(':') or
                            len(cell_text) < 30
                        )
                        
                        if is_label:
                            current_label = cell_text.lower()
                        else:
                            # This is data - match against current label
                            for stat_name, keywords in {
                                'weight': ['mass', 'weight', 'body mass', 'avg mass'],
                                'length': ['length', 'body length', 'total length', 'size'],
                                'height': ['height', 'shoulder height', 'standing height'],
                                'lifespan': ['lifespan', 'longevity', 'life span', 'average lifespan'],
                                'top_speed': ['speed', 'top speed', 'maximum speed', 'max speed'],
                            }.items():
                                if stat_name not in infobox_data:
                                    if any(kw in current_label for kw in keywords):
                                        if re.search(r'[0-9]', cell_text):
                                            infobox_data[stat_name] = cell_text
                                            print(f"      ✅ {stat_name}: {cell_text[:60]}")
                                            break
        
        # ===== STRATEGY 3: Search entire page content as fallback =====
        if not infobox_data:
            print("\n🔍 STRATEGY 3: Searching entire page content...")
            
            # Get main content area
            content_div = soup.find('div', id='mw-content-text')
            if content_div:
                page_text = content_div.get_text()
                
                stat_patterns = {
                    'weight': [r'(?:mass|weight)[:\s]+([0-9.,\s\-–]+\s*(?:kg|lb))'],
                    'length': [r'(?:length)[:\s]+([0-9.,\s\-–]+\s*(?:m|cm|ft|in))'],
                    'height': [r'(?:height)[:\s]+([0-9.,\s\-–]+\s*(?:m|cm|ft|in))'],
                    'lifespan': [r'(?:lifespan|longevity)[:\s]+([0-9.,\s\-–]+\s*(?:years?))'],
                    'top_speed': [r'(?:speed)[:\s]+([0-9.,\s\-–]+\s*(?:km/h|mph))'],
                }
                
                for stat_name, patterns in stat_patterns.items():
                    for pattern in patterns:
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            value = match.group(1).strip()
                            infobox_data[stat_name] = value
                            print(f"      ✅ {stat_name} (from page): {value}")
                            break
        
        print(f"\n✅ Total physical stats captured: {len(infobox_data)}")
        print(f"📦 Keys: {list(infobox_data.keys())}")
        
        if infobox_data:
            print(f"\n🎯 FINAL DATA: {infobox_data}")
        
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
    test_animals = ["Tiger", "African Bush Elephant", "Giraffe"]
    
    for animal in test_animals:
        data = fetch_wikipedia_data(animal)
        print(f"\n🎯 FINAL RESULT for {animal}:")
        print(f"   Infobox: {data['infobox']}")
        print(f"\n\n")
