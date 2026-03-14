import requests
import json
import time

animals = [
"Lion","Tiger","Elephant","Blue Whale","Orca","Great White Shark",
"Dolphin","Octopus","Penguin","Giraffe","Zebra","Bear","Wolf","Fox",
"Kangaroo","Koala","Cheetah","Leopard","Hyena","Moose","Walrus",
"Seal","Sea Lion","Swordfish","Salmon","Tuna","Clownfish",
"Angelfish","Manta Ray","Stingray","Hammerhead Shark","Barracuda",
"Pufferfish","Moray Eel","Manatee","Narwhal","Beluga Whale"
]

API="https://en.wikipedia.org/api/rest_v1/page/summary/"

data=[]

for name in animals:

    try:

        r=requests.get(API+name).json()

        data.append({

            "name":name,
            "description":r.get("description",""),
            "summary":r.get("extract",""),
            "image":r.get("thumbnail",{}).get("source","")

        })

        print("Added",name)

        time.sleep(1)

    except:
        pass

with open("/data/animals.json","w") as f:
    json.dump(data,f,indent=2)
