"""
Wikipedia data fetcher - PRODUCTION v2
WildAtlas Project
"""
import re
import requests
from typing import Dict, Any
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "WildAtlas/1.0"
}


# =============================================================================
# SECTIONS
# =============================================================================
def fetch_wikipedia_sections(name: str) -> Dict[str, str]:
    try:
        r = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "parse",
                "page": name,
                "format": "json",
                "prop": "text|sections",
                "redirects": 1
            },
            headers=HEADERS,
            timeout=10
        )

        if r.status_code != 200:
            return {}

        data = r.json()
        html = data.get("parse", {}).get("text", {}).get("*", "")

        soup = BeautifulSoup(html, "html.parser")

        sections = {}
        current = "description"
        buffer = []

        for el in soup.find_all(["h2", "h3", "p"]):
            if el.name in ["h2", "h3"]:
                if buffer:
                    sections[current] = " ".join(buffer)
                    buffer = []

                current = re.sub(r'\W+', '_', el.get_text().lower())
            else:
                buffer.append(el.get_text())

        if buffer:
            sections[current] = " ".join(buffer)

        return sections

    except Exception:
        return {}


# =============================================================================
# INFOBOX
# =============================================================================
def fetch_wikipedia_infobox(name: str) -> Dict[str, str]:
    try:
        url = f"https://en.wikipedia.org/wiki/{name.replace(' ', '_')}"
        r = requests.get(url, headers=HEADERS, timeout=10)

        if r.status_code != 200:
            return {}

        soup = BeautifulSoup(r.text, "html.parser")
        infobox = soup.find("table", class_="infobox")

        if not infobox:
            return {}

        text = infobox.get_text()

        patterns = {
            "length": r'(\d+(?:\.\d+)?\s*(?:m|cm))',
            "weight": r'(\d+(?:\.\d+)?\s*(?:kg))',
            "lifespan": r'(\d+(?:\.\d+)?\s*years)'
        }

        result = {}

        for key, pat in patterns.items():
            m = re.search(pat, text, re.I)
            if m:
                result[key] = m.group(1)

        return result

    except Exception:
        return {}


# =============================================================================
# MAIN
# =============================================================================
def fetch_wikipedia_data(name: str) -> Dict[str, Any]:
    sections = fetch_wikipedia_sections(name)
    infobox = fetch_wikipedia_infobox(name)

    return {
        "sections": sections,
        "infobox": infobox,
        "has_sections": bool(sections),
        "has_infobox": bool(infobox),
    }


if __name__ == "__main__":
    animals = ["Cheetah", "Tiger", "Bald Eagle"]

    for a in animals:
        data = fetch_wikipedia_data(a)
        print(a, data.keys())
