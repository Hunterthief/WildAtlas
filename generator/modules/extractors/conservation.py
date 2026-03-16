# generator/extractors/conservation.py
"""Conservation status and threats extraction module"""


def extract_conservation_from_sections(sections):
    """Extract conservation status and threats from sections"""
    status = ""
    threats = []
    
    all_text = ""
    for section_text in sections.values():
        all_text += section_text + " "
    
    # Conservation status
    statuses = ["Critically Endangered", "Endangered", "Vulnerable", "Near Threatened", "Least Concern", "Data Deficient"]
    for s in statuses:
        if s.lower() in all_text.lower():
            status = s
            break
    
    # Threats
    if any(w in all_text.lower() for w in ['poach', 'illegal trade', 'body parts', 'fur trade', 'ivory', 'tiger bone', 'medicinal']):
        threats.append('Poaching')
    if any(w in all_text.lower() for w in ['habitat loss', 'habitat destruction', 'habitat fragmentation', 'deforestation', 'logging']):
        threats.append('Habitat loss')
    if any(w in all_text.lower() for w in ['human-wildlife conflict', 'livestock', 'retaliation', 'attack', 'killed']):
        threats.append('Human-wildlife conflict')
    
    return status, ', '.join(threats[:3])
