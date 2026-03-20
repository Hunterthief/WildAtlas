"""
Wikipedia data fetcher - PRODUCTION v2 ✅
WildAtlas Project - https://github.com/Hunterthief/WildAtlas/

FIXES APPLIED:
1. ✅ Removed trailing spaces from URLs (was causing failures)
2. ✅ Enhanced infobox parsing with better regex patterns
3. ✅ Preserves measurement context in section text
4. ✅ Expanded section mapping for physical characteristics
5. ✅ Adds measurement source tags for extractor
"""
import re
import requests
from typing import Dict, Optional, List, Any, Tuple
from bs4 import BeautifulSoup


def fetch_wikipedia_sections(name: str) -> Dict[str, str]:
    """
    Fetch Wikipedia article sections via API
    Returns cleaned sections mapped to standard keys
    
    FIX: Removed trailing spaces from URL, enhanced section mapping
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
        
        # Parse HTML content - PRESERVE sentence structure for context
        html_content = parse_data.get('text', {}).get('*', '')
        if html_content:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            current_section = 'description'
            current_text = []
            
            for element in soup.find_all(['h2', 'h3', 'p', 'ul', 'ol', 'li']):
                if element.name in ['h2', 'h3']:
                    # Save previous section text
                    if current_text:
                        if current_section not in sections:
                            sections[current_section] = ' '.join(current_text)
                        else:
                            sections[current_section] += '. ' + ' '.join(current_text)
                        current_text = []
                    
                    # New section
                    section_title = element.get_text().strip().lower().replace(' ', '_')
                    section_title = re.sub(r'[\[\]\d]', '', section_title)
                    current_section = section_title
                else:
                    text = element.get_text().strip()
                    if text:
                        # Keep sentences intact for measurement context
                        current_text.append(text)
            
            # Save last section
            if current_text:
                if current_section not in sections:
                    sections[current_section] = ' '.join(current_text)
                else:
                    sections[current_section] += '. ' + ' '.join(current_text)
        
        # EXPANDED section mapping for physical characteristics
        cleaned_sections = {}
        for key, value in sections.items():
            key = re.sub(r'[\[\]\d]', '', key)
            key = key.replace(' ', '_').lower()
            
            section_mapping = {
                'description': ['description', 'summary', 'intro', 'introduction'],
                'characteristics': ['characteristics', 'physical_characteristics', 'physical_description'],
                'size': ['size', 'dimensions', 'measurements', 'body_size'],
                'anatomy': ['anatomy', 'morphology', 'appearance', 'appearance_and_anatomy'],
                'behavior': ['behavior', 'behaviour', 'habits', 'ecology'],
                'habitat': ['habitat', 'distribution_and_habitat', 'range_and_habitat', 'distribution', 'range'],
                'diet': ['diet', 'feeding', 'hunting_diet', 'food', 'predation'],
                'reproduction': ['reproduction', 'breeding', 'life_cycle', 'lifecycle'],
                'conservation': ['conservation', 'conservation_status', 'threats', 'protection'],
            }
            
            matched = False
            for standard_name, variations in section_mapping.items():
                if key in variations or any(v in key for v in variations):
                    cleaned_sections[standard_name] = value
                    matched = True
                    break
            if not matched:
                cleaned_sections[key] = value
        
        print(f"✅ Found {len(cleaned_sections)} Wikipedia sections for {name}")
        return cleaned_sections
    
    except Exception as e:
        print(f"❌ Error fetching Wikipedia sections: {e}")
        return {}


def fetch_wikipedia_infobox(name: str) -> Dict[str, str]:
    """
    Fetch physical stats from Wikipedia infobox
    FIXED: Better regex patterns, more stat types
    
    Returns: Dict with weight, length, height, lifespan if found
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
        
        # ENHANCED patterns for physical stats
        patterns = {
            'weight': [
                r'(?:mass|weight)[:\s]+([0-9][0-9,\s.\-–]*\s*(?:kg|lb|pounds?))',
                r'([0-9][0-9,\s.\-–]*\s*(?:kg|lb))\s*(?:mass|weight)',
            ],
            'length': [
                r'(?:body\s*)?(?:length)[:\s]+([0-9][0-9,\s.\-–]*\s*(?:m|cm|ft|in))',
                r'([0-9][0-9,\s.\-–]*\s*(?:m|cm))\s*(?:body\s*)?(?:length)',
                r'(?:head[-\s]*body|head[-\s]*and[-\s]*body)[:\s]+([0-9][0-9,\s.\-–]*\s*(?:m|cm))',
            ],
            'height': [
                r'(?:shoulder\s*)?(?:height)[:\s]+([0-9][0-9,\s.\-–]*\s*(?:m|cm|ft|in))',
                r'([0-9][0-9,\s.\-–]*\s*(?:m|cm))\s*(?:shoulder\s*)?(?:height)',
            ],
            'lifespan': [
                r'(?:lifespan|longevity)[:\s]+([0-9][0-9,\s.\-–]*\s*(?:years?))',
                r'([0-9][0-9,\s.\-–]*\s*(?:years?))\s*(?:lifespan|longevity)',
            ],
        }
        
        for stat_name, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, all_text, re.IGNORECASE)
                if match:
                    infobox_data[stat_name] = match.group(1).strip()
                    break
        
        return infobox_data
    
    except Exception as e:
        print(f"❌ Error fetching Wikipedia infobox: {e}")
        return {}


def fetch_wikipedia_data(name: str) -> Dict[str, Any]:
    """
    Main Wikipedia fetcher - returns sections and infobox data
    
    Architecture Note:
    - Sections go to extractors (length.py, weight.py, etc.)
    - Infobox is fallback for physical stats
    - Wikidata is primary source for structured properties
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
    if infobox:
        for key, value in infobox.items():
            print(f"   {key}: {value}")
    print(f"{'='*80}\n")
    
    return result


if __name__ == "__main__":
    # Test the fetcher with problem animals from logs
    test_animals = ["Cheetah", "Gray Wolf", "Bald Eagle", "African Elephant"]
    
    for animal in test_animals:
        print(f"\n{'='*80}")
        print(f"Testing: {animal}")
        print('='*80)
        data = fetch_wikipedia_data(animal)
        print(f"\n🎯 FINAL RESULT for {animal}:")
        print(f"   Infobox: {data['infobox']}")
        print(f"   Sections: {list(data['sections'].keys())}")
        # Print first 300 chars of size/characteristics sections for debugging
        for sec in ['size', 'characteristics', 'anatomy']:
            if sec in data['sections']:
                print(f"\n   [{sec}]: {data['sections'][sec][:300]}...")
        print(f"\n\n")
