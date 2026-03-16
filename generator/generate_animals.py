# generator/generate_animals.py
import requests, json, time, os, re, sys
from datetime import datetime
from pathlib import Path
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

sys.path.insert(0, str(Path(__file__).parent))
from modules.api_ninjas import fetch_animal_data

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data"
ANIMAL_STATS_DIR = DATA_DIR / "animal_stats"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(ANIMAL_STATS_DIR, exist_ok=True)

CONFIG_DIR = Path(__file__).parent / "config"

session = requests.Session()
retry = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retry))
headers = {"User-Agent": "WildAtlasBot/1.0 (contact@example.com)", "Accept": "application/json"}

WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
WIKI_MOBILE = "https://en.m.wikipedia.org/wiki/"
INAT_API = "https://api.inaturalist.org/v1/taxa"

CLASSIFICATION_FIELDS = ["kingdom", "phylum", "class", "order", "family", "genus", "species"]

# Load configs
def load_config(filename):
    config_path = CONFIG_DIR / filename
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

YOUNG_NAMES = load_config("young_names.json")
GROUP_NAMES = load_config("group_names.json")

def get_young_name(animal_type):
    return YOUNG_NAMES.get(animal_type, YOUNG_NAMES.get("default", "young"))

def get_group_name(animal_type):
    return GROUP_NAMES.get(animal_type, GROUP_NAMES.get("default", "population"))

# Wikipedia
def fetch_wikipedia_summary(name):
    try:
        r = session.get(f"{WIKI_API}{name.replace(' ', '_')}", headers=headers, timeout=15)
        if r.status_code == 200:
            d = r.json()
            return {
                "summary": d.get("extract", ""),
                "description": d.get("description", ""),
                "image": d.get("thumbnail", {}).get("source", ""),
                "url": d.get("content_urls", {}).get("desktop", {}).get("page", "")
            }
    except Exception as e:
        print(f" ⚠ Wikipedia error: {e}")
    return {"summary": "", "description": "", "image": "", "url": ""}

def fetch_wikipedia_full(name):
    try:
        r = session.get(f"{WIKI_MOBILE}{name.replace(' ', '_')}", headers=headers, timeout=15)
        if r.status_code == 200:
            text = re.sub(r'<[^>]+>', ' ', r.text)
            text = re.sub(r'\s+', ' ', text).strip()
            text = re.sub(r'\[\d+\]', '', text)
            return text
    except Exception as e:
        print(f" ⚠ Wikipedia full error: {e}")
    return ""

def clean_wikipedia_text(text):
    """Remove Wikipedia navigation garbage"""
    if not text:
        return ""
    
    text = re.sub(r'Toggle.*?subsection', '', text, flags=re.I)
    text = re.sub(r'Toggle the table of contents', '', text, flags=re.I)
    text = re.sub(r'\d+\s*languages', '', text, flags=re.I)
    text = re.sub(r'Acèh|Адыгабзэ|Afrikaans|Alemannisch|العربية|مصرى|Asturianu|Azərbaycanca|Беларуская|Български|Català|Čeština|Dansk|Deutsch|Eesti|Ελληνικά|Español|Esperanto|Euskara|فارسی|Suomi|Français|עברית|हिन्दी|Hrvatski|Magyar|Bahasa|Íslenska|Italiano|日本語|ქართული|한국어|Latina|Lietuvių|Македонски|മലയാളം|मराठी|Nederlands|Norsk|Polski|Português|Română|Русский|Svenska|தமிழ்|తెలుగు|ไทย|Türkçe|Українська|اردو|Tiếng|中文', '', text, flags=re.I)
    text = re.sub(r'Wikidata|Featured articles|Wikipedia.*?pages|Use.*?dates|All Wikipedia articles|Articles with.*?microformats|Articles containing.*?language text|Pages using.*?image|Short description', '', text, flags=re.I)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def extract_wikipedia_sections(text):
    """Extract Wikipedia sections with full text content under each header"""
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
    
    if not text:
        return sections
    
    text = clean_wikipedia_text(text)
    
    section_patterns = [
        (r'(?:Etymology|Name origin|Naming)[:\s]+(.+?)(?=(?:Description|Distribution|Habitat|Behaviour|Behavior|Ecology|Hunting|Reproduction|Threats|Conservation|References|$))', "etymology"),
        (r'(?:Description|Physical description|Appearance|Characteristics)[:\s]+(.+?)(?=(?:Etymology|Distribution|Habitat|Behaviour|Behavior|Ecology|Hunting|Reproduction|Threats|Conservation|References|$))', "description"),
        (r'(?:Distribution|Range|Geographic distribution)[:\s]+(.+?)(?=(?:Etymology|Description|Habitat|Behaviour|Behavior|Ecology|Hunting|Reproduction|Threats|Conservation|References|$))', "distribution"),
        (r'(?:Habitat|Environment|Ecology)[:\s]+(.+?)(?=(?:Etymology|Description|Distribution|Behaviour|Behavior|Hunting|Reproduction|Threats|Conservation|References|$))', "habitat"),
        (r'(?:Hunting and diet|Diet|Feeding|Prey|Hunting)[:\s]+(.+?)(?=(?:Etymology|Description|Distribution|Habitat|Behaviour|Behavior|Reproduction|Threats|Conservation|References|$))', "hunting_diet"),
        (r'(?:Behaviour|Behavior|Social behavior|Social organisation|Social organization)[:\s]+(.+?)(?=(?:Etymology|Description|Distribution|Habitat|Hunting|Reproduction|Threats|Conservation|References|$))', "behavior"),
        (r'(?:Reproduction|Breeding|Life cycle|Reproduction and life cycle)[:\s]+(.+?)(?=(?:Etymology|Description|Distribution|Habitat|Hunting|Behaviour|Behavior|Threats|Conservation|References|$))', "reproduction"),
        (r'(?:Threats|Predators|Danger)[:\s]+(.+?)(?=(?:Etymology|Description|Distribution|Habitat|Hunting|Behaviour|Behavior|Reproduction|Conservation|References|$))', "threats"),
        (r'(?:Conservation|Status|Protection|Conservation status)[:\s]+(.+?)(?=(?:Etymology|Description|Distribution|Habitat|Hunting|Behaviour|Behavior|Reproduction|Threats|References|$))', "conservation"),
    ]
    
    for pattern, section_name in section_patterns:
        match = re.search(pattern, text, re.I | re.DOTALL)
        if match:
            content = match.group(1).strip()
            content = re.sub(r'\s+', ' ', content)
            content = re.sub(r'\s*\.\s*\.', '.', content)
            if len(content) > 1000:
                content = content[:1000]
                content = content.rsplit('.', 1)[0] + '.'
            sections[section_name] = content
    
    return sections

def extract_stats_from_sections(sections):
    """Extract weight, height, length, lifespan, speed from sections"""
    stats = {"weight": "", "length": "", "height": "", "lifespan": "", "top_speed": ""}
    all_text = sections.get("description", "") + " " + sections.get("habitat", "")
    
    if not all_text:
        return stats
    
    # Weight
    m = re.search(r'weighs?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilograms|tonnes?|t|lbs?|pounds)', all_text, re.I)
    if m:
        stats["weight"] = f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    # Length
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet)\s*(?:long|length|in length)', all_text, re.I)
    if m:
        stats["length"] = f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    # Height
    if 'shoulder' in all_text.lower() or 'stands' in all_text.lower():
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|and)\s*(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?|cm|centimetres?|ft|feet)\s*(?:tall|height|shoulder)', all_text, re.I)
        if m:
            stats["height"] = f"{m.group(1)}–{m.group(2)} {m.group(3)}"
    
    # Lifespan
    m = re.search(r'(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs)\s*(?:lifespan|life|old|age|in the wild)', all_text, re.I)
    if m:
        stats["lifespan"] = f"{m.group(1)} {m.group(2)}"
    
    # Speed
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*(km/h|kmph|mph|mi/h)\s*(?:speed|top speed|maximum|can run)', all_text, re.I)
    if m:
        stats["top_speed"] = f"{m.group(1)} {m.group(2)}"
    
    return stats

def extract_diet_from_sections(sections):
    """Extract diet and prey from sections"""
    diet = ""
    prey = ""
    
    hunting_text = sections.get("hunting_diet", "")
    if not hunting_text:
        hunting_text = sections.get("description", "")
    
    if not hunting_text:
        return diet, prey
    
    if any(w in hunting_text.lower() for w in ['carnivore', 'carnivorous', 'meat-eater', 'predator']):
        diet = "Carnivore"
    elif any(w in hunting_text.lower() for w in ['herbivore', 'herbivorous', 'plant-eater', 'grazes']):
        diet = "Herbivore"
    elif any(w in hunting_text.lower() for w in ['omnivore', 'omnivorous', 'both plants and animals']):
        diet = "Omnivore"
    
    m = re.search(r'(?:preys? on|feeds? on|hunts?|eats?|diet consists of|primary prey)[:\s]+([^.]{10,150})', hunting_text, re.I)
    if m:
        prey = m.group(1).strip()[:120]
    
    return diet, prey

def extract_reproduction_from_sections(sections):
    """Extract reproduction data from sections"""
    repro = {"gestation_period": "", "average_litter_size": "", "name_of_young": ""}
    
    repro_text = sections.get("reproduction", "")
    if not repro_text:
        repro_text = sections.get("behavior", "")
    
    if not repro_text:
        return repro
    
    m = re.search(r'(?:gestation|pregnancy|incubation)\s*(?:period)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(days?|months?|weeks?)', repro_text, re.I)
    if m:
        repro["gestation_period"] = f"{m.group(1)} {m.group(2)}"
    
    m = re.search(r'(?:litter|cubs?|young|offspring)\s*(?:size)?\s*(\d+(?:\s*[-–]\s*\d+)?)', repro_text, re.I)
    if m:
        repro["average_litter_size"] = m.group(1)
    
    m = re.search(r'young\s*(?:are\s*)?(?:called|known as)?\s*(?:a|an)?\s*(\w+)', repro_text, re.I)
    if m:
        repro["name_of_young"] = m.group(1).lower()
    
    return repro

def extract_conservation_from_sections(sections):
    """Extract conservation status and threats from sections"""
    status = ""
    threats = []
    
    conservation_text = sections.get("conservation", "")
    threats_text = sections.get("threats", "")
    all_text = conservation_text + " " + threats_text
    
    if conservation_text:
        statuses = ["Critically Endangered", "Endangered", "Vulnerable", "Near Threatened", "Least Concern", "Data Deficient"]
        for s in statuses:
            if s.lower() in conservation_text.lower():
                status = s
                break
    
    if any(w in all_text.lower() for w in ['poach', 'illegal trade', 'body parts', 'fur trade', 'ivory']):
        threats.append('Poaching')
    if any(w in all_text.lower() for w in ['habitat loss', 'deforestation', 'habitat destruction']):
        threats.append('Habitat loss')
    if any(w in all_text.lower() for w in ['human-wildlife conflict', 'livestock', 'retaliation']):
        threats.append('Human-wildlife conflict')
    
    return status, ', '.join(threats[:3])

def extract_behavior_from_sections(sections):
    """Extract group behavior from sections"""
    behavior_text = sections.get("behavior", "")
    if not behavior_text:
        return ""
    
    t = behavior_text.lower()
    if any(w in t for w in ['solitary', 'alone', 'lives alone', 'mostly solitary']):
        return "Solitary"
    elif any(w in t for w in ['pack', 'herd', 'flock', 'colony', 'social', 'group']):
        return "Social"
    elif any(w in t for w in ['pair', 'mate', 'pairs']):
        return "Pairs"
    
    return ""

def extract_additional_info_from_sections(sections):
    """Extract ALL additional_info fields from Wikipedia sections"""
    info = {
        "group": "",
        "number_of_species": "",
        "estimated_population_size": "",
        "age_of_sexual_maturity": "",
        "age_of_weaning": "",
        "most_distinctive_feature": ""
    }
    
    all_text = ""
    for section_name, section_text in sections.items():
        all_text += section_text + " "
    
    if not all_text:
        return info
    
    # Group (Mammal, Bird, Fish, Reptile, etc.)
    group_patterns = [
        r'is a (?:species of )?(mammal|bird|fish|reptile|amphibian|insect|invertebrate)',
        r'belongs to the (?:class|group|family of )?(mammals|birds|fish|reptiles|amphibians|insects)',
        r'is the (?:largest|smallest|only|sole) (?:living|extant)? (mammal|bird|fish|reptile|amphibian|insect)',
    ]
    for pattern in group_patterns:
        m = re.search(pattern, all_text, re.I)
        if m:
            info["group"] = m.group(1).capitalize()
            break
    
    # Number of species
    species_patterns = [
        r'(?:\d+)\s*(?:species|subspecies)\s*(?:of|in|within|recognized|known)',
        r'(?:there are|includes?|contains?|comprises?)\s*(\d+)\s*(?:species|subspecies)',
        r'(?:about|around|approximately|over|more than|up to)\s*(\d+)\s*(?:species|subspecies)',
        r'species\s*(?:count|number)?\s*(?:of|is)?\s*(\d+)',
    ]
    for pattern in species_patterns:
        m = re.search(pattern, all_text, re.I)
        if m:
            info["number_of_species"] = m.group(1)
            break
    
    # Estimated population size
    population_patterns = [
        r'(?:population|estimated|total)\s*(?:is|of|size)?\s*(?:about|around|approximately|over|under|more than|less than)?\s*(\d+(?:,\d+)*(?:\s*(?:million|billion|thousand))?)',
        r'(?:\d+(?:,\d+)*)\s*(?:million|billion|thousand)\s*(?:individuals?|animals?|population)',
        r'(?:wild population|remaining|left)\s*(?:is|are)?\s*(?:about|around|only)?\s*(\d+(?:,\d+)*(?:\s*(?:million|billion|thousand))?)',
    ]
    for pattern in population_patterns:
        m = re.search(pattern, all_text, re.I)
        if m:
            info["estimated_population_size"] = m.group(1).strip()
            break
    
    # Age of sexual maturity
    maturity_patterns = [
        r'(?:sexual maturity|mature|reproductively mature)\s*(?:at|reached|occurs|at age)?\s*(?:around|about|approximately)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs|months?|weeks?)',
        r'(?:reaches?|becomes?|attains?)\s*(?:sexual)?\s*(?:maturity|mature)\s*(?:at|by|around)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs|months?)',
        r'(?:at|by|around|about)\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs|months?)\s*(?:of age|old)?\s*(?:sexual maturity|mature)',
    ]
    for pattern in maturity_patterns:
        m = re.search(pattern, all_text, re.I)
        if m:
            info["age_of_sexual_maturity"] = f"{m.group(1)} {m.group(2)}"
            break
    
    # Age of weaning
    weaning_patterns = [
        r'(?:weaned|weaning)\s*(?:at|occurs|age)?\s*(?:around|about|approximately)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs|months?|weeks?)',
        r'(?:young|cubs?|pups?|chicks?)\s*(?:are|is)?\s*(?:weaned)\s*(?:at|after|around)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs|months?|weeks?)',
        r'(?:independent|leave mother)\s*(?:at|after|around)?\s*(\d+(?:\s*[-–]\s*\d+)?)\s*(years?|yrs|months?)',
    ]
    for pattern in weaning_patterns:
        m = re.search(pattern, all_text, re.I)
        if m:
            info["age_of_weaning"] = f"{m.group(1)} {m.group(2)}"
            break
    
    # Most distinctive feature
    feature_patterns = [
        r'(?:most distinctive|distinctive|characteristic|notable|unique|remarkable)\s*(?:feature|characteristic|trait)\s*(?:is|are|of|includes?)?\s*(?:the)?\s*([^.]{10,150})',
        r'(?:easily recognized|easily identified|readily identified)\s*(?:by|from|through)\s*(?:its?|their?)?\s*([^.]{10,100})',
        r'(?:known for|famous for|noted for|notable for)\s*(?:its?|their?)?\s*([^.]{10,100})',
        r'(?:distinctive|characteristic|unique)\s*(?:is|are)\s*(?:the|its?|their?)?\s*([^.]{10,100})',
    ]
    for pattern in feature_patterns:
        m = re.search(pattern, all_text, re.I)
        if m:
            feature = m.group(1).strip()
            # Clean up
            feature = re.sub(r'^(?:the |its |their |a |an )', '', feature, flags=re.I)
            if len(feature) > 10 and len(feature) < 150:
                info["most_distinctive_feature"] = feature[:120]
                break
    
    return info

# iNaturalist
def fetch_inaturalist(sci_name):
    try:
        params = {"q": sci_name, "per_page": 1, "rank": "species"}
        r = session.get(INAT_API, params=params, headers=headers, timeout=30)
        if r.status_code != 200:
            params = {"q": sci_name, "per_page": 1}
            r = session.get(INAT_API, params=params, headers=headers, timeout=30)
        if r.status_code == 200:
            results = r.json().get("results", [])
            if results:
                taxon = results[0]
                time.sleep(0.5)
                anc_ids = taxon.get("ancestor_ids", [])
                if anc_ids:
                    r = session.get(f"{INAT_API}/{','.join(map(str, anc_ids))}", headers=headers, timeout=30)
                    if r.status_code == 200:
                        classification = {f: "" for f in CLASSIFICATION_FIELDS}
                        classification["species"] = taxon.get("name", sci_name)
                        for a in r.json().get("results", []):
                            rank = a.get("rank", "").lower()
                            name = a.get("name")
                            if rank == "kingdom": classification["kingdom"] = name
                            elif rank == "phylum": classification["phylum"] = name
                            elif rank == "class": classification["class"] = name
                            elif rank == "order": classification["order"] = name
                            elif rank == "family": classification["family"] = name
                            elif rank == "genus": classification["genus"] = name
                        return classification
    except Exception as e:
        print(f" ⚠ iNaturalist error: {e}")
    return None

# File operations
def get_animal_filename(name, qid):
    clean_name = name.lower().replace(' ', '_').replace('-', '_').replace("'", "")
    return f"{clean_name}_{{QID={qid}}}.json"

def save_animal_file(data, name, qid):
    filename = get_animal_filename(name, qid)
    filepath = ANIMAL_STATS_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f" 💾 Saved: {filename}")

# Build data from ALL sources
def build_animal_data(ninja_data, wiki_summary, wiki_full, wiki_sections, inat_classification, qid, name, sci_name):
    # Get data from each source
    ninja_chars = ninja_data.get("characteristics", {}) if ninja_data else {}
    ninja_taxonomy = ninja_data.get("taxonomy", {}) if ninja_data else {}
    ninja_locations = ninja_data.get("locations", []) if ninja_data else []
    
    # Animal type
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
    
    # Extract ALL possible data from Wikipedia sections
    wiki_stats = extract_stats_from_sections(wiki_sections)
    wiki_diet, wiki_prey = extract_diet_from_sections(wiki_sections)
    wiki_repro = extract_reproduction_from_sections(wiki_sections)
    wiki_conservation_status, wiki_threats = extract_conservation_from_sections(wiki_sections)
    wiki_behavior = extract_behavior_from_sections(wiki_sections)
    wiki_additional = extract_additional_info_from_sections(wiki_sections)
    
    # Build data - Priority: Ninja API > Wikipedia sections > iNaturalist
    data = {
        "id": qid,
        "name": name,
        "scientific_name": sci_name,
        "common_names": [],
        "description": wiki_summary.get("description", "") if wiki_summary else "",
        "summary": wiki_summary.get("summary", "") if wiki_summary else "",
        "image": wiki_summary.get("image", "") if wiki_summary else "",
        "wikipedia_url": wiki_summary.get("url", "") if wiki_summary else "",
        "wikipedia_sections": wiki_sections,
        "classification": {
            "kingdom": inat_classification.get("kingdom", "") if inat_classification else ninja_taxonomy.get("kingdom", ""),
            "phylum": inat_classification.get("phylum", "") if inat_classification else ninja_taxonomy.get("phylum", ""),
            "class": inat_classification.get("class", "") if inat_classification else ninja_taxonomy.get("class", ""),
            "order": inat_classification.get("order", "") if inat_classification else ninja_taxonomy.get("order", ""),
            "family": inat_classification.get("family", "") if inat_classification else ninja_taxonomy.get("family", ""),
            "genus": inat_classification.get("genus", "") if inat_classification else ninja_taxonomy.get("genus", ""),
            "species": inat_classification.get("species", "") if inat_classification else ninja_taxonomy.get("scientific_name", sci_name)
        },
        "animal_type": animal_type,
        "young_name": young_name,
        "group_name": get_group_name(animal_type),
        "physical": {
            "weight": ninja_chars.get("weight", "") or wiki_stats.get("weight", ""),
            "length": wiki_stats.get("length", ""),
            "height": ninja_chars.get("height", "") or wiki_stats.get("height", ""),
            "top_speed": ninja_chars.get("top_speed", "") or wiki_stats.get("top_speed", ""),
            "lifespan": ninja_chars.get("lifespan", "") or wiki_stats.get("lifespan", "")
        },
        "ecology": {
            "diet": ninja_chars.get("diet", "") or wiki_diet,
            "habitat": ninja_chars.get("habitat", "") or wiki_sections.get("habitat", ""),
            "locations": ", ".join(ninja_locations) if ninja_locations else wiki_sections.get("distribution", ""),
            "group_behavior": ninja_chars.get("group_behavior", "") or wiki_behavior,
            "conservation_status": wiki_conservation_status,
            "biggest_threat": ninja_chars.get("biggest_threat", "") or wiki_threats,
            "distinctive_features": [ninja_chars.get("most_distinctive_feature")] if ninja_chars.get("most_distinctive_feature") else [],
            "population_trend": ""
        },
        "reproduction": {
            "gestation_period": ninja_chars.get("gestation_period", "") or wiki_repro.get("gestation_period", ""),
            "average_litter_size": ninja_chars.get("average_litter_size", "") or wiki_repro.get("average_litter_size", ""),
            "name_of_young": ninja_chars.get("name_of_young", "") or wiki_repro.get("name_of_young", "") or young_name
        },
        "additional_info": {
            "lifestyle": ninja_chars.get("lifestyle", ""),
            "color": ninja_chars.get("color", ""),
            "skin_type": ninja_chars.get("skin_type", ""),
            "prey": ninja_chars.get("prey", "") or wiki_prey,
            "slogan": ninja_chars.get("slogan", ""),
            "group": ninja_chars.get("group", "") or wiki_additional.get("group", ""),
            "number_of_species": ninja_chars.get("number_of_species", "") or wiki_additional.get("number_of_species", ""),
            "estimated_population_size": ninja_chars.get("estimated_population_size", "") or wiki_additional.get("estimated_population_size", ""),
            "age_of_sexual_maturity": ninja_chars.get("age_of_sexual_maturity", "") or wiki_additional.get("age_of_sexual_maturity", ""),
            "age_of_weaning": ninja_chars.get("age_of_weaning", "") or wiki_additional.get("age_of_weaning", ""),
            "most_distinctive_feature": ninja_chars.get("most_distinctive_feature", "") or wiki_additional.get("most_distinctive_feature", "")
        },
        "sources": [],
        "last_updated": datetime.now().isoformat()
    }
    
    # Add sources
    if ninja_data is not None:
        data["sources"].append("API Ninjas")
    if wiki_summary and wiki_summary.get("summary"):
        data["sources"].append("Wikipedia")
    if inat_classification:
        data["sources"].append("iNaturalist")
    
    return data

# Main
def generate(animals, force=False):
    output = []
    ninja_api_key = os.environ.get("API_NINJAS_KEY", "")
    
    for i, a in enumerate(animals):
        name, sci, qid = a["name"], a["scientific_name"], a.get("qid", f"animal_{i}")
        print(f"\n{'='*60}")
        print(f"[{i+1}/{len(animals)}] {name} ({sci})")
        print(f"{'='*60}")

        print(" 🥷 Fetching from Ninja API...")
        ninja_data = fetch_animal_data(name, ninja_api_key)
        
        if ninja_data is not None:
            chars = ninja_data.get("characteristics", {})
            print(f"   📊 Got {len(chars)} fields from Ninja API")
        else:
            print(f" ⚠ No data from Ninja API for {name}")
            ninja_data = {"characteristics": {}, "taxonomy": {}, "locations": []}

        print(" 📖 Fetching from Wikipedia...")
        wiki_summary = fetch_wikipedia_summary(name)
        wiki_full = fetch_wikipedia_full(name)
        wiki_sections = extract_wikipedia_sections(wiki_full)
        
        print(" 🔬 Fetching from iNaturalist...")
        inat_classification = fetch_inaturalist(sci)
        
        data = build_animal_data(ninja_data, wiki_summary, wiki_full, wiki_sections, inat_classification, qid, name, sci)
        save_animal_file(data, name, qid)
        
        output.append(data)
        print(f" ✅ {name} complete!")
        time.sleep(1)

    with open(DATA_DIR / "animals.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Done! {len(output)} animals saved to {ANIMAL_STATS_DIR}/")
    return output

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
