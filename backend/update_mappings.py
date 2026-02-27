import re
import os

DESTINATIONS = {
    "goa": "goa beach india landscape architecture",
    "andaman": "andaman islands beach ocean india",
    "kovalam": "kovalam beach kerala india",
    "varkala": "varkala cliff beach kerala sunset",
    "pondicherry": "pondicherry french colony yellow walls",
    "manali": "manali snow mountains himachal pradesh",
    "kasol": "kasol parvati valley himachal forest",
    "coorg": "coorg coffee plantation karnataka hills",
    "munnar": "munnar tea gardens kerala hills",
    "darjeeling": "darjeeling mountains tea gardens toy train",
    "spiti": "spiti valley mountains himachal desert",
    "jaipur": "jaipur pink city palace rajasthan fort",
    "varanasi": "varanasi ghats ganges river morning",
    "hampi": "hampi ruins karnataka ancient temple",
    "mysore": "mysore palace karnataka night",
    "jodhpur": "jodhpur mehrangarh fort blue city",
    "chikmagalur": "chikmagalur hills forest karnataka coffee",
    "wayanad": "wayanad forest kerala waterfall",
    "alleppey": "alleppey backwaters houseboat kerala",
    "jaisalmer": "jaisalmer golden fort thar desert",
    "ziro": "ziro valley arunachal pradesh green",
    "udaipur": "udaipur lake palace rajasthan boat",
    "leh": "leh ladakh mountains monastery landscape",
    "rishikesh": "rishikesh ganges river yoga suspension bridge",
    "ooty": "ooty nilgiris hills tamil nadu train",
    "kerala_hills": "kerala hill stations mountains mist",
    "shimla": "shimla himachal pradesh snow mall road",
    "mahabaleshwar": "mahabaleshwar hills maharashtra western ghats",
    "agra": "agra taj mahal marble architecture",
    "shillong": "shillong meghalaya hills waterfall",
    "gulmarg": "gulmarg kashmir snow skiing gondola",
    "tawang": "tawang arunachal pradesh monastery mountains",
    "kutch": "rann of kutch gujarat white salt desert",
    "khajuraho": "khajuraho temples madhya pradesh erotic sculptures",
    "dalhousie": "dalhousie himachal pradesh pine trees hills",
    "auli": "auli uttarakhand snow skiing mountains",
    "kodaikanal": "kodaikanal tamil nadu lake foggy hills",
    "pushkar": "pushkar rajasthan holy lake camel fair",
    "mount_abu": "mount abu rajasthan aravali hills lake",
    "gokarna": "gokarna karnataka pristine beaches om beach",
    "majuli": "majuli island assam brahmaputra river",
    "lonavala": "lonavala maharashtra monsoon green hills waterfalls",
    "srinagar": "srinagar kashmir dal lake shikara boat",
    "pahalgam": "pahalgam kashmir valley betaab valley river",
    "ranthambore": "ranthambore national park tiger safari rajasthan",
    "kaziranga": "kaziranga national park rhinos assam",
    "sunderbans": "sunderbans mangrove forest bengal tiger",
    "mathura": "mathura vrindavan krishna temples holi",
    "kanyakumari": "kanyakumari tamil nadu ocean meeting point vivekananda rock",
    "rameshwaram": "rameshwaram tamil nadu pamban bridge temple",
    "tirupati": "tirupati balaji temple andhra pradesh hills",
    "madurai": "madurai meenakshi temple gopuram tamil nadu",
    "nainital": "nainital uttarakhand naini lake hills boats",
    "mussoorie": "mussoorie mall road kempty falls uttarakhand",
    "lansdowne": "lansdowne uttarakhand quiet pine forest hills",
    "ranikhet": "ranikhet uttarakhand himalayas golf course",
    "almora": "almora uttarakhand traditional houses kumaon hills",
    "kausani": "kausani uttarakhand himalayan panorama snow peaks",
    "dharamshala": "dharamshala mcleodganj dalai lama temple tibetan",
    "bir_billing": "bir billing paragliding himachal pradesh",
    "khajjiar": "khajjiar mini switzerland himachal green meadow",
    "kinnaur": "kinnaur kailash himachal apple orchards",
    "lahaul": "lahaul valley himachal barren mountains snow",
    "nubra_valley": "nubra valley ladakh sand dunes bactrian camels",
    "pangong_tso": "pangong lake ladakh blue water mountains",
    "tso_moriri": "tso moriri lake ladakh remote mountains",
    "kargil": "kargil ladakh war memorial mountains",
    "sonamarg": "sonamarg kashmir meadow of gold glaciers",
    "amritsar": "amritsar golden temple punjab sikh",
    "chandigarh": "chandigarh rock garden sukhna lake planned city",
    "haridwar": "haridwar ganga aarti river ghat crowd",
    "jim_corbett": "jim corbett national park uttarakhand wildlife safari elephant",
    "bandhavgarh": "bandhavgarh national park madhya pradesh tiger forest",
    "kanha": "kanha national park madhya pradesh wildlife sal forest",
    "gir": "gir national park gujarat asiatic lion safari",
    "somnath": "somnath temple gujarat seashore shiva",
    "dwarka": "dwarka gujarat dwarkadhish temple arabian sea",
    "ajmer": "ajmer sharif dargah rajasthan ana sagar lake",
    "bikaner": "bikaner rajasthan junagarh fort sand dunes",
    "chittorgarh": "chittorgarh fort rajasthan historical ruins",
    "kumbhalgarh": "kumbhalgarh fort rajasthan great wall of india",
    "orchha": "orchha madhya pradesh cenotaphs betwa river",
    "gwalior": "gwalior fort madhya pradesh architecture",
    "sanchi": "sanchi stupa madhya pradesh buddhist monument",
    "bhimbetka": "bhimbetka rock shelters cave paintings madhya pradesh",
    "mandu": "mandu madhya pradesh jahaz mahal afghan architecture",
    "ujjain": "ujjain mahakaleshwar temple shipra river madhya pradesh",
    "pachmarhi": "pachmarhi madhya pradesh waterfalls satpura hills",
    "jabalpur": "jabalpur bhedaghat marble rocks narmada river",
    "chitrakoot": "chitrakoot madhya pradesh waterfalls forest ramayana",
    "bodh_gaya": "bodh gaya bihar mahabodhi temple tree",
    "nalanda": "nalanda bihar ancient university ruins",
    "konark": "konark sun temple odisha chariot wheels",
    "puri": "puri jagannath temple odisha beach",
    "bhubaneswar": "bhubaneswar lingaraja temple odisha architecture",
    "chilika": "chilika lake odisha migratory birds dolphins",
    "araku": "araku valley andhra pradesh eastern ghats coffee",
    "belur": "belur halebidu karnataka hoysala temples intricate carvings",
    "badami": "badami cave temples karnataka red sandstone cliffs",
    "gokak": "gokak falls karnataka waterfalls suspension bridge"
}

def generate_fakes():
    tbo_map = ["DESTINATION_MAP = {"]
    emb_map = ["DESTINATION_MAP = {"]
    
    for i, (folder, query) in enumerate(DESTINATIONS.items()):
        name = folder.replace("_", " ").title()
        tbo_id = f"{folder.upper()}_FAKE_{i+1:03d}"
        
        # Determine pseudo-random hotel codes and budget
        base_h = 1000000 + i*1000
        codes = f"{base_h},{base_h+1},{base_h+2}"
        
        tbo_map.append(f'    "{tbo_id}": {{"name": "{name}", "airport": "ABC", "hotel_codes": "{codes}"}},')
        
        # Budget tier (pseudo-random based on index)
        tier = "budget" if i % 2 == 0 else ("mid-range" if i % 3 == 0 else "premium")
        emb_map.append(f'    "{folder}": {{"tbo_id": "{tbo_id}", "budget_tier": "{tier}"}},')
        
    tbo_map.append("}")
    emb_map.append("}")
    
    return "\n".join(tbo_map), "\n".join(emb_map)

tbo_str, emb_str = generate_fakes()

# 1. Update fake_tbo.py
with open("fake_tbo.py", "r") as f:
    tbo_content = f.read()

tbo_new = re.sub(r"DESTINATION_MAP = \{.*?\n\}", tbo_str, tbo_content, flags=re.DOTALL)
with open("fake_tbo.py", "w") as f:
    f.write(tbo_new)

# 2. Update generate_embeddings.py
with open("generate_embeddings.py", "r") as f:
    emb_content = f.read()

emb_new = re.sub(r"DESTINATION_MAP = \{.*?\n\}", emb_str, emb_content, flags=re.DOTALL)
with open("generate_embeddings.py", "w") as f:
    f.write(emb_new)

print("Updated mock maps.")
