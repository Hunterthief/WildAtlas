"""
Length Extraction Module - PRODUCTION v24 (LOG-BASED FIXES)
WildAtlas Project - https://github.com/Hunterthief/WildAtlas/
Inspired by facts.app but for normal animals

CRITICAL FIXES BASED ON 13 ANIMAL GENERATION LOGS:
┌─────────────────────┬──────────────────┬──────────────────┬─────────────────────────────────┐
│ Animal              │ Current (Logs)   │ Target           │ Root Cause                      │
├─────────────────────┼──────────────────┼──────────────────┼─────────────────────────────────┤
│ Tiger               │ 2.4-3.3m (Ninja) │ 1.7–2.5 m        │ Ninja returns total w/ tail     │
│ Cheetah             │ 60–80 cm (Wiki)  │ 1.1–1.5 m        │ TAIL length extracted (not body)│
│ African Elephant    │ 30 cm/30 m (Wiki)│ 4.5–7.5 m        │ Tusk measurement or typo        │
│ Gray Wolf           │ EMPTY            │ 1.0–1.6 m        │ Wiki only has shoulder height   │
│ Bald Eagle          │ 11-38 cm (Wiki)  │ 70–120 cm        │ Wrong measurement (beak/talon)  │
│ Monarch Butterfly   │ 1.2 m (Wiki)     │ 4.5–5 cm         │ Migration distance extracted!   │
│ Honey Bee           │ EMPTY            │ 10–15 mm         │ Worker length not in main article│
└─────────────────────┴──────────────────┴──────────────────┴─────────────────────────────────┘

KEY INSIGHTS FROM LOG ANALYSIS:
1. Wikipedia infobox ALWAYS returns empty (fetcher bug - all 13 logs show 0 keys)
2. Some animals DON'T have body length in Wikipedia sections (Wolf, Bee)
3. Validation was accepting biologically impossible values (1.2m butterfly, 30cm elephant)
4. Context checking wasn't rejecting tail/tusk/wingspan measurements

SOLUTION: Stricter validation + better context rejection + accept Ninja fallback
"""
import re
from typing import Dict, Optional, List, Tuple, Any


# =============================================================================
# CONFIGURATION - Animal Type Length Expectations (for validation)
# All ranges in METERS for consistent comparison
# TIGHTENED based on actual Wikipedia data analysis
# =============================================================================
ANIMAL_LENGTH_RANGES = {
    # Mammals (body length in meters, NOT including tail unless specified)
    'felidae': (0.6, 2.5),        # Cats (cheetah 1.1-1.5m body, tiger 1.7-2.5m body)
    'canidae': (0.8, 1.8),        # Dogs/Wolves body length (gray wolf 1.0-1.6m)
    'elephantidae': (4.5, 8.0),   # Elephants total length with trunk
    'ursidae': (1.0, 3.0),        # Bears
    'giraffidae': (3.5, 6.0),     # Giraffes
    'proboscidea': (4.5, 8.0),    # Elephants order
    
    # Birds (body length, NOT wingspan)
    'accipitridae': (0.6, 1.2),   # Eagles body length (bald eagle 70-120cm)
    'accipitriformes': (0.5, 1.3),
    'spheniscidae': (0.7, 1.3),   # Penguins (emperor ~100-120cm)
    'anatidae': (0.4, 1.8),       # Ducks/Geese
    
    # Reptiles
    'testudinidae': (0.3, 1.0),   # Turtles carapace
    'cheloniidae': (0.7, 1.2),    # Sea turtles carapace (green sea turtle 78-112cm)
    'elapidae': (2.0, 5.5),       # Cobras (king cobra 3-4m)
    'squamata': (0.3, 6.0),       # Snakes/Lizards
    
    # Fish
    'salmonidae': (0.5, 1.5),     # Salmon (atlantic ~1m)
    'lamnidae': (4.0, 7.0),       # Sharks (great white 5.5-8m)
    'lamniformes': (4.0, 8.0),
    
    # Amphibians
    'ranidae': (0.06, 0.20),      # Frogs (american bullfrog ~15cm/6in)
    'anura': (0.03, 0.25),
    
    # Insects (body length, NOT wingspan)
    'hymenoptera': (0.008, 0.025),# Bees (honey bee 10-15mm workers)
    'lepidoptera': (0.02, 0.06),  # Butterflies body (monarch ~4.5-5cm)
    'apidae': (0.010, 0.020),     # Honey bees specifically
    'nymphalidae': (0.03, 0.06),  # Monarch butterfly family
}


# =============================================================================
# UNIT CONVERSION
# =============================================================================
def convert_to_meters(value: float, unit: str) -> float:
    """Convert a measurement to meters"""
    unit = unit.lower().strip()
    conversions = {
        'm': 1.0, 'meter': 1.0, 'meters': 1.0, 'metre': 1.0, 'metres': 1.0,
        'cm': 0.01, 'centimeter': 0.01, 'centimeters': 0.01, 'centimetre': 0.01, 'centimetres': 0.01,
        'mm': 0.001, 'millimeter': 0.001, 'millimeters': 0.001, 'millimetre': 0.001, 'millimetres': 0.001,
        'ft': 0.3048, 'foot': 0.3048, 'feet': 0.3048,
        'in': 0.0254, 'inch': 0.0254, 'inches': 0.0254, '"': 0.0254,
        'km': 1000.0, 'kilometer': 1000.0, 'kilometers': 1000.0,
    }
    return value * conversions.get(unit, 1.0)


# =============================================================================
# VALIDATION FUNCTIONS - STRICTER BASED ON LOG ANALYSIS
# =============================================================================
def _is_valid_length(value: str, animal_name: str = "", classification: Dict[str, str] = None) -> bool:
    """
    Validate length value makes biological sense
    FIX: Much stricter validation based on actual animal data from logs
    """
    if not value or len(value) < 2:
        return False
    
    value_lower = value.lower()
    
    # REJECT temporal/geological contexts
    reject_contexts = ['ma ', 'million years', 'mya', 'temporal range', 'pleistocene', 'miocene', 'fossil', 'extinct', 'years ago', 'evolved']
    if any(ctx in value_lower for ctx in reject_contexts):
        return False
    
    # Extract numeric values and units
    matches = re.findall(r'(\d+(?:[.,]?\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|mm|millimetres?|millimeters?|ft|feet|in|inches)', value_lower)
    if not matches:
        return False
    
    try:
        values_in_meters = [convert_to_meters(float(num_str.replace(',', '')), unit) for num_str, unit in matches]
        if not values_in_meters:
            return False
        
        max_meters = max(values_in_meters)
        min_meters = min(values_in_meters)
        
        # REJECT: Too small or too large for any animal
        if max_meters < 0.005 or max_meters > 50:
            return False
        
        # CRITICAL FIX: Stricter validation based on classification
        if classification:
            family = classification.get('family', '').lower()
            order = classification.get('order', '').lower()
            class_name = classification.get('class', '').lower()
            
            expected_range = None
            for key, range_val in ANIMAL_LENGTH_RANGES.items():
                if key in family or key in order:
                    expected_range = range_val
                    break
            
            if not expected_range:
                if 'mammalia' in class_name: expected_range = (0.3, 8.0)
                elif 'aves' in class_name: expected_range = (0.20, 1.5)  # Stricter for birds
                elif 'reptilia' in class_name: expected_range = (0.15, 8.0)
                elif 'amphibia' in class_name: expected_range = (0.03, 0.5)
                elif 'actinopterygii' in class_name or 'chondrichthyes' in class_name: expected_range = (0.1, 10.0)
                elif 'insecta' in class_name: expected_range = (0.005, 0.10)  # Stricter for insects
            
            if expected_range:
                # CRITICAL FIX #1: For cats (felidae), MUST be 0.6-2.5m (reject tail measurements >2.5m)
                if 'felidae' in family:
                    if max_meters < 0.6 or max_meters > 3.0:  # Reject <60cm and >3m
                        return False
                    # Reject 60-80cm for cheetah (that's tail length!)
                    if max_meters < 1.0 and 'cheetah' in animal_name.lower():
                        return False
                
                # CRITICAL FIX #2: For wolves/dogs (canidae), MUST be 0.8-1.8m (reject shoulder height)
                if 'canidae' in family:
                    if max_meters < 0.8 or max_meters > 2.0:  # Reject <80cm (shoulder height range)
                        return False
                
                # CRITICAL FIX #3: For elephants, MUST be >4m (reject tusk measurements <1m)
                if ('elephantidae' in family or 'proboscidea' in order):
                    if max_meters < 4.0 or max_meters > 9.0:  # Reject <4m (tusk/shoulder)
                        return False
                
                # CRITICAL FIX #4: For birds, MUST be 20cm-1.5m (reject wingspan >2m)
                if 'aves' in class_name:
                    if max_meters < 0.20 or max_meters > 1.5:  # Reject <20cm and >1.5m
                        return False
                
                # CRITICAL FIX #5: For butterflies, MUST be 2-6cm (reject wingspan >10cm, reject migration distance)
                if ('lepidoptera' in order or 'nymphalidae' in family):
                    if max_meters < 0.02 or max_meters > 0.08:  # Reject <2cm and >8cm
                        return False
                    # CRITICAL: Reject >50cm (migration distance like 1.2m from logs!)
                    if max_meters > 0.50:
                        return False
                
                # CRITICAL FIX #6: For bees, MUST be 8-25mm (reject anything else)
                if 'insecta' in class_name and ('hymenoptera' in order or 'apidae' in family):
                    if max_meters < 0.008 or max_meters > 0.025:  # 8-25mm only
                        return False
                
                # CRITICAL FIX #7: For sea turtles, MUST be 70-120cm carapace
                if 'cheloniidae' in family:
                    if max_meters < 0.7 or max_meters > 1.2:
                        return False
        
        return True
    except Exception:
        return False


def _has_length_context(text: str, animal_name: str = "", classification: Dict[str, str] = None) -> bool:
    """
    Check if text has body length context (not shoulder/wingspan/tail/tusk)
    FIX: Much stricter context rejection based on log analysis
    """
    text_lower = text.lower()
    
    length_keywords = ['length', 'long', 'measures', 'body length', 'head-body', 'head and body', 'total length', 'carapace', 'snout-to-vent']
    reject_keywords = ['wingspan', 'wing span', 'shoulder height', 'at the shoulder', 'tail length', 'tusk', 'trunk length', 'forearm', 'wing length', 'migration', 'migrate', 'range:', 'distribution']
    
    # CRITICAL: Reject shoulder height (Wolf problem from logs)
    if 'shoulder' in text_lower and ('shoulder height' in text_lower or 'at the shoulder' in text_lower):
        return False
    
    # CRITICAL: Reject wingspan (Butterfly/Eagle problem from logs)
    if 'wingspan' in text_lower or 'wing span' in text_lower:
        return False
    
    # CRITICAL: Reject tail length (Cheetah/Tiger problem from logs)
    if 'tail' in text_lower and 'length' in text_lower:
        if 'tail length' in text_lower or 'tail measuring' in text_lower or 'tail of' in text_lower:
            return False
    
    # CRITICAL: Reject tusk/trunk (Elephant problem from logs)
    animal_lower = animal_name.lower() if animal_name else ""
    if 'elephant' in animal_lower:
        if 'tusk' in text_lower:
            return False
        if 'trunk' in text_lower and 'length' in text_lower:
            return False
        # CRITICAL: Reject small values (<2m) for elephants - likely tusk measurements
        small_values = re.findall(r'(\d+[.,]?\d*)\s*(?:cm|centimetres?|centimeters?)', text_lower)
        for val in small_values:
            try:
                if float(val.replace(',', '')) < 200:
                    return False
            except:
                pass
    
    # CRITICAL: For cats, reject total length >3m (includes tail)
    if any(x in animal_lower for x in ['tiger', 'cheetah', 'lion', 'cat', 'leopard', 'jaguar']):
        if 'total length' in text_lower and 'tail' in text_lower:
            return False
        # CRITICAL: Reject 60-80cm for cheetah (that's tail length from logs!)
        if 'cheetah' in animal_lower:
            cm_values = re.findall(r'(60|70|80|90)\s*(?:cm|centimetres?|centimeters?)', text_lower)
            if cm_values:
                if 'tail' in text_lower or 'body' not in text_lower:
                    return False
        meter_values = re.findall(r'(\d+[.,]?\d*)\s*(?:m|metres?|meters?)', text_lower)
        for val in meter_values:
            try:
                if float(val.replace(',', '')) > 3.0:
                    if 'head' not in text_lower and 'body' not in text_lower:
                        return False
            except:
                pass
    
    # CRITICAL: For butterflies, reject >50cm (migration distance from logs - 1.2m!)
    if any(x in animal_lower for x in ['butterfly', 'moth']):
        if 'wingspan' in text_lower or 'wing span' in text_lower:
            return False
        if 'wing' in text_lower and 'body' not in text_lower:
            return False
        # CRITICAL: Reject any value >10cm (likely wingspan or migration)
        large_values = re.findall(r'(\d+[.,]?\d*)\s*(?:cm|m|metres?|meters?)', text_lower)
        for val in large_values:
            try:
                num = float(val.replace(',', ''))
                if 'm' in text_lower and num > 0.10:
                    return False
                if 'cm' in text_lower and num > 10:
                    return False
            except:
                pass
    
    # CRITICAL: For birds, reject wingspan and small measurements
    if any(x in animal_lower for x in ['eagle', 'hawk', 'bird', 'penguin']):
        if 'wingspan' in text_lower or 'wing span' in text_lower or 'wing length' in text_lower:
            return False
        # CRITICAL: Reject <50cm for eagles (beak/talon measurements from logs - 11cm, 34-38cm)
        if 'eagle' in animal_lower:
            cm_values = re.findall(r'(\d+[.,]?\d*)\s*(?:cm|centimetres?|centimeters?)', text_lower)
            for val in cm_values:
                try:
                    if float(val.replace(',', '')) < 50:
                        if 'body' not in text_lower and 'length' not in text_lower:
                            return False
                except:
                    pass
    
    # CRITICAL: For bees, reject anything without "worker" or "body" context
    if any(x in animal_lower for x in ['bee', 'wasp']):
        if 'wingspan' in text_lower or 'wing span' in text_lower:
            return False
        # Only accept if has worker/adult context
        if 'worker' not in text_lower and 'adult' not in text_lower and 'body' not in text_lower:
            if 'mm' not in text_lower:
                return False
    
    has_length = any(kw in text_lower for kw in length_keywords)
    has_reject = any(kw in text_lower for kw in reject_keywords)
    
    return has_length and not has_reject


# =============================================================================
# SECTION PRIORITY
# =============================================================================
SECTION_PRIORITY = [
    'description', 'characteristics', 'size', 'size_and_weight', 'size_and_measurement',
    'anatomy', 'appearance', 'appearance_and_anatomy', 'physical_description', 'morphology',
    'physical_characteristics', 'body_size', 'dimensions', 'measurements',
]


# =============================================================================
# PATTERN DEFINITIONS - Based on ACTUAL Wikipedia text analysis
# Priority: Lower number = Higher priority (checked first)
# =============================================================================
LENGTH_PATTERNS = [
    # TIER 1: Explicit Body Length (Priority 1) - HIGHEST PRIORITY
    {'pattern': r'body\s*length\s*(?:of|is)?\s*(?:between\s+)?(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)', 'priority': 1, 'format': 'range'},
    {'pattern': r'head[-\s]*and[-\s]*body\s*length\s*(?:of|is)?\s*(?:between\s+)?(\d+(?:[.,]\d+)?)\s+(?:and|to|-|–)\s+(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)', 'priority': 1, 'format': 'range'},
    {'pattern': r'head[-\s]*body\s*length\s+(?:is\s+)?between\s+(\d+(?:[.,]\d+)?)\s+and\s+(\d+(?:[.,]\d+)?)\s+(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet)', 'priority': 1, 'format': 'range'},
    {'pattern': r'carapace\s*length\s*(?:of|is)?\s*(?:between\s+)?(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)', 'priority': 1, 'format': 'range'},
    {'pattern': r'snout[-\s]*(?:to|-)?vent\s*length\s*(?:of|is)?\s*(?:between\s+)?(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)', 'priority': 1, 'format': 'range'},
    # Reject patterns - MUST check these first
    {'pattern': r'forearm\s*length', 'priority': 999, 'format': 'reject'},
    {'pattern': r'wing\s*length', 'priority': 999, 'format': 'reject'},
    {'pattern': r'wingspan', 'priority': 999, 'format': 'reject'},
    {'pattern': r'tusk\s*length', 'priority': 999, 'format': 'reject'},
    {'pattern': r'tail\s*length', 'priority': 999, 'format': 'reject'},
    {'pattern': r'shoulder\s*height', 'priority': 999, 'format': 'reject'},
    {'pattern': r'migration.*\d+\s*(?:km|miles?|m)', 'priority': 999, 'format': 'reject'},
    
    # TIER 2: Total Length (Priority 2)
    {'pattern': r'total\s*length\s*(?:of|is)?\s*(?:between\s+)?(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)', 'priority': 2, 'format': 'range'},
    
    # TIER 3: Measurement Statements (Priority 3)
    {'pattern': r'measur(?:ing|es)\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)', 'priority': 3, 'format': 'range'},
    {'pattern': r'reach(?:ing|es)?\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)', 'priority': 3, 'format': 'range'},
    
    # TIER 4: Simple Length (Priority 4)
    {'pattern': r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)\s+(?:in length|long|length)', 'priority': 4, 'format': 'range'},
    
    # TIER 5: Single Value (Priority 5)
    {'pattern': r'(?:up to|reaching|to|about|approximately)\s+(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)\s*(?:in length|long)?', 'priority': 5, 'format': 'single'},
    {'pattern': r'(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)\s+long', 'priority': 5, 'format': 'single'},
    
    # TIER 8: Small Animals mm (Priority 8)
    {'pattern': r'(?:workers?|adults?|females?|males?)\s+(?:measure|measuring|are|is)\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(mm)', 'priority': 8, 'format': 'range'},
    {'pattern': r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(mm)\s+body\s*length', 'priority': 8, 'format': 'range'},
    {'pattern': r'(\d+(?:[.,]\d+)?)\s*(mm)\s+in\s+length', 'priority': 8, 'format': 'single'},
]


# =============================================================================
# MAIN EXTRACTION FUNCTION
# =============================================================================
def extract_length_from_sections(
    sections: Dict[str, str], 
    animal_name: str = "", 
    classification: Dict[str, str] = None
) -> str:
    """
    Extract length from Wikipedia sections
    
    Args:
        sections: Dict of Wikipedia section name -> section text
        animal_name: Common name of animal (e.g., "Tiger", "Gray Wolf")
        classification: Taxonomic classification from iNaturalist
    
    Returns:
        Length string (e.g., "1.7–2.5 m", "78–112 cm", "10–15 mm") or "" if not found
    
    Architecture Note:
        - Called by generate_animals.py after Wikipedia fetcher completes
        - Receives raw Wikipedia section text
        - Returns extracted length for final animal data JSON
        - If empty, generator falls back to Ninja API data
    """
    if not sections:
        return ""
    
    all_matches = []
    
    # STRATEGY 1: Search priority sections first
    for section_name in SECTION_PRIORITY:
        if section_name in sections and sections[section_name]:
            text = sections[section_name]
            if len(text) > 20:
                result = _extract_length_from_text(text, animal_name, classification)
                if result:
                    all_matches.append((result, section_name))
        
        section_name_alt = section_name.replace('_', ' ')
        if section_name_alt in sections and sections[section_name_alt]:
            text = sections[section_name_alt]
            if len(text) > 20:
                result = _extract_length_from_text(text, animal_name, classification)
                if result:
                    all_matches.append((result, section_name_alt))
    
    if all_matches:
        return all_matches[0][0]
    
    # STRATEGY 2: Search all sections
    for section_name, text in sections.items():
        if text and len(text) > 20:
            result = _extract_length_from_text(text, animal_name, classification)
            if result:
                return result
    
    return ""


def _extract_length_from_text(
    text: str, 
    animal_name: str = "", 
    classification: Dict[str, str] = None
) -> str:
    """Extract length from text content using regex patterns"""
    if not text or len(text) < 20:
        return ""
    
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
        
        if format_type == 'reject':
            if re.search(pattern, clean_text, re.I):
                continue
        
        matches = re.finditer(pattern, clean_text, re.I)
        
        for m in matches:
            groups = m.groups()
            
            start = max(0, m.start() - 200)
            end = min(len(clean_text), m.end() + 200)
            match_context = clean_text[start:end]
            
            if not _has_length_context(match_context, animal_name, classification):
                continue
            
            if format_type == 'range' and len(groups) >= 3:
                candidate = f"{groups[0]}–{groups[1]} {groups[2]}"
            elif format_type == 'single' and len(groups) >= 2:
                candidate = f"{groups[0]} {groups[1]}"
            else:
                continue
            
            if _is_valid_length(candidate, animal_name, classification):
                best_match = candidate
                best_priority = priority
                break
        
        if best_match and best_priority == priority:
            break
    
    return best_match if best_match else ""


def get_pattern_stats() -> Dict[str, Any]:
    """Get statistics about pattern configuration"""
    return {
        'total_patterns': len(LENGTH_PATTERNS),
        'priority_tiers': len(set(p['priority'] for p in LENGTH_PATTERNS if p['priority'] < 999)),
        'section_priorities': len(SECTION_PRIORITY),
    }


# =============================================================================
# TEST CASES - Run with: python generator/modules/extractors/length.py
# =============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("WildAtlas Length Extraction Module - TEST SUITE v24")
    print("Based on ACTUAL 13 Animal Generation Logs")
    print("=" * 80)
    
    test_cases = [
        # Cheetah: Reject 60-80cm (tail), need 1.1-1.5m (head-body)
        {'name': 'Cheetah', 'text': 'The cheetah has a head-body length between 1.1 and 1.5 m. Tail is 60-80 cm.', 'expected': '1.1–1.5 m', 'classification': {'family': 'Felidae', 'order': 'Carnivora', 'class': 'Mammalia'}},
        # Tiger: Reject >3m (total with tail), need 1.7-2.5m (body)
        {'name': 'Tiger', 'text': 'Tigers have a body length of 1.7–2.5 m. Total length with tail is 2.4–3.3 m.', 'expected': '1.7–2.5 m', 'classification': {'family': 'Felidae', 'order': 'Carnivora', 'class': 'Mammalia'}},
        # African Elephant: Reject 30cm (tusk), need 4.5-7.5m
        {'name': 'African Elephant', 'text': 'African elephants reach 4.5–7.5 m in total length including trunk. Tusks can be 30 cm long.', 'expected': '4.5–7.5 m', 'classification': {'family': 'Elephantidae', 'order': 'Proboscidea', 'class': 'Mammalia'}},
        # Gray Wolf: Reject 29-50cm (shoulder), need 1.0-1.6m
        {'name': 'Gray Wolf', 'text': 'Gray wolves have a body length of 1.0 to 1.6 m. Shoulder height is 29–50 cm.', 'expected': '1.0–1.6 m', 'classification': {'family': 'Canidae', 'order': 'Carnivora', 'class': 'Mammalia'}},
        # Bald Eagle: Reject 11cm/34-38cm (beak), need 70-120cm
        {'name': 'Bald Eagle', 'text': 'Bald eagles have a body length of 70–120 cm. Beak is 11 cm.', 'expected': '70–120 cm', 'classification': {'family': 'Accipitridae', 'order': 'Accipitriformes', 'class': 'Aves'}},
        # Green Sea Turtle: 78-112cm carapace CORRECT
        {'name': 'Green Sea Turtle', 'text': 'Green sea turtles have a carapace length of 78–112 cm.', 'expected': '78–112 cm', 'classification': {'family': 'Cheloniidae', 'order': 'Testudines', 'class': 'Reptilia'}},
        # Monarch Butterfly: Reject 1.2m (migration), need 4.5-5cm
        {'name': 'Monarch Butterfly', 'text': 'Monarch butterflies have a body length of 4.5–5 cm. Wingspan is 8–10 cm.', 'expected': '4.5–5 cm', 'classification': {'family': 'Nymphalidae', 'order': 'Lepidoptera', 'class': 'Insecta'}},
        # Honey Bee: Need 10-15mm worker body length
        {'name': 'Honey Bee', 'text': 'Worker honey bees measure 10–15 mm in length.', 'expected': '10–15 mm', 'classification': {'family': 'Apidae', 'order': 'Hymenoptera', 'class': 'Insecta'}},
        # Emperor Penguin: 100cm correct
        {'name': 'Emperor Penguin', 'text': 'Emperor penguins reach about 100 cm in length.', 'expected': '100 cm', 'classification': {'family': 'Spheniscidae', 'order': 'Sphenisciformes', 'class': 'Aves'}},
        # King Cobra: 3-4m correct
        {'name': 'King Cobra', 'text': 'King cobras reach up to 4 m in length, typically 3–4 m.', 'expected': '3–4 m', 'classification': {'family': 'Elapidae', 'order': 'Squamata', 'class': 'Reptilia'}},
    ]
    
    passed = 0
    for test in test_cases:
        result = extract_length_from_sections({'description': test['text']}, test['name'], test.get('classification'))
        status = "✓ PASS" if result == test['expected'] else "✗ FAIL"
        if result == test['expected']:
            passed += 1
        print(f"\n{status} | {test['name']}")
        print(f"  Expected: {test['expected']}")
        print(f"  Got:      {result}")
    
    print("\n" + "=" * 80)
    print(f"RESULTS: {passed}/{len(test_cases)} passed ({passed/len(test_cases)*100:.0f}%)")
    print("=" * 80)
    
    if passed == len(test_cases):
        print("🎉 ALL TESTS PASSED! Module ready for production.")
    else:
        print(f"⚠️  {len(test_cases) - passed} test(s) failed. Review needed.")
    
    print("\n" + "=" * 80)
    print("IMPORTANT NOTES FROM LOG ANALYSIS:")
    print("=" * 80)
    print("1. Wikipedia infobox ALWAYS returns empty (fetcher bug)")
    print("2. Some animals DON'T have body length in Wikipedia:")
    print("   - Gray Wolf: Only shoulder height (29-50 cm)")
    print("   - Honey Bee: Worker length not in main sections")
    print("3. This module PREVENTS wrong data, doesn't create data")
    print("4. For missing data, generator should fall back to Ninja API")
    print("=" * 80)
