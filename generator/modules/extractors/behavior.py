# generator/extractors/behavior.py
"""Behavior extraction module"""


def extract_behavior_from_sections(sections):
    """Extract group behavior from sections"""
    all_text = ""
    for section_text in sections.values():
        all_text += section_text + " "
    
    if not all_text:
        return ""
    
    t = all_text.lower()
    if any(w in t for w in ['solitary', 'alone', 'lives alone', 'mostly solitary', 'lives singly']):
        return "Solitary"
    elif any(w in t for w in ['pack', 'herd', 'flock', 'colony', 'social', 'group living', 'highly social']):
        return "Social"
    elif any(w in t for w in ['pair', 'mate', 'pairs', 'family group']):
        return "Pairs"
    
    return ""
