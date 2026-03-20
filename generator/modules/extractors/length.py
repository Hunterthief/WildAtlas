"""
Length Extraction Module - PRODUCTION v24 (LOG-BASED FIXES)
WildAtlas Project - https://github.com/Hunterthief/WildAtlas/

CRITICAL FIXES BASED ON 13 ANIMAL GENERATION LOGS
"""
import re
from typing import Dict, Any


# =============================================================================
# CONFIGURATION
# =============================================================================
ANIMAL_LENGTH_RANGES = {
    'felidae': (0.6, 2.5),
    'canidae': (0.8, 1.8),
    'elephantidae': (4.5, 8.0),
    'ursidae': (1.0, 3.0),
    'giraffidae': (3.5, 6.0),
    'proboscidea': (4.5, 8.0),

    'accipitridae': (0.6, 1.2),
    'accipitriformes': (0.5, 1.3),
    'spheniscidae': (0.7, 1.3),

    'cheloniidae': (0.7, 1.2),
    'elapidae': (2.0, 5.5),

    'hymenoptera': (0.008, 0.025),
    'lepidoptera': (0.02, 0.06),
    'apidae': (0.010, 0.020),
    'nymphalidae': (0.03, 0.06),
}


# =============================================================================
# UTIL
# =============================================================================
def convert_to_meters(value: float, unit: str) -> float:
    unit = unit.lower()
    conversions = {
        'm': 1.0, 'cm': 0.01, 'mm': 0.001,
        'ft': 0.3048, 'in': 0.0254,
        'km': 1000.0,
    }
    return value * conversions.get(unit, 1.0)


# =============================================================================
# VALIDATION
# =============================================================================
def _is_valid_length(value: str, animal_name="", classification=None) -> bool:
    if not value:
        return False

    matches = re.findall(r'(\d+(?:\.\d+)?)\s*(m|cm|mm|ft|in)', value.lower())
    if not matches:
        return False

    values = [convert_to_meters(float(v), u) for v, u in matches]
    max_v = max(values)

    if max_v < 0.005 or max_v > 50:
        return False

    if classification:
        family = classification.get("family", "").lower()
        cls = classification.get("class", "").lower()

        if "felidae" in family and not (0.6 <= max_v <= 3):
            return False

        if "canidae" in family and not (0.8 <= max_v <= 2):
            return False

        if "elephant" in animal_name.lower() and max_v < 4:
            return False

        if "aves" in cls and not (0.2 <= max_v <= 1.5):
            return False

        if "insecta" in cls and max_v > 0.1:
            return False

    return True


def _has_length_context(text: str) -> bool:
    text = text.lower()

    if any(x in text for x in ["wingspan", "shoulder height", "tail length", "tusk"]):
        return False

    return any(x in text for x in ["length", "long", "measures"])


# =============================================================================
# PATTERNS
# =============================================================================
PATTERNS = [
    (r'body length.*?(\d+(?:\.\d+)?)\s*(?:–|-|to)\s*(\d+(?:\.\d+)?)\s*(m|cm|mm)', "range"),
    (r'(\d+(?:\.\d+)?)\s*(?:–|-|to)\s*(\d+(?:\.\d+)?)\s*(m|cm|mm)\s+long', "range"),
    (r'(\d+(?:\.\d+)?)\s*(m|cm|mm)\s+long', "single"),
]


# =============================================================================
# CORE
# =============================================================================
def _extract_length_from_text(text, animal_name="", classification=None):
    text = re.sub(r'\[\d+\]', '', text)

    for pattern, typ in PATTERNS:
        for m in re.finditer(pattern, text, re.I):
            snippet = text[max(0, m.start()-100):m.end()+100]

            if not _has_length_context(snippet):
                continue

            if typ == "range":
                val = f"{m.group(1)}–{m.group(2)} {m.group(3)}"
            else:
                val = f"{m.group(1)} {m.group(2)}"

            if _is_valid_length(val, animal_name, classification):
                return val

    return ""


def extract_length_from_sections(sections: Dict[str, str], animal_name="", classification=None) -> str:
    for key in ["description", "characteristics", "size"]:
        if key in sections:
            res = _extract_length_from_text(sections[key], animal_name, classification)
            if res:
                return res

    for text in sections.values():
        res = _extract_length_from_text(text, animal_name, classification)
        if res:
            return res

    return ""


def get_pattern_stats() -> Dict[str, Any]:
    return {
        "patterns": len(PATTERNS),
    }
