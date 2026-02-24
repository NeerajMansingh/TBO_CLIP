from icrawler.builtin import BingImageCrawler
import os
import time
import shutil

# Matched exactly to generate_embeddings.py DESTINATION_MAP
destinations = {
    "goa": "goa beach india landscape",
    "andaman": "andaman islands beach india",
    "kovalam": "kovalam beach kerala india",
    "varkala": "varkala cliff beach kerala",
    "pondicherry": "pondicherry french colony white buildings",
    "manali": "manali snow mountains himachal pradesh",
    "kasol": "kasol parvati valley himachal",
    "coorg": "coorg coffee plantation karnataka",
    "munnar": "munnar tea gardens kerala",
    "darjeeling": "darjeeling mountains tea gardens",
    "spiti": "spiti valley mountains himachal",
    "jaipur": "jaipur pink city palace rajasthan",
    "varanasi": "varanasi ghats ganges river",
    "hampi": "hampi ruins karnataka",
    "mysore": "mysore palace karnataka",
    "jodhpur": "jodhpur mehrangarh fort rajasthan",
    "chikmagalur": "chikmagalur hills forest karnataka",
    "wayanad": "wayanad forest kerala",
    "alleppey": "alleppey backwaters houseboat kerala",
    "jaisalmer": "jaisalmer golden fort desert rajasthan",
    "ziro": "ziro valley arunachal pradesh",
    "udaipur": "udaipur lake palace rajasthan",
    "leh": "leh ladakh mountains monastery",
    "rishikesh": "rishikesh ganges river yoga",
    "ooty": "ooty nilgiris hills tamil nadu",
    "kerala_hills": "kerala hill stations mountains",
    "shimla": "shimla himachal pradesh snow",
    "mahabaleshwar": "mahabaleshwar hills maharashtra",
    "agra": "agra taj mahal architecture",
    "shillong": "shillong meghalaya hills"
}

print("Cleaning up existing placeholder photos...")
shutil.rmtree("destinations", ignore_errors=True)

for folder, query in destinations.items():
    save_path = f"destinations/{folder}"
    os.makedirs(save_path, exist_ok=True)
    
    print(f"Downloading {folder}...")
    
    crawler = BingImageCrawler(
        storage={"root_dir": save_path},
        feeder_threads=1,
        parser_threads=1,
        downloader_threads=4
    )
    
    # Temporarily suppress icrawler logging to keep output clean
    import logging
    logging.getLogger('icrawler').setLevel(logging.WARNING)
    
    crawler.crawl(
        keyword=query,
        max_num=8,
        min_size=(400, 300),
        file_idx_offset=0
    )
    
    # Rename files to 1.jpg through 8.jpg
    files = sorted([f for f in os.listdir(save_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])
    
    # icrawler often saves as 000001.jpg, etc.
    for i, filename in enumerate(files[:8]):
        old_path = os.path.join(save_path, filename)
        new_path = os.path.join(save_path, f"{i+1}_tmp.jpg")
        os.rename(old_path, new_path)
        
    # Final rename to remove the _tmp (avoids naming conflicts if files were already named 1.jpg)
    files = sorted([f for f in os.listdir(save_path) if f.endswith('_tmp.jpg')])
    for i, filename in enumerate(files):
        old_path = os.path.join(save_path, filename)
        new_path = os.path.join(save_path, f"{i+1}.jpg")
        os.rename(old_path, new_path)
    
    print(f"Done: {folder} — {min(len(files), 8)} photos saved")
    time.sleep(1)

print("All downloads complete.")
