#!/usr/bin/env python3
"""Re-fetch Wikipedia data for animals with empty summaries.
Uses the Wikipedia REST API directly — no Node.js, no SDK, reliable."""
import json, os, re, urllib.request, urllib.parse, time

CACHE_DIR = "data/cache/wikipedia"
HEADERS = {"User-Agent": "WildAtlasBot/1.0 (educational project)"}

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

SECTION_KEYWORDS = {
    'description': ['description', 'characteristics', 'appearance'],
    'habitat': ['distribution and habitat', 'habitat', 'distribution', 'range'],
    'behavior': ['behaviour and ecology', 'behavior and ecology', 'ecology and behaviour', 'behavior', 'behaviour', 'ecology', 'diet', 'feeding'],
    'conservation': ['conservation', 'conservation status', 'status', 'threats'],
}

def pick_section(sections, keywords):
    for kw in keywords:
        for s in sections:
            if kw in s.get('heading', '').lower():
                return s
    return None

def refetch(animal_name, wikipedia_title):
    """Fetch summary + key sections from Wikipedia."""
    title = wikipedia_title or animal_name
    try:
        # 1. Summary
        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
        summary_data = fetch_json(summary_url)
        extract = summary_data.get('extract', '')
        image = summary_data.get('thumbnail', {}).get('source') or summary_data.get('originalimage', {}).get('source', '')
        wiki_url = summary_data.get('content_urls', {}).get('desktop', {}).get('page', '')

        if not extract:
            return None  # Wikipedia didn't find this article

        # 2. Sections list
        sections_url = f"https://en.wikipedia.org/w/api.php?action=parse&page={urllib.parse.quote(title)}&prop=sections&redirects=1&format=json"
        sections_data = fetch_json(sections_url)
        section_list = sections_data.get('parse', {}).get('sections', [])

        # 3. Fetch up to 3 key sections
        article = {'overview': extract}
        picks = []
        seen = set()
        for key, keywords in SECTION_KEYWORDS.items():
            if len(picks) >= 3: break
            if key in seen: continue
            pick = pick_section(section_list, keywords)
            if pick:
                picks.append((key, pick['index']))
                seen.add(key)

        for key, idx in picks:
            try:
                sec_url = f"https://en.wikipedia.org/w/api.php?action=parse&page={urllib.parse.quote(title)}&section={idx}&prop=wikitext&redirects=1&format=json"
                sec_data = fetch_json(sec_url)
                wt = sec_data.get('parse', {}).get('wikitext', {}).get('*', '')
                plain = wikitext_to_plain(wt)[:3500]
                if plain:
                    article[key] = plain
                time.sleep(0.3)
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
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

# Process all empty animals
refetched = 0
for fn in sorted(os.listdir(CACHE_DIR)):
    if not fn.endswith('.json'): continue
    cache_file = os.path.join(CACHE_DIR, fn)
    a = json.load(open(cache_file))
    text = (a.get('summary', '') or '') + ((a.get('article') or {}).get('overview', '') or '')
    if text.strip():
        continue  # has text, skip

    name = a['name']
    wiki_title = a.get('wikipedia_url', '').split('/wiki/')[-1] if a.get('wikipedia_url') else name

    print(f"  Refetching {name}...", end='', flush=True)
    data = refetch(name, wiki_title)
    if data:
        a.update(data)
        json.dump(a, open(cache_file, 'w'), indent=2, ensure_ascii=False)
        refetched += 1
        print(f" OK (overview: {len(data['article']['overview'])} chars)")
    else:
        print(" FAILED")
    time.sleep(0.5)

print(f"\nRefetched {refetched} animals")
