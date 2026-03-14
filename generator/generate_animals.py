import requests
import json
import time
import os

os.makedirs("data", exist_ok=True)

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

# Custom headers to avoid 403
headers = {
    "User-Agent": "WildAtlasBot/1.0 (https://github.com/Hunterthief/WildAtlas)"
}

for name in animals:
    try:
        url_name = name.replace(" ", "_")
        response = requests.get(API + url_name, headers=headers, timeout=10)
        print(f"Fetching {name} -> {API + url_name} (status {response.status_code})")

        if response.status_code != 200:
            print(f"Skipped {name} due to status {response.status_code}")
            continue

        j = response.json()

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
        time.sleep(1)

    except Exception as e:
        print(f"Error fetching {name}: {e}")

with open(os.path.join("data", "animals.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"animals.json written to data/animals.json. Total animals fetched: {len(data)}")
