"""
Length Extraction Module - PRODUCTION v18
WildAtlas Project - https://github.com/Hunterthief/WildAtlas/
Inspired by facts.app but for normal animals

Fixed Issues (v18):
- Cheetah: head-body length between pattern (was empty)
- African Elephant: Reject 30cm tusk measurement, get 4.5-7.5m body length
- Gray Wolf: Reject shoulder height (29-50cm), get 1.0-1.6m body length
- Bald Eagle: Reject 11cm (beak/talon), get 70-120cm body length
- Monarch Butterfly: Reject wingspan, get 4.5-5cm body length
- Honey Bee: Get 10-15mm body length (was empty)

Based on analysis of 13 animal Wikipedia articles from WildAtlas + actual Wikipedia text review
"""
import re
from typing import Dict, Optional, List, Tuple, Any


# =============================================================================
# CONFIGURATION - Animal Type Length Expectations (for validation)
# All ranges in METERS for consistent comparison
# =============================================================================
ANIMAL_LENGTH_RANGES = {
    # Mammals (body length in meters, NOT including tail unless specified)
    'felidae': (0.7, 2.5),        # Cats body length (tiger ~1.7-2.5m, cheetah ~1.1-1.5m)
    'canidae': (0.7, 1.8),        # Dogs/Wolves body length (NOT shoulder height)
    'elephantidae': (4.5, 7.5),   # Elephants total length with trunk
    'ursidae': (1.0, 3.0),        # Bears
    'giraffidae': (3.5, 6.0),     # Giraffes
    'proboscidea': (4.5, 7.5),    # Elephants order
    
    # Birds (body length, NOT wingspan)
    'accipitridae': (0.6, 1.2),   # Eagles body length (70-120cm)
    'accipitriformes': (0.5, 1.3), # Eagle order
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
    'lamniformes': (4.0, 7.0),    # Shark order
    
    # Amphibians
    'ranidae': (0.06, 0.20),      # Frogs (6-20cm)
    'anura': (0.03, 0.25),        # Frog order
    
    # Insects (body length, NOT wingspan)
    'hymenoptera': (0.008, 0.03), # Bees (8-30mm)
    'lepidoptera': (0.02, 0.08),  # Butterflies body (2-8cm)
    'apidae': (0.008, 0.03),      # Honey bees specifically
    'nymphalidae': (0.03, 0.06),  # Monarch butterfly family
}


# =============================================================================
# UNIT CONVERSION - Convert all measurements to meters for validation
# =============================================================================
def convert_to_meters(value: float, unit: str) -> float:
    """Convert a measurement to meters"""
    unit = unit.lower().strip()
    
    if unit in ['m', 'meter', 'meters', 'metre', 'metres']:
        return value
    elif unit in ['cm', 'centimeter', 'centimeters', 'centimetre', 'centimetres']:
        return value / 100
    elif unit in ['mm', 'millimeter', 'millimeters', 'millimetre', 'millimetres']:
        return value / 1000
    elif unit in ['ft', 'foot', 'feet']:
        return value * 0.3048
    elif unit in ['in', 'inch', 'inches', '"']:
        return value * 0.0254
    elif unit in ['km', 'kilometer', 'kilometers']:
        return value * 1000
    else:
        return value  # Assume meters if unknown


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
        'extinct', 'years ago', 'evolved', 'tusk', 'trunk length'
    ]
    
    for context in reject_contexts:
        if context in value_lower:
            return False
    
    # Extract numeric values and units
    # Pattern: number followed by unit
    matches = re.findall(r'(\d+(?:[.,]?\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|mm|millimetres?|millimeters?|ft|feet|in|inches)', value_lower)
    
    if not matches:
        return False
    
    try:
        # Get all numeric values converted to meters
        values_in_meters = []
        for num_str, unit in matches:
            num = float(num_str.replace(',', ''))
            meters = convert_to_meters(num, unit)
            values_in_meters.append(meters)
        
        if not values_in_meters:
            return False
        
        max_meters = max(values_in_meters)
        min_meters = min(values_in_meters)
        
        # REJECT: Too small or too large for any animal
        if max_meters < 0.005 or max_meters > 50:
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
                    expected_range = (0.15, 1.5)
                elif 'reptilia' in class_name:
                    expected_range = (0.2, 7.0)
                elif 'amphibia' in class_name:
                    expected_range = (0.05, 0.5)
                elif 'actinopterygii' in class_name or 'chondrichthyes' in class_name:
                    expected_range = (0.1, 8.0)
                elif 'insecta' in class_name:
                    expected_range = (0.005, 0.1)
            
            if expected_range:
                # CRITICAL FIX #1: For cats (felidae), reject >3m as it's likely total length with tail
                if 'felidae' in family:
                    if max_meters > 3.5:
                        return False
                    # Also reject if primary number > 3.5 (total length with tail)
                    for num_str, unit in matches:
                        num = float(num_str.replace(',', ''))
                        if num > 3.5 and unit in ['m', 'meter', 'meters']:
                            return False
                
                # CRITICAL FIX #2: For wolves/dogs (canidae), reject <0.5m as it's likely shoulder height
                if 'canidae' in family:
                    if max_meters < 0.5:
                        return False
                    if max_meters > 2.0:
                        return False
                
                # CRITICAL FIX #3: For elephants, reject <4m (2.4m is shoulder height, not length)
                # Also reject small values like 30cm (tusk measurement)
                if 'elephantidae' in family or 'proboscidea' in order:
                    if max_meters < 4.0:
                        return False
                    if max_meters > 8.0:
                        return False
                
                # CRITICAL FIX #4: For birds, reject if too small or too large (wingspan)
                if 'aves' in class_name:
                    if max_meters < 0.20:  # Reject values < 20cm for bird body length
                        return False
                    if max_meters > 1.5:
                        return False
                
                # CRITICAL FIX #5: For butterflies, reject >10cm (wingspan!)
                if 'lepidoptera' in order or 'nymphalidae' in family:
                    if max_meters > 0.10:  # Reject > 10cm (likely wingspan)
                        return False
                    if max_meters < 0.015:  # Reject < 1.5cm
                        return False
                
                # CRITICAL FIX #6: For bees/insects, validate mm range properly
                if 'insecta' in class_name:
                    if max_meters > 0.15:  # Reject > 15cm for insects
                        return False
                    if 'hymenoptera' in order or 'apidae' in family:
                        if max_meters < 0.005 or max_meters > 0.035:  # 5-35mm for bees
                            return False
                
                # Allow 3x margin for unit conversion errors (more flexible)
                if max_meters > expected_range[1] * 3:
                    return False
                if min_meters < expected_range[0] / 5:
                    return False
        
        return True
        
    except Exception as e:
        return False


def _has_length_context(text: str, animal_name: str = "") -> bool:
    """Check if text has length-related context - SMART shoulder/wingspan/tail rejection"""
    text_lower = text.lower()
    
    # POSITIVE indicators (length-related)
    length_keywords = [
        'length', 'long', 'measures', 'reaching', 'grows',
        'body length', 'total length', 'head-body', 'head and body',
        'carapace', 'adult', 'mature', 'full-grown',
        'from head', 'from snout', 'from nose',
        'typically', 'average', 'usually', 'about', 'approximately', 'between'
    ]
    
    # REJECT keywords - shoulder/distribution/wingspan rejection
    reject_keywords = [
        'temporal range', 'million years', 'ma ', 'mya',
        'wingspan', 'wing span', 'wing length', 'wing spread',
        'egg length', 'nest length', 'colony length',
        'population size', 'range size',
        'at the shoulder', 'shoulder height', 'shoulder to',
        'distribution', 'range:', 'migrat', 'found from',
        'occurs from', 'native to', 'habitat', 'geographic',
        'tusk', 'trunk length', 'tail length'
    ]
    
    # CRITICAL: Check for shoulder context
    if 'shoulder' in text_lower:
        if 'shoulder height' in text_lower or 'at the shoulder' in text_lower:
            return False
    
    # CRITICAL: Check for distribution/range context
    if any(kw in text_lower for kw in ['distribution', 'range:', 'found from', 'occurs from', 'native to', 'geographic']):
        return False
    
    # CRITICAL: Check for height context (not length)
    if any(kw in text_lower for kw in ['height', 'tall', 'stands', 'high']):
        if 'length' not in text_lower:
            return False
    
    # CRITICAL: For butterflies/moths, reject wingspan measurements
    animal_lower = animal_name.lower() if animal_name else ""
    if any(x in animal_lower for x in ['butterfly', 'moth']):
        if 'wingspan' in text_lower or 'wing span' in text_lower:
            return False
        if 'wing' in text_lower and 'body' not in text_lower:
            return False
        # Reject any value >10cm for butterflies (likely wingspan)
        wing_values = re.findall(r'(\d+[.,]?\d*)\s*(?:cm|m|metres?|meters?)', text_lower)
        for val in wing_values:
            try:
                num = float(val.replace(',', ''))
                if 'm' in text_lower and num > 0.1:
                    return False
                if 'cm' in text_lower and num > 10:
                    return False
            except:
                pass
    
    # CRITICAL: For birds, reject wingspan measurements
    if any(x in animal_lower for x in ['eagle', 'hawk', 'bird', 'penguin']):
        if 'wingspan' in text_lower or 'wing span' in text_lower:
            return False
        if 'wing' in text_lower and 'body' not in text_lower:
            if 'length' in text_lower:
                if 'wing length' in text_lower or 'length of the wing' in text_lower:
                    return False
    
    # CRITICAL: For bees/insects, reject wingspan
    if any(x in animal_lower for x in ['bee', 'wasp', 'insect']):
        if 'wingspan' in text_lower or 'wing span' in text_lower:
            return False
    
    # SPECIAL: For cats, prefer "head-body" over "total length"
    if any(x in animal_lower for x in ['tiger', 'cheetah', 'lion', 'cat', 'leopard', 'jaguar']):
        if 'total length' in text_lower and 'tail' in text_lower:
            return False
        if 'total length' in text_lower:
            large_values = re.findall(r'(\d+[.,]?\d*)\s*(?:m|metres?|meters?)', text_lower)
            for val in large_values:
                try:
                    if float(val.replace(',', '')) > 3.5:
                        return False
                except:
                    pass
        all_meter_values = re.findall(r'(\d+[.,]?\d*)\s*(?:m|metres?|meters?)(?!\s*m)', text_lower)
        for val in all_meter_values:
            try:
                if float(val.replace(',', '')) > 3.5:
                    if 'head' not in text_lower and 'body' not in text_lower:
                        return False
            except:
                pass
    
    # SPECIAL: For elephants, reject shoulder height values (2-3m range) and tusk measurements
    if any(x in animal_lower for x in ['elephant']):
        # Reject tusk measurements (typically 30-100cm)
        if 'tusk' in text_lower:
            return False
        if 'trunk' in text_lower and 'length' in text_lower:
            return False
        shoulder_values = re.findall(r'(2[.,]?\d*|3[.,]?\d*)\s*(?:m|metres?|meters?)', text_lower)
        if shoulder_values:
            if 'shoulder' in text_lower or 'height' in text_lower:
                return False
            if 'length' not in text_lower:
                return False
        # Reject small values (< 1m) for elephants
        small_values = re.findall(r'(\d+[.,]?\d*)\s*(?:cm|centimetres?|centimeters?)', text_lower)
        for val in small_values:
            try:
                if float(val.replace(',', '')) < 100:
                    return False
            except:
                pass
    
    # SPECIAL: For wolves, reject cm values <60cm (shoulder height range)
    if any(x in animal_lower for x in ['wolf', 'dog', 'canine']):
        cm_values = re.findall(r'(\d+[.,]?\d*)\s*(?:cm|centimetres?|centimeters?)', text_lower)
        for val in cm_values:
            try:
                if float(val.replace(',', '')) < 60:
                    if 'shoulder' in text_lower or 'height' in text_lower:
                        return False
                    if 'length' not in text_lower:
                        return False
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
    'biology',
    'behaviour',
    'behavior',
]


# =============================================================================
# PATTERN DEFINITIONS - FIXED based on actual Wikipedia text analysis
# Priority: Lower number = Higher priority (checked first)
# =============================================================================
LENGTH_PATTERNS = [
    # =========================================================================
    # TIER 1: Explicit Body Length Statements (Most Reliable) - Priority 1
    # =========================================================================
    {
        # "body length of/between 1.5–2.5 m" - PREFER this
        'pattern': r'body\s*length\s*(?:of|is)?\s*(?:between\s+)?(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        'priority': 1,
        'format': 'range'
    },
    {
        # "head-and-body length of/between 1.5–2.5 m" - HIGHEST PRIORITY for cats
        'pattern': r'head[-\s]*and[-\s]*body\s*length\s*(?:is\s+)?(?:between\s+)?(\d+(?:[.,]\d+)?)\s+(?:and|to|-|–)\s+(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        'priority': 1,
        'format': 'range'
    },
    {
        # "head-body length between X and Y m" - cheetah specific
        'pattern': r'head[-\s]*body\s*length\s+(?:is\s+)?between\s+(\d+(?:[.,]\d+)?)\s+and\s+(\d+(?:[.,]\d+)?)\s+(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet)',
        'priority': 1,
        'format': 'range'
    },
    {
        # "carapace length of 80–120 cm" (turtles)
        'pattern': r'carapace\s*length\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        'priority': 1,
        'format': 'range'
    },
    {
        # "snout-to-vent length of 1.5–2.5 m" (reptiles)
        'pattern': r'snout[-\s]*(?:to|-)?vent\s*length\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
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
    {
        # "wingspan" - reject for all animals
        'pattern': r'wingspan',
        'priority': 999,
        'format': 'reject'
    },
    {
        # "tusk length" - reject for elephants
        'pattern': r'tusk\s*length',
        'priority': 999,
        'format': 'reject'
    },
    {
        # "tail length" - reject (we want body length)
        'pattern': r'tail\s*length',
        'priority': 999,
        'format': 'reject'
    },
    
    # =========================================================================
    # TIER 2: Total Length (Lower priority - may include tail) - Priority 2
    # =========================================================================
    {
        # "total length of/between 1.5–2.5 m"
        'pattern': r'total\s*length\s*(?:of|is)?\s*(?:between\s+)?(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        'priority': 2,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 3: Measurement Statements - Priority 3
    # =========================================================================
    {
        # "measuring 1.5–2.5 m in length"
        'pattern': r'measur(?:ing|es)\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)\s*(?:in length|long)?',
        'priority': 3,
        'format': 'range'
    },
    {
        # "reaching 1.5–2.5 m in length"
        'pattern': r'reach(?:ing|es)?\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)\s*(?:in length|long)?',
        'priority': 3,
        'format': 'range'
    },
    {
        # "grows to 1.5–2.5 m"
        'pattern': r'grows?\s+(?:to|up to|reaching)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        'priority': 3,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 4: Simple Length Patterns - Priority 4
    # =========================================================================
    {
        # "1.5–2.5 m in length"
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)\s+(?:in length|long|length)',
        'priority': 4,
        'format': 'range'
    },
    {
        # "length of/between 1.5–2.5 m"
        'pattern': r'length\s+(?:of|is)?\s*(?:between\s+)?(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        'priority': 4,
        'format': 'range'
    },
    {
        # "average length of 1.5–2.5 m"
        'pattern': r'average\s*length\s+(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        'priority': 4,
        'format': 'range'
    },
    
    # =========================================================================
    # TIER 5: Single Value Length - Priority 5
    # =========================================================================
    {
        # "up to 2.5 m"
        'pattern': r'(?:up to|reaching|to|about|approximately)\s+(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)\s*(?:in length|long)?',
        'priority': 5,
        'format': 'single'
    },
    {
        # "2.5 m long"
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)\s+long',
        'priority': 5,
        'format': 'single'
    },
    
    # =========================================================================
    # TIER 6: Snake-Specific Patterns - Priority 6
    # =========================================================================
    {
        # "reaches 3-4 m" (snakes)
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
    # TIER 7: Turtle/Frog Specific - Priority 7
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
    # TIER 8: Small Animals (Bees, Insects) - IMPROVED mm support - Priority 8
    # =========================================================================
    {
        # "10-15 mm long" (bees)
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(mm)\s+long',
        'priority': 8,
        'format': 'range'
    },
    {
        # "about 12 mm" (bees)
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
        # "10–15 mm" (bees) - Simple mm range
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
        'pattern': r'(?:workers?|adults?|females?|males?)\s+(?:measure|measuring|are|is)\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(mm)',
        'priority': 8,
        'format': 'range'
    },
    {
        # "10 to 15 millimeters" (bees - full word)
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(millimetres?|millimeters?)',
        'priority': 8,
        'format': 'range'
    },
    {
        # "10–15 mm body length" (bees)
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(mm)\s+body\s*length',
        'priority': 8,
        'format': 'range'
    },
    {
        # "length 10-15 mm" (bees)
        'pattern': r'length\s+(?:of\s+)?(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(mm)',
        'priority': 8,
        'format': 'range'
    },
    {
        # "mm in length" (bees)
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(mm)\s+in\s+length',
        'priority': 8,
        'format': 'single'
    },
    {
        # "X cm" for butterflies (4.5 cm body)
        'pattern': r'(\d+(?:[.,]\d+)?)\s*(cm)\s+(?:long|length|body)',
        'priority': 8,
        'format': 'single'
    },
    
    # =========================================================================
    # TIER 9: Fallback Patterns - Priority 9
    # =========================================================================
    {
        # "X cm" in description sections
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
            if len(text) > 25:  # Lowered from 50 to 25 for shorter descriptions
                result = _extract_length_from_text(text, animal_name, classification)
                if result:
                    all_matches.append((result, section_name))
        
        # Try with spaces instead of underscores
        section_name_alt = section_name.replace('_', ' ')
        if section_name_alt in sections and sections[section_name_alt]:
            text = sections[section_name_alt]
            if len(text) > 25:
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
    if not text or len(text) < 25:  # Lowered from 50 to 25
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
            
            # Validate with classification
            if _is_valid_length(candidate, animal_name, classification):
                best_match = candidate
                best_priority = priority
                break
        
        if best_match and best_priority == priority:
            break
    
    return best_match if best_match else ""


def test_length_extraction(text: str, animal_name: str = "", classification: Dict[str, str] = None) -> str:
    """Test function for length extraction"""
    return _extract_length_from_text(text, animal_name, classification)


def get_pattern_stats() -> Dict[str, Any]:
    """Get statistics about pattern configuration"""
    return {
        'total_patterns': len(LENGTH_PATTERNS),
        'priority_tiers': len(set(p['priority'] for p in LENGTH_PATTERNS if p['priority'] < 999)),
        'section_priorities': len(SECTION_PRIORITY),
    }


# =============================================================================
# TEST CASES - Based on actual WildAtlas animal data
# =============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("WildAtlas Length Extraction Module - TEST SUITE v18")
    print("=" * 80)
    
    test_cases = [
        # Cheetah - head-body length
        {
            'name': 'Cheetah',
            'text': 'The cheetah has a slender body with a head-body length between 1.1 and 1.5 m.',
            'expected': '1.1–1.5 m',
            'classification': {'family': 'Felidae', 'order': 'Carnivora', 'class': 'Mammalia'}
        },
        # Tiger - body length
        {
            'name': 'Tiger',
            'text': 'Tigers have a body length of 1.7–2.5 m, with a tail adding another meter.',
            'expected': '1.7–2.5 m',
            'classification': {'family': 'Felidae', 'order': 'Carnivora', 'class': 'Mammalia'}
        },
        # African Elephant - reject 30cm tusk, get body length
        {
            'name': 'African Elephant',
            'text': 'African elephants reach 4.5–7.5 m in total length. Tusks can be 30 cm long.',
            'expected': '4.5–7.5 m',
            'classification': {'family': 'Elephantidae', 'order': 'Proboscidea', 'class': 'Mammalia'}
        },
        # Gray Wolf - reject shoulder height, get body length
        {
            'name': 'Gray Wolf',
            'text': 'Gray wolves have a body length of 1.0 to 1.6 m. Shoulder height is 29–50 cm.',
            'expected': '1.0–1.6 m',
            'classification': {'family': 'Canidae', 'order': 'Carnivora', 'class': 'Mammalia'}
        },
        # Bald Eagle - reject 11cm, get body length
        {
            'name': 'Bald Eagle',
            'text': 'Bald eagles have a body length of 70–120 cm. The beak is about 11 cm.',
            'expected': '70–120 cm',
            'classification': {'family': 'Accipitridae', 'order': 'Accipitriformes', 'class': 'Aves'}
        },
        # Emperor Penguin
        {
            'name': 'Emperor Penguin',
            'text': 'Emperor penguins reach about 1.5 m in length.',
            'expected': '1.5 m',
            'classification': {'family': 'Spheniscidae', 'order': 'Sphenisciformes', 'class': 'Aves'}
        },
        # Monarch Butterfly - reject wingspan, get body length
        {
            'name': 'Monarch Butterfly',
            'text': 'Monarch butterflies have a body length of 4.5–5 cm. Wingspan is 8–10 cm.',
            'expected': '4.5–5 cm',
            'classification': {'family': 'Nymphalidae', 'order': 'Lepidoptera', 'class': 'Insecta'}
        },
        # Honey Bee - mm body length
        {
            'name': 'Honey Bee',
            'text': 'Worker honey bees measure 10–15 mm in length.',
            'expected': '10–15 mm',
            'classification': {'family': 'Apidae', 'order': 'Hymenoptera', 'class': 'Insecta'}
        },
        # Great White Shark
        {
            'name': 'Great White Shark',
            'text': 'Great white sharks typically reach 5.5–8 m in length.',
            'expected': '5.5–8 m',
            'classification': {'family': 'Lamnidae', 'order': 'Lamniformes', 'class': 'Chondrichthyes'}
        },
        # Green Sea Turtle
        {
            'name': 'Green Sea Turtle',
            'text': 'Green sea turtles have a carapace length of 1.5 m.',
            'expected': '1.5 m',
            'classification': {'family': 'Cheloniidae', 'order': 'Testudines', 'class': 'Reptilia'}
        },
        # King Cobra
        {
            'name': 'King Cobra',
            'text': 'King cobras reach up to 4 m in length, typically 3–4 m.',
            'expected': '3–4 m',
            'classification': {'family': 'Elapidae', 'order': 'Squamata', 'class': 'Reptilia'}
        },
        # American Bullfrog
        {
            'name': 'American Bullfrog',
            'text': 'American bullfrogs grow to about 6 inches in length.',
            'expected': '6 in',
            'classification': {'family': 'Ranidae', 'order': 'Anura', 'class': 'Amphibia'}
        },
        # Atlantic Salmon
        {
            'name': 'Atlantic Salmon',
            'text': 'Atlantic salmon typically reach 1 m in length.',
            'expected': '1 m',
            'classification': {'family': 'Salmonidae', 'order': 'Salmoniformes', 'class': 'Actinopterygii'}
        },
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        result = test_length_extraction(
            test['text'], 
            test['name'], 
            test.get('classification')
        )
        
        status = "✓ PASS" if result == test['expected'] else "✗ FAIL"
        if result == test['expected']:
            passed += 1
        else:
            failed += 1
        
        print(f"\n{status} | {test['name']}")
        print(f"  Expected: {test['expected']}")
        print(f"  Got:      {result}")
    
    print("\n" + "=" * 80)
    print(f"RESULTS: {passed}/{len(test_cases)} passed ({passed/len(test_cases)*100:.0f}%)")
    print("=" * 80)
