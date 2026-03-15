# Add to imports (after line 30)
try:
    from modules.iucn_redlist import fetch_iucn_data
    IUCN_AVAILABLE = True
except ImportError:
    IUCN_AVAILABLE = False
    print(" ⚠ IUCN module not available")

# Add to environment variables (after line 55)
IUCN_API_KEY = os.environ.get("IUCN_API_KEY", "")

# Update fetch_from_all_sources function (add IUCN step)
def fetch_from_all_sources(name, sci, qid):
    """
    Fetch data from all available sources in priority order:
    1. API Ninjas (most structured)
    2. Wikidata (structured)
    3. IUCN Red List (conservation data)
    4. Wikipedia + Regex (fallback)
    """
    
    all_data = initialize_animal_data(qid, name, sci)
    sources_used = []
    
    # ========== 1. API NINJAS (Primary) ==========
    if API_NINJAS_AVAILABLE and API_NINJAS_KEY:
        print(" 🍯 API Ninjas...")
        try:
            ninjas_data = fetch_api_ninjas(name, API_NINJAS_KEY)
            if ninjas_data:
                all_data = merge_data(all_data, ninjas_data)
                sources_used.append("API Ninjas")
                print(" ✓ API Ninjas data received")
        except Exception as e:
            print(f" ⚠ API Ninjas error: {e}")
    
    # ========== 2. WIKIDATA (Secondary) ==========
    if WIKIDATA_AVAILABLE and qid:
        print(" 📊 Wikidata...")
        try:
            wikidata = query_wikidata_animal(qid)
            if wikidata:
                if wikidata.get("physical"):
                    for key, value in wikidata["physical"].items():
                        if value and not all_data["physical"].get(key):
                            all_data["physical"][key] = value
                
                if wikidata.get("description") and not all_data.get("description"):
                    all_data["description"] = wikidata["description"]
                
                if wikidata.get("image") and not all_data.get("image"):
                    all_data["image"] = wikidata["image"]
                
                sources_used.append("Wikidata")
                print(" ✓ Wikidata data received")
        except Exception as e:
            print(f" ⚠ Wikidata error: {e}")
    
    # ========== 3. IUCN RED LIST (Conservation Data) ==========
    if IUCN_AVAILABLE and IUCN_API_KEY and sci:
        print(" 🌍 IUCN Red List...")
        try:
            iucn_data = fetch_iucn_data(sci, IUCN_API_KEY)
            if iucn_data:
                all_data = merge_data(all_data, iucn_data)
                sources_used.append("IUCN Red List")
                status = iucn_data.get("ecology", {}).get("conservation_status")
                if status:
                    print(f" ✓ Conservation: {status}")
        except Exception as e:
            print(f" ⚠ IUCN error: {e}")
    
    # ========== 4. WIKIPEDIA (Fallback + Images/Summary) ==========
    # ... rest of the function remains the same ...
