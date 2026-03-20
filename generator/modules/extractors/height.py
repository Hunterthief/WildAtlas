"""
Height extraction module - PRODUCTION v16
FIXED: Gray Wolf + all mammals work, snakes/fish/insects rejected
Key: More patterns + smart validation
"""
import re
from typing import Dict, Any, Optional, List, Tuple


# =============================================================================
# CONFIGURATION - Animal Type Height Expectations (for validation)
# =============================================================================
ANIMAL_HEIGHT_RANGES = {
    # Mammals (shoulder/standing height in meters)
    'felidae': (0.3, 1.5),
    'canidae': (0.2, 1.2),
    'elephantidae': (2.0, 4.5),
    'ursidae': (0.6, 3.0),
    'giraffidae': (3.0, 6.0),
    'rhinocerotidae': (1.0, 2.0),
    'hippopotamidae': (1.0, 1.7),
    'equidae': (1.0, 2.0),
    'bovidae': (0.5, 2.0),
    'cervidae': (0.5, 2.5),
    'suidae': (0.5, 1.2),
    'primates': (0.3, 2.0),
    'proboscidea': (2.0, 4.5),
    'loxodonta': (2.0, 4.5),
    
    # Birds (standing height)
    'accipitridae': (0.5, 1.2),
    'spheniscidae': (0.4, 1.2),
    'aves_large': (0.5, 2.5),
    'aves_medium': (0.2, 1.0),
    'aves_small': (0.05, 0.3),
    
    # Reptiles (turtles have carapace height, snakes DON'T)
    'testudinidae': (0.1, 1.5),
    'cheloniidae': (0.1, 1.5),
    'crocodylidae': (0.3, 1.0),
    
    # Amphibians (frogs have body height)
    'ranidae': (0.05, 0.3),
    'anura': (0.05, 0.3),
    'caudata': (0.05, 0.5),
}

# Animal types that DON'T have meaningful height (use length instead)
NO_HEIGHT_TAXA = [
    'squamata',      # Snakes/lizards - use length
    'serpentes',     # Snakes specifically
    'elapidae',      # Cobras
    'viperidae',     # Vipers
    'pythonidae',    # Pythons
    'actinopterygii', # Ray-finned fish
    'chondrichthyes', # Cartilaginous fish (sharks)
    'insecta',       # Insects
    'hymenoptera',   # Bees/wasps
    'lepidoptera',   # Butterflies/moths
]


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================
def _is_valid_height(value: str, animal_name: str = "", classification: Dict[str, str] = None) -> bool:
    """Validate height value - REJECTS snakes/fish/insects, ACCEPTS mammals"""
    if not value or len(value) < 2:
        return False
    
    value_lower = value.lower()
    
    # REJECT contexts (SPECIFIC, not broad)
    reject_contexts = [
        'water depth', 'dive depth', 'diving depth', 'ocean depth',
        'migration distance', 'migration range', 'travel distance',
        'temporal range', 'million years', 'population size',
        'elevation', 'altitude', 'above sea',
        'wingspan', 'wing span', 'forewing', 'hindwing'
    ]
    
    for context in reject_contexts:
        if context in value_lower:
            return False
    
    # Extract and validate numeric values
    numbers = re.findall(r'(\d+(?:[.,]?\d+)?)', value)
    if not numbers:
        return False
    
    try:
        max_num = max(float(n.replace(',', '').replace('.', '')) for n in numbers if n)
        
        if classification:
            family = classification.get('family', '').lower()
            genus = classification.get('genus', '').lower()
            order = classification.get('order', '').lower()
            class_name = classification.get('class', '').lower()
            
            # CRITICAL REJECT: Animals that DON'T have height
            for taxon in NO_HEIGHT_TAXA:
                if taxon in order or taxon in family:
                    return False
            
            # Animal-type specific validation
            expected_range = None
            
            for key, range_val in ANIMAL_HEIGHT_RANGES.items():
                if key in genus or key in family or key in order:
                    expected_range = range_val
                    break
            
            if not expected_range:
                if 'mammalia' in class_name:
                    expected_range = (0.1, 5.0)
                elif 'aves' in class_name:
                    expected_range = (0.05, 2.5)
                elif 'reptilia' in class_name:
                    expected_range = (0.05, 2.0)
                elif 'amphibia' in class_name:
                    expected_range = (0.05, 0.5)
            
            if expected_range:
                value_in_meters = max_num / 100 if max_num > 10 else max_num
                
                if value_in_meters > expected_range[1] * 3:
                    return False
                if value_in_meters < expected_range[0] / 10:
                    return False
        
        if max_num > 500 or max_num < 0.001:
            return False
        
        return True
        
    except:
        return False


def _has_height_context(text: str, classification: Dict[str, str] = None) -> bool:
    """Check if text has height-related context - NOT TOO RESTRICTIVE"""
    text_lower = text.lower()
    
    # POSITIVE indicators (height-related) - EXPANDED
    height_keywords = [
        'height', 'tall', 'shoulder', 'stand', 'standing', 'stood',
        'at the shoulder', 'shoulder height', 'body height',
        'upright', 'high', 'body depth',
        'males are', 'females are', 'male', 'female',
        'bulls', 'cows', 'mature', 'adult', 'fully grown',
        'terrestrial', 'elephant', 'reaching', 'measuring', 'wolf',
        'canid', 'canine', 'dogs', 'dog'
    ]
    
    # REJECT keywords (SPECIFIC - removed broad terms)
    reject_keywords = [
        'water depth', 'dive depth', 'diving depth', 'ocean depth',
        'migration distance', 'travel distance',
        'elevation', 'altitude', 'above sea', 'sea level',
        'wingspan', 'wing span',
        'temporal range', 'million years', 'population size'
    ]
    
    has_height = any(kw in text_lower for kw in height_keywords)
    has_reject = any(kw in text_lower for kw in reject_keywords)
    
    if has_reject:
        return False
    
    return has_height


# =============================================================================
# PATTERN DEFINITIONS - Comprehensive for all mammals
# =============================================================================
HEIGHT_PATTERNS = [
    # =========================================================================
    # TIER 1: Shoulder Height (Mammals - most reliable)
    # =========================================================================
    {
        'pattern': r'(?:males?|bulls?)\s+(?:are|is)\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?)\s*(?:\([^)]*\))?\s*(?:tall\s*)?(?:at\s+the\s+shoulder)',
        'priority': 1,
        'format': 'range'
    },
    {
        'pattern': r'(?:females?|cows?)\s+(?:are|is)\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?)\s*(?:\([^)]*\))?\s*(?:tall\s*)?(?:at\s+the\s+shoulder)',
        'priority': 1,
        'format': 'range'
    },
    {
        'pattern': r'shoulder\s*height\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m)',
        'priority': 1,
        'format': 'range'
    },
    {
        'pattern': r'height\s+at\s+the\s+shoulder\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m)',
        'priority': 1,
        'format': 'range'
    },
    {
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m)\s+at\s+the\s+shoulder',
        'priority': 1,
        'format': 'range'
    },
    {
        'pattern': r'(?:mature\s+)?(?:fully\s+grown\s+)?(?:females?|males?|bulls?|cows?)\s+(?:are|is)\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?)\s*(?:\([^)]*\))?\s*(?:tall)?(?:\s+at\s+the\s+shoulder)?',
        'priority': 1,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 2: Standing Height (Mammals, Birds) - ADDED MORE PATTERNS
    # =========================================================================
    {
        'pattern': r'stands?\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m)\s*(?:tall)?',
        'priority': 2,
        'format': 'range'
    },
    {
        'pattern': r'typically\s+stands?\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?)',
        'priority': 2,
        'format': 'range'
    },
    {
        # Wolf pattern: "are 29-50 cm at the shoulder"
        'pattern': r'(?:are|is)\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m)\s+at\s+the\s+shoulder',
        'priority': 2,
        'format': 'range'
    },
    {
        # "stands X cm tall" - Wolf/Coyote pattern
        'pattern': r'stands?\s+(\d+(?:[.,]\d+)?)\s*(cm|m)\s+tall',
        'priority': 2,
        'format': 'single'
    },
    {
        # "X cm at the shoulder" - Common wolf pattern
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(cm|m)\s+at\s+the\s+shoulder',
        'priority': 2,
        'format': 'single'
    },
    
    # =========================================================================
    # TIER 3: Reaches/Measuring (General)
    # =========================================================================
    {
        'pattern': r'reaches?\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m)\s*(?:tall|high)?',
        'priority': 3,
        'format': 'range'
    },
    {
        'pattern': r'measur(?:ing|es)\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m)\s*(?:tall|height|high)?',
        'priority': 3,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 4: Explicit Height Statements
    # =========================================================================
    {
        'pattern': r'height\s+(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m)',
        'priority': 4,
        'format': 'range'
    },
    {
        # "X cm in height"
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(cm|m)\s+in\s+height',
        'priority': 4,
        'format': 'single'
    },
]


# =============================================================================
# SECTION PRIORITY
# =============================================================================
SECTION_PRIORITY = [
    'size',
    'description',
    'characteristics',
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
# MAIN EXTRACTION FUNCTION
# =============================================================================
def extract_height_from_sections(
    sections: Dict[str, str], 
    animal_name: str = "", 
    classification: Dict[str, str] = None
) -> str:
    """Extract height from Wikipedia sections"""
    if not sections:
        return ""
    
    # Check if animal type should NOT have height
    if classification:
        family = classification.get('family', '').lower()
        order = classification.get('order', '').lower()
        
        for taxon in NO_HEIGHT_TAXA:
            if taxon in order or taxon in family:
                return ""
    
    for section_name in SECTION_PRIORITY:
        if section_name in sections and sections[section_name]:
            text = sections[section_name]
            if len(text) > 50:
                result = _extract_height_from_text(text, animal_name, classification)
                if result:
                    return result
        
        section_name_alt = section_name.replace('_', ' ')
        if section_name_alt in sections and sections[section_name_alt]:
            text = sections[section_name_alt]
            if len(text) > 50:
                result = _extract_height_from_text(text, animal_name, classification)
                if result:
                    return result
    
    all_text = " ".join(sections.values())
    return _extract_height_from_text(all_text, animal_name, classification)


def _extract_height_from_text(
    text: str, 
    animal_name: str = "", 
    classification: Dict[str, str] = None
) -> str:
    """Extract height from text content"""
    if not text or len(text) < 50:
        return ""
    
    clean_text = re.sub(r'\[\d+\]', '', text)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    best_match = None
    best_priority = 999
    
    for pattern_info in HEIGHT_PATTERNS:
        pattern = pattern_info['pattern']
        priority = pattern_info['priority']
        format_type = pattern_info['format']
        
        if priority >= best_priority:
            continue
        
        matches = re.finditer(pattern, clean_text, re.I)
        
        for m in matches:
            groups = m.groups()
            
            start = max(0, m.start() - 200)
            end = min(len(clean_text), m.end() + 200)
            match_context = clean_text[start:end]
            
            if not _has_height_context(match_context, classification):
                continue
            
            if format_type == 'range' and len(groups) >= 3:
                candidate = f"{groups[0]}–{groups[1]} {groups[2]}"
            elif format_type == 'single' and len(groups) >= 2:
                candidate = f"{groups[0]} {groups[1]}"
            else:
                continue
            
            if _is_valid_height(candidate, animal_name, classification):
                best_match = candidate
                best_priority = priority
                break
        
        if best_match and best_priority == priority:
            break
    
    return best_match if best_match else ""


def test_height_extraction(text: str, animal_name: str = "") -> str:
    """Test function for height extraction"""
    return _extract_height_from_text(text, animal_name)


def get_pattern_stats() -> Dict[str, Any]:
    """Get statistics about pattern configuration"""
    return {
        'total_patterns': len(HEIGHT_PATTERNS),
        'priority_tiers': len(set(p['priority'] for p in HEIGHT_PATTERNS)),
        'section_priorities': len(SECTION_PRIORITY),
    }
