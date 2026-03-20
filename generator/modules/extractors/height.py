"""
Height extraction module - PRODUCTION READY
Optimized for millions of animals with comprehensive pattern matching
"""
import re
from typing import Dict, Any, Optional, List, Tuple


# =============================================================================
# CONFIGURATION - Animal Type Height Expectations (for validation)
# =============================================================================
ANIMAL_HEIGHT_RANGES = {
    # Mammals (shoulder/standing height in meters)
    'felidae': (0.3, 1.5),      # Cats
    'canidae': (0.3, 1.2),       # Dogs/Wolves
    'elephantidae': (2.0, 4.5),  # Elephants
    'ursidae': (0.6, 3.0),       # Bears
    'giraffidae': (3.0, 6.0),    # Giraffes
    'rhinocerotidae': (1.0, 2.0), # Rhinos
    'hippopotamidae': (1.0, 1.7), # Hippos
    'equidae': (1.0, 2.0),       # Horses
    'bovidae': (0.5, 2.0),       # Cattle/Antelope
    'cervidae': (0.5, 2.5),      # Deer
    'suidae': (0.5, 1.2),        # Pigs
    'primates': (0.3, 2.0),      # Primates
    
    # Birds (standing height in meters)
    'aves_large': (0.5, 2.5),    # Large birds (eagles, ostriches)
    'aves_medium': (0.2, 1.0),   # Medium birds
    'aves_small': (0.05, 0.3),   # Small birds
    'spheniscidae': (0.4, 1.2),  # Penguins
    
    # Reptiles (body height/carapace in meters)
    'testudinidae': (0.1, 0.8),  # Turtles/Tortoises
    'crocodylidae': (0.3, 1.0),  # Crocodiles
    'squamata': (0.05, 0.5),     # Snakes/Lizards (often use length)
    
    # Amphibians (body height in meters)
    'anura': (0.02, 0.3),        # Frogs/Toads
    'caudata': (0.05, 0.5),      # Salamanders
    
    # Fish (body depth/height in meters - often use length)
    'fish_large': (0.2, 2.0),    # Large fish (sharks)
    'fish_medium': (0.05, 0.5),  # Medium fish
    'fish_small': (0.01, 0.2),   # Small fish
    
    # Insects (body height in meters - often use wingspan/length)
    'insecta': (0.001, 0.15),    # Insects
    'hymenoptera': (0.005, 0.05), # Bees/Wasps
    'lepidoptera': (0.01, 0.15),  # Butterflies/Moths
}


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================
def _extract_numeric_value(text: str) -> Optional[float]:
    """Extract numeric value from text, handling various formats"""
    try:
        # Remove commas and handle decimal points
        match = re.search(r'(\d+(?:[.,]\d+)?)', text)
        if match:
            return float(match.group(1).replace(',', ''))
    except:
        pass
    return None


def _is_valid_height(value: str, animal_name: str = "", classification: Dict[str, str] = None) -> bool:
    """
    Validate height value makes biological sense
    Returns False for temporal ranges, populations, or impossible values
    """
    if not value or len(value) < 2:
        return False
    
    value_lower = value.lower()
    
    # REJECT: Temporal/geological ranges
    reject_patterns = [
        r'\bma\b',                    # Mega-annum (million years)
        r'million years',
        r'temporal',
        r'range:',
        r'population',
        r'years ago',
        r'fossil',
        r'extinct',
        r'\bmya\b',                   # Million years ago
    ]
    for pattern in reject_patterns:
        if re.search(pattern, value_lower):
            return False
    
    # REJECT: Nest/colony heights (not animal height)
    if any(kw in value_lower for kw in ['nest', 'colony', 'hive', 'burrow', 'den']):
        return False
    
    # REJECT: Elevation/altitude (not animal height)
    if any(kw in value_lower for kw in ['elevation', 'altitude', 'above sea']):
        return False
    
    # Extract numeric values for range checking
    numbers = re.findall(r'(\d+(?:[.,]?\d+)?)', value)
    if not numbers:
        return False
    
    try:
        # Get the largest number (likely max height)
        max_num = max(float(n.replace(',', '').replace('.', '')) for n in numbers if n)
        
        # REJECT: Too large (population numbers)
        if max_num > 50000:
            return False
        
        # REJECT: Too small (likely not height)
        if max_num < 0.001:
            return False
        
        # Validate against animal type if classification available
        if classification:
            family = classification.get('family', '').lower()
            class_name = classification.get('class', '').lower()
            order = classification.get('order', '').lower()
            
            expected_range = None
            
            # Match family first
            for key, range_val in ANIMAL_HEIGHT_RANGES.items():
                if key in family:
                    expected_range = range_val
                    break
            
            # Fall back to class/order
            if not expected_range:
                if 'mammalia' in class_name:
                    expected_range = (0.1, 5.0)
                elif 'aves' in class_name:
                    expected_range = (0.05, 2.5)
                elif 'reptilia' in class_name:
                    expected_range = (0.05, 2.0)
                elif 'amphibia' in class_name:
                    expected_range = (0.02, 0.5)
                elif 'actinopterygii' in class_name or 'chondrichthyes' in class_name:
                    expected_range = (0.05, 2.0)  # Fish often use length
                elif 'insecta' in class_name:
                    expected_range = (0.001, 0.2)  # Insects often use length/wingspan
            
            # Allow 10x margin for unit conversion errors (cm vs m)
            if expected_range and max_num > expected_range[1] * 10:
                return False
        
        return True
        
    except:
        return False


def _has_height_context(text: str) -> bool:
    """
    Check if text has height-related context
    Returns True for height/shoulder/standing, False for nests/elevation
    """
    text_lower = text.lower()
    
    # POSITIVE indicators (height-related)
    height_keywords = [
        'height', 'tall', 'shoulder', 'stand', 'standing', 'measures',
        'at the shoulder', 'shoulder height', 'body height', 'total height',
        'upright', 'high', 'depth'  # depth for fish body depth
    ]
    
    # NEGATIVE indicators (reject these)
    reject_keywords = [
        'temporal', 'range:', 'population', 'million years', 'ma ',
        'nest height', 'colony', 'elevation', 'altitude', 'above sea',
        'tree height', 'plant', 'vegetation'
    ]
    
    has_height = any(kw in text_lower for kw in height_keywords)
    has_reject = any(kw in text_lower for kw in reject_keywords)
    
    return has_height and not has_reject


# =============================================================================
# PATTERN DEFINITIONS - Organized by specificity
# =============================================================================
HEIGHT_PATTERNS = [
    # =========================================================================
    # TIER 1: Most Specific (Shoulder Height - Mammals)
    # =========================================================================
    {
        'pattern': r'shoulder\s*height\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft|inches|in)',
        'priority': 1,
        'format': 'range'
    },
    {
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft|inches|in)\s*(?:at the shoulder|shoulder height)',
        'priority': 1,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 2: Standing Height (Large Mammals, Birds)
    # =========================================================================
    {
        'pattern': r'stands?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft|inches|in)\s*(?:tall|at the shoulder|high)?',
        'priority': 2,
        'format': 'range'
    },
    {
        'pattern': r'stands?\s*(?:about|approximately|up to)?\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft|inches|in)\s*(?:tall|high)?',
        'priority': 2,
        'format': 'single'
    },
    
    # =========================================================================
    # TIER 3: Reaches/Measuring (General)
    # =========================================================================
    {
        'pattern': r'reaches?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft|inches|in)\s*(?:tall|height|high|at the shoulder)?',
        'priority': 3,
        'format': 'range'
    },
    {
        'pattern': r'measur(?:ing|es)\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft|inches|in)\s*(?:tall|height|high)?',
        'priority': 3,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 4: Explicit Height Statements
    # =========================================================================
    {
        'pattern': r'height\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft|inches|in)',
        'priority': 4,
        'format': 'range'
    },
    {
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(cm|m)\s*(?:–|-)\s*(\d+(?:[.,]\d+)?)\s*(cm|m|in|ft)\s*(?:tall|height|standing|high)?',
        'priority': 4,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 5: Single Value Height
    # =========================================================================
    {
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft|inches|in)\s*(?:tall|height|standing|high)',
        'priority': 5,
        'format': 'single'
    },
    
    # =========================================================================
    # TIER 6: "Up to" Maximum Height
    # =========================================================================
    {
        'pattern': r'up\s*to\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft|inches|in)\s*(?:tall|height|high)?',
        'priority': 6,
        'format': 'single'
    },
    
    # =========================================================================
    # TIER 7: "Between X and Y" Format
    # =========================================================================
    {
        'pattern': r'between\s*(\d+(?:[.,]\d+)?)\s*(?:and|-|–)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft|inches|in)\s*(?:tall|height|high)?',
        'priority': 7,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 8: Body Depth (Fish)
    # =========================================================================
    {
        'pattern': r'body\s*depth\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m)',
        'priority': 8,
        'format': 'range'
    },
]


# =============================================================================
# SECTION PRIORITY - Where height data typically appears
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
        Height string (e.g., "60–100 cm") or empty string if not found
    """
    if not sections:
        return ""
    
    # STRATEGY 1: Search priority sections first (faster for large-scale)
    for section_name in SECTION_PRIORITY:
        # Try exact match
        if section_name in sections and sections[section_name]:
            text = sections[section_name]
            if len(text) > 50:  # Skip very short sections
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
    # Combine all section content with section markers for context
    all_text = " ".join(sections.values())
    return _extract_height_from_text(all_text, animal_name, classification)


def _extract_height_from_text(
    text: str, 
    animal_name: str = "", 
    classification: Dict[str, str] = None
) -> str:
    """
    Extract height from text content using pattern matching
    
    Args:
        text: Text content to search
        animal_name: Name of the animal (for validation)
        classification: Taxonomic classification (for validation)
    
    Returns:
        Height string or empty string
    """
    if not text or len(text) < 50:
        return ""
    
    # Clean text (remove citations, normalize whitespace)
    clean_text = re.sub(r'\[\d+\]', '', text)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    # Track best match (priority + validation)
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
            
            # Get context around match for validation (100 chars each side)
            start = max(0, m.start() - 100)
            end = min(len(clean_text), m.end() + 100)
            match_context = clean_text[start:end]
            
            # VALIDATION: Check context
            if not _has_height_context(match_context):
                continue
            
            # VALIDATION: Skip temporal ranges
            if "temporal" in match_context.lower() or "million years" in match_context.lower():
                continue
            
            # BUILD result based on pattern format
            if format_type == 'range' and len(groups) >= 3:
                candidate = f"{groups[0]}–{groups[1]} {groups[2]}"
            elif format_type == 'single' and len(groups) >= 2:
                candidate = f"{groups[0]} {groups[1]}"
            else:
                continue
            
            # VALIDATION: Check biological plausibility
            if _is_valid_height(candidate, animal_name, classification):
                best_match = candidate
                best_priority = priority
                break  # Found valid match at this priority
        
        # If we found a match at this priority, no need to check lower priorities
        if best_match and best_priority == priority:
            break
    
    return best_match if best_match else ""


# =============================================================================
# UTILITY FUNCTIONS (for debugging/testing)
# =============================================================================
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
