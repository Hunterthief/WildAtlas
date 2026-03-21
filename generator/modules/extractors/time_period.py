"""
Time Period Extractor - Parses Wikipedia Evolution/Phylogeny sections
Extracts species split times, common ancestor dates, fossil records
"""

import re
from typing import Dict, Optional, Any, List
import requests

# Epoch to millions of years mapping
EPOCH_MAPPING = {
    'early pleistocene': {'min': 2.58, 'max': 1.8, 'display': '2.6-1.8'},
    'middle pleistocene': {'min': 1.8, 'max': 0.78, 'display': '1.8-0.78'},
    'late pleistocene': {'min': 0.78, 'max': 0.0117, 'display': '0.78-0.01'},
    'early holocene': {'min': 0.0117, 'max': 0.0082, 'display': '0.01-0.008'},
    'middle holocene': {'min': 0.0082, 'max': 0.0042, 'display': '0.008-0.004'},
    'late holocene': {'min': 0.0042, 'max': 0, 'display': '0.004-Present'},
    'early miocene': {'min': 23, 'max': 16, 'display': '23-16'},
    'middle miocene': {'min': 16, 'max': 11.6, 'display': '16-11.6'},
    'late miocene': {'min': 11.6, 'max': 5.3, 'display': '11.6-5.3'},
    'early oligocene': {'min': 33.9, 'max': 28, 'display': '33.9-28'},
    'late oligocene': {'min': 28, 'max': 23, 'display': '28-23'},
    'early eocene': {'min': 56, 'max': 47.8, 'display': '56-47.8'},
    'late eocene': {'min': 47.8, 'max': 33.9, 'display': '47.8-33.9'},
    'early paleocene': {'min': 66, 'max': 61.6, 'display': '66-61.6'},
    'late paleocene': {'min': 61.6, 'max': 56, 'display': '61.6-56'},
    'early jurassic': {'min': 201, 'max': 174, 'display': '201-174'},
    'middle jurassic': {'min': 174, 'max': 163, 'display': '174-163'},
    'late jurassic': {'min': 163, 'max': 145, 'display': '163-145'},
    'early cretaceous': {'min': 145, 'max': 100, 'display': '145-100'},
    'late cretaceous': {'min': 100, 'max': 66, 'display': '100-66'},
    'early triassic': {'min': 252, 'max': 247, 'display': '252-247'},
    'late triassic': {'min': 247, 'max': 201, 'display': '247-201'}
}

# Time period regex patterns - FIXED: All patterns have consistent groups
TIME_PATTERNS = [
    # "split from each other between 2.70 and 3.70 million years ago"
    {
        'regex': r'split\s+(?:from\s+)?(?:each\s+other\s+)?between\s+([\d.]+)\s+(?:and|to)\s+([\d.]+)\s+(?:million\s+years?\s+ago|mya)',
        'type': 'split_range',
        'priority': 1
    },
    # "diverged approximately 3.7 million years ago"
    {
        'regex': r'diverged\s+(?:approximately\s+)?([\d.]+)\s+(?:million\s+years?\s+ago|mya)',
        'type': 'diverged',
        'priority': 2
    },
    # "lineages split from each other between 2.70 and 3.70 million years ago"
    {
        'regex': r'lineages?\s+split\s+(?:from\s+)?(?:each\s+other\s+)?between\s+([\d.]+)\s+(?:and|to)\s+([\d.]+)\s+(?:million\s+years?\s+ago|mya)',
        'type': 'lineage_split',
        'priority': 1
    },
    # "common ancestor that lived between 108,000 and 72,000 years ago"
    {
        'regex': r'common\s+ancestor\s+(?:that\s+)?lived\s+between\s+([\d,]+)\s+(?:and|to)\s+([\d,]+)\s+years?\s+ago',
        'type': 'ancestor_range',
        'priority': 3
    },
    # "evolved approximately 2 million years ago"
    {
        'regex': r'evolved\s+(?:approximately\s+)?([\d.]+)\s+(?:million\s+years?\s+ago|mya)',
        'type': 'evolved',
        'priority': 2
    },
    # "species emerged around 3 million years ago"
    {
        'regex': r'(?:species|appeared|emerged)\s+(?:around|approximately)?\s*([\d.]+)\s+(?:million\s+years?\s+ago|mya)',
        'type': 'emerged',
        'priority': 2
    },
    # "dated to the early Pleistocene"
    {
        'regex': r'(?:dated\s+to|from)\s+(?:the\s+)?(early|middle|late)\s+(pleistocene|holocene|miocene|oligocene|eocene|paleocene|jurassic|cretaceous|triassic)',
        'type': 'epoch',
        'priority': 4
    },
    # "around 115,000 years ago"
    {
        'regex': r'(?:around|approximately|about)\s+([\d,]+)\s+years?\s+ago',
        'type': 'years_ago',
        'priority': 3
    },
    # "2.70-3.70 million years ago"
    {
        'regex': r'([\d.]+)\s*[-–]\s*([\d.]+)\s+(?:million\s+years?\s+ago|mya)',
        'type': 'range_short',
        'priority': 1
    },
    # "3.7 million years ago" (single value)
    {
        'regex': r'([\d.]+)\s+(?:million\s+years?\s+ago|mya)',
        'type': 'single_million',
        'priority': 2
    }
]


def calculate_timeline_width(millions_years: float) -> str:
    """Calculate timeline width percentage based on millions of years"""
    if millions_years <= 0.1:
        return '10%'
    elif millions_years <= 1:
        return '20%'
    elif millions_years <= 5:
        return '40%'
    elif millions_years <= 10:
        return '55%'
    elif millions_years <= 50:
        return '70%'
    elif millions_years <= 100:
        return '80%'
    elif millions_years <= 200:
        return '85%'
    elif millions_years <= 300:
        return '90%'
    elif millions_years <= 400:
        return '92%'
    elif millions_years <= 500:
        return '94%'
    return '95%'


def format_start_text(millions_years: float) -> str:
    """Format start text for timeline"""
    if millions_years < 0.001:
        return f'{(millions_years * 1000):.1f}K years ago'
    elif millions_years < 1:
        return f'{(millions_years * 1000):.0f}K years ago'
    elif millions_years < 10:
        return f'{millions_years:.1f}M years ago'
    else:
        return f'{millions_years:.0f}M years ago'


def parse_time_periods(text: str, animal_name: str) -> Optional[Dict[str, Any]]:
    """Parse time periods from text content"""
    text_lower = text.lower()
    best_match = None
    
    for pattern in TIME_PATTERNS:
        try:
            match = re.search(pattern['regex'], text, re.IGNORECASE)
            
            if match:
                millions_years = 0
                text_display = ''
                width = '50%'
                
                if pattern['type'] in ['split_range', 'lineage_split', 'range_short']:
                    # Range like "2.70 and 3.70 million years ago"
                    min_val = float(match.group(1).replace(',', ''))
                    max_val = float(match.group(2).replace(',', ''))
                    millions_years = max(min_val, max_val)
                    text_display = f'~{millions_years} million years ago'
                    width = calculate_timeline_width(millions_years)
                    
                elif pattern['type'] in ['ancestor_range', 'years_ago']:
                    # Years ago (not millions)
                    min_val = float(match.group(1).replace(',', ''))
                    max_val = float(match.group(2).replace(',', '')) if match.group(2) else min_val
                    millions_years = max(min_val, max_val) / 1000000
                    if millions_years < 0.1:
                        text_display = f'~{int(max(min_val, max_val)):,} years ago'
                        width = '10%'
                    else:
                        text_display = f'~{millions_years:.2f} million years ago'
                        width = calculate_timeline_width(millions_years)
                        
                elif pattern['type'] == 'epoch':
                    # Geological epoch
                    epoch_key = f'{match.group(1).lower()} {match.group(2).lower()}'
                    epoch_data = EPOCH_MAPPING.get(epoch_key)
                    if epoch_data:
                        millions_years = epoch_data['min']
                        text_display = f'{match.group(1).capitalize()} {match.group(2).capitalize()} (~{epoch_data["display"]} million years ago)'
                        width = calculate_timeline_width(millions_years)
                        
                elif pattern['type'] in ['single_million', 'diverged', 'evolved', 'emerged']:
                    # Single value
                    millions_years = float(match.group(1).replace(',', ''))
                    text_display = f'~{millions_years} million years ago'
                    width = calculate_timeline_width(millions_years)
                
                # FIXED: Use 'priority' from pattern, store as 'confidence' in best_match
                if not best_match or pattern['priority'] < best_match.get('confidence', 999):
                    best_match = {
                        'text': text_display,
                        'width': width,
                        'start': format_start_text(millions_years),
                        'end': 'Present',
                        'millions_years': millions_years,
                        'confidence': pattern['priority'],
                        'raw_match': match.group(0)
                    }
                    
        except (IndexError, ValueError) as e:
            # Skip this pattern if regex groups don't match
            continue
    
    return best_match


def extract_section_content(html: str, section_header: str) -> str:
    """Extract content following a section heading from HTML"""
    # Simple regex-based extraction
    pattern = rf'<h[23][^>]*>{re.escape(section_header)}[^<]*</h[23]>(.*?)(?=<h[23]|$)'
    match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
    
    if match:
        # Strip HTML tags
        content = re.sub(r'<[^>]+>', ' ', match.group(1))
        return ' '.join(content.split())
    
    return ''


def extract_evolution_time(animal_name: str) -> Optional[Dict[str, Any]]:
    """
    Extract evolutionary time period from Wikipedia article
    Looks for species split times, common ancestor dates, fossil records
    """
    try:
        wiki_title = animal_name.replace(' ', '_')
        url = f'https://en.wikipedia.org/wiki/{wiki_title}'
        
        headers = {
            'User-Agent': 'WildAtlas/1.0 (https://github.com/Hunterthief/WildAtlas)'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if not response.ok:
            print(f'⚠️  Could not fetch Wikipedia article for {animal_name}')
            return None
        
        html = response.text
        
        # Section headers to look for
        section_headers = [
            'Evolution',
            'Phylogeny',
            'Evolutionary history',
            'Taxonomy',
            'Phylogeography',
            'Genetics',
            'Fossil record',
            'Origin'
        ]
        
        # Try each section header
        for header in section_headers:
            content = extract_section_content(html, header)
            
            if content:
                time_data = parse_time_periods(content, animal_name)
                
                if time_data:
                    print(f'✅ Found evolution data for {animal_name}: {time_data["text"]}')
                    return time_data
        
        print(f'ℹ️  No evolution data found for {animal_name}')
        return None
        
    except Exception as e:
        print(f'❌ Error extracting evolution time for {animal_name}: {e}')
        return None


def extract_time_period_from_sections(sections: Dict[str, str], animal_name: str) -> Optional[Dict[str, Any]]:
    """
    Extract time period from parsed Wikipedia sections
    
    Args:
        sections: Dictionary of section name -> content
        animal_name: Name of the animal
    
    Returns:
        Dictionary with time period data or None
    """
    # Section names to look for
    evolution_sections = [
        'evolution',
        'phylogeny',
        'evolutionary history',
        'taxonomy',
        'phylogeography',
        'genetics',
        'fossil record',
        'origin'
    ]
    
    # Search through sections
    for section_name, content in sections.items():
        section_lower = section_name.lower()
        
        if any(ev_sec in section_lower for ev_sec in evolution_sections):
            try:
                time_data = parse_time_periods(content, animal_name)
                
                if time_data:
                    print(f'✅ Found time period in section "{section_name}": {time_data["text"]}')
                    return time_data
            except Exception as e:
                continue
    
    return None


def get_fallback_time_period(animal_type: str, classification: Dict[str, str]) -> Dict[str, Any]:
    """
    Fallback time period estimation based on taxonomy
    
    Args:
        animal_type: Type of animal (feline, canine, bird, etc.)
        classification: Taxonomic classification dictionary
    
    Returns:
        Dictionary with time period data
    """
    class_name = classification.get('class', '').lower()
    
    fallbacks = {
        'feline': {'text': 'Evolved ~2-4 million years ago', 'width': '85%', 'start': '2-4M years ago', 'end': 'Present'},
        'canine': {'text': 'Evolved ~5-10 million years ago', 'width': '85%', 'start': '5-10M years ago', 'end': 'Present'},
        'bear': {'text': 'Evolved ~5-6 million years ago', 'width': '85%', 'start': '5-6M years ago', 'end': 'Present'},
        'elephant': {'text': 'Evolved ~6-7 million years ago', 'width': '88%', 'start': '6-7M years ago', 'end': 'Present'},
        'bird': {'text': 'Evolved ~150 million years ago', 'width': '75%', 'start': '150M years ago', 'end': 'Present'},
        'reptile': {'text': 'Evolved ~300 million years ago', 'width': '90%', 'start': '300M years ago', 'end': 'Present'},
        'amphibian': {'text': 'Evolved ~370 million years ago', 'width': '92%', 'start': '370M years ago', 'end': 'Present'},
        'fish': {'text': 'Evolved ~500 million years ago', 'width': '95%', 'start': '500M years ago', 'end': 'Present'},
        'insect': {'text': 'Evolved ~400 million years ago', 'width': '93%', 'start': '400M years ago', 'end': 'Present'}
    }
    
    if animal_type in fallbacks:
        return fallbacks[animal_type]
    
    # Class-based fallbacks
    if 'aves' in class_name:
        return fallbacks['bird']
    elif 'reptilia' in class_name:
        return fallbacks['reptile']
    elif 'amphibia' in class_name:
        return fallbacks['amphibian']
    elif 'actinopterygii' in class_name or 'chondrichthyes' in class_name:
        return fallbacks['fish']
    elif 'insecta' in class_name:
        return fallbacks['insect']
    elif 'mammalia' in class_name:
        return {'text': 'Evolved ~200 million years ago', 'width': '85%', 'start': '200M years ago', 'end': 'Present'}
    
    return {'text': 'Evolution data not available', 'width': '50%', 'start': 'Unknown', 'end': 'Present'}
