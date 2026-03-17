# generator/modules/extractors/stats.py
"""
Physical stats extraction module - V6 PRODUCTION
Proper fallback priority: Infobox > Wikidata > API Ninjas > Text Extraction
"""
import re
from typing import Dict, Any, Optional

from .weight import extract_weight_from_sections
from .length import extract_length_from_sections
from .height import extract_height_from_sections
from .lifespan import extract_lifespan_from_sections
from .speed import extract_speed_from_sections


def extract_stats_with_context(
    sections: Dict[str, str],
    animal_name: str = "",
    scientific_name: str = "",
    infobox_data: Dict[str, str] = None,
    wikidata_data: Dict[str, str] = None,
    api_ninjas_data: Dict[str, str] = None
) -> Dict[str, str]:
    """
    Extract stats with proper fallback priority
    
    Priority Order:
    1. Infobox data (most reliable for physical stats)
    2. Wikidata properties (structured data)
    3. API Ninjas (curated animal database)
    4. Wikipedia text extraction (fallback)
    """
    stats = {
        'weight': '',
        'length': '',
        'height': '',
        'lifespan': '',
        'top_speed': ''
    }
    
    infobox_data = infobox_data or {}
    wikidata_data = wikidata_data or {}
    api_ninjas_data = api_ninjas_data or {}
    
    # ===== WEIGHT =====
    # Priority 1: Infobox
    if infobox_data.get('weight'):
        stats['weight'] = clean_stat_value(infobox_data['weight'])
    
    # Priority 2: Wikidata P2067
    elif wikidata_data.get('weight'):
        stats['weight'] = clean_stat_value(wikidata_data['weight'])
    
    # Priority 3: API Ninjas
    elif api_ninjas_data.get('weight'):
        stats['weight'] = clean_stat_value(api_ninjas_data['weight'])
    
    # Priority 4: Text extraction (last resort)
    else:
        stats['weight'] = extract_weight_from_sections(sections, animal_name)
    
    # ===== LENGTH =====
    # Priority 1: Infobox
    if infobox_data.get('length'):
        stats['length'] = clean_stat_value(infobox_data['length'])
    
    # Priority 2: Wikidata P2048
    elif wikidata_data.get('length'):
        stats['length'] = clean_stat_value(wikidata_data['length'])
    
    # Priority 3: API Ninjas
    elif api_ninjas_data.get('length'):
        stats['length'] = clean_stat_value(api_ninjas_data['length'])
    
    # Priority 4: Text extraction
    else:
        stats['length'] = extract_length_from_sections(sections, animal_name)
    
    # ===== HEIGHT =====
    # Priority 1: Infobox
    if infobox_data.get('height'):
        stats['height'] = clean_stat_value(infobox_data['height'])
    
    # Priority 2: Wikidata (use length if no height)
    elif wikidata_data.get('height'):
        stats['height'] = clean_stat_value(wikidata_data['height'])
    
    # Priority 3: API Ninjas
    elif api_ninjas_data.get('height'):
        stats['height'] = clean_stat_value(api_ninjas_data['height'])
    
    # Priority 4: Text extraction
    else:
        stats['height'] = extract_height_from_sections(sections, animal_name)
    
    # ===== LIFESPAN =====
    # Priority 1: Infobox
    if infobox_data.get('lifespan'):
        stats['lifespan'] = clean_stat_value(infobox_data['lifespan'])
    
    # Priority 2: Wikidata P2283
    elif wikidata_data.get('lifespan'):
        stats['lifespan'] = clean_stat_value(wikidata_data['lifespan'])
    
    # Priority 3: API Ninjas
    elif api_ninjas_data.get('lifespan'):
        stats['lifespan'] = clean_stat_value(api_ninjas_data['lifespan'])
    
    # Priority 4: Text extraction
    else:
        stats['lifespan'] = extract_lifespan_from_sections(sections, animal_name)
    
    # ===== TOP SPEED =====
    # Priority 1: Infobox
    if infobox_data.get('top_speed'):
        stats['top_speed'] = clean_stat_value(infobox_data['top_speed'])
    
    # Priority 2: Wikidata P1347
    elif wikidata_data.get('top_speed'):
        stats['top_speed'] = clean_stat_value(wikidata_data['top_speed'])
    
    # Priority 3: API Ninjas
    elif api_ninjas_data.get('top_speed'):
        stats['top_speed'] = clean_stat_value(api_ninjas_data['top_speed'])
    
    # Priority 4: Text extraction
    else:
        stats['top_speed'] = extract_speed_from_sections(sections, animal_name)
    
    return stats


def clean_stat_value(value: str) -> str:
    """Clean and normalize stat value"""
    if not value:
        return ""
    
    # Remove extra whitespace
    value = re.sub(r'\s+', ' ', value)
    value = value.strip()
    
    # Normalize ranges (convert "to" to "–")
    value = re.sub(r'\s+to\s+', '–', value, flags=re.IGNORECASE)
    
    # Normalize dashes
    value = re.sub(r'[-–—]', '–', value)
    
    return value


def extract_stats_from_sections(sections: Dict[str, str], animal_name: str = "") -> Dict[str, str]:
    """Legacy function - text extraction only (fallback)"""
    return {
        "weight": extract_weight_from_sections(sections, animal_name),
        "length": extract_length_from_sections(sections, animal_name),
        "height": extract_height_from_sections(sections, animal_name),
        "lifespan": extract_lifespan_from_sections(sections, animal_name),
        "top_speed": extract_speed_from_sections(sections, animal_name),
    }
