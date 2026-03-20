"""
Wikipedia data fetcher - FINAL FIX ✅
Extracts physical stats from article sections (not just infobox)
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


def extract_physical_stats_from_text(text: str, animal_name: str) -> Dict[str, str]:
    """
    Extract physical stats from article text using regex patterns
    """
    if not text:
        return {}
    
    stats = {}
    
    # Weight patterns - look for kg/lb measurements near weight keywords
    weight_patterns = [
        r'(?:weighs?|weight|mass)[\s:]+([0-9][0-9,\s.\-–]*\s*(?:kg|kilograms?|lb|pounds?))',
        r'([0-9][0-9,\s.\-–]*\s*(?:kg|kilograms?|lb|pounds?)).*?(?:weighs?|weight|mass)',
        r'(?:weighs?|weight|mass).*?([0-9][0-9,\s.\-–]*\s*(?:kg|kilograms?|lb|pounds?))',
    ]
    
    for pattern in weight_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            stats['weight'] = match.group(1).strip()
            break
    
    # Length patterns
    length_patterns = [
        r'(?:length|body\s*length|total\s*length|measures?|long)[\s:]+([0-9][0-9,\s.\-–]*\s*(?:m|cm|mm|metres?|meters?|feet|ft|inches?|in))',
        r'([0-9][0-9,\s.\-–]*\s*(?:m|cm|mm|metres?|meters?|feet|ft|inches?|in)).*?(?:length|long)',
    ]
    
    for pattern in length_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            stats['length'] = match.group(1).strip()
            break
    
    # Height patterns
    height_patterns = [
        r'(?:height|shoulder\s*height|standing\s*height|tall)[\s:]+([0-9][0-9,\s.\-–]*\s*(?:m|cm|mm|metres?|meters?|feet|ft|inches?|in))',
        r'([0-9][0-9,\s.\-–]*\s*(?:m|cm|mm|metres?|meters?|feet|ft|inches?|in)).*?(?:height|tall)',
    ]
    
    for pattern in height_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            stats['height'] = match.group(1).strip()
            break
    
    # Lifespan patterns
    lifespan_patterns = [
        r'(?:lifespan|longevity|life\s*span|live|lives?)[\s:]+([0-9][0-9,\s.\-–]*\s*(?:years?|yrs?|months?|weeks?|days?))',
        r'([0-9][0-9,\s.\-–]*\s*(?:years?|yrs?|months?|weeks?|days?)).*?(?:lifespan|longevity|life|live)',
    ]
    
    for pattern in lifespan_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            stats['lifespan'] = match.group(1).strip()
            break
    
    # Speed patterns
    speed_patterns = [
        r'(?:speed|top\s*speed|maximum\s*speed|run|runs?)[\s:]+([0-9][0-9,\s.\-–]*\s*(?:km/h|km|mph|mi/h|mi|m/s))',
        r'([0-9][0-9,\s.\-–]*\s*(?:km/h|km|mph|mi/h|mi|m/s)).*?(?:speed|run)',
    ]
    
    for pattern in speed_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            stats['top_speed'] = match.group(1).strip()
            break
    
    return stats


def fetch_wikipedia_infobox(name: str, sections: Dict[str, str] = None) -> Dict[str, str]:
    """
    Extract physical stats from Wikipedia - checks infobox AND article text
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
        infobox_data = {}
        
        # ===== STRATEGY 1: Try infobox first =====
        print("\n🔍 STRATEGY 1: Checking infobox...")
        infobox_table = soup.find('table', class_=lambda x: x and 'infobox' in str(x).lower())
        
        if infobox_table:
            all_text = infobox_table.get_text()
            print(f"   Infobox text: {len(all_text)} chars")
            
            # Search for physical stats in infobox
            infobox_stats = extract_physical_stats_from_text(all_text, name)
            if infobox_stats:
                print(f"   ✅ Found in infobox: {list(infobox_stats.keys())}")
                infobox_data.update(infobox_stats)
            else:
                print(f"   ⚠️ No physical stats in infobox")
        else:
            print(f"   ⚠️ No infobox found")
        
        # ===== STRATEGY 2: Search article sections (if provided) =====
        if sections:
            print("\n🔍 STRATEGY 2: Searching article sections...")
            
            # Priority sections to search
            priority_sections = ['physical_characteristics', 'description', 'size', 'dimensions', 'etymology']
            
            for section_name in priority_sections:
                if section_name in sections and sections[section_name]:
                    section_text = sections[section_name]
                    print(f"   Searching '{section_name}' ({len(section_text)} chars)...")
                    
                    section_stats = extract_physical_stats_from_text(section_text, name)
                    for key, value in section_stats.items():
                        if key not in infobox_data:
                            infobox_data[key] = value
                            print(f"      ✅ {key}: {value}")
        
        # ===== STRATEGY 3: Search full page content as fallback =====
        if not infobox_data:
            print("\n🔍 STRATEGY 3: Searching full page content...")
            
            content_div = soup.find('div', id='mw-content-text')
            if content_div:
                # Get first 5000 chars of content (where physical description usually is)
                page_text = content_div.get_text()[:5000]
                print(f"   Searching page content ({len(page_text)} chars)...")
                
                page_stats = extract_physical_stats_from_text(page_text, name)
                for key, value in page_stats.items():
                    if key not in infobox_data:
                        infobox_data[key] = value
                        print(f"      ✅ {key}: {value}")
        
        print(f"\n✅ Total physical stats captured: {len(infobox_data)}")
        print(f"📦 Keys: {list(infobox_data.keys())}")
        
        if infobox_data:
            print(f"🎯 FINAL DATA: {infobox_data}")
        
        return infobox_data
    
    except Exception as e:
        print(f"❌ Error fetching Wikipedia infobox: {e}")
        import traceback
        traceback.print_exc()
        return {}


def fetch_wikipedia_data(name: str) -> Dict[str, Any]:
    """Main Wikipedia fetcher - sections first, then infobox"""
    print(f"\n{'='*80}")
    print(f"📚 Fetching Wikipedia data for: {name}")
    print(f"{'='*80}")
    
    # Fetch sections FIRST
    sections = fetch_wikipedia_sections(name)
    
    # Then fetch infobox (with sections for context)
    infobox = fetch_wikipedia_infobox(name, sections)
    
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
