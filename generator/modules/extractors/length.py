"""
Length Extraction Module - PRODUCTION v23 (ARCHITECTURE-COMPLIANT)
WildAtlas Project - https://github.com/Hunterthief/WildAtlas/
Inspired by facts.app but for normal animals

Based on analysis of 13 animal generation logs + project architecture review

CRITICAL FIXES:
┌─────────────────────┬──────────────────┬──────────────────┬─────────────────────────────────┐
│ Animal              │ Current (Logs)   │ Target           │ Issue                           │
├─────────────────────┼──────────────────┼──────────────────┼─────────────────────────────────┤
│ Tiger               │ 2.4-3.3m (Ninja) │ 1.7–2.5 m        │ Total length with tail          │
│ Cheetah             │ 60–80 cm (Wiki)  │ 1.1–1.5 m        │ Shoulder height confusion       │
│ African Elephant    │ 30 cm (Wiki)     │ 4.5–7.5 m        │ Tusk measurement extracted      │
│ Gray Wolf           │ EMPTY            │ 1.0–1.6 m        │ Only shoulder height in Wiki    │
│ Bald Eagle          │ 34–38 cm (Wiki)  │ 70–120 cm        │ Wrong measurement source        │
│ Monarch Butterfly   │ 1.2 m (Wiki)     │ 4.5–5 cm         │ Wingspan extracted              │
│ Honey Bee           │ EMPTY            │ 10–15 mm         │ No body length found            │
└─────────────────────┴──────────────────┴──────────────────┴─────────────────────────────────┘
"""
import re
from typing import Dict, Optional, List, Tuple, Any


# =============================================================================
# CONFIGURATION - Animal Type Length Expectations (for validation)
# All ranges in METERS for consistent comparison
# =============================================================================
ANIMAL_LENGTH_RANGES = {
    # Mammals (body length in meters, NOT including tail unless specified)
    'felidae': (0.6, 3.3),        # Cats (cheetah 1.1-1.5m body, tiger 1.7-2.5m body)
    'canidae': (0.6, 2.0),        # Dogs/Wolves body length (gray wolf 1.0-1.6m)
    'elephantidae': (4.0, 8.0),   # Elephants total length with trunk
    'ursidae': (1.0, 3.0),        # Bears
    'giraffidae': (3.5, 6.0),     # Giraffes
    'proboscidea': (4.0, 8.0),    # Elephants order
    
    # Birds (body length, NOT wingspan)
    'accipitridae': (0.3, 1.2),   # Eagles body length (bald eagle 70-120cm)
    'accipitriformes': (0.3, 1.3),
    'spheniscidae': (0.4, 1.3),   # Penguins (emperor ~100-120cm)
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
    'hymenoptera': (0.005, 0.04), # Bees (honey bee 10-15mm workers)
    'lepidoptera': (0.015, 0.08), # Butterflies body (monarch ~4.5-5cm)
    'apidae': (0.008, 0.025),     # Honey bees specifically
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
# VALIDATION FUNCTIONS
# =============================================================================
def _is_valid_length(value: str, animal_name: str = "", classification: Dict[str, str] = None) -> bool:
    """Validate length value makes biological sense"""
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
        
        if max_meters < 0.005 or max_meters > 50:
            return False
        
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
                if 'mammalia' in class_name: expected_range = (0.2, 10.0)
                elif 'aves' in class_name: expected_range = (0.10, 2.0)
                elif 'reptilia' in class_name: expected_range = (0.15, 8.0)
                elif 'amphibia' in class_name: expected_range = (0.03, 0.5)
                elif 'actinopterygii' in class_name or 'chondrichthyes' in class_name: expected_range = (0.1, 10.0)
                elif 'insecta' in class_name: expected_range = (0.003, 0.15)
            
            if expected_range:
                # Animal-specific validation
                if 'felidae' in family and max_meters > 3.5: return False
                if 'canidae' in family and (max_meters < 0.4 or max_meters > 2.5): return False
                if ('elephantidae' in family or 'proboscidea' in order) and (max_meters < 3.5 or max_meters > 9.0): return False
                if 'aves' in class_name and (max_meters < 0.15 or max_meters > 2.0): return False
                if ('lepidoptera' in order or 'nymphalidae' in family) and (max_meters > 0.12 or max_meters < 0.01): return False
                if 'insecta' in class_name:
                    if max_meters > 0.20: return False
                    if ('hymenoptera' in order or 'apidae' in family) and (max_meters < 0.003 or max_meters > 0.040): return False
                if 'cheloniidae' in family and (max_meters < 0.5 or max_meters > 1.5): return False
        
        return True
    except Exception:
        return False


def _has_length_context(text: str, animal_name: str = "", classification: Dict[str, str] = None) -> bool:
    """Check if text has length-related context - SMART shoulder/wingspan/tail rejection"""
    text_lower = text.lower()
    
    length_keywords = ['length', 'long', 'measures', 'reaching', 'grows', 'body length', 'total length', 'head-body', 'head and body', 'carapace', 'adult', 'mature', 'typically', 'average', 'usually', 'about', 'approximately', 'between']
    reject_keywords = ['temporal range', 'million years', 'ma ', 'mya', 'wingspan', 'wing span', 'wing length', 'wing spread', 'egg length', 'nest length', 'colony length', 'at the shoulder', 'shoulder height', 'shoulder to', 'distribution', 'range:', 'migrat', 'found from', 'occurs from', 'native to', 'habitat', 'geographic', 'tusk', 'trunk length', 'tail length', 'forearm', 'wing chord']
    
    # Check for shoulder context
    if 'shoulder' in text_lower and ('shoulder height' in text_lower or 'at the shoulder' in text_lower):
        return False
    if any(kw in text_lower for kw in ['distribution', 'range:', 'found from', 'occurs from', 'native to', 'geographic']):
        return False
    if any(kw in text_lower for kw in ['height', 'tall', 'stands', 'high']) and 'length' not in text_lower:
        return False
    
    animal_lower = animal_name.lower() if animal_name else ""
    
    # Butterfly/moth wingspan rejection
    if any(x in animal_lower for x in ['butterfly', 'moth']):
        if 'wingspan' in text_lower or 'wing span' in text_lower:
            return False
        if 'wing' in text_lower and 'body' not in text_lower:
            return False
    
    # Bird wingspan rejection
    if any(x in animal_lower for x in ['eagle', 'hawk', 'bird', 'penguin']):
        if 'wingspan' in text_lower or 'wing span' in text_lower or 'wing length' in text_lower:
            return False
    
    # Bee/insect wingspan rejection
    if any(x in animal_lower for x in ['bee', 'wasp', 'insect']):
        if 'wingspan' in text_lower or 'wing span' in text_lower:
            return False
    
    # Cat total length with tail rejection
    if any(x in animal_lower for x in ['tiger', 'cheetah', 'lion', 'cat', 'leopard', 'jaguar']):
        if 'total length' in text_lower and 'tail' in text_lower:
            return False
    
    # Elephant tusk/trunk rejection
    if any(x in animal_lower for x in ['elephant']):
        if 'tusk' in text_lower or ('trunk' in text_lower and 'length' in text_lower):
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
    'physical_characteristics', 'body_size', 'dimensions', 'measurements', 'biology', 'behaviour', 'behavior',
]


# =============================================================================
# PATTERN DEFINITIONS - Based on ACTUAL Wikipedia text analysis
# Priority: Lower number = Higher priority (checked first)
# =============================================================================
LENGTH_PATTERNS = [
    # TIER 1: Explicit Body Length (Priority 1)
    {'pattern': r'body\s*length\s*(?:of|is)?\s*(?:between\s+)?(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)', 'priority': 1, 'format': 'range'},
    {'pattern': r'head[-\s]*and[-\s]*body\s*length\s*(?:of|is)?\s*(?:between\s+)?(\d+(?:[.,]\d+)?)\s+(?:and|to|-|–)\s+(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)', 'priority': 1, 'format': 'range'},
    {'pattern': r'head[-\s]*body\s*length\s+(?:is\s+)?between\s+(\d+(?:[.,]\d+)?)\s+and\s+(\d+(?:[.,]\d+)?)\s+(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet)', 'priority': 1, 'format': 'range'},
    {'pattern': r'carapace\s*length\s*(?:of|is)?\s*(?:between\s+)?(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)', 'priority': 1, 'format': 'range'},
    {'pattern': r'snout[-\s]*(?:to|-)?vent\s*length\s*(?:of|is)?\s*(?:between\s+)?(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)', 'priority': 1, 'format': 'range'},
    # Reject patterns
    {'pattern': r'forearm\s*length', 'priority': 999, 'format': 'reject'},
    {'pattern': r'wing\s*length', 'priority': 999, 'format': 'reject'},
    {'pattern': r'wingspan', 'priority': 999, 'format': 'reject'},
    {'pattern': r'tusk\s*length', 'priority': 999, 'format': 'reject'},
    {'pattern': r'tail\s*length', 'priority': 999, 'format': 'reject'},
    
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
    print("WildAtlas Length Extraction Module - TEST SUITE v23")
    print("=" * 80)
    
    test_cases = [
        {'name': 'Cheetah', 'text': 'The cheetah has a head-body length between 1.1 and 1.5 m.', 'expected': '1.1–1.5 m', 'classification': {'family': 'Felidae', 'order': 'Carnivora', 'class': 'Mammalia'}},
        {'name': 'Tiger', 'text': 'Tigers have a body length of 1.7–2.5 m. Total length with tail is 2.4–3.3 m.', 'expected': '1.7–2.5 m', 'classification': {'family': 'Felidae', 'order': 'Carnivora', 'class': 'Mammalia'}},
        {'name': 'African Elephant', 'text': 'African elephants reach 4.5–7.5 m in total length including trunk.', 'expected': '4.5–7.5 m', 'classification': {'family': 'Elephantidae', 'order': 'Proboscidea', 'class': 'Mammalia'}},
        {'name': 'Gray Wolf', 'text': 'Gray wolves have a body length of 1.0 to 1.6 m. Shoulder height is 29–50 cm.', 'expected': '1.0–1.6 m', 'classification': {'family': 'Canidae', 'order': 'Carnivora', 'class': 'Mammalia'}},
        {'name': 'Bald Eagle', 'text': 'Bald eagles have a body length of 70–120 cm.', 'expected': '70–120 cm', 'classification': {'family': 'Accipitridae', 'order': 'Accipitriformes', 'class': 'Aves'}},
        {'name': 'Green Sea Turtle', 'text': 'Green sea turtles have a carapace length of 78–112 cm.', 'expected': '78–112 cm', 'classification': {'family': 'Cheloniidae', 'order': 'Testudines', 'class': 'Reptilia'}},
        {'name': 'Monarch Butterfly', 'text': 'Monarch butterflies have a body length of 4.5–5 cm. Wingspan is 8–10 cm.', 'expected': '4.5–5 cm', 'classification': {'family': 'Nymphalidae', 'order': 'Lepidoptera', 'class': 'Insecta'}},
        {'name': 'Honey Bee', 'text': 'Worker honey bees measure 10–15 mm in length.', 'expected': '10–15 mm', 'classification': {'family': 'Apidae', 'order': 'Hymenoptera', 'class': 'Insecta'}},
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
