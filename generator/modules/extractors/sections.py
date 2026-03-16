# generator/extractors/sections.py
"""Wikipedia section extraction module"""
import re


def clean_wikipedia_text(text):
    """Clean Wikipedia text of garbage"""
    if not text:
        return ""
    
    # Remove templates
    text = re.sub(r'\{\{[^}]*\}\}', ' ', text)
    # Remove references
    text = re.sub(r'\[\d+\]', '', text)
    # Remove wiki links but keep text
    def replace_link(m):
        content = m.group(1)
        return content.split('|')[-1] if '|' in content else content
    text = re.sub(r'\[\[([^]]+)\]\]', replace_link, text)
    # Remove HTML entities
    text = re.sub(r'&[^;]+;', ' ', text)
    # Remove wiki markup
    text = text.replace("'''", '').replace("''", '').replace('|', ' ')
    
    # Remove garbage strings
    garbage_strings = [
        'Jump to content', 'Jump to navigation', 'From Wikipedia', 'free encyclopedia',
        'Wikidata', 'Featured article', 'Use dmy dates', 'Short description',
        'Speciesbox', 'IUCN', 'CITES', 'cite book', 'cite journal', 'Reflist',
        'References', 'External links', 'See also', 'Authority control',
        'Category:', 'Navbox', 'thumb', 'alt=', 'File:', 'Image:',
        '[edit]', 'For other uses', 'disambiguation', 'Binomial name',
        'Scientific classification', 'Kingdom:', 'Phylum:', 'Class:',
        'Conservation status', 'Appendix',
    ]
    for garbage in garbage_strings:
        text = text.replace(garbage, ' ')
    
    # Remove section headers
    text = re.sub(r'==[^=]+==', ' ', text)
    # Remove long parentheticals
    text = re.sub(r'\([^)]{50,}\)', ' ', text)
    # Clean spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def extract_wikipedia_sections(text):
    """Extract Wikipedia sections by keyword categorization"""
    sections = {
        "etymology": "",
        "description": "",
        "distribution": "",
        "habitat": "",
        "hunting_diet": "",
        "behavior": "",
        "reproduction": "",
        "threats": "",
        "conservation": ""
    }
    
    if not text or len(text) < 500:
        return sections
    
    text = clean_wikipedia_text(text)
    
    if len(text) < 500:
        return sections
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Keywords for each section
    section_keywords = {
        "etymology": ['etymology', 'name', 'named', 'called', 'word', 'term', 'origin', 'latin', 'greek', 'persian', 'means', 'derives'],
        "description": ['description', 'physical', 'appearance', 'characteristics', 'weighs', 'measures', 'length', 'size', 'fur', 'coat', 'stripes', 'spots', 'color', 'skull', 'teeth', 'claws', 'tail', 'head', 'body'],
        "distribution": ['distribution', 'range', 'found', 'native', 'lives', 'located', 'region', 'country', 'continent', 'asia', 'africa', 'europe', 'russia', 'india', 'china', 'indonesia'],
        "habitat": ['habitat', 'environment', 'inhabits', 'forest', 'grassland', 'desert', 'mountain', 'tropical', 'temperate', 'mangrove', 'woodland'],
        "hunting_diet": ['diet', 'eats', 'feeds', 'hunts', 'prey', 'predator', 'carnivore', 'herbivore', 'omnivore', 'food', 'feeding', 'kill', 'deer', 'boar', 'ungulate', 'attack'],
        "behavior": ['behavior', 'behaviour', 'social', 'solitary', 'group', 'pack', 'herd', 'territorial', 'nocturnal', 'diurnal', 'active', 'mark', 'territory', 'communication'],
        "reproduction": ['reproduction', 'breeding', 'mating', 'gestation', 'pregnant', 'pregnancy', 'litter', 'cubs', 'young', 'offspring', 'birth', 'wean'],
        "threats": ['threats', 'threatened', 'danger', 'hunted', 'killed', 'poach', 'poaching', 'endangered', 'vulnerable', 'extinct', 'decline', 'destruction', 'fragmentation'],
        "conservation": ['conservation', 'protected', 'status', 'iucn', 'endangered', 'vulnerable', 'least concern', 'population', 'preserve', 'reserve', 'park', 'patrol', 'action plan']
    }
    
    current_section = "description"
    section_content = {k: [] for k in sections}
    
    for sentence in sentences:
        sentence_lower = sentence.lower().strip()
        
        if len(sentence_lower) < 30:
            continue
        
        if any(g in sentence_lower for g in ['{{', '}}', '[[', ']]', 'cite', 'isbn', 'doi', 'http']):
            continue
        
        # Find best matching section
        best_match = None
        best_score = 0
        
        for section_name, keywords in section_keywords.items():
            score = sum(1 for kw in keywords if kw in sentence_lower)
            if score > best_score:
                best_score = score
                best_match = section_name
        
        if best_match and best_score >= 1:
            current_section = best_match
        
        if len(' '.join(section_content[current_section])) < 500:
            section_content[current_section].append(sentence)
    
    # Combine sentences
    for key in sections:
        content = ' '.join(section_content[key]).strip()
        content = re.sub(r'\s+', ' ', content)
        content = content[:600]
        if len(content) > 600:
            content = content.rsplit('.', 1)[0] + '.'
        sections[key] = content
    
    return sections
