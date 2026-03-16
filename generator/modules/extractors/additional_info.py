# generator/extractors/additional_info.py
"""Additional info extraction module"""
import re


def extract_additional_info_from_sections(sections):
    """Extract group, population, maturity, weaning, distinctive feature from sections"""
    info = {
        "group": "",
        "number_of_species": "",
        "estimated_population_size": "",
        "age_of_sexual_maturity": "",
        "age_of_weaning": "",
        "most_distinctive_feature": ""
    }
    
    all_text = ""
    for section_text in sections.values():
        all_text += section_text + " "
    
    if not all_text:
        return info
    
    # Group (Mammal, Bird, etc.)
    m = re.search(r'is a (?:large )?(?:species of )?(mammal|bird|fish|reptile|amphibian|insect|invertebrate|cat|feline)', all_text, re.I)
    if m:
        info["group"] = m.group(1).capitalize()
    
    # Number of species
    m = re.search(r'(?:nine|two|five|three|six|seven|eight|four|10|20|30)\s*(?:recent |living )?(?:sub)?species', all_text, re.I)
    if m:
        num_text = m.group(0)
        num_match = re.search(r'(nine|two|five|three|six|seven|eight|four|10|20|30|\d+)', num_text, re.I)
        if num_match:
            info["number_of_species"] = num_match.group(1)
    
    # Population
    m = re.search(r'(?:population|estimated|total)\s*(?:is|of|size)?\s*(?:about|around|approximately|over|under)?\s*(\d+(?:,\d+)*(?:\s*(?:million|billion|thousand))?)', all_text, re.I)
    if m:
        info["estimated_population_size"] = m.group(1).strip()
    
    # Sexual maturity
    m = re.search(r'(?:sexually mature|sexual maturity|mature)\s*(?:at|reached|occurs|become)?\s*(?:around|about)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs|months?)', all_text, re.I)
    if m:
        info["age_of_sexual_maturity"] = f"{m.group(1)} {m.group(2)}"
    
    # Weaning
    m = re.search(r'(?:weaned|weaning)\s*(?:at|occurs)?\s*(?:around|about)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs|months?|weeks?)', all_text, re.I)
    if m:
        info["age_of_weaning"] = f"{m.group(1)} {m.group(2)}"
    
    # Distinctive feature (avoid genetics)
    feature_patterns = [
        r'(?:most distinctive|distinctive|characteristic|notable|unique)\s*(?:feature|characteristic|trait|marking)?\s*(?:is|are)?\s*(?:the)?\s*([^.]{10,100})',
        r'(?:marked with|has|features?|characterized by)\s*(?:distinctive )?([^.]{10,80}(?:stripes|spots|coat|fur|color|mane|tail|ears))',
    ]
    for pattern in feature_patterns:
        m = re.search(pattern, all_text, re.I)
        if m:
            feature = m.group(1).strip()
            if 'dna' not in feature.lower() and 'mtdna' not in feature.lower() and 'haplotype' not in feature.lower() and 'gene' not in feature.lower():
                feature = re.sub(r'^(?:the |its |their |a |an )', '', feature, flags=re.I)
                if 10 < len(feature) < 150:
                    info["most_distinctive_feature"] = feature[:120]
                    break
    
    return info
