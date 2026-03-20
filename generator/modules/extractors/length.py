"""
Length Extraction Module - PRODUCTION v25 (POST-LOG HARDENED)
WildAtlas Project

FIXES:
- Prevent height misclassification (elephant issue)
- Allow large fish lengths (shark fix)
- Improve cm-range handling (cheetah fix)
- Better fallback extraction when context missing
- Stronger filtering of wrong measurements
"""

import re
from typing import Dict, Any


# =============================================================================
# CONFIGURATION
# =============================================================================
ANIMAL_LENGTH_RANGES = {
    'felidae': (0.6, 3.5),
    'canidae': (0.8, 2.2),
    'elephantidae': (4.0, 8.5),
    'ursidae': (1.0, 3.5),
    'giraffidae': (3.5, 6.5),
    'proboscidea': (4.0, 8.5),

    'accipitridae': (0.4, 1.5),
    'accipitriformes': (0.4, 1.5),
    'spheniscidae': (0.5, 1.5),

    'cheloniidae': (0.6, 1.5),
    'elapidae': (2.0, 6.0),

    'lamnidae': (3.0, 8.5),  # sharks fix

    'hymenoptera': (0.005, 0.03),
    'lepidoptera': (0.02, 0.08),
    'apidae': (0.008, 0.025),
    'nymphalidae': (0.02, 0.08),
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

    # global sanity
    if max_v < 0.003 or max_v > 60:
        return False

    if classification:
        family = classification.get("family", "").lower()
        cls = classification.get("class", "").lower()

        # family-based ranges
        if family in ANIMAL_LENGTH_RANGES:
            low, high = ANIMAL_LENGTH_RANGES[family]
            if not (low * 0.7 <= max_v <= high * 1.3):
                return False

        # elephants safeguard
        if "elephant" in animal_name.lower() and max_v < 3.5:
            return False

        # birds
        if "aves" in cls and not (0.15 <= max_v <= 2.5):
            return False

        # insects
        if "insecta" in cls and max_v > 0.12:
            return False

    return True


def _has_bad_context(text: str) -> bool:
    text = text.lower()
    return any(x in text for x in [
        "wingspan",
        "shoulder height",
        "height at shoulder",
        "tusk",
        "horn",
    ])


def _has_length_context(text: str) -> bool:
    text = text.lower()
    return any(x in text for x in [
        "length",
        "long",
        "measures",
        "measuring",
    ])


# =============================================================================
# PATTERNS (STRONG → WEAK)
# =============================================================================
PATTERNS = [

    # explicit body length
    (r'body length[^.]{0,60}?(\d+(?:\.\d+)?)\s*(?:–|-|to)\s*(\d+(?:\.\d+)?)\s*(m|cm|mm|ft|in)', "range"),
    (r'body length[^.]{0,60}?(\d+(?:\.\d+)?)\s*(m|cm|mm|ft|in)', "single"),

    # standard patterns
    (r'(\d+(?:\.\d+)?)\s*(?:–|-|to)\s*(\d+(?:\.\d+)?)\s*(m|cm|mm|ft|in)\s+(?:long|in length)', "range"),
    (r'(\d+(?:\.\d+)?)\s*(m|cm|mm|ft|in)\s+(?:long|in length)', "single"),

    # fallback: number + unit (used carefully)
    (r'(\d+(?:\.\d+)?)\s*(?:–|-|to)\s*(\d+(?:\.\d+)?)\s*(m|cm|mm|ft|in)', "range_loose"),
    (r'(\d+(?:\.\d+)?)\s*(m|cm|mm|ft|in)', "single_loose"),
]


# =============================================================================
# CORE
# =============================================================================
def _extract_length_from_text(text, animal_name="", classification=None):
    text = re.sub(r'\[\d+\]', '', text)

    for pattern, typ in PATTERNS:
        for m in re.finditer(pattern, text, re.I):

            snippet = text[max(0, m.start()-120):m.end()+120]

            # skip bad contexts early
            if _has_bad_context(snippet):
                continue

            # require context unless loose fallback
            if "loose" not in typ and not _has_length_context(snippet):
                continue

            # build value
            if "range" in typ:
                val = f"{m.group(1)}–{m.group(2)} {m.group(3)}"
            else:
                val = f"{m.group(1)} {m.group(2)}"

            # validate
            if _is_valid_length(val, animal_name, classification):
                return val

    return ""


def extract_length_from_sections(
    sections: Dict[str, str],
    animal_name="",
    classification=None
) -> str:

    # priority sections
    for key in ["description", "characteristics", "size", "biology"]:
        if key in sections:
            res = _extract_length_from_text(
                sections[key],
                animal_name,
                classification
            )
            if res:
                return res

    # fallback all
    for text in sections.values():
        res = _extract_length_from_text(
            text,
            animal_name,
            classification
        )
        if res:
            return res

    return ""


def get_pattern_stats() -> Dict[str, Any]:
    return {
        "patterns": len(PATTERNS),
        "families_with_ranges": len(ANIMAL_LENGTH_RANGES),
    }
