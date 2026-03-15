# generator/modules/cache.py
"""
Cache Module

Handles loading and saving cached animal data to avoid redundant API calls.
"""

import os
import json


def load_cache(qid):
    """
    Load cached animal data from file.
    
    Args:
        qid: Animal identifier (Q-number or animal_id)
        
    Returns:
        dict: Cached animal data or None if not found
    """
    f = f"data/{qid}.json"
    if os.path.exists(f):
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
    with open(f"data/{qid}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
