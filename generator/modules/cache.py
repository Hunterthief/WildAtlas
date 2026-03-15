# generator/modules/cache.py
"""
Cache Module

Handles loading and saving cached animal data to avoid redundant API calls.
Cache is stored in generator/data/ for internal use.
"""

import os
import json
from pathlib import Path

# Cache directory is in generator/data/
CACHE_DIR = Path(__file__).parent.parent / "data"


def load_cache(qid):
    """
    Load cached animal data from file.
    
    Args:
        qid: Animal identifier (Q-number or animal_id)
        
    Returns:
        dict: Cached animal data or None if not found
    """
    CACHE_DIR.mkdir(exist_ok=True)
    f = CACHE_DIR / f"{qid}.json"
    if f.exists():
        try:
            with open(f, "r", encoding="utf-8") as fp:
                return json.load(fp)
        except:
            pass
    return None


def save_cache(qid, data):
    """
    Save animal data to cache file.
    
    Args:
        qid: Animal identifier (Q-number or animal_id)
        data: Animal data dict to save
    """
    CACHE_DIR.mkdir(exist_ok=True)
    with open(CACHE_DIR / f"{qid}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
