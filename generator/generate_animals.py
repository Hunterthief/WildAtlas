# =============================================================================
# IMPORTS - Standard Library
# =============================================================================
import json
import time
import os
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# =============================================================================
# PATH SETUP (CRITICAL for GitHub Actions)
# =============================================================================
GENERATOR_DIR = Path(__file__).parent
sys.path.insert(0, str(GENERATOR_DIR))

# =============================================================================
# IMPORTS - Data Fetchers
# =============================================================================
from modules.fetchers.api_ninjas import fetch_animal_data
from modules.fetchers.wikipedia import fetch_wikipedia_data, fetch_wikipedia_sections, fetch_wikipedia_infobox
from modules.fetchers.inaturalist import fetch_inaturalist
from modules.fetchers.wikidata import fetch_wikidata_properties
from modules.fetchers.gbif_distribution import extract_gbif_all
from modules.fetchers.eol_data import extract_eol_all
from modules.fetchers.iucn_redlist import fetch_iucn_data

# =============================================================================
# IMPORTS - Wikipedia Extractors
# =============================================================================
from modules.extractors.sections import extract_wikipedia_sections
from modules.extractors.weight import extract_weight_from_sections
from modules.extractors.length import extract_length_from_sections
from modules.extractors.height import extract_height_from_sections
from modules.extractors.lifespan import extract_lifespan_from_sections
from modules.extractors.speed import extract_speed_from_sections
from modules.extractors.reproduction import extract_reproduction_from_sections
from modules.extractors.diet import extract_diet_from_sections
from modules.extractors.behavior import extract_behavior_from_sections
from modules.extractors.conservation import extract_conservation_from_sections
from modules.extractors.additional_info import extract_additional_info_from_sections
from modules.extractors.stats import extract_stats_from_sections, extract_stats_with_context
from modules.extractors.wikidata_enhancer import extract_wikidata_all

# =============================================================================
# SETUP PATHS
# =============================================================================
REPO_ROOT = GENERATOR_DIR.parent
DATA_DIR = REPO_ROOT / "data"
ANIMAL_STATS_DIR = DATA_DIR / "animal_stats"
DEBUG_DIR = DATA_DIR / "debug_logs"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(ANIMAL_STATS_DIR, exist_ok=True)
os.makedirs(DEBUG_DIR, exist_ok=True)

CONFIG_DIR = GENERATOR_DIR / "config"

# =============================================================================
# DEBUG HELPERS
# =============================================================================
def print_debug_header(title: str, char: str = "=") -> None:
    """Print a debug section header"""
    print(f"\n{char * 80}")
    print(f"  {title}")
    print(f"{char * 80}")

def print_raw_data(label: str, data: Any, max_length: int = 500) -> None:
    """Print raw data with truncation for large content"""
    print(f"\n📋 {label}:")
    if data is None:
        print("   ⚠️  NONE")
        return
    if isinstance(data, dict):
        print(f"   Type: dict with {len(data)} keys")
        print(f"   Keys: {list(data.keys())[:10]}{'...' if len(data) > 10 else ''}")
        for key, value in list(data.items())[:5]:
            if isinstance(value, str) and len(value) > max_length:
                print(f"   - {key}: {value[:max_length]}... (truncated)")
            else:
                print(f"   - {key}: {value}")
        if len(data) > 5:
            print(f"   ... and {len(data) - 5} more keys")
    elif isinstance(data, list):
        print(f"   Type: list with {len(data)} items")
        print(f"   First 3 items: {data[:3]}")
    elif isinstance(data, str):
        if len(data) > max_length:
            print(f"   {data[:max_length]}... (truncated, total: {len(data)} chars)")
        else:
            print(f"   {data}")
    else:
        print(f"   {data}")

def save_debug_log(name: str, qid: str, data: Dict[str, Any]) -> None:
    """Save debug data to file for inspection"""
    clean_name = name.lower().replace(' ', '_').replace('-', '_').replace("'", "")
    filepath = DEBUG_DIR / f"{clean_name}_{qid}_debug.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    print(f"   💾 Debug log saved: {filepath.name}")

# =============================================================================
# CONFIG LOADING
# =============================================================================
def load_config(filename: str) -> Dict[str, Any]:
    """Load JSON config file if it exists"""
    config_path = CONFIG_DIR / filename
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

YOUNG_NAMES = load_config("young_names.json")
GROUP_NAMES = load_config("group_names.json")

def get_young_name(animal_type: str) -> str:
    """Get young animal name based on type"""
    return YOUNG_NAMES.get(animal_type, YOUNG_NAMES.get("default", "young"))

def get_group_name(animal_type: str) -> str:
    """Get group name based on type"""
    return GROUP_NAMES.get(animal_type, GROUP_NAMES.get("default", "population"))

# =============================================================================
# FILE OPERATIONS
# =============================================================================
def get_animal_filename(name: str, qid: str) -> str:
    """Generate clean filename for animal data"""
    clean_name = name.lower().replace(' ', '_').replace('-', '_').replace("'", "")
    return f"{clean_name}_{{QID={qid}}}.json"

def save_animal_file(data: Dict[str, Any], name: str, qid: str) -> None:
    """Save animal data to JSON file"""
    filename = get_animal_filename(name, qid)
    filepath = ANIMAL_STATS_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f" 💾 Saved: {filename}")

# =============================================================================
# DATA CLEANING HELPERS
# =============================================================================
def clean_wikipedia_text(text: str) -> str:
    """Clean messy Wikipedia text - remove citations, infobox artifacts, etc."""
    if not text:
        return ""
    
    text = re.sub(r'\[\d+\]', '', text)
    
    artifacts = [
        "Temporal range:", "PreꞒ", "Ꞓ", "O", "S", "D", "C", "P", "T", "J", "K", "Pg", "N",
        "Animalia", "Chordata", "Mammalia", "Aves", "Reptilia", "Amphibia",
        "Order:", "Family:", "Genus:", "Species:", "Subspecies:",
        "Least Concern", "Near Threatened", "Vulnerable", "Endangered", "Critically Endangered",
        "IUCN Red List", "Red List of Threatened Species"
    ]
    
    for artifact in artifacts:
        text = text.replace(artifact, "")
    
    text = ' '.join(text.split())
    
    if len(text) < 20:
        return ""
    
    return text.strip()

def extract_clean_habitat(wiki_sections: Dict[str, str], gbif_data: Dict[str, Any]) -> str:
    """Extract clean habitat from multiple sources"""
    if gbif_data and gbif_data.get("habitat"):
        return gbif_data.get("habitat", "")
    
    habitat = wiki_sections.get("habitat", "")
    return clean_wikipedia_text(habitat)

def extract_clean_locations(wiki_sections: Dict[str, str], gbif_data: Dict[str, Any], ninja_locations: List[str]) -> str:
    """Extract clean location data from multiple sources"""
    if gbif_data and gbif_data.get("countries"):
        return ", ".join(gbif_data.get("countries", []))
    
    if ninja_locations:
        return ", ".join(ninja_locations)
    
    distribution = wiki_sections.get("distribution", "")
    return clean_wikipedia_text(distribution)

def fix_diet_based_on_taxonomy(diet: str, classification: Dict[str, str]) -> str:
    """Fix obvious diet errors based on taxonomy"""
    if not diet:
        return diet
    
    diet_lower = diet.lower()
    family = classification.get("family", "").lower()
    order = classification.get("order", "").lower()
    
    if "elephantidae" in family and "carnivore" in diet_lower:
        return "Herbivore"
    
    if "cheloniidae" in family and "carnivore" in diet_lower:
        return "Herbivore"
    
    if "primates" in order and "carnivore" in diet_lower:
        return "Omnivore"
    
    return diet

def get_first_non_empty(*values) -> str:
    """Return first non-empty string from values"""
    for v in values:
        if v and isinstance(v, str) and v.strip():
            return v
    return ""

def _extract_conservation_from_wikipedia_sections(wiki_sections: Dict[str, str]) -> str:
    """Extract conservation status from Wikipedia sections"""
    conservation_text = wiki_sections.get("conservation", "").lower()
    threats_text = wiki_sections.get("threats", "").lower()
    distribution_text = wiki_sections.get("distribution", "").lower()
    
    status_patterns = [
        (r"critically endangered", "Critically Endangered"),
        (r"endangered", "Endangered"),
        (r"vulnerable", "Vulnerable"),
        (r"near threatened", "Near Threatened"),
        (r"least concern", "Least Concern"),
        (r"data deficient", "Data Deficient"),
        (r"extinct in the wild", "Extinct in the Wild"),
        (r"extinct", "Extinct"),
        (r"iucn.*?critically endangered", "Critically Endangered"),
        (r"iucn.*?endangered", "Endangered"),
        (r"iucn.*?vulnerable", "Vulnerable"),
        (r"iucn.*?near threatened", "Near Threatened"),
        (r"iucn.*?least concern", "Least Concern"),
        (r"red list.*?critically endangered", "Critically Endangered"),
        (r"red list.*?endangered", "Endangered"),
        (r"red list.*?vulnerable", "Vulnerable"),
    ]
    
    for text in [conservation_text, threats_text, distribution_text]:
        for pattern, status in status_patterns:
            if re.search(pattern, text):
                return status
    
    return ""

# =============================================================================
# BUILD ANIMAL DATA
# =============================================================================
def build_animal_data(
    ninja_data: Dict[str, Any],
    wiki_sections: Dict[str, str],
    wiki_infobox: Dict[str, str],
    inat_classification: Dict[str, Any],
    wikidata_enhanced: Dict[str, Any],
    gbif_data: Dict[str, Any],
    eol_data: Dict[str, Any],
    qid: str,
    name: str,
    sci_name: str
) -> Dict[str, Any]:
    """Build complete animal data from fetched sources - NO fetching here!"""
    
    print_debug_header(f"BUILDING DATA FOR: {name} ({sci_name})")
    
    # ===== DEBUG: Print all raw inputs =====
    print_debug_header("RAW INPUT DATA TO EXTRACTORS", "-")
    
    print_raw_data("🥷 API Ninjas Data", ninja_data)
    print_raw_data("📖 Wikipedia Sections", wiki_sections)
    print_raw_data("📦 Wikipedia Infobox", wiki_infobox)
    print_raw_data("🔬 iNaturalist Classification", inat_classification)
    print_raw_data("📊 Wikidata Enhanced", wikidata_enhanced)
    print_raw_data("🌍 GBIF Data", gbif_data)
    print_raw_data("📚 EOL Data", eol_data)
    
    # ===== Save complete debug log =====
    debug_data = {
        "name": name,
        "scientific_name": sci_name,
        "qid": qid,
        "timestamp": datetime.now().isoformat(),
        "inputs": {
            "ninja_data": ninja_data,
            "wiki_sections": wiki_sections,
            "wiki_infobox": wiki_infobox,
            "inat_classification": inat_classification,
            "wikidata_enhanced": wikidata_enhanced,
            "gbif_data": gbif_data,
            "eol_data": eol_data
        }
    }
    save_debug_log(name, qid, debug_data)
    
    # ===== Extract stats with proper priority =====
    print_debug_header("EXTRACTOR INPUTS & OUTPUTS", "-")
    
    print("\n📊 Physical Stats Extraction:")
    
    # Prepare API Ninjas physical data
    api_ninjas_physical = {}
    if ninja_data:
        chars = ninja_data.get('characteristics', {})
        api_ninjas_physical = {
            'weight': chars.get('weight', ''),
            'length': chars.get('length', ''),
            'height': chars.get('height', ''),
            'lifespan': chars.get('lifespan', ''),
            'top_speed': chars.get('top_speed', ''),
        }
        print(f"   API Ninjas Physical: {api_ninjas_physical}")
    
    # Show what's being passed to extractor
    print(f"\n   📤 Passing to extract_stats_with_context:")
    print(f"      - sections keys: {list(wiki_sections.keys())}")
    print(f"      - animal_name: {name}")
    print(f"      - scientific_name: {sci_name}")
    print(f"      - infobox keys: {list(wiki_infobox.keys()) if wiki_infobox else 'NONE'}")
    print(f"      - wikidata keys: {list(wikidata_enhanced.keys()) if wikidata_enhanced else 'NONE'}")
    print(f"      - api_ninjas: {api_ninjas_physical}")
    
    # Extract with priority: Infobox > Wikidata > API Ninjas > Text
    physical_stats = extract_stats_with_context(
        sections=wiki_sections,
        animal_name=name,
        scientific_name=sci_name,
        infobox_data=wiki_infobox,
        wikidata_data=wikidata_enhanced,
        api_ninjas_data=api_ninjas_physical
    )
    
    print(f"\n   📥 Extractor returned: {physical_stats}")
    
    # ===== Individual Extractor Debug =====
    print("\n📏 Individual Extractor Calls:")
    
    weight = extract_weight_from_sections(wiki_sections, name)
    print(f"   Weight extractor: '{weight}'")
    
    length = extract_length_from_sections(wiki_sections, name)
    print(f"   Length extractor: '{length}'")
    
    height = extract_height_from_sections(wiki_sections, name)
    print(f"   Height extractor: '{height}'")
    
    lifespan = extract_lifespan_from_sections(wiki_sections, name)
    print(f"   Lifespan extractor: '{lifespan}'")
    
    speed = extract_speed_from_sections(wiki_sections, name)
    print(f"   Speed extractor: '{speed}'")
    
    diet, prey = extract_diet_from_sections(wiki_sections)
    print(f"   Diet extractor: '{diet}'")
    print(f"   Prey extractor: '{prey}'")
    
    repro = extract_reproduction_from_sections(wiki_sections)
    print(f"   Reproduction extractor: {repro}")
    
    behavior = extract_behavior_from_sections(wiki_sections)
    print(f"   Behavior extractor: '{behavior}'")
    
    conservation_status_wiki, threats = extract_conservation_from_sections(wiki_sections)
    print(f"   Conservation extractor: '{conservation_status_wiki}'")
    print(f"   Threats extractor: '{threats}'")
    
    additional = extract_additional_info_from_sections(wiki_sections)
    print(f"   Additional info extractor: {additional}")
    
    # ===== Animal Type Detection =====
    animal_type = "default"
    taxonomy_to_use = inat_classification if inat_classification else {}
    
    if taxonomy_to_use:
        family = taxonomy_to_use.get("family", "").lower()
        if "felidae" in family:
            animal_type = "feline"
        elif "canidae" in family:
            animal_type = "canine"
        elif "ursidae" in family:
            animal_type = "bear"
        elif "elephantidae" in family:
            animal_type = "elephant"
    
    print(f"\n🏷️  Animal Type: {animal_type}")
    
    young_name = get_young_name(animal_type)
    
    # ===== Classification - Priority: iNaturalist > Wikidata > Ninja =====
    classification = {
        "kingdom": "",
        "phylum": "",
        "class": "",
        "order": "",
        "family": "",
        "genus": "",
        "species": sci_name
    }
    
    ninja_chars = ninja_data.get("characteristics", {}) if ninja_data else {}
    ninja_taxonomy = ninja_data.get("taxonomy", {}) if ninja_data else {}
    
    if inat_classification:
        for key in classification.keys():
            if key != "species":
                classification[key] = inat_classification.get(key, "")
    elif wikidata_enhanced.get("taxonomy"):
        for key in classification.keys():
            if key != "species":
                classification[key] = wikidata_enhanced.get("taxonomy", {}).get(key, "")
    elif ninja_taxonomy:
        for key in classification.keys():
            if key != "species":
                classification[key] = ninja_taxonomy.get(key, "")
    
    print(f"\n📋 Classification: {classification}")
    
    # ===== Conservation Status - Priority: Wikidata > Wikipedia > Ninja =====
    conservation_status = get_first_non_empty(
        wikidata_enhanced.get("conservation", {}).get("status"),
        wiki_conservation_status,
        ninja_chars.get("conservation_status"),
        _extract_conservation_from_wikipedia_sections(wiki_sections)
    )
    
    if not conservation_status:
        conservation_status = "Unknown"
    
    print(f"\n🛡️  Conservation Status: {conservation_status}")
    
    # ===== Physical Data - Priority: Ninja > Wikipedia > EOL =====
    physical = {
        "weight": get_first_non_empty(
            ninja_chars.get("weight", ""),
            wiki_stats.get("weight", "") if (wiki_stats := extract_stats_with_context(wiki_sections, name, sci_name)) else ""
        ),
        "length": get_first_non_empty(
            ninja_chars.get("length", ""),
            wiki_stats.get("length", "") if 'wiki_stats' in locals() else ""
        ),
        "height": get_first_non_empty(
            ninja_chars.get("height", ""),
            wiki_stats.get("height", "") if 'wiki_stats' in locals() else ""
        ),
        "top_speed": get_first_non_empty(
            ninja_chars.get("top_speed", ""),
            wiki_stats.get("top_speed", "") if 'wiki_stats' in locals() else ""
        ),
        "lifespan": get_first_non_empty(
            ninja_chars.get("lifespan", ""),
            eol_data.get("life_expectancy", ""),
            wiki_stats.get("lifespan", "") if 'wiki_stats' in locals() else ""
        )
    }
    
    print(f"\n💪 Physical Data: {physical}")
    
    # ===== Ecology - Multi-source merge with cleaning =====
    diet = get_first_non_empty(
        ninja_chars.get("diet", ""),
        wiki_diet if (wiki_diet := extract_diet_from_sections(wiki_sections)[0]) else "",
        eol_data.get("trophic_level", "")
    )
    diet = fix_diet_based_on_taxonomy(diet, classification)
    
    ninja_locations = ninja_data.get("locations", []) if ninja_data else []
    
    ecology = {
        "diet": diet,
        "habitat": get_first_non_empty(
            extract_clean_habitat(wiki_sections, gbif_data),
            ninja_chars.get("habitat", "")
        ),
        "locations": get_first_non_empty(
            extract_clean_locations(wiki_sections, gbif_data, ninja_locations),
        ),
        "group_behavior": get_first_non_empty(
            ninja_chars.get("group_behavior", ""),
            wiki_behavior if (wiki_behavior := extract_behavior_from_sections(wiki_sections)) else ""
        ),
        "conservation_status": conservation_status,
        "biggest_threat": get_first_non_empty(
            ninja_chars.get("biggest_threat", ""),
            wiki_threats if (wiki_threats := extract_conservation_from_sections(wiki_sections)[1]) else ""
        ),
        "distinctive_features": [ninja_chars.get("most_distinctive_feature")] if ninja_chars.get("most_distinctive_feature") else [],
        "population_trend": wikidata_enhanced.get("population", "")
    }
    
    print(f"\n🌍 Ecology: {ecology}")
    
    # ===== Reproduction - Priority: Ninja > Wikipedia =====
    reproduction = {
        "gestation_period": get_first_non_empty(
            ninja_chars.get("gestation_period", ""),
            wiki_repro.get("gestation_period", "") if (wiki_repro := extract_reproduction_from_sections(wiki_sections)) else ""
        ),
        "average_litter_size": get_first_non_empty(
            ninja_chars.get("average_litter_size", ""),
            wiki_repro.get("average_litter_size", "") if 'wiki_repro' in locals() else ""
        ),
        "name_of_young": get_first_non_empty(
            ninja_chars.get("name_of_young", ""),
            wiki_repro.get("name_of_young", "") if 'wiki_repro' in locals() else "",
            young_name
        )
    }
    
    print(f"\n👶 Reproduction: {reproduction}")
    
    # ===== Additional Info - Multi-source merge =====
    additional_info = {
        "lifestyle": ninja_chars.get("lifestyle", ""),
        "color": ninja_chars.get("color", ""),
        "skin_type": ninja_chars.get("skin_type", ""),
        "prey": get_first_non_empty(
            ninja_chars.get("prey", ""),
            wiki_prey if (wiki_prey := extract_diet_from_sections(wiki_sections)[1]) else ""
        ),
        "slogan": ninja_chars.get("slogan", ""),
        "group": get_first_non_empty(
            ninja_chars.get("group", ""),
            wiki_additional.get("group", "") if (wiki_additional := extract_additional_info_from_sections(wiki_sections)) else ""
        ),
        "number_of_species": get_first_non_empty(
            ninja_chars.get("number_of_species", ""),
            wiki_additional.get("number_of_species", "") if 'wiki_additional' in locals() else ""
        ),
        "estimated_population_size": get_first_non_empty(
            ninja_chars.get("estimated_population_size", ""),
            wikidata_enhanced.get("population", ""),
            wiki_additional.get("estimated_population_size", "") if 'wiki_additional' in locals() else ""
        ),
        "age_of_sexual_maturity": get_first_non_empty(
            ninja_chars.get("age_of_sexual_maturity", ""),
            wiki_additional.get("age_of_sexual_maturity", "") if 'wiki_additional' in locals() else ""
        ),
        "age_of_weaning": get_first_non_empty(
            ninja_chars.get("age_of_weaning", ""),
            wiki_additional.get("age_of_weaning", "") if 'wiki_additional' in locals() else ""
        ),
        "most_distinctive_feature": get_first_non_empty(
            ninja_chars.get("most_distinctive_feature", ""),
            wiki_additional.get("most_distinctive_feature", "") if 'wiki_additional' in locals() else ""
        )
    }
    
    print(f"\nℹ️  Additional Info: {additional_info}")
    
    # ===== Build Final Data Structure =====
    wiki_summary = {}  # Not used anymore with new fetcher
    
    data = {
        "id": qid,
        "name": name,
        "scientific_name": sci_name,
        "common_names": wikidata_enhanced.get("common_names", []),
        "description": get_first_non_empty(
            wikidata_enhanced.get("description", ""),
            wiki_summary.get("description", "") if wiki_summary else ""
        ),
        "summary": wiki_summary.get("summary", "") if wiki_summary else "",
        "image": wiki_summary.get("image", "") if wiki_summary else "",
        "images": wikidata_enhanced.get("images", []) + eol_data.get("images", []),
        "wikipedia_url": wiki_summary.get("url", "") if wiki_summary else "",
        "wikidata_url": f"https://www.wikidata.org/wiki/{qid}",
        "eol_url": eol_data.get("eol_url", ""),
        "gbif_key": gbif_data.get("gbif_key", ""),
        "wikipedia_sections": wiki_sections,
        "classification": classification,
        "animal_type": animal_type,
        "young_name": young_name,
        "group_name": get_group_name(animal_type),
        "physical": physical,
        "ecology": ecology,
        "reproduction": reproduction,
        "additional_info": additional_info,
        "distribution": {
            "countries": gbif_data.get("countries", []),
            "coordinates": gbif_data.get("coordinates", {}),
            "occurrence_count": gbif_data.get("occurrence_count", 0)
        },
        "sources": [],
        "last_updated": datetime.now().isoformat()
    }
    
    # ===== Track Sources =====
    if ninja_data is not None and ninja_data.get("characteristics"):
        data["sources"].append("API Ninjas")
    if wiki_sections:
        data["sources"].append("Wikipedia")
    if inat_classification:
        data["sources"].append("iNaturalist")
    if wikidata_enhanced:
        data["sources"].append("Wikidata")
    if gbif_data and gbif_data.get("countries"):
        data["sources"].append("GBIF")
    if eol_data and eol_data.get("page_id"):
        data["sources"].append("EOL")
    
    return data


# =============================================================================
# MAIN GENERATION
# =============================================================================
def generate(animals: List[Dict[str, str]], force: bool = False) -> List[Dict[str, Any]]:
    """Generate animal data from all sources"""
    output = []
    ninja_api_key = os.environ.get("API_NINJAS_KEY", "")
    
    total = len(animals)
    
    for i, a in enumerate(animals):
        name, sci, qid = a["name"], a["scientific_name"], a.get("qid", f"animal_{i}")
        
        print(f"\n{'='*80}")
        print(f"  [{i+1}/{total}] {name} ({sci})")
        print(f"{'='*80}")

        # ===== API Ninjas =====
        print("\n🥷 Fetching from Ninja API...")
        ninja_data = fetch_animal_data(name, ninja_api_key)
        
        if ninja_data is not None:
            chars = ninja_data.get("characteristics", {})
            print(f"   ✅ Got {len(chars)} fields from Ninja API")
            print(f"   Fields: {list(chars.keys())}")
        else:
            print(f"   ⚠️  No data from Ninja API for {name}")
            ninja_data = {"characteristics": {}, "taxonomy": {}, "locations": []}

        # ===== Wikipedia =====
        print("\n📖 Fetching from Wikipedia...")
        wiki_data = fetch_wikipedia_data(name)
        wiki_sections = wiki_data.get('sections', {})
        wiki_infobox = wiki_data.get('infobox', {})
        
        filled_sections = sum(1 for v in wiki_sections.values() if v and len(v) > 20)
        print(f"   ✅ Extracted {filled_sections} Wikipedia sections")
        print(f"   Section names: {list(wiki_sections.keys())}")
        
        # Show section content lengths
        print(f"   Section content lengths:")
        for section, content in list(wiki_sections.items())[:5]:
            length = len(content) if content else 0
            print(f"      - {section}: {length} chars")
        
        # ===== iNaturalist =====
        print("\n🔬 Fetching from iNaturalist...")
        inat_classification = fetch_inaturalist(sci)
        if inat_classification:
            print(f"   ✅ Got classification from iNaturalist")
            print(f"   Classification: {inat_classification}")
        else:
            print(f"   ⚠️  No classification from iNaturalist")
        
        # ===== Wikidata =====
        print("\n📊 Fetching from Wikidata...")
        wikidata_enhanced = extract_wikidata_all(qid, sci)
        if wikidata_enhanced:
            print(f"   ✅ Got Wikidata enhancements")
            print(f"   Keys: {list(wikidata_enhanced.keys())}")
            if wikidata_enhanced.get("conservation", {}).get("status"):
                print(f"      🏷️  Conservation: {wikidata_enhanced['conservation']['status']}")
        else:
            print(f"   ⚠️  No data from Wikidata")
            wikidata_enhanced = {}
        
        time.sleep(0.3)
        
        # ===== GBIF =====
        print("\n🌍 Fetching from GBIF...")
        gbif_data = extract_gbif_all(sci)
        if gbif_data and gbif_data.get("countries"):
            print(f"   ✅ Found in {len(gbif_data.get('countries', []))} countries")
            print(f"   Countries: {gbif_data.get('countries', [])[:5]}{'...' if len(gbif_data.get('countries', [])) > 5 else ''}")
        else:
            print(f"   ⚠️  Limited GBIF data")
            print(f"   GBIF keys: {list(gbif_data.keys()) if gbif_data else 'NONE'}")
        
        time.sleep(0.3)
        
        # ===== EOL =====
        print("\n📚 Fetching from EOL...")
        eol_data = extract_eol_all(sci)
        if eol_data and eol_data.get("page_id"):
            print(f"   ✅ Got EOL data (Page ID: {eol_data.get('page_id')})")
            print(f"   EOL keys: {list(eol_data.keys())}")
        else:
            print(f"   ⚠️  No data from EOL")
            eol_data = {}
        
        time.sleep(0.3)
        
        # ===== Build Animal Data =====
        data = build_animal_data(
            ninja_data=ninja_data,
            wiki_sections=wiki_sections,
            wiki_infobox=wiki_infobox,
            inat_classification=inat_classification,
            wikidata_enhanced=wikidata_enhanced,
            gbif_data=gbif_data,
            eol_data=eol_data,
            qid=qid,
            name=name,
            sci_name=sci
        )
        
        save_animal_file(data, name, qid)
        output.append(data)
        
        print(f"\n✅ {name} complete! Sources: {', '.join(data['sources'])}")
        print(f"   Physical: {data['physical']}")
        print(f"   Ecology: diet={data['ecology']['diet']}, conservation={data['ecology']['conservation_status']}")
        
        time.sleep(0.5)

    with open(DATA_DIR / "animals.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print(f"✅ Done! {len(output)} animals saved to {ANIMAL_STATS_DIR}/")
    print(f"📁 Combined file: {DATA_DIR / 'animals.json'}")
    print(f"📂 Debug logs: {DEBUG_DIR}/")
    print(f"{'='*80}")
    
    return output


# =============================================================================
# TEST ANIMALS
# =============================================================================
TEST_ANIMALS = [
    {"name": "Tiger", "scientific_name": "Panthera tigris", "qid": "Q132186"},
    {"name": "Cheetah", "scientific_name": "Acinonyx jubatus", "qid": "Q35625"},
    {"name": "African Elephant", "scientific_name": "Loxodonta africana", "qid": "Q7372"},
    {"name": "Gray Wolf", "scientific_name": "Canis lupus", "qid": "Q213537"},
    {"name": "Bald Eagle", "scientific_name": "Haliaeetus leucocephalus", "qid": "Q25319"},
    {"name": "Emperor Penguin", "scientific_name": "Aptenodytes forsteri", "qid": "Q43306"},
    {"name": "Great White Shark", "scientific_name": "Carcharodon carcharias", "qid": "Q47164"},
    {"name": "Atlantic Salmon", "scientific_name": "Salmo salar", "qid": "Q39709"},
    {"name": "Green Sea Turtle", "scientific_name": "Chelonia mydas", "qid": "Q7785"},
    {"name": "King Cobra", "scientific_name": "Ophiophagus hannah", "qid": "Q189609"},
    {"name": "American Bullfrog", "scientific_name": "Lithobates catesbeianus", "qid": "Q270238"},
    {"name": "Monarch Butterfly", "scientific_name": "Danaus plexippus", "qid": "Q165980"},
    {"name": "Honey Bee", "scientific_name": "Apis mellifera", "qid": "Q7316"},
]

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    force = "--force" in sys.argv
    generate(TEST_ANIMALS, force)
