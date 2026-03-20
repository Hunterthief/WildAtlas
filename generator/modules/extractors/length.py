"""
Length Extraction Module - PRODUCTION v27 (CRITICAL BUG FIXES)
WildAtlas Project

CRITICAL FIXES:
- Added "tail" to bad context (wolf fix - 9-11in was tail length)
- Added "wingspan" filtering (butterfly fix - 1.2m was wingspan)
- Added strict insect validation (bee fix - 34m is impossible)
- Added reversed range detection (elephant fix - 7-6m → 6-7m)
- Added unit conversion validation
"""

import re
from typing import Dict, Any, Optional


# =============================================================================
# CONFIGURATION - Length Ranges in METERS
# =============================================================================
ANIMAL_LENGTH_RANGES = {
    # Mammals
    'felidae': (0.6, 3.5),
    'canidae': (0.5, 2.0),
    'elephantidae': (4.0, 8.5),
    'ursidae': (1.0, 3.5),
    'giraffidae': (3.5, 6.5),
    'proboscidea': (4.0, 8.5),
    
    # Birds
    'accipitridae': (0.4, 1.5),
    'accipitriformes': (0.4, 1.5),
    'spheniscidae': (0.5, 1.3),
    'aves': (0.1, 2.5),
    
    # Reptiles
    'cheloniidae': (0.6, 1.5),
    'elapidae': (2.0, 6.0),
    'reptilia': (0.1, 10.0),
    
    # Fish
    'lamnidae': (3.0, 8.5),
    'salmonidae': (0.5, 1.5),
    'actinopterygii': (0.01, 5.0),
    
    # Insects - CRITICAL: Proper ranges
    'hymenoptera': (0.005, 0.03),  # Bees: 0.5-3 cm
    'lepidoptera': (0.02, 0.15),   # Butterflies: 2-15 cm
    'apidae': (0.008, 0.025),      # Honey bees: 0.8-2.5 cm
    'nymphalidae': (0.02, 0.12),   # Monarchs: 2-12 cm
    'insecta': (0.001, 0.20),      # General insects: 0.1-20 cm MAX
}


# =============================================================================
# UTIL - Unit Conversion
# =============================================================================
def convert_to_meters(value: float, unit: str) -> float:
    """Convert value to meters"""
    unit = unit.lower().strip()
    conversions = {
        'm': 1.0, 'meter': 1.0, 'meters': 1.0,
        'cm': 0.01, 'centimeter': 0.01, 'centimeters': 0.01,
        'mm': 0.001, 'millimeter': 0.001, 'millimeters': 0.001,
        'ft': 0.3048, 'foot': 0.3048, 'feet': 0.3048,
        'in': 0.0254, 'inch': 0.0254, 'inches': 0.0254,
        'km': 1000.0,
    }
    return value * conversions.get(unit, 1.0)


# =============================================================================
# VALIDATION - CRITICAL FIXES
# =============================================================================
def _is_valid_length(value: str, animal_name="", classification=None) -> bool:
    """Validate length value makes sense for animal type"""
    if not value:
        return False
    
    # Extract all measurements from value
    matches = re.findall(r'(\d+(?:\.\d+)?)\s*(m|cm|mm|ft|in|meter|centimeter|millimeter|inch|foot)', value.lower())
    if not matches:
        return False
    
    # Convert all to meters
    try:
        values_m = [convert_to_meters(float(v), u) for v, u in matches]
    except:
        return False
    
    if not values_m:
        return False
    
    max_v = max(values_m)
    min_v = min(values_m)
    
    # GLOBAL SANITY CHECKS
    if max_v < 0.001:  # Less than 1mm - too small
        return False
    if max_v > 50:  # More than 50m - too large
        return False
    
    # Check for reversed ranges (e.g., "7-6 m")
    if len(values_m) >= 2 and min_v > max_v * 1.1:
        return False
    
    # ANIMAL-SPECIFIC VALIDATION
    if classification:
        family = classification.get("family", "").lower()
        order = classification.get("order", "").lower()
        cls = classification.get("class", "").lower()
        animal_lower = animal_name.lower() if animal_name else ""
        
        # Family-based ranges (most specific)
        for taxon, (low, high) in ANIMAL_LENGTH_RANGES.items():
            if taxon in family or taxon in order:
                # Allow 50% tolerance
                if not (low * 0.5 <= max_v <= high * 1.5):
                    return False
                break
        
        # Elephant safeguard
        if "elephant" in animal_lower:
            if max_v < 3.0 or max_v > 10.0:
                return False
        
        # Wolf/canine safeguard
        if "wolf" in animal_lower or "canis" in family:
            if max_v < 0.5 or max_v > 2.5:
                return False
        
        # Bird safeguard
        if "aves" in cls:
            if not (0.15 <= max_v <= 3.0):
                return False
        
        # Insect safeguard - CRITICAL FIX
        if "insecta" in cls:
            if max_v > 0.25:  # Nothing insect is > 25cm body length
                return False
        
        # Butterfly/moth specific
        if "lepidoptera" in order or "butterfly" in animal_lower or "moth" in animal_lower:
            if max_v > 0.20:  # Wingspan max ~20cm for most
                return False
        
        # Bee specific - CRITICAL FIX
        if "bee" in animal_lower or "apis" in classification.get("genus", "").lower():
            if max_v > 0.05:  # Bees are < 5cm
                return False
    
    return True


def _has_bad_context(text: str) -> bool:
    """Check if measurement is about wrong body part"""
    text_lower = text.lower()
    
    # CRITICAL FIX: Added "tail" for wolf fix
    bad_keywords = [
        "wingspan", "wing span", "wing length",
        "shoulder height", "height at shoulder", "at the shoulder",
        "tusk", "tusks", "ivory",
        "horn", "horns", "antler",
        "tail", "tail length", "long tail",  # CRITICAL: Wolf fix
        "trunk", "ear", "ears",
        "neck", "head length", "skull",
        "forearm", "wings", "wing chord",
    ]
    
    return any(kw in text_lower for kw in bad_keywords)


def _has_length_context(text: str) -> bool:
    """Check if text is about body length"""
    text_lower = text.lower()
    
    good_keywords = [
        "length", "long", "measures", "measuring",
        "body length", "total length", "snout",
        "from head", "nose to", "tip of",
        "adults measure", "adults reach",
    ]
    
    return any(kw in text_lower for kw in good_keywords)


def _fix_reversed_range(value: str) -> str:
    """Fix reversed ranges like '7-6 m' → '6-7 m'"""
    match = re.match(r'(\d+(?:\.\d+)?)\s*[–-]\s*(\d+(?:\.\d+)?)\s*(\w+)', value)
    if match:
        v1, v2, unit = float(match.group(1)), float(match.group(2)), match.group(3)
        if v1 > v2 * 1.1:  # Reversed
            return f"{v2}–{v1} {unit}"
    return value


# =============================================================================
# PATTERNS - Ordered by Specificity
# =============================================================================
PATTERNS = [
    # 1. Explicit body length (highest priority)
    (r'body length[^.]{0,80}?(\d+(?:\.\d+)?)\s*(?:–|-|to)\s*(\d+(?:\.\d+)?)\s*(m|cm|mm|ft|in)', "range"),
    (r'body length[^.]{0,80}?(\d+(?:\.\d+)?)\s*(m|cm|mm|ft|in)', "single"),
    
    # 2. Standard length patterns with context
    (r'(\d+(?:\.\d+)?)\s*(?:–|-|to)\s*(\d+(?:\.\d+)?)\s*(m|cm|mm|ft|in)\s+(?:long|in length|body length)', "range"),
    (r'(\d+(?:\.\d+)?)\s*(m|cm|mm|ft|in)\s+(?:long|in length|body length)', "single"),
    
    # 3. "measures X to Y" patterns
    (r'measures?\s*(?:between|from|about)?\s*(\d+(?:\.\d+)?)\s*(?:–|-|to)\s*(\d+(?:\.\d+)?)\s*(m|cm|mm|ft|in)', "range"),
    (r'measures?\s*(?:about|approximately)?\s*(\d+(?:\.\d+)?)\s*(m|cm|mm|ft|in)', "single"),
    
    # 4. "reaches X" patterns
    (r'reaches?\s*(?:lengths? of|up to|about)?\s*(\d+(?:\.\d+)?)\s*(?:–|-|to)?\s*(\d+(?:\.\d+)?)?\s*(m|cm|mm|ft|in)', "range"),
    
    # 5. Loose fallback (use carefully)
    (r'(\d+(?:\.\d+)?)\s*(?:–|-|to)\s*(\d+(?:\.\d+)?)\s*(m|cm|mm|ft|in)', "range_loose"),
    (r'(\d+(?:\.\d+)?)\s*(m|cm|mm|ft|in)', "single_loose"),
]


# =============================================================================
# CORE EXTRACTION
# =============================================================================
def _extract_length_from_text(text: str, animal_name: str = "", classification: Dict = None) -> str:
    """Extract length from text with validation"""
    if not text or len(text) < 20:
        return ""
    
    # Clean citations
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\s+', ' ', text)
    
    for pattern, pattern_type in PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            # Get context window (300 chars)
            start = max(0, match.start() - 150)
            end = min(len(text), match.end() + 150)
            snippet = text[start:end]
            
            # CRITICAL: Skip bad contexts early
            if _has_bad_context(snippet):
                continue
            
            # Require length context for non-loose patterns
            if "loose" not in pattern_type and not _has_length_context(snippet):
                continue
            
            # Build value string
            groups = match.groups()
            if len(groups) >= 3 and groups[1]:  # Range
                value = f"{groups[0]}–{groups[1]} {groups[2]}"
            elif len(groups) >= 2:  # Single
                value = f"{groups[0]} {groups[1]}"
            else:
                continue
            
            # Fix reversed ranges
            value = _fix_reversed_range(value)
            
            # Validate
            if _is_valid_length(value, animal_name, classification):
                return value
    
    return ""


def extract_length_from_sections(
    sections: Dict[str, str],
    animal_name: str = "",
    classification: Dict = None
) -> str:
    """Extract length from Wikipedia sections"""
    
    if not sections:
        return ""
    
    # Priority sections (most likely to have body length)
    priority_order = [
        "description", "characteristics", "size", "biology",
        "physical_description", "morphology", "anatomy"
    ]
    
    # Try priority sections first
    for key in priority_order:
        if key in sections and sections[key]:
            result = _extract_length_from_text(
                sections[key],
                animal_name,
                classification
            )
            if result:
                return result
    
    # Fallback: search all sections
    for section_name, section_text in sections.items():
        if section_name in priority_order:
            continue  # Already tried
        if section_text and len(section_text) > 50:
            result = _extract_length_from_text(
                section_text,
                animal_name,
                classification
            )
            if result:
                return result
    
    return ""


def get_pattern_stats() -> Dict[str, Any]:
    return {
        "patterns": len(PATTERNS),
        "families_with_ranges": len(ANIMAL_LENGTH_RANGES),
    }
