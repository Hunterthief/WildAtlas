def extract_locations(text, animal_type):
    """Extract locations - FIXED"""
    if not text: 
        return None
    
    # Get animal-specific locations FIRST
    animal_locations = LOCATIONS.get("animal_specific", {}).get(animal_type, [])
    
    # Add region locations
    for region, locs in LOCATIONS.get("regions", {}).items():
        animal_locations.extend(locs)
    
    # Find matching locations
    locs = []
    text_lower = text.lower()
    for loc in animal_locations:
        if loc.lower() in text_lower:
            locs.append(loc)
    
    # Remove duplicates and filter out wrong continents
    seen = set()
    unique_locs = []
    for loc in locs:
        loc_lower = loc.lower()
        # Filter out obviously wrong locations
        if animal_type == 'elephant' and any(w in loc_lower for w in ['asia', 'china', 'indonesia']):
            continue  # African elephants don't live in Asia
        if animal_type == 'raptor' and 'asia' in loc_lower:
            continue  # Bald eagles are North American
        if loc_lower not in seen:
            seen.add(loc_lower)
            unique_locs.append(loc)
    
    return ", ".join(unique_locs[:5]) if unique_locs else None

def extract_behavior(text, animal_type):
    """Extract behavior - FIXED"""
    if not text: 
        return None
    
    t = text.lower()
    
    # Check for social animals FIRST (more specific)
    social_indicators = {
        'elephant': ['herd', 'family', 'matriarch', 'social', 'group'],
        'bee': ['colony', 'hive', 'social', 'eusocial', 'worker', 'queen'],
        'penguin': ['colony', 'rookery', 'huddle', 'group', 'social'],
        'canine': ['pack', 'social', 'group', 'hunting together'],
        'ant': ['colony', 'social', 'eusocial', 'worker', 'queen']
    }
    
    # Check animal-specific social indicators
    if animal_type in social_indicators:
        for indicator in social_indicators[animal_type]:
            if indicator in t:
                return "Social"
    
    # Check for solitary indicators
    if any(w in t for w in ['solitary', 'alone', 'lives alone', 'mostly solitary', 'lives singly', 'lone', 'territorial']):
        return "Solitary"
    
    # Check for social/pack animals (general)
    elif any(w in t for w in ['pack', 'herd', 'flock', 'school', 'swarm', 'colony', 'social', 'group living', 'highly social', 'live in groups']):
        return "Social"
    
    # Check for pair/family groups
    elif any(w in t for w in ['pair', 'mate', 'family group', 'monogamous', 'nuclear family', 'pairs']):
        return "Family groups"
    
    # Default based on animal type
    social_types = ['elephant', 'bee', 'ant', 'penguin', 'canine', 'whale']
    if animal_type in social_types:
        return "Social"
    
    return "Solitary"

def extract_features(text, animal_type):
    """Extract features - FIXED with better filtering"""
    if not text: 
        return None
    
    type_features = FEATURES.get(animal_type, FEATURES.get("default", {}))
    positive = type_features.get("positive", [])
    negative = type_features.get("negative", [])
    
    features = []
    text_lower = text.lower()
    
    # Check positive features first
    for feature in positive:
        if feature in text_lower:
            display_feature = feature.replace('_', ' ').title()
            if display_feature not in features:
                features.append(display_feature)
    
    # Check common features with NEGATIVE filtering
    common_features = {
        "striped": "Striped coat",
        "stripe": "Striped coat",
        "spotted": "Spotted coat",
        "spot": "Spotted coat",
        "mane": "Distinctive mane",
        "trunk": "Long trunk",
        "tusk": "Large tusks",
        "horn": "Prominent horns",
        "antler": "Large antlers",
        "wing": "Distinctive wings",
        "tail": "Long tail",
        "fin": "Distinctive fins",
        "shell": "Protective shell",
        "venom": "Venomous",
        "claw": "Sharp claws",
        "fang": "Large fangs",
        "beak": "Distinctive beak",
        "feather": "Distinctive plumage",
        "scale": "Scaled skin",
        "fur": "Thick fur"
    }
    
    for keyword, feature in common_features.items():
        if keyword in text_lower and feature not in features:
            # Check if this feature is in the negative list for this animal type
            blocked = False
            for neg in negative:
                if neg in keyword or keyword in neg:
                    blocked = True
                    break
            
            # Also block obviously wrong features
            if animal_type not in ['fish', 'shark', 'ray'] and 'fin' in keyword:
                blocked = True
            if animal_type not in ['bird', 'raptor', 'penguin', 'butterfly', 'bee', 'bat'] and 'wing' in keyword:
                blocked = True
            if animal_type not in ['turtle'] and 'shell' in keyword:
                blocked = True
            if animal_type not in ['elephant'] and 'trunk' in keyword:
                blocked = True
            if animal_type not in ['elephant', 'bovine', 'deer'] and 'tusk' in keyword:
                blocked = True
            if animal_type not in ['feline'] and 'stripe' in keyword:
                blocked = True
            if animal_type not in ['frog', 'fish', 'salmon', 'shark', 'ray'] and 'tail' in keyword and 'long' in text_lower:
                # Adult frogs don't have tails
                if animal_type == 'frog':
                    blocked = True
            
            if not blocked:
                features.append(feature)
    
    return features[:3] if features else None
