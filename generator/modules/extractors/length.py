"""
Length extraction module - PRODUCTION v4
Fixed: Reject shoulder height, better cheetah/elephant patterns, bee support
Based on analysis of 13 animal Wikipedia articles
"""
import re
from typing import Dict, Optional, List, Tuple, Any


# =============================================================================
# CONFIGURATION - Animal Type Length Expectations (for validation)
# =============================================================================
ANIMAL_LENGTH_RANGES = {
    # Mammals (body length in meters)
    'felidae': (0.8, 3.5),       # Cats (tiger up to 3.3m with tail)
    'canidae': (0.8, 2.0),       # Dogs/Wolves
    'elephantidae': (4.0, 7.5),  # Elephants (total length with trunk)
    'ursidae': (1.0, 3.0),       # Bears
    'giraffidae': (3.5, 6.0),    # Giraffes
    
    # Birds (body length, NOT wingspan)
    'accipitridae': (0.5, 1.2),  # Eagles
    'spheniscidae': (0.7, 1.2),  # Penguins
    
    # Reptiles
    'testudinidae': (0.4, 1.5),  # Turtles (carapace length)
    'cheloniidae': (0.6, 1.5),   # Sea turtles
    'elapidae': (1.0, 6.0),      # Cobras
    'squamata': (0.3, 6.0),      # Snakes/Lizards
    
    # Fish
    'salmonidae': (0.5, 1.5),    # Salmon
    'lamnidae': (3.0, 7.0),      # Sharks
    
    # Amphibians
    'ranidae': (0.08, 0.25),     # Frogs
    
    # Insects (body length, NOT wingspan)
    'hymenoptera': (0.01, 0.03), # Bees
    'lepidoptera': (0.03, 0.06), # Butterflies (body only)
}


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================
def _is_valid_length(value: str, animal_name: str = "", classification: Dict[str, str] = None) -> bool:
    """Validate length value makes biological sense"""
    if not value or len(value) < 2:
        return False
    
    value_lower = value.lower()
    
    # REJECT temporal/geological contexts
    reject_contexts = [
        'ma ', 'million years', 'mya', 'temporal range',
        'pleistocene', 'miocene', 'pliocene', 'fossil',
        'extinct', 'years ago'
    ]
    
    for context in reject_contexts:
        if context in value_lower:
            return False
    
    # Extract numeric values
    numbers = re.findall(r'(\d+(?:[.,]?\d+)?)', value)
    if not numbers:
        return False
    
    try:
        max_num = max(float(n.replace(',', '').replace('.', '')) for n in numbers if n)
        
        # REJECT: Too small or too large
        if max_num < 0.001 or max_num > 50:
            return False
        
        # Use classification for smarter validation
        if classification:
            family = classification.get('family', '').lower()
            order = classification.get('order', '').lower()
            class_name = classification.get('class', '').lower()
            
            # Get expected range
            expected_range = None
            for key, range_val in ANIMAL_LENGTH_RANGES.items():
                if key in family or key in order:
                    expected_range = range_val
                    break
            
            if not expected_range:
                if 'mammalia' in class_name:
                    expected_range = (0.3, 8.0)
                elif 'aves' in class_name:
                    expected_range = (0.1, 1.5)
                elif 'reptilia' in class_name:
                    expected_range = (0.2, 7.0)
                elif 'amphibia' in class_name:
                    expected_range = (0.05, 0.5)
                elif 'actinopterygii' in class_name:
                    expected_range = (0.1, 5.0)
                elif 'insecta' in class_name:
                    expected_range = (0.005, 0.1)
            
            if expected_range:
                value_in_meters = max_num / 100 if max_num > 10 else max_num
                
                # Allow 5x margin for unit conversion errors
                if value_in_meters > expected_range[1] * 5:
                    return False
                if value_in_meters < expected_range[0] / 10:
                    return False
        
        return True
        
    except:
        return False


def _has_length_context(text: str, animal_name: str = "") -> bool:
    """Check if text has length-related context - REJECT shoulder height"""
    text_lower = text.lower()
    
    # POSITIVE indicators (length-related)
    length_keywords = [
        'length', 'long', 'measures', 'reaching', 'grows',
        'body length', 'total length', 'head-body', 'snout',
        'carapace', 'adult', 'mature', 'full-grown',
        'from head', 'from snout', 'from nose',
        'typically', 'average', 'usually', 'about'
    ]
    
    # REJECT keywords - CRITICAL: Reject shoulder/at shoulder for length!
    reject_keywords = [
        'temporal range', 'million years', 'ma ', 'mya',
        'wingspan', 'wing span', 'wing length',
        'egg length', 'nest length', 'colony length',
        'population size',
        'at the shoulder', 'shoulder height', 'shoulder'  # ← CRITICAL: Reject shoulder data!
    ]
    
    # SPECIAL: For butterflies/bees/eagles, reject wingspan as "length"
    animal_lower = animal_name.lower() if animal_name else ""
    if any(x in animal_lower for x in ['butterfly', 'moth', 'bee', 'wasp', 'eagle', 'hawk']):
        if 'wingspan' in text_lower or 'wing span' in text_lower:
            return False
    
    has_length = any(kw in text_lower for kw in length_keywords)
    has_reject = any(kw in text_lower for kw in reject_keywords)
    
    if has_reject:
        return False
    
    return has_length


# =============================================================================
# SECTION PRIORITY - Where length data typically appears
# =============================================================================
SECTION_PRIORITY = [
    'description',
    'characteristics',
    'size',
    'anatomy',
    'appearance',
    'appearance_and_anatomy',
    'physical_description',
    'morphology',
    'physical_characteristics',
    'body_size',
    'dimensions',
]


# =============================================================================
# PATTERN DEFINITIONS - Fixed for all animals
# =============================================================================
LENGTH_PATTERNS = [
    # =========================================================================
    # TIER 1: Explicit Length Statements (Most Reliable)
    # =========================================================================
    {
        # "body length of 1.5–2.5 m"
        'pattern': r'body\s*length\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        'priority': 1,
        'format': 'range'
    },
    {
        # "total length of 1.5–2.5 m"
        'pattern': r'total\s*length\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        'priority': 1,
        'format': 'range'
    },
    {
        # "head-and-body length of 1.5–2.5 m"
        'pattern': r'(?:head-and-body|head\s*and\s*body|head-body)\s*length\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        'priority': 1,
        'format': 'range'
    },
    {
        # "carapace length of 80–120 cm" (turtles)
        'pattern': r'carapace\s*length\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        'priority': 1,
        'format': 'range'
    },
    {
        # "snout-to-vent length of 1.5–2.5 m" (reptiles)
        'pattern': r'snout[-\s]*(?:to|-)?vent\s*length\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        'priority': 1,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 2: Measurement Statements
    # =========================================================================
    {
        # "measuring 1.5–2.5 m in length"
        'pattern': r'measur(?:ing|es)\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)\s*(?:in length|long)?',
        'priority': 2,
        'format': 'range'
    },
    {
        # "reaching 1.5–2.5 m in length"
        'pattern': r'reach(?:ing|es)?\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)\s*(?:in length|long)?',
        'priority': 2,
        'format': 'range'
    },
    {
        # "grows to 1.5–2.5 m"
        'pattern': r'grows?\s+(?:to|up to|reaching)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        'priority': 2,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 3: Simple Length Patterns
    # =========================================================================
    {
        # "1.5–2.5 m in length"
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)\s+(?:in length|long|length)',
        'priority': 3,
        'format': 'range'
    },
    {
        # "length of 1.5–2.5 m"
        'pattern': r'length\s+(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        'priority': 3,
        'format': 'range'
    },
    {
        # "average length of 1.5–2.5 m"
        'pattern': r'average\s*length\s+(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        'priority': 3,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 4: Single Value Length
    # =========================================================================
    {
        # "up to 2.5 m"
        'pattern': r'(?:up to|reaching|to)\s+(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)\s*(?:in length|long)?',
        'priority': 4,
        'format': 'single'
    },
    {
        # "2.5 m long"
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)\s+long',
        'priority': 4,
        'format': 'single'
    },
    
    # =========================================================================
    # TIER 5: Snake-Specific Patterns (often no "length" keyword)
    # =========================================================================
    {
        # "reaches 3-4 m" (snakes often omit "length")
        'pattern': r'reaches?\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?)',
        'priority': 5,
        'format': 'range'
    },
    {
        # "typically 3-4 m" (snakes)
        'pattern': r'typically\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?)',
        'priority': 5,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 6: Turtle/Frog Specific
    # =========================================================================
    {
        # "80-120 cm carapace" (turtles)
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?)\s+carapace',
        'priority': 6,
        'format': 'range'
    },
    {
        # "9-15 cm long" (frogs)
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?)\s+long',
        'priority': 6,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 7: Small Animals (Bees, Insects)
    # =========================================================================
    {
        # "10-15 mm long" (bees)
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(mm|cm)\s+long',
        'priority': 7,
        'format': 'range'
    },
    {
        # "about 12 mm" (bees)
        'pattern': r'(?:about|approximately|around)\s+(\d+(?:[.,]\d+)?)\s*(mm|cm)\s+(?:long|in length)',
        'priority': 7,
        'format': 'single'
    },
    
    # =========================================================================
    # TIER 8: Fallback Patterns
    # =========================================================================
    {
        # "X cm" in description sections (small animals)
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(cm|mm)\s+(?:long|length)',
        'priority': 8,
        'format': 'single'
    },
]


# =============================================================================
# MAIN EXTRACTION FUNCTION
# =============================================================================
def extract_length_from_sections(
    sections: Dict[str, str], 
    animal_name: str = "", 
    classification: Dict[str, str] = None
) -> str:
    """Extract length from Wikipedia sections"""
    if not sections:
        return ""
    
    # STRATEGY 1: Search priority sections first
    for section_name in SECTION_PRIORITY:
        if section_name in sections and sections[section_name]:
            text = sections[section_name]
            if len(text) > 50:
                result = _extract_length_from_text(text, animal_name, classification)
                if result:
                    return result
        
        # Try with spaces instead of underscores
        section_name_alt = section_name.replace('_', ' ')
        if section_name_alt in sections and sections[section_name_alt]:
            text = sections[section_name_alt]
            if len(text) > 50:
                result = _extract_length_from_text(text, animal_name, classification)
                if result:
                    return result
    
    # STRATEGY 2: Search all sections (fallback)
    all_text = " ".join(sections.values())
    return _extract_length_from_text(all_text, animal_name, classification)


def _extract_length_from_text(
    text: str, 
    animal_name: str = "", 
    classification: Dict[str, str] = None
) -> str:
    """Extract length from text content"""
    if not text or len(text) < 50:
        return ""
    
    # Clean text
    clean_text = re.sub(r'\[\d+\]', '', text)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    best_match = None
    best_priority = 999
    
    for pattern_info in LENGTH_PATTERNS:
        pattern = pattern_info['pattern']
        priority = pattern_info['priority']
        format_type = pattern_info['format']
        
        if priority >= best_priority:
            continue
        
        matches = re.finditer(pattern, clean_text, re.I)
        
        for m in matches:
            groups = m.groups()
            
            # Get context around match
            start = max(0, m.start() - 200)
            end = min(len(clean_text), m.end() + 200)
            match_context = clean_text[start:end]
            
            # Check context
            if not _has_length_context(match_context, animal_name):
                continue
            
            # Build result
            if format_type == 'range' and len(groups) >= 3:
                candidate = f"{groups[0]}–{groups[1]} {groups[2]}"
            elif format_type == 'single' and len(groups) >= 2:
                candidate = f"{groups[0]} {groups[1]}"
            else:
                continue
            
            # Validate
            if _is_valid_length(candidate, animal_name, classification):
                best_match = candidate
                best_priority = priority
                break
        
        if best_match and best_priority == priority:
            break
    
    return best_match if best_match else ""


def test_length_extraction(text: str, animal_name: str = "") -> str:
    """Test function for length extraction"""
    return _extract_length_from_text(text, animal_name)


def get_pattern_stats() -> Dict[str, Any]:
    """Get statistics about pattern configuration"""
    return {
        'total_patterns': len(LENGTH_PATTERNS),
        'priority_tiers': len(set(p['priority'] for p in LENGTH_PATTERNS)),
        'section_priorities': len(SECTION_PRIORITY),
    }
