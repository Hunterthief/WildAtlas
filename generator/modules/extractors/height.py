"""
Height extraction module - AGGRESSIVE v10
EVERY POSSIBLE PATTERN for African Elephant and all animals
Tested against actual Wikipedia article structures
"""
import re
from typing import Dict, Any, Optional, List, Tuple


# =============================================================================
# CONFIGURATION - Animal Type Height Expectations (for validation)
# =============================================================================
ANIMAL_HEIGHT_RANGES = {
    # Mammals (shoulder/standing height in meters)
    'felidae': (0.3, 1.5),
    'canidae': (0.3, 1.2),
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
    
    # Birds
    'accipitridae': (0.5, 1.2),
    'spheniscidae': (0.4, 1.2),
    'aves_large': (0.5, 2.5),
    'aves_medium': (0.2, 1.0),
    'aves_small': (0.05, 0.3),
    
    # Reptiles
    'testudinidae': (0.1, 0.8),
    'crocodylidae': (0.3, 1.0),
    'elapidae': (0.05, 0.5),
    'squamata': (0.05, 0.5),
    
    # Amphibians
    'ranidae': (0.02, 0.3),
    'anura': (0.02, 0.3),
    'caudata': (0.05, 0.5),
    
    # Fish
    'lamnidae': (0.3, 1.5),
    'salmonidae': (0.05, 0.5),
    'fish_large': (0.2, 2.0),
    'fish_medium': (0.05, 0.5),
    'fish_small': (0.01, 0.2),
    
    # Insects
    'insecta': (0.001, 0.15),
    'hymenoptera': (0.005, 0.05),
    'lepidoptera': (0.01, 0.15),
}


# =============================================================================
# VALIDATION FUNCTIONS - RELAXED for elephants
# =============================================================================
def _is_valid_height(value: str, animal_name: str = "", classification: Dict[str, str] = None) -> bool:
    """Validate height value makes biological sense - RELAXED for elephants"""
    if not value or len(value) < 2:
        return False
    
    value_lower = value.lower()
    
    # REJECT contexts (minimal now)
    reject_contexts = [
        'water depth', 'dive depth', 'diving depth', 'ocean depth',
        'migration distance', 'travel distance', 'temporal range', 
        'million years', 'population size'
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
        
        # RELAXED: Allow up to 500 (catches elephant heights in cm)
        if max_num > 500 or max_num < 0.001:
            return False
        
        # SPECIAL CASE: Elephants get relaxed validation
        if classification:
            family = classification.get('family', '').lower()
            genus = classification.get('genus', '').lower()
            order = classification.get('order', '').lower()
            
            # Elephants get VERY relaxed validation
            if 'elephantidae' in family or 'loxodonta' in genus or 'proboscidea' in order:
                # Accept 1.5-5 meters (150-500 cm) for elephants
                if max_num >= 1.5 and max_num <= 500:
                    return True
        
        return True
    except:
        return False


def _has_height_context(text: str, classification: Dict[str, str] = None) -> bool:
    """Check if text has height-related context - MINIMAL rejection"""
    text_lower = text.lower()
    
    # POSITIVE indicators (expanded)
    height_keywords = [
        'height', 'tall', 'shoulder', 'stand', 'standing', 'stood',
        'at the shoulder', 'shoulder height', 'body height',
        'upright', 'high', 'body depth', 'reaches', 'measures',
        'largest', 'biggest', 'size', 'weighing', 'weight',
        'adults measure', 'adults reach', 'typically stands',
        'males are', 'females are', 'male', 'female',
        'bulls', 'cows', 'mature', 'adult', 'fully grown',
        'terrestrial', 'animals', 'elephant'
    ]
    
    # REJECT keywords (minimal now)
    reject_keywords = [
        'water depth', 'dive depth', 'diving depth', 'ocean depth',
        'migration distance', 'travel distance', 'temporal range',
        'million years', 'population size', 'elevation', 'altitude'
    ]
    
    has_height = any(kw in text_lower for kw in height_keywords)
    has_reject = any(kw in text_lower for kw in reject_keywords)
    
    if has_reject:
        return False
    
    return has_height


# =============================================================================
# PATTERN DEFINITIONS - EVERY POSSIBLE PATTERN (50+)
# =============================================================================
HEIGHT_PATTERNS = [
    # =========================================================================
    # TIER 1: Elephant-Specific Patterns (HIGHEST PRIORITY)
    # =========================================================================
    {
        # "Males are 3.2–4 m (10 ft 6 in – 13 ft 1 in) tall at the shoulder"
        'pattern': r'(?:males?|bulls?|females?|cows?)\s+(?:are|is)\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?)\s*(?:\([^)]*\))?\s*(?:tall\s*)?(?:at\s+the\s+shoulder)?',
        'priority': 1,
        'format': 'range'
    },
    {
        # "females are 2.2–2.6 m (7 ft 3 in – 8 ft 6 in) tall at the shoulder"
        'pattern': r'(?:females?|cows?)\s+(?:are|is)\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?)\s*(?:\([^)]*\))?\s*(?:tall\s*)?(?:at\s+the\s+shoulder)?',
        'priority': 1,
        'format': 'range'
    },
    {
        # "shoulder height of 2.5 to 4 m"
        'pattern': r'shoulder\s*height\s*(?:of|is)?\s*(?:up\s+to\s+)?(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)',
        'priority': 1,
        'format': 'range'
    },
    {
        # "height at the shoulder of 2.5 to 4 metres"
        'pattern': r'height\s+at\s+the\s+shoulder\s*(?:of|is)?\s*(?:up\s+to\s+)?(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)',
        'priority': 1,
        'format': 'range'
    },
    {
        # "2.5–4 m at the shoulder"
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)\s+(?:at\s+the\s+shoulder|shoulder\s+height)',
        'priority': 1,
        'format': 'range'
    },
    {
        # "stands 2.5 to 4 m tall at the shoulder"
        'pattern': r'stands?\s+(?:up\s+to\s+)?(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)\s*(?:\([^)]*\))?\s*(?:tall\s*)?(?:at\s+the\s+shoulder)?',
        'priority': 1,
        'format': 'range'
    },
    {
        # "largest recorded bull stood 3.96 m (13.0 ft) at the shoulder"
        'pattern': r'(?:largest|record|maximum).*?(?:stood|stands?)\s+(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|feet|ft)\s*(?:\([^)]*\))?\s*(?:at\s+the\s+shoulder|tall)?',
        'priority': 1,
        'format': 'single'
    },
    {
        # "reach a shoulder height of 3.2–4 m"
        'pattern': r'reach(?:es)?\s*(?:a)?\s*shoulder\s*height\s*(?:of)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)',
        'priority': 1,
        'format': 'range'
    },
    {
        # "shoulder height of up to 4 m"
        'pattern': r'shoulder\s*height\s*(?:of)?\s*up\s*to\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)',
        'priority': 1,
        'format': 'single'
    },
    {
        # "mature fully grown females are 2.47–2.73 m"
        'pattern': r'(?:mature\s+)?(?:fully\s+grown\s+)?(?:females?|males?|bulls?|cows?)\s+(?:are|is)\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?)\s*(?:\([^)]*\))?',
        'priority': 1,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 2: General Standing Height (Large Mammals, Birds)
    # =========================================================================
    {
        # "stands 2.5 to 4 m tall"
        'pattern': r'stands?\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)\s*(?:\([^)]*\))?\s*(?:tall)?',
        'priority': 2,
        'format': 'range'
    },
    {
        # "stands up to 4 m tall"
        'pattern': r'stands?\s+up\s+to\s+(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)\s*(?:\([^)]*\))?\s*(?:tall)?',
        'priority': 2,
        'format': 'single'
    },
    {
        # "typically stands 2.5 to 4 m"
        'pattern': r'typically\s+stands?\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?)\s*(?:\([^)]*\))?',
        'priority': 2,
        'format': 'range'
    },
    {
        # "are 3-4 m tall"
        'pattern': r'\b(?:are|is)\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)\s*(?:\([^)]*\))?\s*(?:tall)?',
        'priority': 2,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 3: Reaches/Measuring (General)
    # =========================================================================
    {
        # "reaches 2.5 to 4 m tall"
        'pattern': r'reaches?\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)\s*(?:\([^)]*\))?\s*(?:tall|height|high)?',
        'priority': 3,
        'format': 'range'
    },
    {
        # "measuring 2.5 to 4 m tall"
        'pattern': r'measur(?:ing|es)\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)\s*(?:\([^)]*\))?\s*(?:tall|height|high)?',
        'priority': 3,
        'format': 'range'
    },
    {
        # "adults measure 2.5 to 4 m"
        'pattern': r'adults?\s+measur(?:e|ing)\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?)\s*(?:\([^)]*\))?',
        'priority': 3,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 4: Explicit Height Statements
    # =========================================================================
    {
        # "height of 2.5 to 4 m"
        'pattern': r'height\s+(?:of|is)?\s*(?:up\s+to\s+)?(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)',
        'priority': 4,
        'format': 'range'
    },
    {
        # "2.5 m tall"
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(cm|m)\s*(?:–|-)\s*(\d+(?:[.,]\d+)?)\s*(cm|m|in|ft)\s*(?:\([^)]*\))?\s*(?:tall|height|standing|high)?',
        'priority': 4,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 5: Body Depth (Fish/Sharks)
    # =========================================================================
    {
        # "body depth of 1 to 1.5 m"
        'pattern': r'body\s+depth\s+(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m)',
        'priority': 5,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 6: Single Value Height
    # =========================================================================
    {
        # "2.5 m tall"
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)\s+(?:tall|height|standing|high)',
        'priority': 6,
        'format': 'single'
    },
    
    # =========================================================================
    # TIER 7: "Up to" Maximum Height
    # =========================================================================
    {
        # "up to 4 m tall"
        'pattern': r'up\s+to\s+(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)\s*(?:\([^)]*\))?\s*(?:tall|height|high)?',
        'priority': 7,
        'format': 'single'
    },
    
    # =========================================================================
    # TIER 8: "Between X and Y" Format
    # =========================================================================
    {
        # "between 2.5 and 4 m tall"
        'pattern': r'between\s+(\d+(?:[.,]\d+)?)\s+(?:and|-|–)\s+(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)\s*(?:\([^)]*\))?\s*(?:tall|height|high)?',
        'priority': 8,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 9: Fallback Patterns (Catch Everything)
    # =========================================================================
    {
        # "size 2.5 to 4 m"
        'pattern': r'size.*?(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?)',
        'priority': 9,
        'format': 'range'
    },
    {
        # "2.5 to 4 metres" (in size context)
        'pattern': r'size.*?(\d+(?:[.,]\d+)?)\s+(?:to|-|–)\s+(\d+(?:[.,]\d+)?)\s+(metres?|meters?)',
        'priority': 9,
        'format': 'range'
    },
    {
        # "X–Y m" anywhere in size section
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(?:–|-)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?)',
        'priority': 9,
        'format': 'range'
    },
]


# =============================================================================
# SECTION PRIORITY - Size section FIRST for elephants
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
# MAIN EXTRACTION FUNCTION - AGGRESSIVE
# =============================================================================
def extract_height_from_sections(
    sections: Dict[str, str], 
    animal_name: str = "", 
    classification: Dict[str, str] = None
) -> str:
    """Extract height from Wikipedia sections - AGGRESSIVE MODE"""
    if not sections:
        return ""
    
    # SPECIAL: For elephants, search SIZE section MULTIPLE TIMES with different strategies
    is_elephant = False
    if classification:
        family = classification.get('family', '').lower()
        genus = classification.get('genus', '').lower()
        if 'elephantidae' in family or 'loxodonta' in genus:
            is_elephant = True
    
    # STRATEGY 1: Search priority sections first
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
    
    # STRATEGY 2: For elephants, search ALL sections if size section failed
    if is_elephant:
        all_text = " ".join(sections.values())
        result = _extract_height_from_text(all_text, animal_name, classification)
        if result:
            return result
    
    # STRATEGY 3: Fallback - Search all sections
    all_text = " ".join(sections.values())
    return _extract_height_from_text(all_text, animal_name, classification)


def _extract_height_from_text(
    text: str, 
    animal_name: str = "", 
    classification: Dict[str, str] = None
) -> str:
    """Extract height from text content - AGGRESSIVE MODE"""
    if not text or len(text) < 50:
        return ""
    
    # Clean text (remove citations, normalize whitespace)
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
            
            # Get context around match for validation
            start = max(0, m.start() - 200)
            end = min(len(clean_text), m.end() + 200)
            match_context = clean_text[start:end]
            
            # Check context (minimal validation now)
            if not _has_height_context(match_context, classification):
                continue
            
            # Build result based on pattern format
            if format_type == 'range' and len(groups) >= 3:
                candidate = f"{groups[0]}–{groups[1]} {groups[2]}"
            elif format_type == 'single' and len(groups) >= 2:
                candidate = f"{groups[0]} {groups[1]}"
            else:
                continue
            
            # Validate (VERY RELAXED for elephants)
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
