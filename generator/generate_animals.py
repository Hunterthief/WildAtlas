import requests
import json
import time
import os

# Make sure data folder exists
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

for name in animals:
    try:
        # Replace spaces with underscores for Wikipedia API
        url_name = name.replace(" ", "_")
        r = requests.get(API + url_name)
        
        if r.status_code != 200:
            print("Skipped:", name, "Status:", r.status_code)
            continue

        j = r.json()

        # Only add if extract exists
        if "extract" not in j:
            print("Skipped (no extract):", name)
            continue

        data.append({
            "name": name,
            "description": j.get("description", ""),
            "summary": j.get("extract", ""),
            "image": j.get("thumbnail", {}).get("source", "")
        })

        print("Added", name)
        time.sleep(1)  # be polite to Wikipedia

    except Exception as e:
        print("Error fetching", name, e)

# Write to data folder
with open("data/animals.json", "w") as f:
    json.dump(data, f, indent=2)

print("animals.json written to data/animals.json. Total:", len(data))
