#!/usr/bin/env python3
"""Re-fetch AND enrich all catalog animals in one pass.
1. Fetches Wikipedia summary + sections (if missing or empty)
2. Extracts scientific name + classification + stats via LLM (z-ai CLI)
3. Saves enriched data to data/cache/wikipedia/<slug>.json
Rate-limit-safe: 2s delay between Wikipedia calls, 3s between LLM calls."""
import json, os, re, subprocess, time, urllib.request, urllib.parse

CACHE_DIR = "data/cache/wikipedia"
HEADERS = {"User-Agent": "WildAtlasBot/1.0 (educational project)"}

# Read catalog for wikipedia titles
with open("src/lib/curated-catalog.ts") as f:
    content = f.read()
CATALOG = re.findall(
    r'\{\s*name:\s*"([^"]+)"\s*,\s*wikipediaTitle:\s*"([^"]+)"\s*,\s*type:\s*"(\w+)"\s*\}',
    content
)

def slugify(name):
    return ''.join(c if c.isalnum() else '-' for c in name.lower()).strip('-')

def fetch_json(url, timeout=10):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)

def wikitext_to_plain(wt):
    if not wt: return ""
    t = wt
    t = re.sub(r'<!--.*?-->', '', t, flags=re.DOTALL)
    t = re.sub(r'\{\{[^{}]*\}\}', '', t)
    t = re.sub(r'<ref[^>]*>.*?</ref>', '', t, flags=re.DOTALL)
    t = re.sub(r'<ref[^/]*/>', '', t)
    t = re.sub(r'<[^>]+>', '', t)
    t = re.sub(r'\[\[[^\]]*\|([^\]]*)\]\]', r'\1', t)
    t = re.sub(r'\[\[([^\]]*)\]\]', r'\1', t)
    t = re.sub(r'\[https?://\S* ([^\]]*)\]', r'\1', t)
    t = re.sub(r'\[https?://\S*\]', '', t)
    t = re.sub(r"'{2,}", '', t)
    t = re.sub(r'^=+\s*([^=]*)\s*=+$', r'\1', t, flags=re.MULTILINE)
    t = re.sub(r'\n{3,}', '\n\n', t)
    t = re.sub(r'[ \t]+', ' ', t)
    return t.strip()

SECTION_KW = {
    'description': ['description', 'characteristics', 'appearance'],
    'habitat': ['distribution and habitat', 'habitat', 'distribution', 'range'],
    'behavior': ['behaviour and ecology', 'behavior and ecology', 'ecology and behaviour', 'behavior', 'behaviour', 'ecology', 'diet', 'feeding'],
    'conservation': ['conservation', 'conservation status', 'status', 'threats'],
}

def fetch_wikipedia(title):
    """Fetch summary + up to 3 key sections."""
    try:
        # Summary
        summary_data = fetch_json(f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}")
        extract = summary_data.get('extract', '')
        image = summary_data.get('thumbnail', {}).get('source') or summary_data.get('originalimage', {}).get('source', '')
        wiki_url = summary_data.get('content_urls', {}).get('desktop', {}).get('page', '')
        if not extract:
            return None
    except:
        return None

    time.sleep(0.5)

    # Sections
    try:
        sections_data = fetch_json(f"https://en.wikipedia.org/w/api.php?action=parse&page={urllib.parse.quote(title)}&prop=sections&redirects=1&format=json")
        section_list = sections_data.get('parse', {}).get('sections', [])
    except:
        section_list = []

    article = {'overview': extract}
    picks = []
    seen = set()
    for key, keywords in SECTION_KW.items():
        if len(picks) >= 3: break
        if key in seen: continue
        for kw in keywords:
            for s in section_list:
                if kw in s.get('heading', '').lower():
                    picks.append((key, s['index']))
                    seen.add(key)
                    break
            if key in seen: break

    for key, idx in picks:
        try:
            sec_data = fetch_json(f"https://en.wikipedia.org/w/api.php?action=parse&page={urllib.parse.quote(title)}&section={idx}&prop=wikitext&redirects=1&format=json")
            wt = sec_data.get('parse', {}).get('wikitext', {}).get('*', '')
            plain = wikitext_to_plain(wt)[:3500]
            if plain: article[key] = plain
            time.sleep(0.5)
        except:
            pass

    return {
        'summary': extract,
        'description': extract,
        'image': image,
        'images': [image] if image else [],
        'wikipedia_url': wiki_url,
        'article': article,
    }

def llm_extract(name, text):
    """Call z-ai CLI to extract structured data."""
    prompt = f"""You are a precise wildlife data extractor. Given the Wikipedia article text about an animal, extract structured facts. Only include values actually stated in the text. Use metric units.

Output STRICT JSON (no markdown fences) with this shape:
{{"scientific_name":"","young_name":"","group_name":"","physical":{{"length":"","height":"","weight":"","top_speed":"","lifespan":""}},"ecology":{{"diet":"","habitat":"","locations":"","group_behavior":"","conservation_status":"","biggest_threat":"","distinctive_features":[]}},"classification":{{"kingdom":"","phylum":"","class":"","order":"","family":"","genus":"","species":""}},"reproduction":{{"gestation_period":"","average_litter_size":"","name_of_young":""}},"time_period_text":""}}

diet: one of Carnivore/Herbivore/Omnivore/Piscivore/Insectivore/Nectarivore/Scavenger/Filter feeder. conservation_status: one of Least Concern/Near Threatened/Vulnerable/Endangered/Critically Endangered/Extinct in the Wild/Extinct/Data Deficient. Use ranges with en-dash. For egg-layers: gestation=incubation, litter=clutch. Do NOT invent values.

Animal name: {name}

Wikipedia article text:
{text[:5000]}"""

    try:
        result = subprocess.run(["z-ai", "chat", "-p", prompt], capture_output=True, text=True, timeout=30)
        m = re.search(r'\{[\s\S]*"choices"[\s\S]*\}', result.stdout)
        if not m: return {}
        resp = json.loads(m.group(0))
        content = resp["choices"][0]["message"]["content"]
        content = re.sub(r'^```(?:json)?\s*', '', content.strip())
        content = re.sub(r'\s*```$', '', content)
        try:
            return json.loads(content)
        except:
            m2 = re.search(r'\{[\s\S]*\}', content)
            return json.loads(m2.group(0)) if m2 else {}
    except Exception as e:
        print(f"    LLM error: {e}")
        return {}

def merge(animal, extracted):
    if not extracted: return animal
    if extracted.get("scientific_name", "").strip():
        animal["scientific_name"] = extracted["scientific_name"].strip()
    if extracted.get("young_name", "").strip():
        animal["young_name"] = extracted["young_name"].strip()
    if extracted.get("group_name", "").strip():
        animal["group_name"] = extracted["group_name"].strip()
    for section in ["physical", "ecology", "classification", "reproduction"]:
        if extracted.get(section):
            animal[section] = {**(animal.get(section) or {})}
            for k, v in extracted[section].items():
                if isinstance(v, str) and v.strip():
                    animal[section][k] = v
                elif isinstance(v, list) and v:
                    animal[section][k] = v
    if extracted.get("time_period_text", "").strip():
        animal["time_period"] = {"text": extracted["time_period_text"].strip(), "width": "50%", "start": "Ancient", "end": "Present"}
    return animal

# Process all catalog animals
processed = 0
for name, wiki_title, type_ in CATALOG:
    slug = slugify(name)
    cache_file = os.path.join(CACHE_DIR, f"{slug}.json")

    # Load existing or create new
    if os.path.exists(cache_file):
        animal = json.load(open(cache_file))
    else:
        animal = {"id": f"cat:{wiki_title}", "name": name, "scientific_name": "",
                  "wikipediaTitle": wiki_title, "type": type_, "classification": {},
                  "ecology": {}, "physical": {}, "reproduction": {}, "article": {},
                  "sources": ["Wikipedia"]}

    # Check if needs re-fetch (no text)
    text = (animal.get("summary", "") or "") + ((animal.get("article") or {}).get("overview", "") or "")
    if not text.strip():
        print(f"  [{processed+1}] Fetching {name}...", end="", flush=True)
        data = fetch_wikipedia(wiki_title)
        if data:
            animal.update(data)
            print(f" OK ({len(data['article']['overview'])} chars)")
        else:
            print(" FAILED")
        time.sleep(1)

    # Check if needs LLM enrichment (no scientific name or classification)
    if not animal.get("scientific_name", "").strip() or not (animal.get("classification") or {}).get("class", "").strip():
        blob = [animal.get("summary", ""), (animal.get("article") or {}).get("overview", ""),
                (animal.get("article") or {}).get("description", ""),
                (animal.get("article") or {}).get("habitat", ""),
                (animal.get("article") or {}).get("behavior", ""),
                (animal.get("article") or {}).get("conservation", "")]
        blob_text = "\n\n".join(p for p in blob if p)[:5000]
        if blob_text.strip():
            print(f"  [{processed+1}] Enriching {name}...", end="", flush=True)
            extracted = llm_extract(name, blob_text)
            animal = merge(animal, extracted)
            sci = animal.get("scientific_name", "?")
            cls = (animal.get("classification") or {}).get("class", "?")
            print(f" sci={sci} class={cls}")
            time.sleep(2)

    # Save
    json.dump(animal, open(cache_file, "w"), indent=2, ensure_ascii=False)
    processed += 1

print(f"\nProcessed {processed} animals")
