# generator/modules/extractors/stats.py
"""
Physical stats extraction module - COMPREHENSIVE
Extracts weight, length, height, lifespan, speed from Wikipedia text
Covers ALL real Wikipedia patterns found in animal articles
"""
import re
from typing import Dict, Any, List, Tuple, Optional


def extract_stats_from_sections(sections: Dict[str, str]) -> Dict[str, str]:
    """Extract weight, length, height, lifespan, speed from sections"""
    stats = {
        "weight": "",
        "length": "",
        "height": "",
        "lifespan": "",
        "top_speed": ""
    }
    
    # Combine all section text
    all_text = " ".join(sections.values())
    
    if not all_text or len(all_text) < 50:
        return stats
    
    # Clean text for better matching
    clean_text = re.sub(r'\[\d+\]', '', all_text)  # Remove citations
    clean_text = re.sub(r'\s+', ' ', clean_text)  # Normalize whitespace
    
    # =============================================================================
    # WEIGHT EXTRACTION - 25+ Patterns
    # =============================================================================
    weight_patterns = [
        # "weighing from 22 to 45 kg" (Emperor Penguin)
        r'weighing\s*(?:from|between|about|around|approximately|up to)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g|oz|ounces)',
        
        # "Adults weigh between 21 and 65 kg" (Cheetah)
        r'(?:adults|males|females|species|they|it|average|typically)?\s*weighs?\s*(?:between|from|about|around|approximately|up to|an average of)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g|oz|ounces)',
        
        # "weigh from 23 to 45 kg" (Elephant tusks)
        r'weigh\s*(?:from|between)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g|oz|ounces)',
        
        # "weight of 100-200 kg"
        r'weight\s*(?:of|is|ranges from)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g|oz|ounces)',
        
        # "100 to 200 kilograms in weight"
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g|oz|ounces)\s*(?:in weight|weight|heavy|mass)',
        
        # "mass of 100-200 kg"
        r'mass\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g|oz|ounces)',
        
        # Single value: "weighs 150 kg"
        r'weighs?\s*(?:about|around|approximately|up to|an average of)?\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g|oz|ounces)',
        
        # "from 22 to 45 kg" with weighing context
        r'weighing?\s*from\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g|oz|ounces)',
        
        # "140kg - 300kg (309lbs - 660lbs)" (Tiger format)
        r'(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)\s*(?:-|–|to)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "1,110kg - 2,240kg" (with comma separator)
        r'(\d{1,3}(?:,\d{3})+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)\s*(?:-|–|to)\s*(\d{1,3}(?:,\d{3})+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds)',
        
        # "ranges from 100 to 200 kg"
        r'ranges?\s*(?:from)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g)',
        
        # "between 100 and 200 kg"
        r'between\s*(\d+(?:[.,]\d+)?)\s*(?:and|to)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g)',
        
        # "100–200 kg" (en-dash without spaces)
        r'(\d+(?:[.,]\d+)?)\s*[–-]\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g)',
        
        # "can weigh up to 100 kg"
        r'can\s*weigh\s*(?:up to)?\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g)',
        
        # "may weigh" patterns
        r'may\s*weigh\s*(?:from|between)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g)',
        
        # "with a weight of"
        r'with\s*a\s*weight\s*of\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g)',
        
        # "body weight" patterns
        r'body\s*weight\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g)',
        
        # "average weight"
        r'average\s*weight\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g)',
        
        # "typically weighs"
        r'typically\s*weighs?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g)',
        
        # "usually weighs"
        r'usually\s*weighs?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g)',
        
        # "can reach weights of"
        r'can\s*reach\s*weights?\s*of\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g)',
        
        # "reaching weights of"
        r'reaching\s*weights?\s*of\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|tonnes?|tons?|t|lbs?|pounds|grams?|g)',
        
        # Metric with imperial conversion: "100 kg (220 lb)"
        r'(\d+(?:[.,]\d+)?)\s*(kg|kilograms?)\s*\((\d+(?:[.,]\d+)?)\s*(lbs?|pounds)\)',
        
        # Imperial with metric conversion: "220 lb (100 kg)"
        r'(\d+(?:[.,]\d+)?)\s*(lbs?|pounds)\s*\((\d+(?:[.,]\d+)?)\s*(kg|kilograms?)\)',
        
        # "tonnes" specifically for large animals
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(tonnes?|tons?|t)',
    ]
    
    for pattern in weight_patterns:
        m = re.search(pattern, clean_text, re.I)
        if m:
            groups = m.groups()
            if len(groups) >= 3:
                # Handle different group patterns
                if groups[0] and groups[1] and groups[2]:
                    stats["weight"] = f"{groups[0]}–{groups[1]} {groups[2]}"
                elif groups[0] and groups[1]:
                    stats["weight"] = f"{groups[0]} {groups[1]}"
            elif len(groups) >= 2:
                stats["weight"] = f"{groups[0]} {groups[1]}"
            break
    
    # =============================================================================
    # LENGTH EXTRACTION - 25+ Patterns
    # =============================================================================
    length_patterns = [
        # "reaching 100 cm (39 in) in length" (Emperor Penguin)
        r'reaching?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches|mm|millimetres?|millimeters?)\s*(?:in length|long|length)?',
        
        # "head-and-body length is between 1.1 and 1.5 m" (Cheetah)
        r'(?:body|head-and-body|total|overall|snout-to-vent|standard)?\s*length\s*(?:is|of|ranges from|between)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches|mm|millimetres?|millimeters?)',
        
        # "100 to 200 cm long"
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches|mm|millimetres?|millimeters?)\s*(?:long|in length|length)',
        
        # "grows to 100-200 cm"
        r'grows?\s*(?:to|up to|reaching|as large as)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches|mm|millimetres?|millimeters?)',
        
        # "measures 100-200 cm"
        r'measures?\s*(?:about|approximately)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches|mm|millimetres?|millimeters?)',
        
        # "100 cm in length"
        r'(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches|mm|millimetres?|millimeters?)\s*(?:in length|long)',
        
        # Single value: "100 cm long"
        r'(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches|mm|millimetres?|millimeters?)\s*(?:long|length)',
        
        # "average length of 3.18 to 4 m" (King Cobra)
        r'average\s*length\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        
        # "can reach lengths of"
        r'can\s*reach\s*lengths?\s*of\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        
        # "reaching lengths of"
        r'reaching\s*lengths?\s*of\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        
        # "up to 100 cm"
        r'up\s*to\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        
        # "as long as"
        r'as\s*long\s*as\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        
        # "typically 100-200 cm"
        r'typically\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        
        # "usually 100-200 cm"
        r'usually\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        
        # "ranges from 100 to 200 cm"
        r'ranges?\s*(?:from)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        
        # "between 100 and 200 cm"
        r'between\s*(\d+(?:[.,]\d+)?)\s*(?:and|to)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        
        # "100–200 cm" (en-dash)
        r'(\d+(?:[.,]\d+)?)\s*[–-]\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        
        # "2.4m - 3.3m (6.8ft - 11ft)" (Tiger format)
        r'(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?)\s*(?:-|–|to)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?)',
        
        # Wingspan specifically
        r'wingspan\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        
        # "total length"
        r'total\s*length\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        
        # "maximum length"
        r'maximum\s*length\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        
        # "minimum length"
        r'minimum\s*length\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        
        # "body length"
        r'body\s*length\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        
        # Metric with imperial: "100 cm (39 in)"
        r'(\d+(?:[.,]\d+)?)\s*(cm|metres?|meters?)\s*\((\d+(?:[.,]\d+)?)\s*(in|feet|ft)\)',
        
        # "record length of"
        r'record\s*length\s*of\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
    ]
    
    for pattern in length_patterns:
        m = re.search(pattern, clean_text, re.I)
        if m:
            groups = m.groups()
            if len(groups) >= 3 and groups[0] and groups[1] and groups[2]:
                stats["length"] = f"{groups[0]}–{groups[1]} {groups[2]}"
            elif len(groups) >= 2 and groups[0] and groups[1]:
                stats["length"] = f"{groups[0]} {groups[1]}"
            break
    
    # =============================================================================
    # HEIGHT EXTRACTION - 20+ Patterns
    # =============================================================================
    height_patterns = [
        # "reaches 67–94 cm (2.20–3.08 ft) at the shoulder" (Cheetah)
        r'reaches?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)\s*(?:at the shoulder|shoulder height|at shoulder|tall)?',
        
        # "stands 100 to 200 cm tall at the shoulder"
        r'stands?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)\s*(?:tall|at the shoulder|shoulder height)?',
        
        # "shoulder height of 100-200 cm"
        r'shoulder\s*height\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        
        # "height at shoulder 100-200 cm"
        r'height\s*(?:at\s*)?(?:the\s*)?shoulder\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        
        # "100 to 200 cm at the shoulder"
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)\s*(?:at the shoulder|shoulder)',
        
        # Single value: "100 cm tall"
        r'(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)\s*(?:tall|height)',
        
        # "28-38 inches" (Bald Eagle)
        r'(\d+(?:[.,]\d+)?)\s*(?:-|–|to)\s*(\d+(?:[.,]\d+)?)\s*(in|inches|ft|feet)',
        
        # "height of"
        r'height\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        
        # "stands about"
        r'stands?\s*(?:about|approximately)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        
        # "can stand"
        r'can\s*stand\s*(?:up to)?\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        
        # "up to 100 cm tall"
        r'up\s*to\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)\s*(?:tall|height)',
        
        # "typically stands"
        r'typically\s*stands?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        
        # "usually stands"
        r'usually\s*stands?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        
        # "average height"
        r'average\s*height\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        
        # "ranges from 100 to 200 cm"
        r'ranges?\s*(?:from)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        
        # "between 100 and 200 cm"
        r'between\s*(\d+(?:[.,]\d+)?)\s*(?:and|to)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        
        # "100–200 cm" (en-dash)
        r'(\d+(?:[.,]\d+)?)\s*[–-]\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
        
        # "100cm - 120cm (39in - 47in)" (Emperor Penguin format)
        r'(\d+(?:[.,]\d+)?)\s*(cm|m)\s*(?:-|–|to)\s*(\d+(?:[.,]\d+)?)\s*(cm|m|in|ft)',
        
        # "at the hip"
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)\s*(?:at the hip|hip height)',
        
        # "withers height"
        r'withers\s*height\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet|in|inches)',
    ]
    
    for pattern in height_patterns:
        m = re.search(pattern, clean_text, re.I)
        if m:
            groups = m.groups()
            if len(groups) >= 3 and groups[0] and groups[1] and groups[2]:
                stats["height"] = f"{groups[0]}–{groups[1]} {groups[2]}"
            elif len(groups) >= 2 and groups[0] and groups[1]:
                stats["height"] = f"{groups[0]} {groups[1]}"
            break
    
    # =============================================================================
    # LIFESPAN EXTRACTION - 20+ Patterns
    # =============================================================================
    lifespan_patterns = [
        # "lifespan of an emperor penguin is typically 20 years"
        r'lifespan\s*(?:of|is|for)?\s*(?:a|an|the|wild|in captivity|typically|usually|about|around|average)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)',
        
        # "average lifespan of a wild king cobra is about 20 years"
        r'average\s*lifespan\s*(?:of|is)?\s*(?:a|an|the|wild|in captivity|typically|usually|about|around)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)',
        
        # "15-20 years in the wild" (Bald Eagle)
        r'(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)\s*(?:in the wild|in captivity|typically|usually|old|age|lifespan|average)',
        
        # "life expectancy of 10-20 years"
        r'life\s*expectancy\s*(?:of|is)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)',
        
        # "can live up to 20 years"
        r'(?:can\s*)?live[s]?\s*(?:up to|about|around|typically|usually)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)',
        
        # "live 10 to 20 years"
        r'live[s]?\s*(?:up to|about|around|typically|usually)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)',
        
        # "20 years" near lifespan context
        r'(?:lifespan|life|live|years? old|age|longevity)\s*(?:of|is|about|around|typically|usually)?\s*(\d+)\s*(years?|yrs)',
        
        # Single value: "20 years"
        r'(?:about|around|approximately|typically|usually)?\s*(\d+)\s*(years?|yrs)\s*(?:old|age|lifespan|in the wild|in captivity|average)',
        
        # "typically 20 years"
        r'typically\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)',
        
        # "usually 20 years"
        r'usually\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)',
        
        # "ranges from 10 to 20 years"
        r'ranges?\s*(?:from)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)',
        
        # "between 10 and 20 years"
        r'between\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(?:and|to)\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)',
        
        # "10–20 years" (en-dash)
        r'(\d+)\s*[–-]\s*(\d+)\s*(years?|yrs)',
        
        # "up to 20 years"
        r'up\s*to\s*(\d+)\s*(years?|yrs)',
        
        # "as long as 20 years"
        r'as\s*long\s*as\s*(\d+)\s*(years?|yrs)',
        
        # "maximum of 20 years"
        r'maximum\s*(?:of|lifespan)?\s*(\d+)\s*(years?|yrs)',
        
        # "minimum of 10 years"
        r'minimum\s*(?:of|lifespan)?\s*(\d+)\s*(years?|yrs)',
        
        # "longevity of"
        r'longevity\s*(?:of|is)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)',
        
        # "years in the wild"
        r'(\d+(?:\s*[-–]\s*\d+)?)\s*(?:years?|yrs)\s*in\s*the\s*wild',
        
        # "years in captivity"
        r'(\d+(?:\s*[-–]\s*\d+)?)\s*(?:years?|yrs)\s*in\s*captivity',
    ]
    
    for pattern in lifespan_patterns:
        m = re.search(pattern, clean_text, re.I)
        if m:
            groups = m.groups()
            if len(groups) >= 2:
                stats["lifespan"] = f"{groups[0]} {groups[1]}"
            break
    
    # =============================================================================
    # SPEED EXTRACTION - 20+ Patterns
    # =============================================================================
    speed_patterns = [
        # "capable of running at 93 to 104 km/h" (Cheetah)
        r'capable\s*of\s*(?:running|swimming|flying|moving|traveling)?\s*(?:at|speeds? of)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(km/h|kmph|kph|mph|mi/h|miles per hour|kilometers per hour|kilometres per hour)',
        
        # "speed of 100 km/h"
        r'speed\s*(?:of|is|reaches)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(km/h|kmph|kph|mph|mi/h|miles per hour|kilometers per hour|kilometres per hour)',
        
        # "can run at 100 km/h"
        r'can\s*(?:run|swim|fly|move|travel|reach)\s*(?:at|up to|speeds? of)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(km/h|kmph|kph|mph|mi/h|miles per hour|kilometers per hour|kilometres per hour)',
        
        # "100 km/h top speed"
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(km/h|kmph|kph|mph|mi/h|miles per hour|kilometers per hour|kilometres per hour)\s*(?:top speed|maximum speed|speed)',
        
        # "reaches speeds of 100 km/h"
        r'reaches?\s*(?:speeds? of|up to|about)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(km/h|kmph|kph|mph|mi/h|miles per hour|kilometers per hour|kilometres per hour)',
        
        # "100 km/h" near speed keywords
        r'(?:speed|fast|rapid|swift|run|swim|fly|sprint|dash)\s*(?:of|is|at|up to)?\s*(\d+(?:[.,]\d+)?)\s*(km/h|kmph|kph|mph|mi/h|miles per hour|kilometers per hour|kilometres per hour)',
        
        # "up to 100 km/h"
        r'up\s*to\s*(\d+(?:[.,]\d+)?)\s*(km/h|kmph|kph|mph|mi/h|miles per hour|kilometers per hour|kilometres per hour)',
        
        # "maximum speed of"
        r'maximum\s*speed\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(km/h|kmph|kph|mph|mi/h|miles per hour|kilometers per hour|kilometres per hour)',
        
        # "top speed of"
        r'top\s*speed\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(km/h|kmph|kph|mph|mi/h|miles per hour|kilometers per hour|kilometres per hour)',
        
        # "can reach speeds of"
        r'can\s*reach\s*speeds?\s*of\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(km/h|kmph|kph|mph|mi/h|miles per hour|kilometers per hour|kilometres per hour)',
        
        # "can sprint up to"
        r'can\s*sprint\s*(?:up to)?\s*(\d+(?:[.,]\d+)?)\s*(km/h|kmph|kph|mph|mi/h|miles per hour|kilometers per hour|kilometres per hour)',
        
        # "sprints at"
        r'sprints?\s*(?:at)?\s*(\d+(?:[.,]\d+)?)\s*(km/h|kmph|kph|mph|mi/h|miles per hour|kilometers per hour|kilometres per hour)',
        
        # "travels at"
        r'travels?\s*(?:at)?\s*(\d+(?:[.,]\d+)?)\s*(km/h|kmph|kph|mph|mi/h|miles per hour|kilometers per hour|kilometres per hour)',
        
        # "cruising speed"
        r'cruising\s*speed\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(km/h|kmph|kph|mph|mi/h|miles per hour|kilometers per hour|kilometres per hour)',
        
        # "dive speed"
        r'dive\s*speed\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(km/h|kmph|kph|mph|mi/h|miles per hour|kilometers per hour|kilometres per hour)',
        
        # "flight speed"
        r'flight\s*speed\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(km/h|kmph|kph|mph|mi/h|miles per hour|kilometers per hour|kilometres per hour)',
        
        # "swimming speed"
        r'swimming\s*speed\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(km/h|kmph|kph|mph|mi/h|miles per hour|kilometers per hour|kilometres per hour)',
        
        # "running speed"
        r'running\s*speed\s*(?:of|is)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)?\s*(\d+(?:[.,]\d+)?)?\s*(km/h|kmph|kph|mph|mi/h|miles per hour|kilometers per hour|kilometres per hour)',
        
        # "60 mph" (Tiger format - single value)
        r'(\d+(?:[.,]\d+)?)\s*(mph|km/h|kmph|kph)',
        
        # "fastest land animal at"
        r'fastest\s*(?:land|sea|air)?\s*(?:animal|bird|fish|creature)?\s*(?:at|reaching)?\s*(\d+(?:[.,]\d+)?)\s*(km/h|kmph|kph|mph|mi/h|miles per hour|kilometers per hour|kilometres per hour)',
    ]
    
    for pattern in speed_patterns:
        m = re.search(pattern, clean_text, re.I)
        if m:
            groups = m.groups()
            if len(groups) >= 2 and groups[0] and groups[1]:
                if len(groups) >= 3 and groups[1]:
                    stats["top_speed"] = f"{groups[0]}–{groups[1]} {groups[2]}"
                else:
                    stats["top_speed"] = f"{groups[0]} {groups[1]}"
            elif len(groups) >= 1 and groups[0]:
                stats["top_speed"] = f"{groups[0]}"
            break
    
    return stats


def extract_stats_with_context(sections: Dict[str, str], animal_name: str = "", scientific_name: str = "") -> Dict[str, str]:
    """
    Enhanced extraction with animal-specific context and fallbacks
    """
    stats = extract_stats_from_sections(sections)
    
    # Combine all text for context-aware extraction
    all_text = " ".join(sections.values())
    all_text = re.sub(r'\[\d+\]', '', all_text)
    
    # Animal-specific fallbacks for large animals
    if animal_name:
        name_lower = animal_name.lower()
        
        # Elephants - look for tonne patterns
        if "elephant" in name_lower and not stats["weight"]:
            m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to)\s*(\d+(?:[.,]\d+)?)\s*(tonnes?|tons)', all_text, re.I)
            if m:
                stats["weight"] = f"{m.group(1)}–{m.group(2)} {m.group(3)}"
        
        # Whales/Sharks - look for tonne patterns
        if any(x in name_lower for x in ["whale", "shark"]) and not stats["weight"]:
            m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to)\s*(\d+(?:[.,]\d+)?)\s*(tonnes?|tons|kg|kilograms)', all_text, re.I)
            if m:
                stats["weight"] = f"{m.group(1)}–{m.group(2)} {m.group(3)}"
        
        # Snakes - look for meter length patterns
        if any(x in name_lower for x in ["snake", "cobra", "python"]) and not stats["length"]:
            m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to)\s*(\d+(?:[.,]\d+)?)\s*(m|metres|meters)', all_text, re.I)
            if m:
                stats["length"] = f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    return stats
