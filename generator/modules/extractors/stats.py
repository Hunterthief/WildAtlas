# generator/extractors/stats.py
"""Physical stats extraction module"""
import re


def extract_stats_from_sections(sections):
    """Extract weight, length, height, lifespan, speed from sections"""
    stats = {"weight": "", "length": "", "height": "", "lifespan": "", "top_speed": ""}
    
    all_text = ""
    for section_text in sections.values():
        all_text += section_text + " "
    
    if not all_text:
        return stats
    
    # Weight
    m = re.search(r'weighs?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms|tonnes?|t|lbs?|pounds)', all_text, re.I)
    if m:
        stats["weight"] = f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    # Length
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet)\s*(?:long|length|in length)', all_text, re.I)
    if m:
        stats["length"] = f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    # Height
    if 'shoulder' in all_text.lower() or 'stands' in all_text.lower():
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet)\s*(?:tall|height|shoulder)', all_text, re.I)
        if m:
            stats["height"] = f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    # Lifespan
    m = re.search(r'(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)\s*(?:lifespan|life|old|age|in the wild|in captivity)', all_text, re.I)
    if m:
        stats["lifespan"] = f"{m.group(1)} {m.group(2)}"
    
    # Speed
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*(km/h|kmph|mph|mi/h)\s*(?:speed|top speed|maximum|can run|sprint)', all_text, re.I)
    if m:
        stats["top_speed"] = f"{m.group(1)} {m.group(2)}"
    
    return stats
