from icrawler.builtin import BingImageCrawler
import os
import shutil
import time

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

def download_images():
    print(f"Starting download for {len(DESTINATIONS)} destinations (100 images each)...")
    
    for folder, query in DESTINATIONS.items():
        save_path = f"destinations/{folder}"
        os.makedirs(save_path, exist_ok=True)
        
        # Check if already downloaded (at least 50 images) to allow resuming
        existing = [f for f in os.listdir(save_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        if len(existing) >= 90:
            print(f"Skipping {folder}, already has {len(existing)} images.")
            continue
            
        print(f"Downloading 100 images for {folder}...")
        
        # icrawler outputs a lot of warnings. Suppress them.
        import logging
        logging.getLogger('icrawler').setLevel(logging.ERROR)
        
        crawler = BingImageCrawler(
            storage={"root_dir": save_path},
            feeder_threads=1,
            parser_threads=2,
            downloader_threads=4
        )
        
        try:
            crawler.crawl(
                keyword=query,
                max_num=100,
                min_size=(400, 300),
                file_idx_offset=0
            )
        except Exception as e:
            print(f"Error crawling {folder}: {e}")
            
        # Clean up files into sequential format
        files = sorted([f for f in os.listdir(save_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])
        
        # Temporary rename to avoid conflicts
        for i, filename in enumerate(files):
            old_path = os.path.join(save_path, filename)
            new_path = os.path.join(save_path, f"{i+1}_tmp.jpg")
            try:
                os.rename(old_path, new_path)
            except:
                pass
            
        # Final rename
        files = sorted([f for f in os.listdir(save_path) if f.endswith('_tmp.jpg')])
        for i, filename in enumerate(files):
            old_path = os.path.join(save_path, filename)
            new_path = os.path.join(save_path, f"{i+1}.jpg")
            try:
                os.rename(old_path, new_path)
            except:
                pass
                
        print(f"Done: {folder} — {len(files)} photos saved")
        time.sleep(1) # Small delay to not get immediately banned by Bing

if __name__ == "__main__":
    download_images()
    print("All downloads complete. You can now update the database embeddings.")
