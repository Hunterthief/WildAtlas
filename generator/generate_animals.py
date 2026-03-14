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
            # Strip HTML but keep text content
            text = re.sub(r'<[^>]+>', ' ', r.text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text
    except: pass
    return ""

def extract_stats(text):
    """Extract physical stats with en-dash support (–) and proper context"""
    stats = {"weight": None, "length": None, "height": None, "lifespan": None, "top_speed": None}
    if not text: return stats
    
    # Weight - look for kg/t/lb with range (en-dash – or hyphen -)
    # Pattern: "200–260 kg" or "200-260 kg" or "300 kg"
    weight_matches = re.findall(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to)\s*(\d+(?:[.,]\d+)?)\s*(kg|tonnes?|t\b|lbs?)', text, re.I)
    for v1, v2, unit in weight_matches:
        try:
            val1, val2 = float(v1.replace(',','.')), float(v2.replace(',','.'))
            u = unit.lower()
            # Tiger weight should be 50-400 kg range
            if u in ['kg'] and 50 < val1 < val2 < 400:
                stats["weight"] = f"{val1}–{val2} {u}"
                break
            elif u in ['t','tonne','tonnes'] and 0.5 < val1 < val2 < 10:
                stats["weight"] = f"{val1}–{val2} t"
                break
            elif u in ['lb','lbs','pounds'] and 100 < val1 < val2 < 900:
                stats["weight"] = f"{val1}–{val2} {u}"
                break
        except: pass
    
    # Single weight value
    if not stats["weight"]:
        m = re.search(r'\b(\d+(?:[.,]\d+)?)\s*(kg|tonnes?|t\b|lbs?)\b', text, re.I)
        if m:
            try:
                val, unit = float(m.group(1).replace(',','.')), m.group(2).lower()
                if unit in ['kg'] and 50 < val < 400:
                    stats["weight"] = f"{val} {unit}"
                elif unit in ['t','tonne','tonnes'] and 0.5 < val < 10:
                    stats["weight"] = f"{val} t"
                elif unit in ['lb','lbs','pounds'] and 100 < val < 900:
                    stats["weight"] = f"{val} {unit}"
            except: pass
    
    # Length - look for meters with range
    # Pattern: "1.4–2.8 m" (head-body length)
    length_matches = re.findall(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to)\s*(\d+(?:[.,]\d+)?)\s*(m\b|metres?|cm\b|ft\b)', text, re.I)
    for v1, v2, unit in length_matches:
        try:
            val1, val2 = float(v1.replace(',','.')), float(v2.replace(',','.'))
            u = unit.lower()
            # Tiger length 1-4 m range
            if u in ['m','metre','metres','meter','meters'] and 1 < val1 < val2 < 4:
                stats["length"] = f"{val1}–{val2} {u}"
                break
            elif u in ['cm'] and 100 < val1 < val2 < 400:
                stats["length"] = f"{val1}–{val2} cm"
                break
            elif u in ['ft','feet'] and 3 < val1 < val2 < 13:
                stats["length"] = f"{val1}–{val2} ft"
                break
        except: pass
    
    # Height - look for "at the shoulder" context
    if 'shoulder' in text.lower():
        height_matches = re.findall(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to)\s*(\d+(?:[.,]\d+)?)\s*(m\b|metres?|cm\b|ft\b)', text, re.I)
        for v1, v2, unit in height_matches:
            try:
                val1, val2 = float(v1.replace(',','.')), float(v2.replace(',','.'))
                u = unit.lower()
                # Tiger shoulder height 0.6-1.5 m
                if u in ['m','metre','metres','meter','meters'] and 0.5 < val1 < val2 < 2:
                    stats["height"] = f"{val1}–{val2} {u}"
                    break
            except: pass
    
    # Lifespan - look for "years" with numbers
    lifespan_matches = re.findall(r'(\d+(?:-\d+)?)\s*(years?|yrs?)', text, re.I)
    for value, unit in lifespan_matches:
        try:
            if '-' in value:
                parts = value.split('-')
                if 5 < int(parts[0]) < int(parts[1]) < 30:
                    stats["lifespan"] = f"{value} years"
                    break
            else:
                val = int(value)
                if 5 < val < 30:
                    stats["lifespan"] = f"{value} years"
                    break
        except: pass
    
    # Speed - look for km/h or mph
    speed_matches = re.findall(r'(\d+(?:[.,]\d+)?)\s*(km/h|kmph|mph)', text, re.I)
    for value, unit in speed_matches:
        try:
            val = float(value.replace(',','.'))
            # Tiger speed 30-80 km/h
            if 30 < val < 100:
                stats["top_speed"] = f"{val} {unit.lower()}"
                break
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
    """Extract IUCN conservation status"""
    if not text: return None
    statuses = ["Critically Endangered", "Endangered", "Vulnerable", "Near Threatened", "Least Concern", "Extinct in the Wild", "Extinct"]
    for s in statuses:
        if s.lower() in text.lower():
            return s
    return None

def extract_locations(text, animal_name):
    """Extract geographic locations - filtered by animal type"""
    if not text: return None
    
    # Tiger-specific locations (from actual distribution)
    tiger_locations = ["Asia", "India", "China", "Russia", "Indonesia", "Sumatra", "Thailand", "Malaysia", "Bangladesh", "Nepal", "Bhutan", "Myanmar", "Vietnam", "Cambodia", "Laos", "Siberia", "Southeast Asia", "Indian subcontinent"]
    
    # Elephant-specific
    elephant_locations = ["Asia", "India", "China", "Thailand", "Sri Lanka", "Indonesia", "Sumatra", "Borneo", "South Asia", "Southeast Asia"]
    
    # Eagle-specific
    eagle_locations = ["North America", "Canada", "Alaska", "United States", "Mexico", "USA", "American"]
    
    # Determine animal type
    animal_lower = animal_name.lower()
    if any(w in animal_lower for w in ['tiger', 'lion', 'leopard', 'cat']):
        keywords = tiger_locations
    elif any(w in animal_lower for w in ['elephant']):
        keywords = elephant_locations
    elif any(w in animal_lower for w in ['eagle', 'hawk', 'falcon']):
        keywords = eagle_locations
    else:
        keywords = tiger_locations  # Default
    
    # Find matching locations
    locs = []
    for loc in keywords:
        if loc.lower() in text.lower():
            locs.append(loc)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_locs = []
    for loc in locs:
        if loc.lower() not in seen:
            seen.add(loc.lower())
            unique_locs.append(loc)
    
    return ", ".join(unique_locs[:5]) if unique_locs else None

def extract_habitat(text):
    """Extract habitat description"""
    if not text: return None
    
    habitat_keywords = ["forest", "grassland", "savanna", "desert", "mountain", "wetland", "swamp", "jungle", "woodland", "plain", "tundra", "rainforest"]
    found = []
    
    for keyword in habitat_keywords:
        if keyword in text.lower():
            found.append(keyword)
    
    # Look for more specific habitat description
    habitat_patterns = [
        r'(?:inhabits?|lives? in|found in|habitat)[:\s]+([^.,]+?)(?:[.,]|$)',
        r'(?:tropical|temperate|coniferous|broadleaf|moist|dry)\s*(?:forest|woodland)',
    ]
    
    for pattern in habitat_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            found.append(m.group(0).strip()[:100])
    
    return ", ".join(list(set(found))[:3]) if found else None

def extract_behavior(text):
    """Extract social behavior"""
    if not text: return None
    
    if any(w in text.lower() for w in ['solitary', 'alone', 'lives alone']):
        return "Solitary"
    elif any(w in text.lower() for w in ['pack', 'group', 'social', 'herd']):
        return "Social"
    elif any(w in text.lower() for w in ['pair', 'mate', 'family']):
        return "Family groups"
    
    return None

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
        
        # Wikipedia
        if not data["image"] or force:
            print("  📖 Wikipedia...")
            wiki = fetch_wikipedia_summary(name)
            if wiki["summary"]:
                data["summary"] = wiki["summary"]
                data["description"] = wiki["description"]
                data["image"] = wiki["image"]
                data["wikipedia_url"] = wiki["url"]
                if "Wikipedia" not in data["sources"]: data["sources"].append("Wikipedia")
                
                # Fetch full article for detailed extraction
                full = fetch_wikipedia_full(name)
                all_text = wiki["summary"] + " " + full
                
                # Extract physical stats
                stats = extract_stats(all_text)
                for k, v in stats.items():
                    if v:
                        data["physical"][k] = v
                        print(f"    ✓ {k}: {v}")
                
                # Extract diet
                diet = extract_diet(all_text)
                if diet:
                    data["ecology"]["diet"] = diet
                    print(f"    ✓ diet: {diet}")
                
                # Extract conservation
                cons = extract_conservation(all_text)
                if cons:
                    data["ecology"]["conservation_status"] = cons
                    print(f"    ✓ conservation: {cons}")
                
                # Extract locations (filtered by animal type)
                locs = extract_locations(all_text, name)
                if locs:
                    data["ecology"]["locations"] = locs
                    print(f"    ✓ locations: {locs}")
                
                # Extract habitat
                habitat = extract_habitat(all_text)
                if habitat:
                    data["ecology"]["habitat"] = habitat
                    print(f"    ✓ habitat: {habitat}")
                
                # Extract behavior
                behavior = extract_behavior(all_text)
                if behavior:
                    data["ecology"]["group_behavior"] = behavior
                    print(f"    ✓ behavior: {behavior}")
        
        # iNaturalist
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
