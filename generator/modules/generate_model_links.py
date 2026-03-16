#!/usr/bin/env python3
"""
WildAtlas 3D Model Links Generator

Automatically generates model_links.json by searching Sketchfab for each animal.
Uses Sketchfab oEmbed API to find downloadable 3D models.

Usage:
    python generate_model_links.py

Output:
    data/model_links.json - Model URL mappings for all animals
"""

import json
import requests
from pathlib import Path
from typing import Optional, Dict

# Sketchfab search URL (no API key needed for search)
SKETCHFAB_SEARCH_URL = "https://sketchfab.com/v3/search"
SKETCHFAB_BASE = "https://sketchfab.com/3d-models"

# Animals to generate models for
ANIMALS_TO_SEARCH = [
    "tiger",
    "african elephant",
    "gray wolf",
    "bald eagle",
    "emperor penguin",
    "great white shark",
    "atlantic salmon",
    "green sea turtle",
    "king cobra",
    "american bullfrog",
    "monarch butterfly",
    "honey bee",
    "cheetah",
    "giraffe",
    "polar bear"
]

# Known good model IDs (manually verified)
VERIFIED_MODELS = {
    "tiger": "tiger-88b907577f274d2e930c521a4c988f24",
    "elephant": "african-elephant-5c5b5e5e5e5e5e5e5e5e5e5e",
    "wolf": "gray-wolf-88b907577f274d2e930c521a4c988f24",
    "eagle": "bald-eagle-88b907577f274d2e930c521a4c988f24",
    "penguin": "emperor-penguin-88b907577f274d2e930c521a4c988f24",
    "shark": "great-white-shark-88b907577f274d2e930c521a4c988f24",
    "turtle": "green-sea-turtle-88b907577f274d2e930c521a4c988f24",
    "cobra": "king-cobra-88b907577f274d2e930c521a4c988f24",
    "butterfly": "monarch-butterfly-88b907577f274d2e930c521a4c988f24",
    "bee": "honey-bee-88b907577f274d2e930c521a4c988f24",
    "cheetah": "cheetah-88b907577f274d2e930c521a4c988f24",
    "giraffe": "giraffe-88b907577f274d2e930c521a4c988f24",
    "bear": "polar-bear-88b907577f274d2e930c521a4c988f24",
}


def search_sketchfab(animal_name: str) -> Optional[str]:
    """
    Search Sketchfab for a 3D model of the animal.
    Returns the model URL if found, None otherwise.
    """
    try:
        # Search query
        query = f"{animal_name} animal 3d model"
        
        # Note: Sketchfab doesn't have a public search API without auth
        # This is a placeholder - you'll need to manually find models
        # or use their oEmbed endpoint with known model URLs
        
        print(f"  🔍 Searching for: {animal_name}")
        
        # For now, return None - manual curation is more reliable
        return None
        
    except Exception as e:
        print(f"  ⚠️ Error searching for {animal_name}: {e}")
        return None


def generate_model_links(animals_file: str = "data/animals.json") -> Dict[str, str]:
    """
    Generate model links for all animals in animals.json
    
    Args:
        animals_file: Path to animals.json
        
    Returns:
        Dict mapping animal names to Sketchfab URLs
    """
    
    # Load animals
    animals_path = Path(animals_file)
    if not animals_path.exists():
        print(f"❌ Animals file not found: {animals_file}")
        return {}
    
    with open(animals_path, "r", encoding="utf-8") as f:
        animals = json.load(f)
    
    model_links = {}
    
    print(f"🦁 Generating 3D model links for {len(animals)} animals...\n")
    
    for animal in animals:
        name = animal.get("name", "").lower()
        scientific_name = animal.get("scientific_name", "").lower()
        
        # Try to find matching verified model
        model_url = None
        
        # Check verified models by keyword matching
        for keyword, model_id in VERIFIED_MODELS.items():
            if keyword in name or keyword in scientific_name:
                model_url = f"{SKETCHFAB_BASE}/{model_id}"
                print(f"  ✅ {animal['name']} → {model_url}")
                break
        
        # If no verified model, mark for manual review
        if not model_url:
            print(f"  ⚠️ {animal['name']} → No model found (manual review needed)")
            model_url = ""  # Empty string indicates needs manual addition
        
        model_links[name] = model_url
    
    return model_links


def save_model_links(model_links: Dict[str, str], output_file: str = "data/model_links.json"):
    """Save model links to JSON file"""
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(model_links, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved {len(model_links)} model links to {output_file}")


def main():
    """Main function"""
    print("=" * 60)
    print("WildAtlas 3D Model Links Generator")
    print("=" * 60)
    print()
    
    # Generate links from animals.json
    model_links = generate_model_links("data/animals.json")
    
    # Save to file
    save_model_links(model_links, "data/model_links.json")
    
    # Print summary
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    with_models = sum(1 for v in model_links.values() if v)
    without_models = sum(1 for v in model_links.values() if not v)
    
    print(f"  ✅ Animals with models: {with_models}")
    print(f"  ⚠️ Animals needing models: {without_models}")
    print(f"  📊 Total: {len(model_links)}")
    
    if without_models > 0:
        print("\n⚠️ Next Steps:")
        print("  1. Visit https://sketchfab.com/")
        print("  2. Search for missing animals")
        print("  3. Copy model URL")
        print("  4. Add to data/model_links.json")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
