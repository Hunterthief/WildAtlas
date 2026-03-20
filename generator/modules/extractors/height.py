"""
Height extraction module - PRODUCTION READY v2
Fixed: Elephant patterns, Depth rejection, Animal-type validation
"""
import re
from typing import Dict, Any, Optional, List, Tuple


# =============================================================================
# CONFIGURATION - Animal Type Height Expectations (for validation)
# =============================================================================
ANIMAL_HEIGHT_RANGES = {
    # Mammals (shoulder/standing height in meters)
    'felidae': (0.3, 1.5),       # Cats
    'canidae': (0.3, 1.2),        # Dogs/Wolves
    'elephantidae': (2.0, 4.5),   # Elephants
    'ursidae': (0.6, 3.0),        # Bears
    'giraffidae': (3.0, 6.0),     # Giraffes
    'rhinocerotidae': (1.0, 2.0), # Rhinos
    'hippopotamidae': (1.0, 1.7), # Hippos
    'equidae': (1.0, 2.0),        # Horses
    'bovidae': (0.5, 2.0),        # Cattle/Antelope
    'cervidae': (0.5, 2.5),       # Deer
    'suidae': (0.5, 1.2),         # Pigs
    'primates': (0.3, 2.0),       # Primates
    
    # Birds (standing height in meters)
    'accipitridae': (0.5, 1.2),   # Eagles/Hawks
    'spheniscidae': (0.4, 1.2),   # Penguins
    'aves_large': (0.5, 2.5),     # Large birds (ostriches)
    'aves_medium': (0.2, 1.0),    # Medium birds
    'aves_small': (0.05, 0.3),    # Small birds
    
    # Reptiles (body height/carapace in meters)
    'testudinidae': (0.1, 0.8),   # Turtles/Tortoises (carapace height)
    'crocodylidae': (0.3, 1.0),   # Crocodiles
    'elapidae': (0.05, 0.5),      # Cobras/Snakes (body diameter, not length)
    'squamata': (0.05, 0.5),      # Snakes/Lizards
    
    # Amphibians (body height in meters)
    'ranidae': (0.02, 0.3),       # Frogs
    'anura': (0.02, 0.3),         # Frogs/Toads
    'caudata': (0.05, 0.5),       # Salamanders
    
    # Fish (body depth in meters - NOT length!)
    'lamnidae': (0.3, 1.5),       # Great White Shark (body depth)
    'fish_large': (0.2, 2.0),     # Large fish
    'fish_medium': (0.05, 0.5),   # Medium fish
    'fish_small': (0.01, 0.2),    # Small fish
    
    # Insects (body height in meters)
    'insecta': (0.001, 0.15),     # Insects
    'hymenoptera': (0.005, 0.05), # Bees/Wasps
    'lepidoptera': (0.01, 0.15),  # Butterflies/Moths
}


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================
def _is_valid_height(value: str, animal_name: str = "", classification: Dict[str, str] = None) -> bool:
    """
    Validate height value makes biological sense
    CRITICAL: Rejects depth, dive, migration, distance values
    """
    if not value or len(value) < 2:
        return False
    
    value_lower = value.lower()
    
    # ========================================================================
    # CRITICAL REJECT: Context that indicates NOT body height
    # ========================================================================
    depth_context = [
        'depth', 'dive', 'diving', 'deep', 'underwater', 'submerge',
        'ocean floor', 'sea floor', 'bottom', 'descend'
    ]
    
    distance_context = [
        'migration', 'migrate', 'distance', 'range', 'travel', 'journey',
        'nesting beach', 'breeding ground', 'habitat range', 'distribution'
    ]
    
    temporal_context = [
        'million years', 'ma ', 'mya', 'temporal', 'fossil', 'extinct',
        'years ago', 'ancient', 'prehistoric'
    ]
    
    population_context = [
        'population', 'individuals', 'specimens', 'count', 'abundance'
    ]
    
    # Check for reject contexts
    for context in depth_context + distance_context + temporal_context + population_context:
        if context in value_lower:
            return False
    
    # ========================================================================
    # Extract and validate numeric values
    # ========================================================================
    numbers = re.findall(r'(\d+(?:[.,]?\d+)?)', value)
    if not numbers:
        return False
    
    try:
        # Get the largest number
        max_num = max(float(n.replace(',', '').replace('.', '')) for n in numbers if n)
        
        # REJECT: Too large (clearly not body height)
        if max_num > 100:  # Nothing is 100+ meters tall
            return False
        
        # REJECT: Too small
        if max_num < 0.001:
            return False
        
        # ====================================================================
        # Animal-type specific validation
        # ====================================================================
        if classification:
            family = classification.get('family', '').lower()
            class_name = classification.get('class', '').lower()
            
            expected_range = None
            
            # Match family first (most specific)
            for key, range_val in ANIMAL_HEIGHT_RANGES.items():
                if key in family:
                    expected_range = range_val
                    break
            
            # Fall back to class
            if not expected_range:
                if 'mammalia' in class_name:
                    expected_range = (0.1, 5.0)
                elif 'aves' in class_name:
                    expected_range = (0.05, 2.5)
                elif 'reptilia' in class_name:
                    expected_range = (0.05, 2.0)
                elif 'amphibia' in class_name:
                    expected_range = (0.02, 0.5)
                elif 'chondrichthyes' in class_name:  # Sharks
                    expected_range = (0.3, 2.0)  # Body depth only
                elif 'actinopterygii' in class_name:  # Fish
                    expected_range = (0.05, 1.0)
                elif 'insecta' in class_name:
                    expected_range = (0.001, 0.2)
            
            # Validate against expected range (with 5x margin for unit errors)
            if expected_range:
                # Convert to meters if needed (assume cm if > 10)
                value_in_meters = max_num
                if max_num > 10:  # Likely cm
                    value_in_meters = max_num / 100
                
                if value_in_meters > expected_range[1] * 5:
                    return False
                if value_in_meters < expected_range[0] / 10:
                    return False
        
        return True
        
    except:
        return False


def _has_height_context(text: str, classification: Dict[str, str] = None) -> bool:
    """
    Check if text has height-related context
    CRITICAL: Rejects depth/dive/migration contexts
    """
    text_lower = text.lower()
    
    # POSITIVE indicators (height-related)
    height_keywords = [
        'height', 'tall', 'shoulder', 'stand', 'standing',
        'at the shoulder', 'shoulder height', 'body height',
        'upright', 'high', 'body depth'  # body depth for fish
    ]
    
    # NEGATIVE indicators (REJECT these strongly)
    reject_keywords = [
        'depth', 'dive', 'diving', 'deep', 'underwater',
        'migration', 'migrate', 'distance', 'range:',
        'nesting beach', 'breeding ground', 'habitat range',
        'temporal', 'million years', 'population',
        'elevation', 'altitude', 'above sea',
        'tree height', 'plant', 'vegetation'
    ]
    
    has_height = any(kw in text_lower for kw in height_keywords)
    has_reject = any(kw in text_lower for kw in reject_keywords)
    
    # If it has reject keywords, it's NOT height (even if it has height keywords)
    if has_reject:
        return False
    
    return has_height


# =============================================================================
# PATTERN DEFINITIONS - Improved for elephants and large mammals
# =============================================================================
HEIGHT_PATTERNS = [
    # =========================================================================
    # TIER 1: Most Specific (Shoulder Height - Elephants, Large Mammals)
    # =========================================================================
    {
        'pattern': r'shoulder\s*height\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)',
        'priority': 1,
        'format': 'range'
    },
    {
        'pattern': r'height\s*at\s*the\s*shoulder\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)',
        'priority': 1,
        'format': 'range'
    },
    {
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)\s*(?:at the shoulder|shoulder height)',
        'priority': 1,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 2: Standing Height (Large Mammals, Birds)
    # =========================================================================
    {
        'pattern': r'stands?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)\s*(?:tall|at the shoulder|high)?',
        'priority': 2,
        'format': 'range'
    },
    {
        'pattern': r'stands?\s*(?:about|approximately|up to)?\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)\s*(?:tall|high)?',
        'priority': 2,
        'format': 'single'
    },
    
    # =========================================================================
    # TIER 3: Reaches/Measuring (General)
    # =========================================================================
    {
        'pattern': r'reaches?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)\s*(?:tall|height|high|at the shoulder)?',
        'priority': 3,
        'format': 'range'
    },
    {
        'pattern': r'measur(?:ing|es)\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)\s*(?:tall|height|high)?',
        'priority': 3,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 4: Explicit Height Statements
    # =========================================================================
    {
        'pattern': r'height\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)',
        'priority': 4,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 5: Body Depth (Fish/Sharks - NOT length!)
    # =========================================================================
    {
        'pattern': r'body\s*depth\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m)',
        'priority': 5,
        'format': 'range'
    },
    {
        'pattern': r'body\s*depth\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m)',
        'priority': 5,
        'format': 'single'
    },
    
    # =========================================================================
    # TIER 6: Single Value Height
    # =========================================================================
    {
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)\s*(?:tall|height|standing|high)',
        'priority': 6,
        'format': 'single'
    },
]


# =============================================================================
# SECTION PRIORITY - Where height data typically appears
# =============================================================================
SECTION_PRIORITY = [
    'size',                    # Elephants, large mammals
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
    """
    Extract height from Wikipedia sections
    
    Args:
        sections: Dictionary of section name -> content
        animal_name: Name of the animal (for validation)
        classification: Taxonomic classification (for validation)
    
    Returns:
        Height string (e.g., "2.5–4 m") or empty string if not found
    """
    if not sections:
        return ""
    
    # STRATEGY 1: Search priority sections first
    for section_name in SECTION_PRIORITY:
        # Try exact match
        if section_name in sections and sections[section_name]:
            text = sections[section_name]
            if len(text) > 50:
                result = _extract_height_from_text(
                    text, 
                    animal_name, 
                    classification
                )
                if result:
                    return result
        
        # Try fuzzy match (underscores vs spaces)
        section_name_alt = section_name.replace('_', ' ')
        if section_name_alt in sections and sections[section_name_alt]:
            text = sections[section_name_alt]
            if len(text) > 50:
                result = _extract_height_from_text(
                    text, 
                    animal_name, 
                    classification
                )
                if result:
                    return result
    
    # STRATEGY 2: Search all sections (fallback)
    all_text = " ".join(sections.values())
    return _extract_height_from_text(all_text, animal_name, classification)


def _extract_height_from_text(
    text: str, 
    animal_name: str = "", 
    classification: Dict[str, str] = None
) -> str:
    """
    Extract height from text content using pattern matching
    """
    if not text or len(text) < 50:
        return ""
    
    # Clean text
    clean_text = re.sub(r'\[\d+\]', '', text)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    # Track best match
    best_match = None
    best_priority = 999
    
    # Search through all patterns by priority
    for pattern_info in HEIGHT_PATTERNS:
        pattern = pattern_info['pattern']
        priority = pattern_info['priority']
        format_type = pattern_info['format']
        
        # Skip if we already have a better priority match
        if priority >= best_priority:
            continue
        
        # Find all matches
        matches = re.finditer(pattern, clean_text, re.I)
        
        for m in matches:
            groups = m.groups()
            
            # Get context around match for validation (150 chars each side)
            start = max(0, m.start() - 150)
            end = min(len(clean_text), m.end() + 150)
            match_context = clean_text[start:end]
            
            # CRITICAL VALIDATION: Check context
            if not _has_height_context(match_context, classification):
                continue
            
            # BUILD result based on pattern format
            if format_type == 'range' and len(groups) >= 3:
                candidate = f"{groups[0]}–{groups[1]} {groups[2]}"
            elif format_type == 'single' and len(groups) >= 2:
                candidate = f"{groups[0]} {groups[1]}"
            else:
                continue
            
            # CRITICAL VALIDATION: Check biological plausibility
            if _is_valid_height(candidate, animal_name, classification):
                best_match = candidate
                best_priority = priority
                break
        
        if best_match and best_priority == priority:
            break
    
    return best_match if best_match else ""
