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
from modules.fetchers.wikipedia import fetch_wikipedia_summary, fetch_wikipedia_full
from modules.fetchers.inaturalist import fetch_inaturalist
from modules.fetchers.wikidata import fetch_wikidata_properties
from modules.fetchers.gbif_distribution import fetch_gbif_distribution
from modules.fetchers.eol_data import fetch_eol_data
from modules.fetchers.iucn_redlist import fetch_iucn_status

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

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(ANIMAL_STATS_DIR, exist_ok=True)

CONFIG_DIR = GENERATOR_DIR / "config"

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
    name: str,
    sci_name: str,
    qid: str,
    force: bool = False
) -> Dict[str, Any]:
    """Build complete animal data with proper source priority"""
    
    print(f"======================================================================")
    print(f"[{current}/{total}] {name} ({sci_name})")
    print(f"======================================================================")
    
    # ===== Fetch from all sources =====
    
    # 1. API Ninjas (already working)
    print(" 🥷 Fetching from Ninja API...")
    ninja_data = fetch_from_ninja_api(name)
    
    # 2. Wikipedia (NEW - with infobox)
    print(" 📖 Fetching from Wikipedia...")
    wiki_data = fetch_wikipedia_data(name)  # Now returns sections + infobox
    wiki_sections = wiki_data.get('sections', {})
    wiki_infobox = wiki_data.get('infobox', {})
    
    # 3. Wikidata (NEW - with P2067 mass)
    print(" 📊 Fetching from Wikidata...")
    wikidata_data = fetch_wikidata_properties(qid) if qid else {}
    
    # 4. Other sources (iNaturalist, GBIF, EOL) - unchanged
    print(" 🔬 Fetching from iNaturalist...")
    inat_data = fetch_inaturalist(sci_name)
    
    print(" 🌍 Fetching from GBIF...")
    gbif_data = fetch_gbif(sci_name)
    
    print(" 📚 Fetching from EOL...")
    eol_data = fetch_eol(sci_name)
    
    # ===== Extract stats with proper priority =====
    print(" 📊 Extracting physical stats...")
    
    # Prepare API Ninjas physical data
    api_ninjas_physical = {}
    if ninja_data:
        physical = ninja_data.get('physical', {})
        api_ninjas_physical = {
            'weight': physical.get('weight', ''),
            'length': physical.get('length', ''),
            'height': physical.get('height', ''),
            'lifespan': physical.get('lifespan', ''),
            'top_speed': physical.get('top_speed', ''),
        }
    
    # Extract with priority: Infobox > Wikidata > API Ninjas > Text
    physical_stats = extract_stats_with_context(
        sections=wiki_sections,
        animal_name=name,
        scientific_name=sci_name,
        infobox_data=wiki_infobox,
        wikidata_data=wikidata_data,
        api_ninjas_data=api_ninjas_physical
    )
    
    # ===== Build final data structure =====
    data = {
        'id': qid,
        'name': name,
        'scientific_name': sci_name,
        'physical': physical_stats,
        'sources': build_sources_list(
            has_ninja=bool(ninja_data),
            has_wiki=bool(wiki_data),
            has_wikidata=bool(wikidata_data),
            has_inat=bool(inat_data),
            has_gbif=bool(gbif_data),
            has_eol=bool(eol_data)
        ),
        # ... rest of data structure
    }
    
    return data


def build_sources_list(
    has_ninja: bool = False,
    has_wiki: bool = False,
    has_wikidata: bool = False,
    has_inat: bool = False,
    has_gbif: bool = False,
    has_eol: bool = False
) -> list:
    """Build list of data sources used"""
    sources = []
    if has_ninja:
        sources.append("API Ninjas")
    if has_wiki:
        sources.append("Wikipedia")
    if has_wikidata:
        sources.append("Wikidata")
    if has_inat:
        sources.append("iNaturalist")
    if has_gbif:
        sources.append("GBIF")
    if has_eol:
        sources.append("EOL")
    return sources
    
    # =============================================================================
    # ANIMAL TYPE DETECTION
    # =============================================================================
    animal_type = "default"
    taxonomy_to_use = inat_classification if inat_classification else ninja_taxonomy
    
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
    
    young_name = ninja_chars.get("name_of_young", "") or get_young_name(animal_type)
    
    # =============================================================================
    # WIKIPEDIA EXTRACTIONS (Fallback)
    # =============================================================================
    # Use enhanced stats extraction with animal name for better validation
    wiki_stats = extract_stats_with_context(wiki_sections, name, sci_name)
    wiki_diet, wiki_prey = extract_diet_from_sections(wiki_sections)
    wiki_repro = extract_reproduction_from_sections(wiki_sections)
    wiki_conservation_status, wiki_threats = extract_conservation_from_sections(wiki_sections)
    wiki_behavior = extract_behavior_from_sections(wiki_sections)
    wiki_additional = extract_additional_info_from_sections(wiki_sections)
    
    # =============================================================================
    # CLASSIFICATION - Priority: iNaturalist > Wikidata > Ninja > Wikipedia
    # =============================================================================
    classification = {
        "kingdom": "",
        "phylum": "",
        "class": "",
        "order": "",
        "family": "",
        "genus": "",
        "species": sci_name
    }
    
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
    
    # =============================================================================
    # CONSERVATION STATUS - Priority: Wikidata > Wikipedia > Ninja > Fallback
    # =============================================================================
    conservation_status = get_first_non_empty(
        wikidata_enhanced.get("conservation", {}).get("status"),
        wiki_conservation_status,
        ninja_chars.get("conservation_status"),
        _extract_conservation_from_wikipedia_sections(wiki_sections)
    )
    
    if not conservation_status:
        conservation_status = "Unknown"
    
    # =============================================================================
    # PHYSICAL DATA - Priority: Ninja > Wikipedia > EOL
    # =============================================================================
    physical = {
        "weight": get_first_non_empty(
            ninja_chars.get("weight", ""),
            wiki_stats.get("weight", "")
        ),
        "length": get_first_non_empty(
            ninja_chars.get("length", ""),
            wiki_stats.get("length", "")
        ),
        "height": get_first_non_empty(
            ninja_chars.get("height", ""),
            wiki_stats.get("height", "")
        ),
        "top_speed": get_first_non_empty(
            ninja_chars.get("top_speed", ""),
            wiki_stats.get("top_speed", "")
        ),
        "lifespan": get_first_non_empty(
            ninja_chars.get("lifespan", ""),
            eol_data.get("life_expectancy", ""),
            wiki_stats.get("lifespan", "")
        )
    }
    
    # =============================================================================
    # ECOLOGY - Multi-source merge with cleaning
    # =============================================================================
    diet = get_first_non_empty(
        ninja_chars.get("diet", ""),
        wiki_diet,
        eol_data.get("trophic_level", "")
    )
    diet = fix_diet_based_on_taxonomy(diet, classification)
    
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
            wiki_behavior
        ),
        "conservation_status": conservation_status,
        "biggest_threat": get_first_non_empty(
            ninja_chars.get("biggest_threat", ""),
            wiki_threats
        ),
        "distinctive_features": [ninja_chars.get("most_distinctive_feature")] if ninja_chars.get("most_distinctive_feature") else [],
        "population_trend": wikidata_enhanced.get("population", "")
    }
    
    # =============================================================================
    # REPRODUCTION - Priority: Ninja > Wikipedia
    # =============================================================================
    reproduction = {
        "gestation_period": get_first_non_empty(
            ninja_chars.get("gestation_period", ""),
            wiki_repro.get("gestation_period", "")
        ),
        "average_litter_size": get_first_non_empty(
            ninja_chars.get("average_litter_size", ""),
            wiki_repro.get("average_litter_size", "")
        ),
        "name_of_young": get_first_non_empty(
            ninja_chars.get("name_of_young", ""),
            wiki_repro.get("name_of_young", ""),
            young_name
        )
    }
    
    # =============================================================================
    # ADDITIONAL INFO - Multi-source merge
    # =============================================================================
    additional_info = {
        "lifestyle": ninja_chars.get("lifestyle", ""),
        "color": ninja_chars.get("color", ""),
        "skin_type": ninja_chars.get("skin_type", ""),
        "prey": get_first_non_empty(
            ninja_chars.get("prey", ""),
            wiki_prey
        ),
        "slogan": ninja_chars.get("slogan", ""),
        "group": get_first_non_empty(
            ninja_chars.get("group", ""),
            wiki_additional.get("group", "")
        ),
        "number_of_species": get_first_non_empty(
            ninja_chars.get("number_of_species", ""),
            wiki_additional.get("number_of_species", "")
        ),
        "estimated_population_size": get_first_non_empty(
            ninja_chars.get("estimated_population_size", ""),
            wikidata_enhanced.get("population", ""),
            wiki_additional.get("estimated_population_size", "")
        ),
        "age_of_sexual_maturity": get_first_non_empty(
            ninja_chars.get("age_of_sexual_maturity", ""),
            wiki_additional.get("age_of_sexual_maturity", "")
        ),
        "age_of_weaning": get_first_non_empty(
            ninja_chars.get("age_of_weaning", ""),
            wiki_additional.get("age_of_weaning", "")
        ),
        "most_distinctive_feature": get_first_non_empty(
            ninja_chars.get("most_distinctive_feature", ""),
            wiki_additional.get("most_distinctive_feature", "")
        )
    }
    
    # =============================================================================
    # BUILD FINAL DATA STRUCTURE
    # =============================================================================
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
    
    # =============================================================================
    # TRACK SOURCES
    # =============================================================================
    if ninja_data is not None and ninja_data.get("characteristics"):
        data["sources"].append("API Ninjas")
    if wiki_summary and wiki_summary.get("summary"):
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
        
        print(f"\n{'='*70}")
        print(f"[{i+1}/{total}] {name} ({sci})")
        print(f"{'='*70}")

        print(" 🥷 Fetching from Ninja API...")
        ninja_data = fetch_animal_data(name, ninja_api_key)
        
        if ninja_data is not None:
            chars = ninja_data.get("characteristics", {})
            print(f"   ✅ Got {len(chars)} fields from Ninja API")
        else:
            print(f"   ⚠ No data from Ninja API for {name}")
            ninja_data = {"characteristics": {}, "taxonomy": {}, "locations": []}

        print(" 📖 Fetching from Wikipedia...")
        wiki_summary = fetch_wikipedia_summary(name)
        wiki_full = fetch_wikipedia_full(name)
        wiki_sections = extract_wikipedia_sections(wiki_full)
        
        filled_sections = sum(1 for v in wiki_sections.values() if v and len(v) > 20)
        print(f"   ✅ Extracted {filled_sections}/9 Wikipedia sections")
        
        print(" 🔬 Fetching from iNaturalist...")
        inat_classification = fetch_inaturalist(sci)
        if inat_classification:
            print(f"   ✅ Got classification from iNaturalist")
        else:
            print(f"   ⚠ No classification from iNaturalist")
        
        print(" 📊 Fetching from Wikidata...")
        wikidata_enhanced = extract_wikidata_all(qid, sci)
        if wikidata_enhanced:
            print(f"   ✅ Got Wikidata enhancements")
            if wikidata_enhanced.get("conservation", {}).get("status"):
                print(f"      🏷 Conservation: {wikidata_enhanced['conservation']['status']}")
        else:
            print(f"   ⚠ No data from Wikidata")
            wikidata_enhanced = {}
        
        time.sleep(0.3)
        
        print(" 🌍 Fetching from GBIF...")
        gbif_data = extract_gbif_all(sci)
        if gbif_data and gbif_data.get("countries"):
            print(f"   ✅ Found in {len(gbif_data.get('countries', []))} countries")
        else:
            print(f"   ⚠ Limited GBIF data")
        
        time.sleep(0.3)
        
        print(" 📚 Fetching from EOL...")
        eol_data = extract_eol_all(sci)
        if eol_data and eol_data.get("page_id"):
            print(f"   ✅ Got EOL data (Page ID: {eol_data.get('page_id')})")
        else:
            print(f"   ⚠ No data from EOL")
        
        time.sleep(0.3)
        
        data = build_animal_data(
            ninja_data, 
            wiki_summary, 
            wiki_sections, 
            inat_classification,
            wikidata_enhanced,
            gbif_data,
            eol_data,
            qid, 
            name, 
            sci
        )
        
        save_animal_file(data, name, qid)
        output.append(data)
        
        print(f" ✅ {name} complete! Sources: {', '.join(data['sources'])}")
        time.sleep(0.5)

    with open(DATA_DIR / "animals.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*70}")
    print(f"✅ Done! {len(output)} animals saved to {ANIMAL_STATS_DIR}/")
    print(f"📁 Combined file: {DATA_DIR / 'animals.json'}")
    print(f"{'='*70}")
    
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
