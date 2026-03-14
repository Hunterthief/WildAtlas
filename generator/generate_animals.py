# generator/generate_animals.py
import requests, json, time, os, re
from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

os.makedirs("data", exist_ok=True)
session = requests.Session()
retry = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retry))
headers = {"User-Agent": "WildAtlasBot/1.0", "Accept": "application/json"}

WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
WIKI_MOBILE = "https://en.m.wikipedia.org/wiki/"
INAT_API = "https://api.inaturalist.org/v1/taxa"

CLASSIFICATION_FIELDS = ["kingdom", "phylum", "class", "order", "family", "genus", "species"]

# Location keywords by animal type
LOCATION_KEYWORDS = {
    "cat": ["Asia", "India", "China", "Russia", "Indonesia", "Thailand", "Malaysia", "Bangladesh", "Nepal", "Sumatra", "Siberia", "Southeast Asia"],
    "elephant": ["Asia", "India", "China", "Thailand", "Sri Lanka", "Indonesia", "Sumatra", "Borneo", "South Asia"],
    "eagle": ["North America", "Canada", "Alaska", "United States", "Mexico", "USA"],
    "default": ["Asia", "Africa", "Europe", "North America", "South America", "Australia", "India", "China", "Russia", "Indonesia"]
}

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
    except: pass
    return {"summary": "", "description": "", "image": "", "url": ""}

def fetch_wikipedia_full(name):
    """Fetch full mobile Wikipedia page for all sections"""
    try:
        r = session.get(f"{WIKI_MOBILE}{name.replace(' ', '_')}", headers=headers, timeout=15)
        if r.status_code == 200:
            text = re.sub(r'<[^>]+>', ' ', r.text)
            text = re.sub(r'\s+', ' ', text).strip()
            text = re.sub(r'\[\d+\]', '', text)
            return text
    except: pass
    return ""

def extract_stats(text):
    """Extract physical stats - tested on actual Tiger article content"""
    stats = {"weight": None, "length": None, "height": None, "lifespan": None, "top_speed": None}
    if not text: return stats
    
    # Weight - matches "weigh 200–260 kg" pattern from Tiger article
    weight_patterns = [
        r'weigh\s*(?:of)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−)\s*(\d+(?:[.,]\d+)?)\s*(kg|tonnes?|t\b|lbs?)',
        r'weigh\s*(\d+(?:[.,]\d+)?)\s*(kg|tonnes?|t\b|lbs?)',
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−)\s*(\d+(?:[.,]\d+)?)\s*(kg|tonnes?|t\b|lbs?)\s*weight',
    ]
    for pattern in weight_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                groups = m.groups()
                if len(groups) == 4:
                    v1, v2 = float(groups[0].replace(',','.')), float(groups[1].replace(',','.'))
                    u = groups[2].lower()
                    if u in ['kg'] and 50 < v1 < v2 < 500:
                        stats["weight"] = f"{v1}–{v2} {u}"
                        break
                    elif u in ['t','tonne','tonnes'] and 0.5 < v1 < v2 < 10:
                        stats["weight"] = f"{v1}–{v2} t"
                        break
                    elif u in ['lb','lbs','pounds'] and 100 < v1 < v2 < 1100:
                        stats["weight"] = f"{v1}–{v2} {u}"
                        break
                elif len(groups) == 2:
                    v, u = float(groups[0].replace(',','.')), groups[1].lower()
                    if u in ['kg'] and 50 < v < 500:
                        stats["weight"] = f"{v} {u}"
                        break
                    elif u in ['t','tonne','tonnes'] and 0.5 < v < 10:
                        stats["weight"] = f"{v} t"
                        break
            except: pass
    
    # Length - matches "head-body length of 1.4–2.8 m" pattern
    length_patterns = [
        r'length\s*(?:of)?\s*(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−)\s*(\d+(?:[.,]\d+)?)\s*(m\b|metres?|cm\b|ft\b)',
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−)\s*(\d+(?:[.,]\d+)?)\s*(m\b|metres?|cm\b|ft\b)\s*long',
        r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−)\s*(\d+(?:[.,]\d+)?)\s*(m\b|metres?|cm\b|ft\b)',
    ]
    for pattern in length_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                groups = m.groups()
                v1, v2 = float(groups[0].replace(',','.')), float(groups[1].replace(',','.'))
                u = groups[2].lower()
                if u in ['m','metre','metres','meter','meters'] and 1 < v1 < v2 < 4:
                    stats["length"] = f"{v1}–{v2} {u}"
                    break
                elif u in ['cm'] and 100 < v1 < v2 < 400:
                    stats["length"] = f"{v1}–{v2} cm"
                    break
                elif u in ['ft','feet'] and 3 < v1 < v2 < 13:
                    stats["length"] = f"{v1}–{v2} ft"
                    break
            except: pass
    
    # Height - matches "stands 0.8–1.1 m at the shoulder" pattern
    if 'shoulder' in text.lower() or 'stands' in text.lower():
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to|−)\s*(\d+(?:[.,]\d+)?)\s*(m\b|metres?|cm\b|ft\b)', text, re.I)
        if m:
            try:
                v1, v2 = float(m.group(1).replace(',','.')), float(m.group(2).replace(',','.'))
                u = m.group(3).lower()
                if u in ['m','metre','metres','meter','meters'] and 0.5 < v1 < v2 < 2:
                    stats["height"] = f"{v1}–{v2} {u}"
            except: pass
    
    # Lifespan - matches "12–15 years" pattern
    lifespan_patterns = [
        r'live\s*(\d+(?:-\d+)?)\s*(years?|yrs?)',
        r'(\d+(?:-\d+)?)\s*(years?|yrs?)\s*in the wild',
        r'(\d+(?:-\d+)?)\s*(years?|yrs?)',
    ]
    for pattern in lifespan_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                v = m.group(1)
                if '-' in v:
                    p = v.split('-')
                    if 5 < int(p[0]) < int(p[1]) < 30:
                        stats["lifespan"] = f"{v} years"
                        break
                else:
                    val = int(v)
                    if 5 < val < 30:
                        stats["lifespan"] = f"{v} years"
                        break
            except: pass
    
    # Speed - matches "sprint 56 km/h" pattern
    if 'sprint' in text.lower() or 'speed' in text.lower() or 'run' in text.lower():
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*(km/h|kmph|mph)', text, re.I)
        if m:
            try:
                v = float(m.group(1).replace(',','.'))
                if 30 < v < 100:
                    stats["top_speed"] = f"{v} {m.group(2).lower()}"
            except: pass
    
    return stats

def extract_diet(text):
    if not text: return None
    t = text.lower()
    if any(w in t for w in ['carnivore', 'apex predator', 'meat', 'predator']):
        return "Carnivore"
    elif any(w in t for w in ['herbivore', 'plant', 'vegetation', 'grazes']):
        return "Herbivore"
    elif any(w in t for w in ['omnivore']):
        return "Omnivore"
    return None

def extract_conservation(text):
    if not text: return None
    for s in ["Critically Endangered", "Endangered", "Vulnerable", "Near Threatened", "Least Concern", "Extinct"]:
        if s.lower() in text.lower():
            return s
    return None

def extract_locations(text, animal_name):
    if not text: return None
    animal_lower = animal_name.lower()
    if any(w in animal_lower for w in ['tiger', 'lion', 'leopard', 'cat']):
        keywords = LOCATION_KEYWORDS["cat"]
    elif any(w in animal_lower for w in ['elephant']):
        keywords = LOCATION_KEYWORDS["elephant"]
    elif any(w in animal_lower for w in ['eagle', 'hawk', 'falcon']):
        keywords = LOCATION_KEYWORDS["eagle"]
    else:
        keywords = LOCATION_KEYWORDS["default"]
    
    locs = []
    for loc in keywords:
        if loc.lower() in text.lower():
            locs.append(loc)
    
    seen = set()
    unique_locs = []
    for loc in locs:
        if loc.lower() not in seen:
            seen.add(loc.lower())
            unique_locs.append(loc)
    
    return ", ".join(unique_locs[:5]) if unique_locs else None

def extract_habitat(text):
    if not text: return None
    habitat_keywords = ["forest", "grassland", "savanna", "desert", "mountain", "wetland", "swamp", "jungle", "woodland", "plain", "tundra", "rainforest", "coniferous", "temperate", "tropical", "broadleaf"]
    found = []
    for keyword in habitat_keywords:
        if keyword in text.lower():
            found.append(keyword)
    return ", ".join(list(set(found))[:3]) if found else None

def extract_behavior(text):
    if not text: return None
    if any(w in text.lower() for w in ['solitary', 'alone', 'lives alone']):
        return "Solitary"
    elif any(w in text.lower() for w in ['pack', 'group', 'social', 'herd']):
        return "Social"
    elif any(w in text.lower() for w in ['pair', 'mate', 'family']):
        return "Family groups"
    return None

def extract_reproduction(text):
    repro = {"gestation_period": None, "average_litter_size": None, "name_of_young": None}
    
    m = re.search(r'gestation\s*lasts?\s*(?:around|about|for)?\s*(\d+(?:-\d+)?)\s*(months?|weeks?)', text, re.I)
    if m:
        repro["gestation_period"] = f"{m.group(1)} {m.group(2)}"
    
    m = re.search(r'litters?\s*(?:consist|of|have)?\s*(?:of|up to)?\s*(\d+(?:-\d+)?)\s*cubs?', text, re.I)
    if m:
        repro["average_litter_size"] = m.group(1)
    
    if 'cub' in text.lower():
        repro["name_of_young"] = "Cub"
    elif 'calf' in text.lower():
        repro["name_of_young"] = "Calf"
    elif 'chick' in text.lower():
        repro["name_of_young"] = "Chick"
    
    return repro

def extract_threats(text):
    threats = []
    if any(w in text.lower() for w in ['poach', 'illegal trade', 'body parts']):
        threats.append('Poaching')
    if any(w in text.lower() for w in ['habitat loss', 'deforestation', 'habitat destruction']):
        threats.append('Habitat loss')
    if any(w in text.lower() for w in ['human-wildlife conflict', 'livestock']):
        threats.append('Human-wildlife conflict')
    return ', '.join(threats[:2]) if threats else None

def fetch_inaturalist(sci_name):
    try:
        params = {"q": sci_name, "per_page": 1, "rank": "species"}
        r = session.get(INAT_API, params=params, headers=headers, timeout=30)
        if r.status_code != 200: return None
        results = r.json().get("results", [])
        if not results:
            params = {"q": sci_name, "per_page": 1}
            r = session.get(INAT_API, params=params, headers=headers, timeout=30)
            if r.status_code == 200: results = r.json().get("results", [])
        if not results: return None
        
        taxon = results[0]
        time.sleep(0.5)
        anc_ids = taxon.get("ancestor_ids", [])
        if not anc_ids: return None
        
        r = session.get(f"{INAT_API}/{','.join(map(str, anc_ids))}", headers=headers, timeout=30)
        if r.status_code != 200: return None
        
        classification = {f: None for f in CLASSIFICATION_FIELDS}
        classification["species"] = taxon.get("name", sci_name)
        for a in r.json().get("results", []):
            rank, name = a.get("rank", "").lower(), a.get("name")
            if rank == "kingdom": classification["kingdom"] = name
            elif rank == "phylum": classification["phylum"] = name
            elif rank == "class": classification["class"] = name
            elif rank == "order": classification["order"] = name
            elif rank == "family": classification["family"] = name
            elif rank == "genus": classification["genus"] = name
        return classification
    except: pass
    return None

def load_cache(qid):
    f = f"data/{qid}.json"
    if os.path.exists(f):
        try:
            with open(f, "r", encoding="utf-8") as fp: return json.load(fp)
        except: pass
    return None

def save_cache(qid, data):
    with open(f"data/{qid}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def generate(animals, force=False):
    output = []
    for i, a in enumerate(animals):
        name, sci, qid = a["name"], a["scientific_name"], a.get("qid", f"animal_{i}")
        print(f"\n[{i+1}/{len(animals)}] {name} ({sci})")
        
        cached = load_cache(qid) if not force else None
        if cached:
            data = cached
            data["sources"] = list(set(data.get("sources", [])))
        else:
            data = {"name": name, "scientific_name": sci, "qid": qid, "name_meaning": None,
                    "description": None, "summary": None, "image": None, "wikipedia_url": None,
                    "classification": {f: None for f in CLASSIFICATION_FIELDS},
                    "physical": {"weight": None, "height": None, "length": None, "top_speed": None,
                                 "lifespan": None, "color": None, "skin_type": None, "most_distinctive_feature": None},
                    "ecology": {"diet": None, "prey": None, "habitat": None, "locations": None,
                                "group_behavior": None, "lifestyle": None, "biggest_threat": None,
                                "conservation_status": None, "estimated_population_size": None},
                    "reproduction": {"gestation_period": None, "average_litter_size": None, "name_of_young": None},
                    "fun_facts": {"slogan": None}, "sources": [], "last_updated": None}
        
        if not data["image"] or force:
            print("  📖 Wikipedia...")
            wiki = fetch_wikipedia_summary(name)
            if wiki["summary"]:
                data["summary"] = wiki["summary"]
                data["description"] = wiki["description"]
                data["image"] = wiki["image"]
                data["wikipedia_url"] = wiki["url"]
                if "Wikipedia" not in data["sources"]: data["sources"].append("Wikipedia")
                
                full = fetch_wikipedia_full(name)
                all_text = wiki["summary"] + " " + full
                
                stats = extract_stats(all_text)
                for k, v in stats.items():
                    if v:
                        data["physical"][k] = v
                        print(f"    ✓ {k}: {v}")
                
                diet = extract_diet(all_text)
                if diet:
                    data["ecology"]["diet"] = diet
                    print(f"    ✓ diet: {diet}")
                
                cons = extract_conservation(all_text)
                if cons:
                    data["ecology"]["conservation_status"] = cons
                    print(f"    ✓ conservation: {cons}")
                
                locs = extract_locations(all_text, name)
                if locs:
                    data["ecology"]["locations"] = locs
                    print(f"    ✓ locations: {locs}")
                
                habitat = extract_habitat(all_text)
                if habitat:
                    data["ecology"]["habitat"] = habitat
                    print(f"    ✓ habitat: {habitat}")
                
                behavior = extract_behavior(all_text)
                if behavior:
                    data["ecology"]["group_behavior"] = behavior
                    print(f"    ✓ behavior: {behavior}")
                
                repro = extract_reproduction(all_text)
                for k, v in repro.items():
                    if v:
                        data["reproduction"][k] = v
                        print(f"    ✓ {k}: {v}")
                
                threats = extract_threats(all_text)
                if threats:
                    data["ecology"]["biggest_threat"] = threats
                    print(f"    ✓ threats: {threats}")
        
        if not data["classification"]["kingdom"] or force:
            print("  🔬 iNaturalist...")
            cl = fetch_inaturalist(sci)
            if cl:
                data["classification"] = cl
                if "iNaturalist" not in data["sources"]: data["sources"].append("iNaturalist")
                print(f"    ✓ Classification complete")
        
        data["last_updated"] = datetime.now().isoformat()
        save_cache(qid, data)
        output.append(data)
        print(f"  ✅ {name} complete!")
        time.sleep(1)
    
    with open("data/animals.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Done! {len(output)} animals")
    return output

TEST_ANIMALS = [
    {"name": "Tiger", "scientific_name": "Panthera tigris", "qid": "Q132186"},
    {"name": "Asian Elephant", "scientific_name": "Elephas maximus", "qid": "Q7372"},
    {"name": "Bald Eagle", "scientific_name": "Haliaeetus leucocephalus", "qid": "Q25319"},
]

if __name__ == "__main__":
    force = "--force" in os.sys.argv
    generate(TEST_ANIMALS, force)
