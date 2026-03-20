"""
Height extraction module - PRODUCTION READY v8
Fixed: Handles parenthetical imperial conversions AFTER metric measurement
Based on ACTUAL African Elephant Wikipedia "Size" section text
"""
import re
from typing import Dict, Any, Optional, List, Tuple


# =============================================================================
# CONFIGURATION - Animal Type Height Expectations (for validation)
# =============================================================================
ANIMAL_HEIGHT_RANGES = {
    # Mammals (shoulder/standing height in meters)
    'felidae': (0.3, 1.5),        # Cats
    'canidae': (0.3, 1.2),         # Dogs/Wolves
    'elephantidae': (2.0, 4.5),    # Elephants - CRITICAL for African Elephant
    'ursidae': (0.6, 3.0),         # Bears
    'giraffidae': (3.0, 6.0),      # Giraffes
    'rhinocerotidae': (1.0, 2.0),  # Rhinos
    'hippopotamidae': (1.0, 1.7),  # Hippos
    'equidae': (1.0, 2.0),         # Horses
    'bovidae': (0.5, 2.0),         # Cattle/Antelope
    'cervidae': (0.5, 2.5),        # Deer
    'suidae': (0.5, 1.2),          # Pigs
    'primates': (0.3, 2.0),        # Primates
    'proboscidea': (2.0, 4.5),     # Elephants (order level) - CRITICAL
    'loxodonta': (2.0, 4.5),       # African Elephant genus - MOST SPECIFIC
    
    # Birds (standing height in meters)
    'accipitridae': (0.5, 1.2),    # Eagles/Hawks
    'spheniscidae': (0.4, 1.2),    # Penguins
    'struthionidae': (1.5, 2.8),   # Ostriches
    'aves_large': (0.5, 2.5),      # Large birds
    'aves_medium': (0.2, 1.0),     # Medium birds
    'aves_small': (0.05, 0.3),     # Small birds
    
    # Reptiles (body height/carapace in meters)
    'testudinidae': (0.1, 0.8),    # Turtles/Tortoises (carapace height)
    'crocodylidae': (0.3, 1.0),    # Crocodiles
    'elapidae': (0.05, 0.5),       # Cobras/Snakes (body diameter)
    'squamata': (0.05, 0.5),       # Snakes/Lizards
    
    # Amphibians (body height in meters)
    'ranidae': (0.02, 0.3),        # Frogs
    'anura': (0.02, 0.3),          # Frogs/Toads
    'caudata': (0.05, 0.5),        # Salamanders
    
    # Fish (body depth in meters - NOT length!)
    'lamnidae': (0.3, 1.5),        # Great White Shark (body depth)
    'salmonidae': (0.05, 0.5),     # Salmon (body depth)
    'fish_large': (0.2, 2.0),      # Large fish
    'fish_medium': (0.05, 0.5),    # Medium fish
    'fish_small': (0.01, 0.2),     # Small fish
    
    # Insects (body height in meters)
    'insecta': (0.001, 0.15),      # Insects
    'hymenoptera': (0.005, 0.05),  # Bees/Wasps
    'lepidoptera': (0.01, 0.15),   # Butterflies/Moths
}


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================
def _is_valid_height(value: str, animal_name: str = "", classification: Dict[str, str] = None) -> bool:
    """Validate height value makes biological sense"""
    if not value or len(value) < 2:
        return False
    
    value_lower = value.lower()
    
    # REJECT contexts
    reject_contexts = [
        'water depth', 'dive depth', 'diving depth', 'ocean depth',
        'migration distance', 'travel distance', 'nesting beach',
        'breeding ground', 'temporal range', 'million years',
        'population', 'individuals', 'specimens'
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
        
        if max_num > 200 or max_num < 0.001:
            return False
        
        if classification:
            family = classification.get('family', '').lower()
            genus = classification.get('genus', '').lower()
            order = classification.get('order', '').lower()
            class_name = classification.get('class', '').lower()
            
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
                    expected_range = (0.02, 0.5)
                elif 'chondrichthyes' in class_name:
                    expected_range = (0.3, 2.0)
                elif 'actinopterygii' in class_name:
                    expected_range = (0.05, 1.0)
                elif 'insecta' in class_name:
                    expected_range = (0.001, 0.2)
            
            if expected_range:
                value_in_meters = max_num / 100 if max_num > 10 else max_num
                if value_in_meters > expected_range[1] * 10 or value_in_meters < expected_range[0] / 10:
                    return False
        
        return True
    except:
        return False


def _has_height_context(text: str, classification: Dict[str, str] = None) -> bool:
    """Check if text has height-related context"""
    text_lower = text.lower()
    
    height_keywords = [
        'height', 'tall', 'shoulder', 'stand', 'standing', 'stood',
        'at the shoulder', 'shoulder height', 'body height',
        'upright', 'high', 'body depth', 'reaches', 'measures',
        'largest', 'biggest', 'size', 'weighing', 'weight',
        'adults measure', 'adults reach', 'typically stands',
        'males are', 'females are', 'male', 'female',
        'bulls', 'cows', 'mature', 'adult', 'fully grown'
    ]
    
    reject_keywords = [
        'water depth', 'dive depth', 'diving depth', 'ocean depth',
        'migration distance', 'travel distance', 'nesting beach',
        'breeding ground', 'temporal range', 'million years',
        'population size', 'elevation', 'altitude', 'above sea level',
        'tree height', 'plant height', 'vegetation height',
        'home range', 'territory range'
    ]
    
    has_height = any(kw in text_lower for kw in height_keywords)
    has_reject = any(kw in text_lower for kw in reject_keywords)
    
    if has_reject:
        return False
    
    return has_height


# =============================================================================
# PATTERN DEFINITIONS - Fixed for parenthetical handling
# =============================================================================
HEIGHT_PATTERNS = [
    # =========================================================================
    # TIER 1: Most Specific (Shoulder Height - Elephants, Large Mammals)
    # =========================================================================
    {
        # "shoulder height of 2.5 to 4 m"
        'pattern': r'shoulder\s*height\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)',
        'priority': 1,
        'format': 'range'
    },
    {
        # "height at the shoulder of 2.5 to 4 metres"
        'pattern': r'height\s*at\s*the\s*shoulder\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)',
        'priority': 1,
        'format': 'range'
    },
    {
        # "2.5–4 m at the shoulder"
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)\s*(?:at the shoulder|shoulder height)',
        'priority': 1,
        'format': 'range'
    },
    {
        # "reach a shoulder height of 3.2–4 m"
        'pattern': r'reach\s*(?:a)?\s*shoulder\s*height\s*(?:of)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)',
        'priority': 1,
        'format': 'range'
    },
    {
        # "shoulder height of up to 4 m"
        'pattern': r'shoulder\s*height\s*(?:of)?\s*up\s*to\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)',
        'priority': 1,
        'format': 'single'
    },
    
    # =========================================================================
    # TIER 2: Standing Height (Large Mammals, Birds) - ELEPHANT CRITICAL
    # =========================================================================
    {
        # "mature fully grown females are 2.47–2.73 m (...) tall at the shoulder"
        # FIXED: Handles parenthetical AFTER unit, BEFORE "tall"
        'pattern': r'(?:mature\s+)?(?:fully\s+grown\s+)?(?:females?|males?|bulls?|cows?|adults?)\s+(?:are|is)\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?)\s*(?:\s*\([^)]*\))?\s*(?:tall(?:\s+at\s+the\s+shoulder)?|at\s+the\s+shoulder|high)?',
        'priority': 2,
        'format': 'range'
    },
    {
        # "The largest recorded bull stood 3.96 m (...) at the shoulder"
        'pattern': r'(?:largest|record|maximum).*?(?:stood|stands?)\s+(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|feet|ft)\s*(?:\s*\([^)]*\))?\s*(?:at\s+the\s+shoulder|tall|high)?',
        'priority': 2,
        'format': 'single'
    },
    {
        # "Males are 3.2–4 m tall at the shoulder"
        'pattern': r'(?:males?|females?|bulls?|cows?|adults?)\s+(?:are|is)\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)\s*(?:\s*\([^)]*\))?\s*(?:tall|at the shoulder|high)?',
        'priority': 2,
        'format': 'range'
    },
    {
        # "stands 2.5 to 4 m tall"
        'pattern': r'stands?\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)\s*(?:\s*\([^)]*\))?\s*(?:tall|at the shoulder|high)?',
        'priority': 2,
        'format': 'range'
    },
    {
        # "stands up to 4 m tall"
        'pattern': r'stands?\s+(?:up\s+to|about|approximately)?\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)\s*(?:\s*\([^)]*\))?\s*(?:tall|high)?',
        'priority': 2,
        'format': 'single'
    },
    {
        # "typically stands 2.5 to 4 m"
        'pattern': r'typically\s+stands?\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?)\s*(?:\s*\([^)]*\))?\s*(?:tall)?',
        'priority': 2,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 3: Reaches/Measuring (General)
    # =========================================================================
    {
        # "reaches 2.5 to 4 m tall"
        'pattern': r'reaches?\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)\s*(?:\s*\([^)]*\))?\s*(?:tall|height|high|at the shoulder)?',
        'priority': 3,
        'format': 'range'
    },
    {
        # "measuring 2.5 to 4 m tall"
        'pattern': r'measur(?:ing|es)\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)\s*(?:\s*\([^)]*\))?\s*(?:tall|height|high)?',
        'priority': 3,
        'format': 'range'
    },
    {
        # "adults measure 2.5 to 4 m"
        'pattern': r'adults?\s+measur(?:e|ing)\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?)\s*(?:\s*\([^)]*\))?\s*(?:tall|height)?',
        'priority': 3,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 4: Explicit Height Statements
    # =========================================================================
    {
        # "height of 2.5 to 4 m"
        'pattern': r'height\s+(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)',
        'priority': 4,
        'format': 'range'
    },
    {
        # "2.5 m tall"
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(cm|m)\s*(?:–|-)\s*(\d+(?:[.,]\d+)?)\s*(cm|m|in|ft)\s*(?:\s*\([^)]*\))?\s*(?:tall|height|standing|high)?',
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
        'pattern': r'up\s+to\s+(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)\s*(?:\s*\([^)]*\))?\s*(?:tall|height|high)?',
        'priority': 7,
        'format': 'single'
    },
    
    # =========================================================================
    # TIER 8: "Between X and Y" Format
    # =========================================================================
    {
        # "between 2.5 and 4 m tall"
        'pattern': r'between\s+(\d+(?:[.,]\d+)?)\s+(?:and|-|–)\s+(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?|m|feet|ft)\s*(?:\s*\([^)]*\))?\s*(?:tall|height|high)?',
        'priority': 8,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 9: Fallback Patterns
    # =========================================================================
    {
        # "size 2.5 to 4 m"
        'pattern': r'size.*?(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?)',
        'priority': 9,
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
    
    # Search priority sections first
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
    
    # Fallback: Search all sections
    all_text = " ".join(sections.values())
    return _extract_height_from_text(all_text, animal_name, classification)


def _extract_height_from_text(
    text: str, 
    animal_name: str = "", 
    classification: Dict[str, str] = None
) -> str:
    """Extract height from text content using pattern matching"""
    if not text or len(text) < 50:
        return ""
    
    # Clean text
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
