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
WIKI_ACTION = "https://en.wikipedia.org/w/api.php"
INAT_API = "https://api.inaturalist.org/v1/taxa"
GBIF_API = "https://api.gbif.org/v1/species"

CLASSIFICATION_FIELDS = ["kingdom", "phylum", "class", "order", "family", "genus", "species"]

def fetch_wikipedia(name):
    try:
        r = session.get(f"{WIKI_API}{name.replace(' ', '_')}", headers=headers, timeout=15)
        if r.status_code == 200:
            d = r.json()
            return {"summary": d.get("extract", ""), "description": d.get("description", ""),
                    "image": d.get("thumbnail", {}).get("source", ""),
                    "url": d.get("content_urls", {}).get("desktop", {}).get("page", "")}
    except: pass
    return {"summary": "", "description": "", "image": "", "url": ""}

def fetch_wikipedia_full(name):
    try:
        r = session.get(WIKI_ACTION, params={"action": "parse", "page": name.replace(" ", "_"),
                                              "prop": "text", "format": "json"}, headers=headers, timeout=15)
        if r.status_code == 200:
            text = r.json().get("parse", {}).get("text", {}).get("*", "")
            return re.sub(r'<[^>]+>', ' ', text)
    except: pass
    return ""

def extract_stats(text):
    stats = {"weight": None, "length": None, "height": None, "lifespan": None, "top_speed": None}
    if not text: return stats
    
    # Weight with range support
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to)\s*(\d+(?:[.,]\d+)?)\s*(kg|tonnes?|t\b|lbs?)', text, re.I)
    if m:
        v1, v2, u = float(m.group(1).replace(',','.')), float(m.group(2).replace(',','.')), m.group(3).lower()
        if u in ['kg'] and 1 < v1 < v2 < 500: stats["weight"] = f"{v1}–{v2} {u}"
        elif u in ['t','tonne','tonnes'] and 0.1 < v1 < v2 < 10: stats["weight"] = f"{v1}–{v2} t"
        elif u in ['lb','lbs','pounds'] and 2 < v1 < v2 < 1100: stats["weight"] = f"{v1}–{v2} {u}"
    else:
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*(kg|tonnes?|t\b|lbs?)', text, re.I)
        if m:
            v, u = float(m.group(1).replace(',','.')), m.group(2).lower()
            if u in ['kg'] and 1 < v < 500: stats["weight"] = f"{v} {u}"
            elif u in ['t','tonne','tonnes'] and 0.1 < v < 10: stats["weight"] = f"{v} t"
            elif u in ['lb','lbs','pounds'] and 2 < v < 1100: stats["weight"] = f"{v} {u}"
    
    # Length with range support
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to)\s*(\d+(?:[.,]\d+)?)\s*(m\b|metres?|cm\b|ft\b)', text, re.I)
    if m:
        v1, v2, u = float(m.group(1).replace(',','.')), float(m.group(2).replace(',','.')), m.group(3).lower()
        if u in ['m','metre','metres','meter','meters'] and 0.3 < v1 < v2 < 10: stats["length"] = f"{v1}–{v2} {u}"
        elif u in ['cm'] and 10 < v1 < v2 < 500: stats["length"] = f"{v1}–{v2} cm"
        elif u in ['ft','feet'] and 1 < v1 < v2 < 30: stats["length"] = f"{v1}–{v2} ft"
    else:
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*(m\b|metres?|cm\b|ft\b)', text, re.I)
        if m:
            v, u = float(m.group(1).replace(',','.')), m.group(2).lower()
            if u in ['m','metre','metres','meter','meters'] and 0.3 < v < 10: stats["length"] = f"{v} {u}"
            elif u in ['cm'] and 10 < v < 500: stats["length"] = f"{v} cm"
            elif u in ['ft','feet'] and 1 < v < 30: stats["length"] = f"{v} ft"
    
    # Height
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:–|-|to)\s*(\d+(?:[.,]\d+)?)\s*(m\b|metres?|cm\b|ft\b)', text, re.I)
    if m and 'shoulder' in text.lower() or 'stands' in text.lower():
        v1, v2, u = float(m.group(1).replace(',','.')), float(m.group(2).replace(',','.')), m.group(3).lower()
        if u in ['m','metre','metres','meter','meters'] and 0.3 < v1 < v2 < 5: stats["height"] = f"{v1}–{v2} {u}"
    
    # Lifespan
    m = re.search(r'(\d+(?:-\d+)?)\s*(years?|yrs?)', text, re.I)
    if m:
        v = m.group(1)
        if '-' in v:
            p = v.split('-')
            if 1 < int(p[0]) < 100 and 1 < int(p[1]) < 100: stats["lifespan"] = f"{v} years"
        elif 1 < int(v) < 100: stats["lifespan"] = f"{v} years"
    
    # Speed
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*(km/h|kmph|mph)', text, re.I)
    if m:
        v = float(m.group(1).replace(',','.'))
        if 10 < v < 150: stats["top_speed"] = f"{v} {m.group(2).lower()}"
    
    return stats

def extract_diet(text):
    if not text: return None
    t = text.lower()
    if any(w in t for w in ['carnivore','meat','predator','hunts']): return "Carnivore"
    elif any(w in t for w in ['herbivore','plant','vegetation','grazes']): return "Herbivore"
    elif any(w in t for w in ['omnivore']): return "Omnivore"
    return None

def extract_conservation(text):
    if not text: return None
    for s in ["Critically Endangered", "Endangered", "Vulnerable", "Near Threatened", "Least Concern", "Extinct"]:
        if s.lower() in text.lower(): return s
    return None

def extract_locations(text):
    if not text: return None
    locs = []
    for c in ["Asia", "Africa", "Europe", "North America", "South America", "India", "China", "Russia", "Indonesia", "Thailand", "Malaysia", "Bangladesh", "Nepal"]:
        if c.lower() in text.lower(): locs.append(c)
    return ", ".join(locs[:5]) if locs else None

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

def fetch_gbif(sci_name):
    try:
        r = session.get(f"{GBIF_API}/search", params={"q": sci_name, "type": "SPECIES", "limit": 1}, headers=headers, timeout=30)
        if r.status_code != 200: return None
        results = r.json().get("results", [])
        if not results: return None
        d = results[0]
        if d.get("numOccurrences", 0) == 0: return None
        return {"conservation_status": d.get("conservationStatus")}
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
            wiki = fetch_wikipedia(name)
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
                
                diet = extract_diet(wiki["summary"])
                if diet:
                    data["ecology"]["diet"] = diet
                    print(f"    ✓ diet: {diet}")
                
                cons = extract_conservation(full)
                if cons:
                    data["ecology"]["conservation_status"] = cons
                    print(f"    ✓ conservation: {cons}")
                
                locs = extract_locations(full)
                if locs:
                    data["ecology"]["locations"] = locs
                    print(f"    ✓ locations: {locs[:50]}...")
        
        # iNaturalist
        if not data["classification"]["kingdom"] or force:
            print("  🔬 iNaturalist...")
            cl = fetch_inaturalist(sci)
            if cl:
                data["classification"] = cl
                if "iNaturalist" not in data["sources"]: data["sources"].append("iNaturalist")
                print(f"    ✓ Classification complete")
        
        # GBIF
        if not data["ecology"]["locations"] or force:
            print("  🌍 GBIF...")
            gbif = fetch_gbif(sci)
            if gbif:
                if gbif.get("conservation_status") and not data["ecology"]["conservation_status"]:
                    data["ecology"]["conservation_status"] = gbif["conservation_status"]
                    print(f"    ✓ Conservation: {gbif['conservation_status']}")
                if "GBIF" not in data["sources"]: data["sources"].append("GBIF")
            else:
                print("    ⚠ No GBIF data")
        
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
