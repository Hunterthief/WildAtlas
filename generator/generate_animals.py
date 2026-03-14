# generator/generate_animals.py
import requests
import json
import time
import os

# Ensure the data folder exists
os.makedirs("data", exist_ok=True)

# List of animals (can expand later)
animals = [
    "Lion","Tiger","Elephant","Blue Whale","Orca","Great White Shark",
    "Dolphin","Octopus","Penguin","Giraffe","Zebra","Bear","Wolf","Fox",
    "Kangaroo","Koala","Cheetah","Leopard","Hyena","Moose","Walrus",
    "Seal","Sea Lion","Swordfish","Salmon","Tuna","Clownfish",
    "Angelfish","Manta Ray","Stingray","Hammerhead Shark","Barracuda",
    "Pufferfish","Moray Eel","Manatee","Narwhal","Beluga Whale"
]

API = "https://en.wikipedia.org/api/rest_v1/page/summary/"

data = []

for name in animals:
    try:
        # Replace spaces with underscores for API
        url_name = name.replace(" ", "_")
        response = requests.get(API + url_name, timeout=10)
        print(f"Fetching {name} -> {API + url_name} (status {response.status_code})")

        if response.status_code != 200:
            print(f"Skipped {name} due to status {response.status_code}")
            continue

        j = response.json()

        # Skip if no extract available
        if "extract" not in j:
            print(f"Skipped {name} (no extract)")
            continue

        data.append({
            "name": name,
            "description": j.get("description", ""),
            "summary": j.get("extract", ""),
            "image": j.get("thumbnail", {}).get("source", "")
        })

        print(f"Added {name}")
        time.sleep(1)  # polite to Wikipedia

    except Exception as e:
        print(f"Error fetching {name}: {e}")

# Write to repo root data folder
output_path = os.path.join("data", "animals.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"animals.json written to {output_path}. Total animals fetched: {len(data)}")
