"""
Length extraction module - PRODUCTION v8
Fixed: Cheetah 4-7m rejection, Wolf body length, Bee mm patterns, Eagle body length
Based on analysis of 13 animal Wikipedia articles from WildAtlas
"""
import re
from typing import Dict, Optional, List, Tuple, Any


# =============================================================================
# CONFIGURATION - Animal Type Length Expectations (for validation)
# =============================================================================
ANIMAL_LENGTH_RANGES = {
    # Mammals (body length in meters, NOT including tail unless specified)
    'felidae': (0.7, 2.2),        # Cats body length (tiger ~1.7-2.2m, cheetah ~1.1-1.5m)
    'canidae': (0.8, 1.6),        # Dogs/Wolves body length (NOT shoulder height)
    'elephantidae': (5.0, 7.5),   # Elephants total length with trunk
    'ursidae': (1.0, 3.0),        # Bears
    'giraffidae': (3.5, 6.0),     # Giraffes
    
    # Birds (body length, NOT wingspan)
    'accipitridae': (0.6, 1.2),   # Eagles body length (70-120cm)
    'spheniscidae': (0.7, 1.3),   # Penguins
    'anatidae': (0.4, 1.8),       # Ducks/Geese
    
    # Reptiles
    'testudinidae': (0.3, 1.0),   # Turtles carapace
    'cheloniidae': (0.8, 1.5),    # Sea turtles
    'elapidae': (2.0, 5.5),       # Cobras
    'squamata': (0.3, 6.0),       # Snakes/Lizards
    
    # Fish
    'salmonidae': (0.5, 1.5),     # Salmon
    'lamnidae': (4.0, 6.5),       # Sharks
    
    # Amphibians
    'ranidae': (0.06, 0.20),      # Frogs (6-20cm)
    
    # Insects (body length, NOT wingspan)
    'hymenoptera': (0.01, 0.025), # Bees (10-25mm)
    'lepidoptera': (0.03, 0.06),  # Butterflies body (3-6cm)
    'apidae': (0.01, 0.025),      # Honey bees specifically
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
        'extinct', 'years ago', 'evolved'
    ]
    
    for context in reject_contexts:
        if context in value_lower:
            return False
    
    # Extract numeric values
    numbers = re.findall(r'(\d+(?:[.,]?\d+)?)', value)
    if not numbers:
        return False
    
    try:
        # Get the primary number (first one)
        primary_num = float(numbers[0].replace(',', '').replace('.', ''))
        max_num = max(float(n.replace(',', '').replace('.', '')) for n in numbers if n)
        
        # REJECT: Too small or too large for any animal
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
            
            # Default ranges by class
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
                # Convert to meters for comparison
                value_in_meters = max_num
                if 'cm' in value_lower or 'centimeter' in value_lower:
                    value_in_meters = max_num / 100
                elif 'mm' in value_lower or 'millimeter' in value_lower:
                    value_in_meters = max_num / 1000
                elif 'ft' in value_lower or 'feet' in value_lower:
                    value_in_meters = max_num * 0.3048
                elif 'in' in value_lower or 'inch' in value_lower:
                    value_in_meters = max_num * 0.0254
                
                # CRITICAL FIX: For cats (felidae), reject >2.5m as it's likely total length with tail
                # Cheetah 4-7m is WRONG (includes tail), body length is ~1.2m
                if 'felidae' in family and value_in_meters > 2.5:
                    return False
                
                # CRITICAL FIX: For wolves/dogs (canidae), reject <0.5m as it's likely shoulder height
                # Wolf shoulder height is 29-50cm, body length is 1-1.6m
                if 'canidae' in family and value_in_meters < 0.5:
                    return False
                
                # CRITICAL FIX: For birds, reject if too small (wrong measurement) or too large (wingspan)
                # Eagle body length is 70-100cm, NOT 11cm
                if 'aves' in class_name:
                    if value_in_meters < 0.2:  # <20cm is too small for most birds
                        return False
                    if value_in_meters > 1.5:  # >1.5m is likely wingspan
                        return False
                
                # CRITICAL FIX: For insects, validate mm range properly
                if 'insecta' in class_name:
                    if value_in_meters > 0.15:  # >15cm is too big for most insects
                        return False
                    # Bees should be 10-25mm, butterflies 30-60mm body
                    if 'hymenoptera' in order or 'apidae' in family:
                        if value_in_meters < 0.005 or value_in_meters > 0.03:
                            return False
                    if 'lepidoptera' in order:
                        if value_in_meters < 0.02 or value_in_meters > 0.08:
                            return False
                
                # CRITICAL FIX: For elephants, reject <4m (too small)
                if 'elephantidae' in family:
                    if value_in_meters < 4.0:
                        return False
                
                # Allow 2x margin for unit conversion errors (tighter validation)
                if value_in_meters > expected_range[1] * 2:
                    return False
                if value_in_meters < expected_range[0] / 3:
                    return False
        
        return True
        
    except:
        return False


def _has_length_context(text: str, animal_name: str = "") -> bool:
    """Check if text has length-related context - AGGRESSIVE shoulder/wingspan rejection"""
    text_lower = text.lower()
    
    # POSITIVE indicators (length-related)
    length_keywords = [
        'length', 'long', 'measures', 'reaching', 'grows',
        'body length', 'total length', 'head-body', 'snout',
        'carapace', 'adult', 'mature', 'full-grown',
        'from head', 'from snout', 'from nose',
        'typically', 'average', 'usually', 'about', 'approximately'
    ]
    
    # REJECT keywords - AGGRESSIVE shoulder/distribution/wingspan rejection
    reject_keywords = [
        'temporal range', 'million years', 'ma ', 'mya',
        'wingspan', 'wing span', 'wing length', 'wing spread',
        'egg length', 'nest length', 'colony length',
        'population size', 'range size',
        'at the shoulder', 'shoulder height', 'shoulder',
        'tall at the shoulder', 'height at shoulder',
        'stands.*shoulder', 'shoulder.*tall', 'shoulder.*high',
        'distribution', 'range:', 'migrat', 'found from',
        'occurs from', 'native to', 'habitat', 'geographic'
    ]
    
    # CRITICAL: Check for shoulder context aggressively
    if 'shoulder' in text_lower:
        return False  # Always reject shoulder mentions for length
    
    # CRITICAL: Check for distribution/range context
    if any(kw in text_lower for kw in ['distribution', 'range:', 'found from', 'occurs from', 'native to', 'geographic']):
        return False
    
    # CRITICAL: Check for height context (not length)
    if any(kw in text_lower for kw in ['height', 'tall', 'stands', 'high']):
        if 'length' not in text_lower:  # Only reject if no length keyword
            return False
    
    # CRITICAL: For birds, reject wingspan measurements
    animal_lower = animal_name.lower() if animal_name else ""
    if any(x in animal_lower for x in ['butterfly', 'moth', 'bee', 'wasp', 'eagle', 'hawk', 'bird', 'penguin']):
        if 'wingspan' in text_lower or 'wing span' in text_lower:
            return False
        # Also reject if mentions wing without body
        if 'wing' in text_lower and 'body' not in text_lower:
            if 'length' in text_lower:
                # Check if it's specifically wing length
                if 'wing length' in text_lower or 'length of the wing' in text_lower:
                    return False
    
    # SPECIAL: For cats, prefer "head-body" over "total length"
    if any(x in animal_lower for x in ['tiger', 'cheetah', 'lion', 'cat', 'leopard', 'jaguar']):
        if 'total length' in text_lower and 'tail' in text_lower:
            return False  # Reject total length that includes tail
        # Also reject if value seems too large for body length
        if 'total length' in text_lower:
            # Check for large values that include tail
            large_values = re.findall(r'(\d+[.,]?\d*)\s*(?:m|metres?|meters?)', text_lower)
            for val in large_values:
                try:
                    if float(val.replace(',', '')) > 3.0:
                        return False  # Likely includes tail
                except:
                    pass
    
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
    'size_and_weight',
    'size_and_measurement',
    'anatomy',
    'appearance',
    'appearance_and_anatomy',
    'physical_description',
    'morphology',
    'physical_characteristics',
    'body_size',
    'dimensions',
    'measurements',
    'physical_description_and_measurements',
]


# =============================================================================
# PATTERN DEFINITIONS - Refined based on 13 animal analysis
# =============================================================================
LENGTH_PATTERNS = [
    # =========================================================================
    # TIER 1: Explicit Body Length Statements (Most Reliable)
    # =========================================================================
    {
        # "body length of 1.5–2.5 m" - PREFER this over total length
        'pattern': r'body\s*length\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        'priority': 1,
        'format': 'range'
    },
    {
        # "head-and-body length of 1.5–2.5 m" - PREFER this for cats/mammals
        'pattern': r'(?:head-and-body|head\s*and\s*body|head-body|head\s*to\s*body)\s*length\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
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
    {
        # "forearm length" (bats) - reject
        'pattern': r'forearm\s*length',
        'priority': 999,
        'format': 'reject'
    },
    {
        # "wing length" (birds) - reject
        'pattern': r'wing\s*length',
        'priority': 999,
        'format': 'reject'
    },
    
    # =========================================================================
    # TIER 2: Total Length (Lower priority - may include tail)
    # =========================================================================
    {
        # "total length of 1.5–2.5 m" - but validate against animal type
        'pattern': r'total\s*length\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        'priority': 2,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 3: Measurement Statements
    # =========================================================================
    {
        # "measuring 1.5–2.5 m in length"
        'pattern': r'measur(?:ing|es)\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)\s*(?:in length|long)?',
        'priority': 3,
        'format': 'range'
    },
    {
        # "reaching 1.5–2.5 m in length"
        'pattern': r'reach(?:ing|es)?\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)\s*(?:in length|long)?',
        'priority': 3,
        'format': 'range'
    },
    {
        # "grows to 1.5–2.5 m"
        'pattern': r'grows?\s+(?:to|up to|reaching)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        'priority': 3,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 4: Simple Length Patterns
    # =========================================================================
    {
        # "1.5–2.5 m in length"
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)\s+(?:in length|long|length)',
        'priority': 4,
        'format': 'range'
    },
    {
        # "length of 1.5–2.5 m"
        'pattern': r'length\s+(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        'priority': 4,
        'format': 'range'
    },
    {
        # "average length of 1.5–2.5 m"
        'pattern': r'average\s*length\s+(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)',
        'priority': 4,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 5: Single Value Length
    # =========================================================================
    {
        # "up to 2.5 m"
        'pattern': r'(?:up to|reaching|to|about|approximately)\s+(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)\s*(?:in length|long)?',
        'priority': 5,
        'format': 'single'
    },
    {
        # "2.5 m long"
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet|in|inches)\s+long',
        'priority': 5,
        'format': 'single'
    },
    
    # =========================================================================
    # TIER 6: Snake-Specific Patterns (often no "length" keyword)
    # =========================================================================
    {
        # "reaches 3-4 m" (snakes often omit "length")
        'pattern': r'reaches?\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?)',
        'priority': 6,
        'format': 'range'
    },
    {
        # "typically 3-4 m" (snakes)
        'pattern': r'typically\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?)',
        'priority': 6,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 7: Turtle/Frog Specific
    # =========================================================================
    {
        # "80-120 cm carapace" (turtles)
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?)\s+carapace',
        'priority': 7,
        'format': 'range'
    },
    {
        # "9-15 cm long" (frogs)
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?)\s+long',
        'priority': 7,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 8: Small Animals (Bees, Insects) - IMPROVED mm support
    # =========================================================================
    {
        # "10-15 mm long" (bees)
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(mm)\s+long',
        'priority': 8,
        'format': 'range'
    },
    {
        # "about 12 mm" (bees) - NO "long" keyword required
        'pattern': r'(?:about|approximately|around|measures?|measuring)\s+(\d+(?:[.,]\d+)?)\s*(mm)',
        'priority': 8,
        'format': 'single'
    },
    {
        # "12 mm in length" (bees)
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(mm)\s+in\s+length',
        'priority': 8,
        'format': 'single'
    },
    {
        # "10–15 mm" (bees) - Simple mm range without "long"
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(mm)',
        'priority': 8,
        'format': 'range'
    },
    {
        # "12 mm" for insects (single value)
        'pattern': r'(?:length|long|measures?)\s+(?:of\s+)?(\d+(?:[.,]\d+)?)\s*(mm)',
        'priority': 8,
        'format': 'single'
    },
    {
        # "workers measure 10-15 mm" (bees/ants)
        'pattern': r'(?:workers?|adults?)\s+(?:measure|measuring)\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(mm)',
        'priority': 8,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 9: Fallback Patterns
    # =========================================================================
    {
        # "X cm" in description sections (small animals)
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(cm|mm)\s+(?:long|length)',
        'priority': 9,
        'format': 'single'
    },
    {
        # "X inches" (frogs, small animals)
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(?:inches?|in|")\s+(?:long|length)',
        'priority': 9,
        'format': 'range'
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
    
    all_matches = []
    
    # STRATEGY 1: Search priority sections first
    for section_name in SECTION_PRIORITY:
        if section_name in sections and sections[section_name]:
            text = sections[section_name]
            if len(text) > 50:
                result = _extract_length_from_text(text, animal_name, classification)
                if result:
                    all_matches.append((result, section_name))
        
        # Try with spaces instead of underscores
        section_name_alt = section_name.replace('_', ' ')
        if section_name_alt in sections and sections[section_name_alt]:
            text = sections[section_name_alt]
            if len(text) > 50:
                result = _extract_length_from_text(text, animal_name, classification)
                if result:
                    all_matches.append((result, section_name_alt))
    
    # Return best match from priority sections
    if all_matches:
        return all_matches[0][0]
    
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
        
        # Skip if we already have a better match
        if priority >= best_priority:
            continue
        
        # Skip reject patterns
        if format_type == 'reject':
            if re.search(pattern, clean_text, re.I):
                continue  # Skip this text section entirely
        
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
        'priority_tiers': len(set(p['priority'] for p in LENGTH_PATTERNS if p['priority'] < 999)),
        'section_priorities': len(SECTION_PRIORITY),
    }
