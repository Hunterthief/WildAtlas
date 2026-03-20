"""
Wikipedia data fetcher - ENHANCED
Now includes infobox scraping for physical stats
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
    Extract data from Wikipedia infobox - CRITICAL for physical stats
    Returns dict with weight, length, height, lifespan, speed if found
    """
    try:
        response = requests.get(
            'https://en.wikipedia.org/w/api.php',
            params={
                'action': 'query',
                'titles': name,
                'format': 'json',
                'prop': 'revisions',
                'rvprop': 'content',
                'redirects': 1
            },
            headers={'User-Agent': 'WildAtlas/1.0'}
        )
        
        if response.status_code != 200:
            return {}
        
        data = response.json()
        pages = data.get('query', {}).get('pages', {})
        if not pages:
            return {}
        
        page_data = list(pages.values())[0]
        if 'revisions' not in page_data:
            return {}
        
        wikitext = page_data['revisions'][0].get('*', '')
        
        # FIXED: Better infobox detection with multiple patterns
        infobox_text = ""
        
        infobox_patterns = [
            r'\{\{Infobox\s+species[^}]*\}\}',
            r'\{\{Infobox\s+animal[^}]*\}\}',
            r'\{\{Speciesbox[^}]*\}\}',
            r'\{\{Taxobox[^}]*\}\}',
            r'\{\{Infobox\s+bird[^}]*\}\}',
            r'\{\{Infobox\s+fish[^}]*\}\}',
            r'\{\{Infobox\s+reptile[^}]*\}\}',
        ]
        
        for pattern in infobox_patterns:
            match = re.search(pattern, wikitext, re.DOTALL | re.IGNORECASE)
            if match:
                infobox_text = match.group(0)
                break
        
        # If still no infobox, try to find any infobox-like structure
        if not infobox_text:
            infobox_match = re.search(r'\{\{Infobox[^}]*\}\}', wikitext, re.DOTALL | re.IGNORECASE)
            if infobox_match:
                infobox_text = infobox_match.group(0)
        
        if not infobox_text:
            return {}
        
        infobox_data = {}
        
        # Weight/Mass patterns
        mass_patterns = [
            r'\|\s*mass\s*=\s*([^\n\|}]+)',
            r'\|\s*weight\s*=\s*([^\n\|}]+)',
            r'\|\s*body_mass\s*=\s*([^\n\|}]+)',
        ]
        
        for pattern in mass_patterns:
            match = re.search(pattern, infobox_text, re.IGNORECASE)
            if match:
                infobox_data['weight'] = clean_infobox_value(match.group(1))
                break
        
        # Length patterns
        length_patterns = [
            r'\|\s*length\s*=\s*([^\n\|}]+)',
            r'\|\s*body_length\s*=\s*([^\n\|}]+)',
            r'\|\s*total_length\s*=\s*([^\n\|}]+)',
        ]
        
        for pattern in length_patterns:
            match = re.search(pattern, infobox_text, re.IGNORECASE)
            if match:
                infobox_data['length'] = clean_infobox_value(match.group(1))
                break
        
        # Height patterns
        height_patterns = [
            r'\|\s*height\s*=\s*([^\n\|}]+)',
            r'\|\s*shoulder_height\s*=\s*([^\n\|}]+)',
            r'\|\s*standing_height\s*=\s*([^\n\|}]+)',
        ]
        
        for pattern in height_patterns:
            match = re.search(pattern, infobox_text, re.IGNORECASE)
            if match:
                infobox_data['height'] = clean_infobox_value(match.group(1))
                break
        
        # Lifespan patterns
        lifespan_patterns = [
            r'\|\s*lifespan\s*=\s*([^\n\|}]+)',
            r'\|\s*longevity\s*=\s*([^\n\|}]+)',
        ]
        
        for pattern in lifespan_patterns:
            match = re.search(pattern, infobox_text, re.IGNORECASE)
            if match:
                infobox_data['lifespan'] = clean_infobox_value(match.group(1))
                break
        
        # Speed patterns
        speed_patterns = [
            r'\|\s*speed\s*=\s*([^\n\|}]+)',
            r'\|\s*top_speed\s*=\s*([^\n\|}]+)',
        ]
        
        for pattern in speed_patterns:
            match = re.search(pattern, infobox_text, re.IGNORECASE)
            if match:
                infobox_data['top_speed'] = clean_infobox_value(match.group(1))
                break
        
        return infobox_data
    
    except Exception as e:
        print(f"❌ Error fetching Wikipedia infobox: {e}")
        return {}


def clean_infobox_value(value: str) -> str:
    """Clean infobox value - remove wiki markup, citations, etc."""
    if not value:
        return ""
    
    value = re.sub(r'\[\[([^\]|]+)\|?([^\]]*)\]\]', r'\1\2', value)
    value = re.sub(r'<ref.*?>.*?</ref>', '', value, flags=re.DOTALL)
    value = re.sub(r'\[\d+\]', '', value)
    value = re.sub(r'\{\{.*?\}\}', '', value)
    value = re.sub(r'\s+', ' ', value)
    value = value.strip()
    
    convert_match = re.search(r'\{\{convert\|([^|]+)\|([^\|]+)\|([^\|]+)\}\}', value)
    if convert_match:
        value = f"{convert_match.group(1)} {convert_match.group(2)}"
    
    return value


def fetch_wikipedia_data(name: str) -> Dict[str, Any]:
    """
    Main Wikipedia fetcher - combines sections and infobox
    Returns combined data structure
    """
    sections = fetch_wikipedia_sections(name)
    infobox = fetch_wikipedia_infobox(name)
    
    return {
        'sections': sections,
        'infobox': infobox,
        'has_infobox': bool(infobox),
        'has_sections': bool(sections)
    }
