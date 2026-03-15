# generator/modules/extractors/ecology/threats.py
"""
Threats Extraction Module

Extracts threats from Wikipedia text.
Edit this file only for threats-related changes.
"""

THREAT_KEYWORDS = {
    'Poaching': ['poach', 'illegal trade', 'body parts', 'fur trade', 'ivory', 'horn trade'],
    'Habitat loss': ['habitat loss', 'deforestation', 'habitat destruction', 'habitat fragmentation', 'loss of habitat'],
    'Human-wildlife conflict': ['human-wildlife conflict', 'livestock', 'retaliation', 'persecution', 'killed by humans'],
    'Climate change': ['climate change', 'global warming', 'ocean acidification', 'rising temperatures'],
    'Pollution': ['pollution', 'pesticide', 'contamination', 'pollutants'],
    'Overfishing': ['overfishing', 'bycatch', 'fishing', 'overhunting', 'hunting']
}


def extract_threats(text):
    """
    Extract threats from text.
    
    Args:
        text: Wikipedia article text
        
    Returns:
        str: Comma-separated threats or None
    """
    if not text:
        return None

    threats = []
    t = text.lower()
    
    for threat, keywords in THREAT_KEYWORDS.items():
        if any(w in t for w in keywords):
            threats.append(threat)

    return ', '.join(threats[:3]) if threats else None
