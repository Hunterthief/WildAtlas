# generator/modules/extractors/ecology/behavior.py
"""
Behavior Extraction Module

Extracts social behavior from Wikipedia text.
Edit this file only for behavior-related changes.
"""

SOCIAL_INDICATORS = {
    'elephant': ['herd', 'family', 'matriarch', 'social', 'group'],
    'bee': ['colony', 'hive', 'social', 'eusocial', 'worker', 'queen'],
    'penguin': ['colony', 'rookery', 'huddle', 'group', 'social'],
    'canine': ['pack', 'social', 'group', 'hunting together'],
    'ant': ['colony', 'social', 'eusocial', 'worker', 'queen']
}

SOLITARY_KEYWORDS = [
    'solitary', 'alone', 'lives alone', 'mostly solitary',
    'lives singly', 'lone', 'territorial'
]

SOCIAL_KEYWORDS = [
    'pack', 'herd', 'flock', 'school', 'swarm', 'colony',
    'social', 'group living', 'highly social', 'live in groups'
]

FAMILY_KEYWORDS = [
    'pair', 'mate', 'family group', 'monogamous',
    'nuclear family', 'pairs'
]

SOCIAL_TYPES = ['elephant', 'bee', 'ant', 'penguin', 'canine', 'whale']


def extract_behavior(text, animal_type):
    """
    Extract social behavior from text.
    
    Args:
        text: Wikipedia article text
        animal_type: Detected animal type
        
    Returns:
        str: Behavior type (Social, Solitary, Family groups) or None
    """
    if not text:
        return None

    t = text.lower()

    # Check animal-specific indicators first
    if animal_type in SOCIAL_INDICATORS:
        for indicator in SOCIAL_INDICATORS[animal_type]:
            if indicator in t:
                return "Social"

    # Check general keywords
    if any(w in t for w in SOLITARY_KEYWORDS):
        return "Solitary"
    elif any(w in t for w in SOCIAL_KEYWORDS):
        return "Social"
    elif any(w in t for w in FAMILY_KEYWORDS):
        return "Family groups"

    # Default based on animal type
    if animal_type in SOCIAL_TYPES:
        return "Social"

    return "Solitary"
