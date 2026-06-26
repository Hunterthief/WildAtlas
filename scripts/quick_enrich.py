#!/usr/bin/env python3
"""Quickly extract scientific names and classification from Wikipedia summaries
using regex, without the LLM. Much faster than batch_enrich.py."""
import json, os, re

CACHE_DIR = "data/cache/wikipedia"

def extract_sci_name(summary):
    """Extract scientific name from Wikipedia summary.
    Usually in the first sentence in parentheses: 'The tiger (Panthera tigris) is...'"""
    if not summary:
        return ""
    # Look for pattern: (Genus species) in the first 200 chars
    m = re.search(r'\(([A-Z][a-z]+ [a-z]+(?:\s+[a-z]+)?)\)', summary[:300])
    if m:
        return m.group(1)
    return ""

def extract_classification_from_text(text):
    """Try to extract classification keywords from article text."""
    if not text:
        return {}
    cls = {}
    # Look for explicit mentions
    patterns = {
        'kingdom': r'Kingdom[:\s]+([A-Za-z]+)',
        'phylum': r'Phylum[:\s]+([A-Za-z]+)',
        'class': r'Class[:\s]+([A-Za-z]+)',
        'order': r'Order[:\s]+([A-Za-z]+)',
        'family': r'Family[:\s]+([A-Za-z]+)',
        'genus': r'Genus[:\s]+([A-Za-z]+)',
        'species': r'Species[:\s]+([A-Za-z\s]+)',
    }
    for key, pat in patterns.items():
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            cls[key] = m.group(1).strip()
    return cls

# Also try to get classification from the Wikipedia API (dbpedia-style)
import urllib.request, urllib.parse, time

def get_wikidata_classification(wikipedia_title):
    """Get taxonomic classification from Wikidata via the Wikipedia article's
    Wikidata item. Uses the public Wikidata API with CORS support."""
    try:
        # Get the Wikidata Q ID from the Wikipedia article
        url = f"https://en.wikipedia.org/w/api.php?action=query&prop=pageprops&titles={urllib.parse.quote(wikipedia_title)}&format=json&origin=*"
        req = urllib.request.Request(url, headers={'User-Agent': 'WildAtlasBot/1.0'})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.load(r)
        pages = data.get('query', {}).get('pages', {})
        for page in pages.values():
            qid = page.get('pageprops', {}).get('wikibase_item', '')
            if qid:
                return qid
        return None
    except:
        return None

count = 0
for fn in sorted(os.listdir(CACHE_DIR)):
    if not fn.endswith('.json'):
        continue
    cache_file = os.path.join(CACHE_DIR, fn)
    a = json.load(open(cache_file))

    changed = False

    # Extract scientific name if missing
    if not a.get('scientific_name', '').strip():
        summary = a.get('summary', '') or (a.get('article') or {}).get('overview', '')
        sci = extract_sci_name(summary)
        if sci:
            a['scientific_name'] = sci
            changed = True

    # Extract classification if missing
    if not (a.get('classification') or {}).get('class', '').strip():
        text = a.get('summary', '') + '\n' + '\n'.join(
            (a.get('article') or {}).get(k, '') for k in ['description', 'habitat', 'behavior', 'conservation']
        )
        cls = extract_classification_from_text(text)
        if cls:
            a['classification'] = {**(a.get('classification') or {}), **cls}
            changed = True

    if changed:
        json.dump(a, open(cache_file, 'w'), indent=2, ensure_ascii=False)
        count += 1

    # Log
    sci = a.get('scientific_name', '?')
    cls = (a.get('classification') or {}).get('class', '?')
    print(f"  {a['name']:<28} sci={sci:<28} class={cls}")

print(f"\nUpdated {count} animals")
