"""
Height extraction module - PRODUCTION v14
FIXED: Reject migration distance, snake length, insect measurements
Key: Stricter taxon rejection + better context validation
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
    
    # Reptiles (turtles have carapace height, snakes DON'T have height)
    'testudinidae': (0.1, 1.5),
    'cheloniidae': (0.1, 1.5),
    'crocodylidae': (0.3, 1.0),
    # NO SNAKES - they use length only!
    
    # Amphibians (frogs have body length/height)
    'ranidae': (0.05, 0.3),
    'anura': (0.05, 0.3),
    'caudata': (0.05, 0.5),
    
    # Fish - use length/body depth (reject as height)
    # NO FISH - they use length
    
    # Insects - use length/wingspan (reject height)
    # NO INSECTS - they use length/wingspan
}

# Animal types that DON'T have meaningful height (use length instead)
NO_HEIGHT_TAXA = [
    'squamata',      # Snakes/lizards - use length
    'serpentes',     # Snakes specifically
    'elapidae',      # Cobras
    'viperidae',     # Vipers
    'pythonidae',    # Pythons
    'colubridae',    # Colubrid snakes
    'actinopterygii', # Ray-finned fish
    'chondrichthyes', # Cartilaginous fish (sharks)
    'insecta',       # Insects
    'hymenoptera',   # Bees/wasps
    'lepidoptera',   # Butterflies/moths
    'coleoptera',    # Beetles
    'diptera',       # Flies
    'arthropoda',    # All arthropods (includes insects)
]


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================
def _is_valid_height(value: str, animal_name: str = "", classification: Dict[str, str] = None) -> bool:
    """
    Validate height value makes biological sense
    CRITICAL: Rejects fish/snakes/insects/migration distances
    """
    if not value or len(value) < 2:
        return False
    
    value_lower = value.lower()
    
    # ========================================================================
    # REJECT contexts (expanded to catch migration/distance)
    # ========================================================================
    reject_contexts = [
        'water depth', 'dive depth', 'diving depth', 'ocean depth',
        'migration distance', 'migration range', 'travel distance',
        'temporal range', 'million years', 'population size',
        'elevation', 'altitude', 'above sea',
        'wingspan', 'wing span', 'forewing', 'hindwing',
        'migrate', 'migratory', 'nesting', 'breeding ground',
        'range:', 'distributed', 'found from', 'occurs from',
        'distance of', 'distance to', 'away from'
    ]
    
    for context in reject_contexts:
        if context in value_lower:
            return False
    
    # ========================================================================
    # Extract and validate numeric values
    # ========================================================================
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
            phylum = classification.get('phylum', '').lower()
            
            # ====================================================================
            # CRITICAL REJECT: Animals that DON'T have height
            # ====================================================================
            for taxon in NO_HEIGHT_TAXA:
                if taxon in phylum or taxon in class_name or taxon in order or taxon in family:
                    return False  # These animals use length, not height
            
            # ====================================================================
            # Animal-type specific validation (ACCEPT legitimate ranges)
            # ====================================================================
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
                
                # Allow 3x margin
                if value_in_meters > expected_range[1] * 3:
                    return False
                if value_in_meters < expected_range[0] / 10:
                    return False
        
        # ====================================================================
        # General sanity checks
        # ====================================================================
        # REJECT: Too large (nothing is 500+ meters tall)
        if max_num > 500:
            return False
        
        # REJECT: Too small
        if max_num < 0.001:
            return False
        
        return True
        
    except:
        return False


def _has_height_context(text: str, classification: Dict[str, str] = None) -> bool:
    """
    Check if text has height-related context
    CRITICAL: Rejects migration/distance/nesting contexts
    """
    text_lower = text.lower()
    
    # POSITIVE indicators (height-related)
    height_keywords = [
        'height', 'tall', 'shoulder', 'stand', 'standing', 'stood',
        'at the shoulder', 'shoulder height', 'body height',
        'upright', 'high', 'body depth',
        'males are', 'females are', 'male', 'female',
        'bulls', 'cows', 'mature', 'adult', 'fully grown',
        'terrestrial', 'elephant', 'reaching', 'measuring'
    ]
    
    # REJECT keywords (expanded to catch migration/distance)
    reject_keywords = [
        'water depth', 'dive depth', 'diving depth', 'ocean depth',
        'migration', 'migrate', 'migratory', 'migrates',
        'elevation', 'altitude', 'above sea', 'sea level',
        'wingspan', 'wing span',
        'temporal range', 'million years', 'population size',
        'nesting', 'breeding ground', 'range:', 'distributed',
        'found from', 'occurs from', 'distance', 'away from'
    ]
    
    has_height = any(kw in text_lower for kw in height_keywords)
    has_reject = any(kw in text_lower for kw in reject_keywords)
    
    if has_reject:
        return False
    
    return has_height


# =============================================================================
# PATTERN DEFINITIONS - Conservative, height-specific only
# =============================================================================
HEIGHT_PATTERNS = [
    # =========================================================================
    # TIER 1: Shoulder Height (Mammals ONLY - most reliable)
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
    # TIER 2: Standing Height (Mammals, Birds)
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
        'pattern': r'(?:are|is)\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m)\s+at\s+the\s+shoulder',
        'priority': 2,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 3: Reaches/Measuring (General)
    # =========================================================================
    {
        'pattern': r'reaches?\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m)\s*(?:tall|high)?',
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
    
    # CRITICAL: Check if animal type should NOT have height
    if classification:
        family = classification.get('family', '').lower()
        order = classification.get('order', '').lower()
        class_name = classification.get('class', '').lower()
        phylum = classification.get('phylum', '').lower()
        
        for taxon in NO_HEIGHT_TAXA:
            if taxon in phylum or taxon in class_name or taxon in order or taxon in family:
                return ""  # Snakes, fish, insects don't have height
    
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
