"""
Length Extraction Module - PRODUCTION v25 (ROBUST EXTRACTION)
WildAtlas Project

Fixes:
- Expanded regex patterns (real-world Wikipedia formats)
- Relaxed context filtering
- Parentheses cleanup (imperial units)
- Improved validation ranges
"""

import re
from typing import Dict, Any


# =============================================================================
# CONFIGURATION
# =============================================================================
ANIMAL_LENGTH_RANGES = {
    'felidae': (0.6, 3.0),
    'canidae': (0.8, 2.0),
    'elephantidae': (4.5, 8.0),
    'ursidae': (1.0, 3.0),
    'giraffidae': (3.5, 6.0),
    'proboscidea': (4.5, 8.0),

    'accipitridae': (0.3, 2.5),
    'accipitriformes': (0.3, 2.5),
    'spheniscidae': (0.5, 1.5),

    'cheloniidae': (0.5, 1.5),
    'elapidae': (1.0, 6.0),

    'hymenoptera': (0.005, 0.05),
    'lepidoptera': (0.01, 0.1),
    'apidae': (0.005, 0.03),
    'nymphalidae': (0.02, 0.1),
}


# =============================================================================
# UTIL
# =============================================================================
def convert_to_meters(value: float, unit: str) -> float:
    unit = unit.lower()
    conversions = {
        'm': 1.0,
        'cm': 0.01,
        'mm': 0.001,
        'ft': 0.3048,
        'in': 0.0254,
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

    # Hard sanity limits
    if max_v < 0.005 or max_v > 50:
        return False

    if classification:
        family = classification.get("family", "").lower()
        cls = classification.get("class", "").lower()

        if "felidae" in family and not (0.6 <= max_v <= 3.5):
            return False

        if "canidae" in family and not (0.5 <= max_v <= 2.5):
            return False

        if "elephant" in animal_name.lower() and max_v < 3:
            return False

        if "aves" in cls and not (0.1 <= max_v <= 3.5):
            return False

        if "insecta" in cls and max_v > 0.2:
            return False

    return True


def _has_length_context(text: str) -> bool:
    text = text.lower()

    # Reject other dimensions
    if any(x in text for x in [
        "wingspan", "shoulder height", "tail length",
        "tusk", "horn length"
    ]):
        return False

    # Accept broader context
    return any(x in text for x in [
        "length", "long", "measure", "reach", "grow"
    ])


# =============================================================================
# PATTERNS (EXPANDED)
# =============================================================================
PATTERNS = [
    # Standard ranges
    (r'(\d+(?:\.\d+)?)\s*(?:–|-|to)\s*(\d+(?:\.\d+)?)\s*(m|cm|mm)', "range"),

    # With "long"
    (r'(\d+(?:\.\d+)?)\s*(?:–|-|to)\s*(\d+(?:\.\d+)?)\s*(m|cm|mm)\s+long', "range"),

    # "X m long"
    (r'(\d+(?:\.\d+)?)\s*(m|cm|mm)\s+long', "single"),

    # "X m in length"
    (r'(\d+(?:\.\d+)?)\s*(m|cm|mm)\s+(?:in length)', "single"),

    # "up to X m"
    (r'(?:up to|as much as|reaches?|reach|can reach)\s*(\d+(?:\.\d+)?)\s*(m|cm|mm)', "single"),

    # "measuring X m"
    (r'(?:measuring|measures)\s*(\d+(?:\.\d+)?)\s*(m|cm|mm)', "single"),
]


# =============================================================================
# CORE
# =============================================================================
def _extract_length_from_text(text, animal_name="", classification=None):
    # Remove citations
    text = re.sub(r'\[\d+\]', '', text)

    # Remove imperial units in parentheses (keep metric)
    text = re.sub(r'\([^)]*(ft|feet|inch|in)[^)]*\)', '', text, flags=re.I)

    for pattern, typ in PATTERNS:
        for m in re.finditer(pattern, text, re.I):
            snippet = text[max(0, m.start()-120):m.end()+120]

            if not _has_length_context(snippet):
                continue

            if typ == "range":
                val = f"{m.group(1)}–{m.group(2)} {m.group(3)}"
            else:
                val = f"{m.group(1)} {m.group(2)}"

            if _is_valid_length(val, animal_name, classification):
                return val

    return ""


def extract_length_from_sections(
    sections: Dict[str, str],
    animal_name="",
    classification=None
) -> str:

    # Priority sections first
    for key in ["description", "characteristics", "size"]:
        if key in sections:
            res = _extract_length_from_text(
                sections[key],
                animal_name,
                classification
            )
            if res:
                return res

    # Fallback: scan everything
    for text in sections.values():
        res = _extract_length_from_text(text, animal_name, classification)
        if res:
            return res

    return ""


# =============================================================================
# DEBUG / STATS
# =============================================================================
def get_pattern_stats() -> Dict[str, Any]:
    return {
        "patterns": len(PATTERNS),
        "supports_ranges": True,
        "supports_context_filtering": True,
        "supports_parentheses_cleanup": True,
    }
