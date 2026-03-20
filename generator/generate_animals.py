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
from typing import Dict, Any, List, Optional, Tuple

# =============================================================================
# PATH SETUP
# =============================================================================
GENERATOR_DIR = Path(__file__).parent
sys.path.insert(0, str(GENERATOR_DIR))

# =============================================================================
# IMPORTS - Data Fetchers
# =============================================================================
from modules.fetchers.api_ninjas import fetch_animal_data
from modules.fetchers.wikipedia import fetch_wikipedia_data
from modules.fetchers.inaturalist import fetch_inaturalist
from modules.fetchers.gbif_distribution import extract_gbif_all
from modules.fetchers.eol_data import extract_eol_all

# =============================================================================
# IMPORTS - Extractors (including Wikidata)
# =============================================================================
from modules.extractors.stats import extract_stats_with_context
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

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def get_first_non_empty(*values) -> str:
    """Return first non-empty string from values"""
    for v in values:
        if v and isinstance(v, str) and v.strip():
            return v.strip()
    return ""

def clean_wikipedia_text(text: str) -> str:
    """Clean messy Wikipedia text"""
    if not text: 
        return ""
    text = re.sub(r'\[\d+\]', '', text)
    text = ' '.join(text.split())
    return text.strip() if len(text) > 20 else ""

def fix_diet_based_on_taxonomy(diet: str, classification: Dict[str, str]) -> str:
    """Fix obvious diet errors based on taxonomy"""
    if not diet: 
        return diet
    diet_lower = diet.lower()
    family = classification.get("family", "").lower()
    if "elephantidae" in family and "carnivore" in diet_lower: 
        return "Herbivore"
    if "cheloniidae" in family and "carnivore" in diet_lower: 
        return "Herbivore"
    return diet

def get_animal_filename(name: str, qid: str) -> str:
    """Generate clean filename for animal data"""
    clean_name = name.lower().replace(' ', '_').replace('-', '_').replace("'", "")
    return f"{clean_name}_{{QID={qid}}}.json"

def get_young_name(animal_type: str, ninja_data: Dict) -> str:
    """Get young animal name - priority: Ninja > Extracted > Fallback"""
    ninja_young = ninja_data.get("characteristics", {}).get("name_of_young", "")
    if ninja_young:
        return ninja_young
    
    fallbacks = {
        "feline": "cub",
        "canine": "pup", 
        "bear": "cub",
        "elephant": "calf",
        "bird": "chick",
        "fish": "fry",
        "reptile": "hatchling",
        "amphibian": "tadpole",
        "insect": "larva"
    }
    return fallbacks.get(animal_type, "young")

def get_group_name(animal_type: str, ninja_data: Dict) -> str:
    """Get group name - priority: Ninja > Fallback"""
    ninja_group = ninja_data.get("characteristics", {}).get("group", "")
    if ninja_group:
        return ninja_group
    
    fallbacks = {
        "feline": "pride",
        "canine": "pack",
        "bear": "sleuth",
        "elephant": "herd",
        "bird": "flock",
        "fish": "school",
        "insect": "colony"
    }
    return fallbacks.get(animal_type, "group")

def get_group_behavior(animal_type: str, ninja_data: Dict, wiki_behavior: str) -> str:
    """Get group behavior with smart fallbacks"""
    # Priority 1: Ninja API
    ninja_behavior = ninja_data.get("characteristics", {}).get("group_behavior", "")
    if ninja_behavior:
        return ninja_behavior
    
    # Priority 2: Wiki extraction
    if wiki_behavior and len(wiki_behavior) > 3:
        return wiki_behavior
    
    # Priority 3: Taxonomy-based defaults
    behavior_defaults = {
        "feline": "Solitary (except lions)",
        "canine": "Pack",
        "bear": "Solitary",
        "elephant": "Herd",
        "bird": "Flock",
        "fish": "School",
        "insect": "Colony",
        "reptile": "Solitary",
        "amphibian": "Solitary"
    }
    return behavior_defaults.get(animal_type, "Solitary")

def get_habitat(gbif_data: Dict, wiki_sections: Dict, ninja_chars: Dict) -> str:
    """Get habitat with proper fallback chain"""
    # Priority 1: GBIF habitat
    if gbif_data and gbif_data.get("habitat"):
        habitat = clean_wikipedia_text(gbif_data.get("habitat", ""))
        if len(habitat) > 20:
            return habitat
    
    # Priority 2: Wikipedia habitat section
    wiki_habitat = wiki_sections.get("habitat", "")
    if wiki_habitat:
        habitat = clean_wikipedia_text(wiki_habitat)
        if len(habitat) > 20:
            return habitat
    
    # Priority 3: Wikipedia ecology/distribution section
    for section_name in ["ecology", "distribution", "habitat_and_distribution"]:
        if section_name in wiki_sections:
            habitat = clean_wikipedia_text(wiki_sections[section_name][:500])
            if len(habitat) > 20:
                return habitat
    
    # Priority 4: Ninja API
    ninja_habitat = ninja_chars.get("habitat", "")
    if ninja_habitat and len(ninja_habitat) > 10:
        return ninja_habitat
    
    return ""

# =============================================================================
# DEBUG SUMMARY CLASS
# =============================================================================
class DebugSummary:
    def __init__(self, name: str, qid: str):
        self.name = name
        self.qid = qid
        self.start_time = datetime.now()
        self.sources_used = []
        self.warnings = []
        
        self.inputs = {
            "ninja": {},
            "wiki_sections": {},
            "wiki_infobox": {},
            "inat": {},
            "wikidata": {},
            "gbif": {},
            "eol": {}
        }
        
        self.extractions = {}
        self.final_data = {}

    def add_warning(self, msg: str):
        self.warnings.append(msg)

    def log_source(self, source: str):
        if source not in self.sources_used:
            self.sources_used.append(source)

    def save(self):
        clean_name = self.name.lower().replace(' ', '_').replace('-', '_').replace("'", "")
        filepath = DEBUG_DIR / f"{clean_name}_{self.qid}_summary.json"
        
        report = {
            "meta": {
                "name": self.name,
                "qid": self.qid,
                "timestamp": self.start_time.isoformat(),
                "duration": str(datetime.now() - self.start_time),
                "sources_used": self.sources_used,
                "warnings": self.warnings
            },
            "inputs_summary": {
                "ninja_fields": list(self.inputs["ninja"].get("characteristics", {}).keys()) if self.inputs["ninja"] else [],
                "wiki_sections_count": len(self.inputs["wiki_sections"]),
                "wikidata_keys": list(self.inputs["wikidata"].keys()) if self.inputs["wikidata"] else [],
                "gbif_countries": self.inputs["gbif"].get("countries", []) if self.inputs["gbif"] else []
            },
            "extraction_comparison": self.extractions,
            "final_result": self.final_data
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        return filepath

# =============================================================================
# DATA BUILDING LOGIC
# =============================================================================
def build_animal_data(debug: DebugSummary, name: str, sci_name: str, qid: str) -> Dict[str, Any]:
    
    # 1. Prepare Inputs
    ninja_data = debug.inputs["ninja"]
    wiki_sections = debug.inputs["wiki_sections"]
    wiki_infobox = debug.inputs["wiki_infobox"]
    inat_class = debug.inputs["inat"]
    wikidata_enh = debug.inputs["wikidata"]
    gbif_data = debug.inputs["gbif"]
    eol_data = debug.inputs["eol"]

    ninja_chars = ninja_data.get("characteristics", {}) if ninja_data else {}
    ninja_locs = ninja_data.get("locations", []) if ninja_data else []

    # 2. Perform Extractions
    wiki_stats = extract_stats_with_context(wiki_sections, name, sci_name)
    
    debug.extractions["physical_stats"] = {
        "wiki_raw": wiki_stats,
        "ninja_raw": {k: ninja_chars.get(k, "") for k in ['weight', 'length', 'height', 'lifespan', 'top_speed']}
    }

    wiki_diet, wiki_prey = extract_diet_from_sections(wiki_sections)
    wiki_repro = extract_reproduction_from_sections(wiki_sections)
    wiki_cons_status, wiki_threats = extract_conservation_from_sections(wiki_sections)
    wiki_behavior = extract_behavior_from_sections(wiki_sections)
    wiki_additional = extract_additional_info_from_sections(wiki_sections)

    # 3. Determine Animal Type
    animal_type = "default"
    taxonomy_to_use = inat_class if inat_class else {}
    if taxonomy_to_use:
        family = taxonomy_to_use.get("family", "").lower()
        class_name = taxonomy_to_use.get("class", "").lower()
        
        if "felidae" in family: 
            animal_type = "feline"
        elif "canidae" in family: 
            animal_type = "canine"
        elif "ursidae" in family: 
            animal_type = "bear"
        elif "elephantidae" in family: 
            animal_type = "elephant"
        elif "aves" in class_name:
            animal_type = "bird"
        elif "reptilia" in class_name:
            animal_type = "reptile"
        elif "amphibia" in class_name:
            animal_type = "amphibian"
        elif "insecta" in class_name:
            animal_type = "insect"
        elif "actinopterygii" in class_name or "chondrichthyes" in class_name:
            animal_type = "fish"

    # 4. Build Classification
    classification = {"kingdom": "", "phylum": "", "class": "", "order": "", "family": "", "genus": "", "species": sci_name}
    if inat_class:
        for k in classification.keys():
            if k != "species": 
                classification[k] = inat_class.get(k, "")
    elif wikidata_enh.get("taxonomy"):
        for k in classification.keys():
            if k != "species": 
                classification[k] = wikidata_enh.get("taxonomy", {}).get(k, "")
    
    # 5. Merge Final Fields
    physical = {
        "weight": get_first_non_empty(ninja_chars.get("weight"), wiki_stats.get("weight")),
        "length": get_first_non_empty(ninja_chars.get("length"), wiki_stats.get("length")),
        "height": get_first_non_empty(ninja_chars.get("height"), wiki_stats.get("height")),
        "top_speed": get_first_non_empty(ninja_chars.get("top_speed"), wiki_stats.get("top_speed")),
        "lifespan": get_first_non_empty(ninja_chars.get("lifespan"), eol_data.get("life_expectancy"), wiki_stats.get("lifespan"))
    }

    debug.extractions["physical_sources"] = {
        "weight": "Ninja" if ninja_chars.get("weight") else ("Wiki" if wiki_stats.get("weight") else "None"),
        "length": "Ninja" if ninja_chars.get("length") else ("Wiki" if wiki_stats.get("length") else "None"),
        "height": "Ninja" if ninja_chars.get("height") else ("Wiki" if wiki_stats.get("height") else "None"),
        "top_speed": "Ninja" if ninja_chars.get("top_speed") else ("Wiki" if wiki_stats.get("top_speed") else "None"),
        "lifespan": "Ninja" if ninja_chars.get("lifespan") else ("EOL" if eol_data.get("life_expectancy") else ("Wiki" if wiki_stats.get("lifespan") else "None"))
    }

    # Ecology
    diet = get_first_non_empty(ninja_chars.get("diet"), wiki_diet, eol_data.get("trophic_level"))
    diet = fix_diet_based_on_taxonomy(diet, classification)
    habitat = get_habitat(gbif_data, wiki_sections, ninja_chars)
    
    locations = ""
    if gbif_data and gbif_data.get("countries"):
        locations = ", ".join(gbif_data.get("countries", []))
    elif ninja_locs:
        locations = ", ".join(ninja_locs)
    else:
        locations = clean_wikipedia_text(wiki_sections.get("distribution", ""))

    conservation_status = get_first_non_empty(
        wikidata_enh.get("conservation", {}).get("status"),
        wiki_cons_status,
        ninja_chars.get("conservation_status")
    ) or "Unknown"

    group_behavior = get_group_behavior(animal_type, ninja_data, wiki_behavior)

    ecology = {
        "diet": diet,
        "habitat": habitat,
        "locations": locations,
        "group_behavior": group_behavior,
        "conservation_status": conservation_status,
        "biggest_threat": get_first_non_empty(ninja_chars.get("biggest_threat"), wiki_threats),
        "distinctive_features": [ninja_chars.get("most_distinctive_feature")] if ninja_chars.get("most_distinctive_feature") else [],
        "population_trend": wikidata_enh.get("population", "")
    }

    # Reproduction
    young_name = get_young_name(animal_type, ninja_data)
    group_name = get_group_name(animal_type, ninja_data)
    
    reproduction = {
        "gestation_period": get_first_non_empty(ninja_chars.get("gestation_period"), wiki_repro.get("gestation_period")),
        "average_litter_size": get_first_non_empty(ninja_chars.get("average_litter_size"), wiki_repro.get("average_litter_size")),
        "name_of_young": young_name
    }

    # Additional
    additional_info = {
        "lifestyle": ninja_chars.get("lifestyle", ""),
        "color": ninja_chars.get("color", ""),
        "skin_type": ninja_chars.get("skin_type", ""),
        "prey": get_first_non_empty(ninja_chars.get("prey"), wiki_prey),
        "slogan": ninja_chars.get("slogan", ""),
        "group": group_name,
        "number_of_species": get_first_non_empty(ninja_chars.get("number_of_species"), wiki_additional.get("number_of_species")),
        "estimated_population_size": get_first_non_empty(ninja_chars.get("estimated_population_size"), wikidata_enh.get("population"), wiki_additional.get("estimated_population_size")),
        "most_distinctive_feature": get_first_non_empty(ninja_chars.get("most_distinctive_feature"), wiki_additional.get("most_distinctive_feature"))
    }

    # Sources Tracking
    if ninja_data and ninja_data.get("characteristics"): 
        debug.log_source("API Ninjas")
    if wiki_sections: 
        debug.log_source("Wikipedia")
    if inat_class: 
        debug.log_source("iNaturalist")
    if wikidata_enh: 
        debug.log_source("Wikidata")
    if gbif_data and gbif_data.get("countries"): 
        debug.log_source("GBIF")
    if eol_data and eol_data.get("page_id"): 
        debug.log_source("EOL")

    # =============================================================================
    # FIX: Image Handling - Direct URLs from Wikidata
    # =============================================================================
    all_images = wikidata_enh.get("images", []) + eol_data.get("images", [])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_images = []
    for img in all_images:
        if img and img.strip() and img not in seen:
            seen.add(img)
            unique_images.append(img)
    
    # Set primary image (first valid image)
    primary_image = unique_images[0] if unique_images else ""

    # =============================================================================
    # Construct Final Object
    # =============================================================================
    final_data = {
        "id": qid,
        "name": name,
        "scientific_name": sci_name,
        "common_names": wikidata_enh.get("common_names", []),
        "summary": get_first_non_empty(wikidata_enh.get("description", "")),
        "description": get_first_non_empty(wikidata_enh.get("description", "")),
        # Single 'image' field for frontend
        "image": primary_image,
        "images": unique_images,
        # FIXED: No spaces in URLs
        "wikipedia_url": f"https://en.wikipedia.org/wiki/{name.replace(' ', '_')}",
        "wikidata_url": f"https://www.wikidata.org/wiki/{qid}",
        "eol_url": eol_data.get("eol_url", ""),
        "classification": classification,
        "animal_type": animal_type,
        "young_name": young_name,
        "group_name": group_name,
        "physical": physical,
        "ecology": ecology,
        "reproduction": reproduction,
        "additional_info": additional_info,
        "distribution": {
            "countries": gbif_data.get("countries", []),
            "coordinates": gbif_data.get("coordinates", {}),
            "occurrence_count": gbif_data.get("occurrence_count", 0)
        },
        "sources": debug.sources_used,
        "last_updated": datetime.now().isoformat()
    }

    debug.final_data = final_data
    return final_data

# =============================================================================
# PRINT HELPERS
# =============================================================================
def print_data_table(final_data: Dict, debug: DebugSummary) -> None:
    """Print complete data overview table"""
    print(f"\n📊 COMPLETE DATA OVERVIEW:")
    print(f"   {'Category':<20} | {'Field':<22} | {'Value':<35} | {'Source'}")
    print(f"   {'-'*20}-+-{'-'*22}-+-{'-'*35}-+-{'-'*10}")
    
    p = final_data['physical']
    ps = debug.extractions.get('physical_sources', {})
    physical_fields = [
        ('Weight', p['weight']),
        ('Length', p['length']),
        ('Height', p['height']),
        ('Top Speed', p['top_speed']),
        ('Lifespan', p['lifespan'])
    ]
    for field, value in physical_fields:
        src = ps.get(field.lower().replace(' ', '_'), 'None')
        display_val = value[:33] + '...' if len(str(value)) > 35 else str(value)
        print(f"   {'Physical':<20} | {field:<22} | {display_val:<35} | {src}")
    
    e = final_data['ecology']
    es = debug.extractions.get('ecology_sources', {})
    ecology_fields = [
        ('Diet', e['diet']),
        ('Habitat', e['habitat'][:33] + '...' if len(e['habitat']) > 35 else e['habitat']),
        ('Conservation', e['conservation_status']),
        ('Group Behavior', e['group_behavior'][:33] + '...' if len(str(e['group_behavior'])) > 35 else str(e['group_behavior'])),
        ('Biggest Threat', e['biggest_threat'][:33] + '...' if len(str(e['biggest_threat'])) > 35 else str(e['biggest_threat']))
    ]
    for field, value in ecology_fields:
        key = field.lower().replace(' ', '_')
        src = es.get(key, 'None')
        print(f"   {'Ecology':<20} | {field:<22} | {value:<35} | {src}")
    
    d = final_data['distribution']
    print(f"   {'Distribution':<20} | {'Countries':<22} | {len(d['countries'])} countries{'':<24} | GBIF")
    print(f"   {'Distribution':<20} | {'Occurrences':<22} | {d['occurrence_count']}{'':<30} | GBIF")

# =============================================================================
# MAIN GENERATION LOOP
# =============================================================================
def generate(animals: List[Dict[str, str]], force: bool = False) -> List[Dict[str, Any]]:
    output = []
    ninja_api_key = os.environ.get("API_NINJAS_KEY", "")
    total = len(animals)

    for i, a in enumerate(animals):
        name, sci, qid = a["name"], a["scientific_name"], a.get("qid", f"animal_{i}")
        debug = DebugSummary(name, qid)
        
        print(f"\n{'='*80}")
        print(f"[{i+1}/{total}] {name} ({sci})")
        print(f"{'='*80}")

        try:
            # Ninja
            print(f"   🔍 Searching Ninja API for: {name}")
            ninja_data = fetch_animal_data(name, ninja_api_key) or {"characteristics": {}, "taxonomy": {}, "locations": []}
            debug.inputs["ninja"] = ninja_data
            if ninja_data:
                chars = ninja_data.get("characteristics", {})
                if chars:
                    print(f"   ✓ Found {len(chars)} fields from Ninja API")
            
            # Wikipedia
            print(f"   📖 Fetching Wikipedia data for: {name}")
            wiki_data = fetch_wikipedia_data(name)
            wiki_sections = wiki_data.get('sections', {})
            wiki_infobox = wiki_data.get('infobox', {})
            debug.inputs["wiki_sections"] = wiki_sections
            debug.inputs["wiki_infobox"] = wiki_infobox
            if wiki_sections:
                print(f"   ✓ Found {len(wiki_sections)} Wikipedia sections")
            else:
                debug.add_warning("No Wikipedia sections found")

            # iNaturalist
            inat_class = fetch_inaturalist(sci) or {}
            debug.inputs["inat"] = inat_class
            if inat_class:
                print(f"   ✓ Got classification from iNaturalist")

            # Wikidata
            wikidata_enh = extract_wikidata_all(qid, sci) or {}
            debug.inputs["wikidata"] = wikidata_enh
            if wikidata_enh:
                print(f"   ✓ Got Wikidata enhancements")

            time.sleep(0.2)

            # GBIF
            gbif_data = extract_gbif_all(sci) or {}
            debug.inputs["gbif"] = gbif_data
            if gbif_data and gbif_data.get("countries"):
                print(f"   ✓ Found in {len(gbif_data.get('countries', []))} countries via GBIF")

            time.sleep(0.2)

            # EOL
            eol_data = extract_eol_all(sci) or {}
            debug.inputs["eol"] = eol_data
            if eol_data and eol_data.get("page_id"):
                print(f"   ✓ Got EOL data (Page ID: {eol_data.get('page_id')})")

            # Build
            final_data = build_animal_data(debug, name, sci, qid)
            
            # Save
            filename = get_animal_filename(name, qid)
            filepath = ANIMAL_STATS_DIR / filename
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(final_data, f, indent=2, ensure_ascii=False)

            summary_path = debug.save()

            print(f"\n✅ COMPLETE | Sources: {', '.join(debug.sources_used)}")
            if debug.warnings:
                print(f"   ⚠️  Warnings: {'; '.join(debug.warnings)}")
            
            print_data_table(final_data, debug)

            print(f"\n💾 Files Saved:")
            print(f"   📄 Data: {filepath.name}")
            print(f"   🐞 Debug: {summary_path.name}")

            output.append(final_data)

        except Exception as ex:
            print(f"\n❌ ERROR processing {name}: {str(ex)}")
            debug.add_warning(f"Critical Error: {str(ex)}")
            debug.save()
            continue

        time.sleep(0.3)

    # Save Combined
    combined_path = DATA_DIR / "animals.json"
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print(f"🎉 GENERATION FINISHED")
    print(f"   Total Animals: {len(output)}")
    print(f"   Combined Data: {combined_path}")
    print(f"   Debug Logs: {DEBUG_DIR}/")
    print(f"{'='*80}\n")
    
    return output

# =============================================================================
# TEST DATA
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

if __name__ == "__main__":
    force = "--force" in sys.argv
    generate(TEST_ANIMALS, force)
