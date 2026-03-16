# generator/extractors/reproduction.py
"""Reproduction data extraction module"""
import re


def extract_reproduction_from_sections(sections):
    """Extract gestation, litter size, young name from sections"""
    repro = {"gestation_period": "", "average_litter_size": "", "name_of_young": ""}
    
    all_text = ""
    for section_text in sections.values():
        all_text += section_text + " "
    
    if not all_text:
        return repro
    
    # Gestation
    m = re.search(r'(?:gestation|pregnancy)\s*(?:period)?\s*(?:lasts?|is|of)?\s*(?:around|about)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(days?|months?|weeks?)', all_text, re.I)
    if m:
        repro["gestation_period"] = f"{m.group(1)} {m.group(2)}"
    
    # Litter size
    m = re.search(r'(?:litter|cubs?|young|offspring)\s*(?:size)?\s*(?:of|is)?\s*(?:usually|typically|about)?\s*(\d+(?:\s*[-–]\s*\d+)?)', all_text, re.I)
    if m:
        repro["average_litter_size"] = m.group(1)
    
    # Name of young
    m = re.search(r'young\s*(?:are\s*)?(?:called|known as)?\s*(?:a|an)?\s*(\w+)', all_text, re.I)
    if m:
        repro["name_of_young"] = m.group(1).lower()
    
    return repro
