import os
import requests
import time
from duckduckgo_search import DDGS

# These names match generate_embeddings.py DESTINATION_MAP exactly
DESTINATION_CONFIG = [
    ("goa beach india", "goa"),
    ("andaman islands india", "andaman"),
    ("kovalam beach kerala", "kovalam"),
    ("varkala beach kerala", "varkala"),
    ("pondicherry french quarter", "pondicherry"),
    ("manali mountains himachal", "manali"),
    ("kasol himachal pradesh", "kasol"),
    ("coorg karnataka", "coorg"),
    ("munnar kerala tea", "munnar"),
    ("darjeeling west bengal", "darjeeling"),
    ("spiti valley himachal", "spiti"),
    ("jaipur rajasthan", "jaipur"),
    ("varanasi ghats india", "varanasi"),
    ("hampi karnataka ruins", "hampi"),
    ("mysore palace karnataka", "mysore"),
    ("jodhpur blue city rajasthan", "jodhpur"),
    ("chikmagalur karnataka coffee", "chikmagalur"),
    ("wayanad kerala", "wayanad"),
    ("alleppey backwaters kerala", "alleppey"),
    ("jaisalmer desert rajasthan", "jaisalmer"),
    ("ziro valley arunachal", "ziro"),
    ("udaipur lake rajasthan", "udaipur"),
    ("leh ladakh mountains", "leh"),
    ("rishikesh uttarakhand ganges", "rishikesh"),
    ("ooty nilgiris tamil nadu", "ooty"),
    ("kerala hill stations", "kerala_hills"),
    ("shimla himachal pradesh", "shimla"),
    ("mahabaleshwar maharashtra", "mahabaleshwar"),
    ("agra taj mahal", "agra"),
    ("shillong meghalaya", "shillong")
]

def main():
    print("Deleting old placeholder images...")
    os.system("rm -rf destinations/*")
    
    print("Downloading real photos using DuckDuckGo Images...")
    with DDGS() as ddgs:
        for query, folder in DESTINATION_CONFIG:
            os.makedirs(f"destinations/{folder}", exist_ok=True)
            print(f"Searching for {folder} ({query})...")
            
            try:
                results = list(ddgs.images(query, max_results=12))
                
                downloaded = 0
                for i, res in enumerate(results):
                    if downloaded >= 8:
                        break
                        
                    img_url = res.get('image')
                    if not img_url:
                        continue
                        
                    try:
                        resp = requests.get(img_url, timeout=10)
                        if resp.status_code == 200:
                            content_type = resp.headers.get('content-type', '')
                            # Save as jpg if it's an image
                            if 'image' in content_type:
                                with open(f"destinations/{folder}/{downloaded+1}.jpg", "wb") as f:
                                    f.write(resp.content)
                                downloaded += 1
                                print(f"  ✓ Downloaded {downloaded}/8: {img_url[:60]}...")
                    except Exception as e:
                        pass
                
                if downloaded < 8:
                    print(f"  ⚠️ Only got {downloaded} images for {folder}")
                    
            except Exception as e:
                print(f"  ❌ Error searching for {folder}: {e}")
                
            time.sleep(1.5)  # Rate limiting
            
    print("All real photos downloaded.")

if __name__ == "__main__":
    main()
