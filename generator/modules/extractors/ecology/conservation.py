# generator/modules/extractors/ecology/conservation.py
"""
Conservation Status Extraction Module

Extracts IUCN conservation status from Wikipedia text.
Edit this file only for conservation-related changes.
"""

CONSERVATION_STATUSES = [
    "Critically Endangered",
    "Endangered",
    "Vulnerable",
    "Near Threatened",
    "Least Concern",
    "Data Deficient",
    "Extinct in the Wild",
    "Extinct"
]


def extract_conservation(text):
    """
    Extract conservation status from text.
    
    Args:
        text: Wikipedia article text
        
    Returns:
        str: Conservation status or None
    """
    if not text:
        return None

    text_lower = text.lower()
    
    for status in CONSERVATION_STATUSES:
        if status.lower() in text_lower:
            return status
    
    return None
