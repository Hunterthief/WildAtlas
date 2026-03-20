"""
Length Extraction Module - PRODUCTION v22 (ALL FREE SOLUTIONS)
WildAtlas Project - https://github.com/Hunterthief/WildAtlas/
Inspired by facts.app but for normal animals

FREE PROFESSIONAL SOLUTIONS INTEGRATED:
┌────────────────────────┬──────────────┬──────────┬─────────────────────────────────┐
│ Solution               │ Cost         │ Accuracy │ Implementation Status           │
├────────────────────────┼──────────────┼──────────┼─────────────────────────────────┤
│ Wikidata SPARQL        │ FREE         │ ⭐⭐⭐⭐⭐   │ ✅ IMPLEMENTED                   │
│ DBpedia SPARQL         │ FREE         │ ⭐⭐⭐⭐    │ ✅ IMPLEMENTED                   │
│ spaCy NER              │ FREE         │ ⭐⭐⭐⭐    │ ✅ IMPLEMENTED (optional)        │
│ Regex Patterns         │ FREE         │ ⭐⭐⭐     │ ✅ IMPLEMENTED (fallback)        │
├────────────────────────┼──────────────┼──────────┼─────────────────────────────────┤
│ GROBID-quantities      │ FREE (Docker)│ ⭐⭐⭐⭐⭐   │ ⏸️ Available but requires Docker │
│ LLM Extraction         │ PAID         │ ⭐⭐⭐⭐⭐   │ ❌ Not included (costs money)    │
└────────────────────────┴──────────────┴──────────┴─────────────────────────────────┘

Based on analysis of 13 animal generation logs + professional NLP research
"""
import re
import json
from typing import Dict, Optional, List, Tuple, Any
from enum import Enum
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import quote


# =============================================================================
# CONFIGURATION - Animal Type Length Expectations (for validation)
# All ranges in METERS for consistent comparison
# =============================================================================
ANIMAL_LENGTH_RANGES = {
    # Mammals (body length in meters, NOT including tail unless specified)
    'felidae': (0.6, 3.3),
    'canidae': (0.6, 2.0),
    'elephantidae': (4.0, 8.0),
    'ursidae': (1.0, 3.0),
    'giraffidae': (3.5, 6.0),
    'proboscidea': (4.0, 8.0),
    
    # Birds (body length, NOT wingspan)
    'accipitridae': (0.3, 1.2),
    'accipitriformes': (0.3, 1.3),
    'spheniscidae': (0.4, 1.3),
    'anatidae': (0.4, 1.8),
    
    # Reptiles
    'testudinidae': (0.3, 1.0),
    'cheloniidae': (0.7, 1.2),
    'elapidae': (2.0, 5.5),
    'squamata': (0.3, 6.0),
    
    # Fish
    'salmonidae': (0.5, 1.5),
    'lamnidae': (4.0, 7.0),
    'lamniformes': (4.0, 8.0),
    
    # Amphibians
    'ranidae': (0.06, 0.20),
    'anura': (0.03, 0.25),
    
    # Insects (body length, NOT wingspan)
    'hymenoptera': (0.005, 0.04),
    'lepidoptera': (0.015, 0.08),
    'apidae': (0.008, 0.025),
    'nymphalidae': (0.03, 0.06),
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


def _has_length_context(text: str, animal_name: str = "") -> bool:
    """Check if text has length-related context"""
    text_lower = text.lower()
    
    length_keywords = ['length', 'long', 'measures', 'reaching', 'grows', 'body length', 'total length', 'head-body', 'head and body', 'carapace', 'adult', 'mature', 'typically', 'average', 'usually', 'about', 'approximately', 'between']
    reject_keywords = ['temporal range', 'million years', 'ma ', 'mya', 'wingspan', 'wing span', 'wing length', 'wing spread', 'egg length', 'nest length', 'colony length', 'at the shoulder', 'shoulder height', 'shoulder to', 'distribution', 'range:', 'migrat', 'found from', 'occurs from', 'native to', 'habitat', 'geographic', 'tusk', 'trunk length', 'tail length', 'forearm', 'wing chord']
    
    if 'shoulder' in text_lower and ('shoulder height' in text_lower or 'at the shoulder' in text_lower):
        return False
    if any(kw in text_lower for kw in ['distribution', 'range:', 'found from', 'occurs from', 'native to', 'geographic']):
        return False
    if any(kw in text_lower for kw in ['height', 'tall', 'stands', 'high']) and 'length' not in text_lower:
        return False
    
    animal_lower = animal_name.lower() if animal_name else ""
    if any(x in animal_lower for x in ['butterfly', 'moth']) and ('wingspan' in text_lower or 'wing span' in text_lower):
        return False
    if any(x in animal_lower for x in ['butterfly', 'moth']) and 'wing' in text_lower and 'body' not in text_lower:
        return False
    if any(x in animal_lower for x in ['eagle', 'hawk', 'bird', 'penguin']) and ('wingspan' in text_lower or 'wing span' in text_lower or 'wing length' in text_lower):
        return False
    if any(x in animal_lower for x in ['bee', 'wasp', 'insect']) and ('wingspan' in text_lower or 'wing span' in text_lower):
        return False
    if any(x in animal_lower for x in ['tiger', 'cheetah', 'lion', 'cat', 'leopard', 'jaguar']) and 'total length' in text_lower and 'tail' in text_lower:
        return False
    if any(x in animal_lower for x in ['elephant']) and ('tusk' in text_lower or ('trunk' in text_lower and 'length' in text_lower)):
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
# PATTERN DEFINITIONS
# =============================================================================
LENGTH_PATTERNS = [
    {'pattern': r'body\s*length\s*(?:of|is)?\s*(?:between\s+)?(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)', 'priority': 1, 'format': 'range'},
    {'pattern': r'head[-\s]*and[-\s]*body\s*length\s*(?:of|is)?\s*(?:between\s+)?(\d+(?:[.,]\d+)?)\s+(?:and|to|-|–)\s+(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)', 'priority': 1, 'format': 'range'},
    {'pattern': r'head[-\s]*body\s*length\s+(?:is\s+)?between\s+(\d+(?:[.,]\d+)?)\s+and\s+(\d+(?:[.,]\d+)?)\s+(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet)', 'priority': 1, 'format': 'range'},
    {'pattern': r'carapace\s*length\s*(?:of|is)?\s*(?:between\s+)?(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)', 'priority': 1, 'format': 'range'},
    {'pattern': r'forearm\s*length', 'priority': 999, 'format': 'reject'},
    {'pattern': r'wing\s*length', 'priority': 999, 'format': 'reject'},
    {'pattern': r'wingspan', 'priority': 999, 'format': 'reject'},
    {'pattern': r'tusk\s*length', 'priority': 999, 'format': 'reject'},
    {'pattern': r'tail\s*length', 'priority': 999, 'format': 'reject'},
    {'pattern': r'total\s*length\s*(?:of|is)?\s*(?:between\s+)?(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)', 'priority': 2, 'format': 'range'},
    {'pattern': r'measur(?:ing|es)\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)', 'priority': 3, 'format': 'range'},
    {'pattern': r'reach(?:ing|es)?\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)', 'priority': 3, 'format': 'range'},
    {'pattern': r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)\s+(?:in length|long|length)', 'priority': 4, 'format': 'range'},
    {'pattern': r'(?:up to|reaching|to|about|approximately)\s+(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)\s*(?:in length|long)?', 'priority': 5, 'format': 'single'},
    {'pattern': r'(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)\s+long', 'priority': 5, 'format': 'single'},
    {'pattern': r'(?:workers?|adults?|females?|males?)\s+(?:measure|measuring|are|is)\s+(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(mm)', 'priority': 8, 'format': 'range'},
    {'pattern': r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(mm)\s+body\s*length', 'priority': 8, 'format': 'range'},
    {'pattern': r'(\d+(?:[.,]\d+)?)\s*(mm)\s+in\s+length', 'priority': 8, 'format': 'single'},
]


# =============================================================================
# EXTRACTION METHOD ENUM
# =============================================================================
class ExtractionMethod(Enum):
    WIKIDATA = "wikidata_sparql"
    DBPEDIA = "dbpedia_sparql"
    SPACY_NER = "spacy_ner"
    REGEX = "regex_patterns"


# =============================================================================
# FREE PROFESSIONAL SOLUTION #1: WIKIDATA SPARQL
# =============================================================================
def try_wikidata_query(animal_name: str, scientific_name: str = "", classification: Dict[str, str] = None) -> Optional[str]:
    """
    Query Wikidata for animal length using SPARQL
    FREE: https://query.wikidata.org/
    
    Properties checked:
    - P2052 (speed) - not length
    - P2048 (height) - sometimes used
    - P2050 (length) - main length property
    - P2051 (width)
    - Custom body length properties
    
    Returns: Length string or None
    """
    try:
        # First, get the QID for the animal
        qid = None
        
        # Try to get QID from scientific name first (more accurate)
        if scientific_name:
            search_query = f"""
            SELECT ?item WHERE {{
              ?item wdt:P31 wd:Q729;
                    wdt:P225 "{scientific_name}"@en.
            }} LIMIT 1
            """
            url = f"https://query.wikidata.org/sparql?query={quote(search_query)}&format=json"
            req = Request(url, headers={'User-Agent': 'WildAtlas/1.0'})
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                if data.get('results', {}).get('bindings'):
                    qid = data['results']['bindings'][0]['item']['value'].split('/')[-1]
        
        # If no QID from scientific name, try common name
        if not qid and animal_name:
            search_query = f"""
            SELECT ?item WHERE {{
              ?item wdt:P31 wd:Q729;
                    rdfs:label "{animal_name}"@en.
            }} LIMIT 1
            """
            url = f"https://query.wikidata.org/sparql?query={quote(search_query)}&format=json"
            req = Request(url, headers={'User-Agent': 'WildAtlas/1.0'})
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                if data.get('results', {}).get('bindings'):
                    qid = data['results']['bindings'][0]['item']['value'].split('/')[-1]
        
        if not qid:
            return None
        
        # Now query for length properties
        length_query = f"""
        SELECT ?length ?lengthUnit ?prop WHERE {{
          wd:{qid} ?prop ?length .
          OPTIONAL {{ ?length wikibase:unit ?lengthUnit . }}
          FILTER(?prop IN (wdt:P2050, wdt:P2048, wdt:P2051))
        }} LIMIT 5
        """
        url = f"https://query.wikidata.org/sparql?query={quote(length_query)}&format=json"
        req = Request(url, headers={'User-Agent': 'WildAtlas/1.0'})
        
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            bindings = data.get('results', {}).get('bindings', [])
            
            for binding in bindings:
                length_val = binding.get('length', {}).get('value', '')
                if length_val:
                    # Try to parse and validate
                    length_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(m|cm|mm|ft|in)?', str(length_val), re.I)
                    if length_match:
                        candidate = f"{length_match.group(1)} {length_match.group(2) or 'm'}"
                        if _is_valid_length(candidate, animal_name, classification):
                            return candidate
            
            return None
            
    except (URLError, HTTPError, json.JSONDecodeError, Exception) as e:
        return None


# =============================================================================
# FREE PROFESSIONAL SOLUTION #2: DBPEDIA SPARQL
# =============================================================================
def try_dbpedia_extraction(animal_name: str, scientific_name: str = "", classification: Dict[str, str] = None) -> Optional[str]:
    """
    Extract length from DBpedia using SPARQL
    FREE: http://dbpedia.org/sparql
    
    DBpedia extracts structured Wikipedia infobox data.
    
    Returns: Length string or None
    """
    try:
        # Build resource URI from animal name
        resource_name = animal_name.replace(' ', '_')
        
        # Query DBpedia for length properties
        query = f"""
        PREFIX dbp: <http://dbpedia.org/property/>
        PREFIX dbo: <http://dbpedia.org/ontology/>
        
        SELECT ?length WHERE {{
          <http://dbpedia.org/resource/{resource_name}> dbo:length ?length .
        }} LIMIT 1
        """
        
        url = f"http://dbpedia.org/sparql?query={quote(query)}&format=json"
        req = Request(url, headers={'User-Agent': 'WildAtlas/1.0', 'Accept': 'application/json'})
        
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            bindings = data.get('results', {}).get('bindings', [])
            
            for binding in bindings:
                length_val = binding.get('length', {}).get('value', '')
                if length_val:
                    # Parse length value (DBpedia returns typed literals)
                    length_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(m|cm|mm|ft|in)?', str(length_val), re.I)
                    if length_match:
                        candidate = f"{length_match.group(1)} {length_match.group(2) or 'm'}"
                        if _is_valid_length(candidate, animal_name, classification):
                            return candidate
            
            return None
            
    except (URLError, HTTPError, json.JSONDecodeError, Exception) as e:
        return None


# =============================================================================
# FREE PROFESSIONAL SOLUTION #3: SPACY NER (Optional)
# =============================================================================
def try_spacy_ner(text: str, animal_name: str = "", classification: Dict[str, str] = None) -> Optional[str]:
    """
    Extract measurements using spaCy NER
    FREE: https://spacy.io/
    
    Install: pip install spacy
    Model: python -m spacy download en_core_web_sm
    
    Returns: Length string or None
    """
    try:
        # Check if spaCy is available
        import spacy
        
        # Load model (cached after first load)
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Model not installed, skip spaCy
            return None
        
        doc = nlp(text)
        
        # Look for CARDINAL + UNIT patterns
        for ent in doc.ents:
            if ent.label_ in ['CARDINAL', 'QUANTITY']:
                # Check next token for unit
                for token in ent.doc[ent.end:ent.end + 3]:
                    if token.text.lower() in ['m', 'cm', 'mm', 'meters', 'centimeters', 'millimeters', 'feet', 'inches']:
                        candidate = f"{ent.text} {token.text.lower()}"
                        if _is_valid_length(candidate, animal_name, classification):
                            return candidate
        
        # Also check for patterns like "X meters long"
        for token in doc:
            if token.text.lower() in ['long', 'length']:
                # Look back for number + unit
                for i in range(max(0, token.i - 5), token.i):
                    if doc[i].text.lower() in ['m', 'cm', 'mm', 'meters', 'centimeters', 'millimeters']:
                        if i > 0 and doc[i-1].like_num:
                            candidate = f"{doc[i-1].text} {doc[i].text.lower()}"
                            if _is_valid_length(candidate, animal_name, classification):
                                return candidate
        
        return None
        
    except ImportError:
        # spaCy not installed
        return None
    except Exception as e:
        return None


# =============================================================================
# REGEX PATTERNS (Fallback)
# =============================================================================
def _extract_length_from_text(text: str, animal_name: str = "", classification: Dict[str, str] = None) -> str:
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
            
            if not _has_length_context(match_context, animal_name):
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


# =============================================================================
# MAIN EXTRACTION FUNCTION - HYBRID FREE APPROACH
# =============================================================================
def extract_length_from_sections(
    sections: Dict[str, str], 
    animal_name: str = "", 
    classification: Dict[str, str] = None,
    scientific_name: str = ""
) -> Tuple[str, ExtractionMethod]:
    """
    Extract length using ALL FREE professional approaches
    
    Priority order:
    1. Wikidata SPARQL (FREE, structured knowledge graph) ⭐⭐⭐⭐⭐
    2. DBpedia SPARQL (FREE, Wikipedia structured data) ⭐⭐⭐⭐
    3. spaCy NER (FREE, quantity recognition) ⭐⭐⭐⭐
    4. Regex patterns (FREE, fast fallback) ⭐⭐⭐
    
    Returns: (length_string, extraction_method)
    """
    if not sections:
        return "", ExtractionMethod.REGEX
    
    # STRATEGY 1: Wikidata SPARQL (FREE)
    wikidata_result = try_wikidata_query(animal_name, scientific_name, classification)
    if wikidata_result:
        return wikidata_result, ExtractionMethod.WIKIDATA
    
    # STRATEGY 2: DBpedia SPARQL (FREE)
    dbpedia_result = try_dbpedia_extraction(animal_name, scientific_name, classification)
    if dbpedia_result:
        return dbpedia_result, ExtractionMethod.DBPEDIA
    
    # STRATEGY 3: spaCy NER (FREE, optional)
    all_text = " ".join(sections.values())
    spacy_result = try_spacy_ner(all_text, animal_name, classification)
    if spacy_result:
        return spacy_result, ExtractionMethod.SPACY_NER
    
    # STRATEGY 4: Regex patterns (FREE, working fallback)
    all_matches = []
    
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
        return all_matches[0][0], ExtractionMethod.REGEX
    
    # Search all sections
    for section_name, text in sections.items():
        if text and len(text) > 20:
            result = _extract_length_from_text(text, animal_name, classification)
            if result:
                return result, ExtractionMethod.REGEX
    
    return "", ExtractionMethod.REGEX


def test_length_extraction(text: str, animal_name: str = "", classification: Dict[str, str] = None) -> str:
    """Test function for length extraction"""
    result, method = extract_length_from_sections(
        {'description': text}, 
        animal_name, 
        classification
    )
    return result


def get_pattern_stats() -> Dict[str, Any]:
    """Get statistics about pattern configuration"""
    return {
        'total_patterns': len(LENGTH_PATTERNS),
        'priority_tiers': len(set(p['priority'] for p in LENGTH_PATTERNS if p['priority'] < 999)),
        'section_priorities': len(SECTION_PRIORITY),
        'extraction_methods': [m.value for m in ExtractionMethod],
        'free_solutions': ['Wikidata SPARQL', 'DBpedia SPARQL', 'spaCy NER', 'Regex Patterns'],
    }


# =============================================================================
# TEST CASES - Based on 13 Animal Generation Logs
# =============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("WildAtlas Length Extraction Module - TEST SUITE v22 (ALL FREE)")
    print("FREE Solutions: Wikidata, DBpedia, spaCy, Regex")
    print("=" * 80)
    
    test_cases = [
        {'name': 'Cheetah', 'text': 'The cheetah has a head-body length between 1.1 and 1.5 m.', 'expected': '1.1–1.5 m', 'classification': {'family': 'Felidae', 'order': 'Carnivora', 'class': 'Mammalia'}},
        {'name': 'Tiger', 'text': 'Tigers have a body length of 1.7–2.5 m. Total length with tail is 2.4–3.3 m.', 'expected': '1.7–2.5 m', 'classification': {'family': 'Felidae', 'order': 'Carnivora', 'class': 'Mammalia'}},
        {'name': 'African Elephant', 'text': 'African elephants reach 4.5–7.5 m in total length including trunk.', 'expected': '4.5–7.5 m', 'classification': {'family': 'Elephantidae', 'order': 'Proboscidea', 'class': 'Mammalia'}},
        {'name': 'Gray Wolf', 'text': 'Gray wolves have a body length of 1.0 to 1.6 m. Shoulder height is 29–50 cm.', 'expected': '1.0–1.6 m', 'classification': {'family': 'Canidae', 'order': 'Carnivora', 'class': 'Mammalia'}},
        {'name': 'Bald Eagle', 'text': 'Bald eagles have a body length of 70–120 cm.', 'expected': '70–120 cm', 'classification': {'family': 'Accipitridae', 'order': 'Accipitriformes', 'class': 'Aves'}},
        {'name': 'Emperor Penguin', 'text': 'Emperor penguins reach about 100 cm in length.', 'expected': '100 cm', 'classification': {'family': 'Spheniscidae', 'order': 'Sphenisciformes', 'class': 'Aves'}},
        {'name': 'Green Sea Turtle', 'text': 'Green sea turtles have a carapace length of 78–112 cm.', 'expected': '78–112 cm', 'classification': {'family': 'Cheloniidae', 'order': 'Testudines', 'class': 'Reptilia'}},
        {'name': 'Monarch Butterfly', 'text': 'Monarch butterflies have a body length of 4.5–5 cm. Wingspan is 8–10 cm.', 'expected': '4.5–5 cm', 'classification': {'family': 'Nymphalidae', 'order': 'Lepidoptera', 'class': 'Insecta'}},
        {'name': 'Honey Bee', 'text': 'Worker honey bees measure 10–15 mm in length.', 'expected': '10–15 mm', 'classification': {'family': 'Apidae', 'order': 'Hymenoptera', 'class': 'Insecta'}},
    ]
    
    passed = 0
    for test in test_cases:
        result = test_length_extraction(test['text'], test['name'], test.get('classification'))
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
    print("FREE SOLUTIONS SUMMARY:")
    print("=" * 80)
    print("✅ Wikidata SPARQL - FREE structured knowledge graph queries")
    print("✅ DBpedia SPARQL  - FREE Wikipedia infobox extraction")
    print("✅ spaCy NER       - FREE quantity entity recognition (optional)")
    print("✅ Regex Patterns  - FREE fast pattern matching (fallback)")
    print("\n💰 Total Cost: $0.00 (100% FREE)")
    print("=" * 80)
