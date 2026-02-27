from icrawler.builtin import BingImageCrawler
import os
import shutil
import time
import logging

# We will use the same 100 destinations from the previous script
# Extracting them dynamically from update_mappings.py or just redefining them
DESTINATIONS = [
    "goa", "andaman", "kovalam", "varkala", "pondicherry", "manali", "kasol", "coorg", 
    "munnar", "darjeeling", "spiti", "jaipur", "varanasi", "hampi", "mysore", "jodhpur", 
    "chikmagalur", "wayanad", "alleppey", "jaisalmer", "ziro", "udaipur", "leh", "rishikesh", 
    "ooty", "kerala_hills", "shimla", "mahabaleshwar", "agra", "shillong", "gulmarg", 
    "tawang", "kutch", "khajuraho", "dalhousie", "auli", "kodaikanal", "pushkar", 
    "mount_abu", "gokarna", "majuli", "lonavala", "srinagar", "pahalgam", "ranthambore", 
    "kaziranga", "sunderbans", "mathura", "kanyakumari", "rameshwaram", "tirupati", 
    "madurai", "nainital", "mussoorie", "lansdowne", "ranikhet", "almora", "kausani", 
    "dharamshala", "bir_billing", "khajjiar", "kinnaur", "lahaul", "nubra_valley", 
    "pangong_tso", "tso_moriri", "kargil", "sonamarg", "amritsar", "chandigarh", 
    "haridwar", "jim_corbett", "bandhavgarh", "kanha", "gir", "somnath", "dwarka", 
    "ajmer", "bikaner", "chittorgarh", "kumbhalgarh", "orchha", "gwalior", "sanchi", 
    "bhimbetka", "mandu", "ujjain", "pachmarhi", "jabalpur", "chitrakoot", "bodh_gaya", 
    "nalanda", "konark", "puri", "bhubaneswar", "chilika", "araku", "belur", "badami", "gokak"
]

def get_diverse_queries(dest_name):
    # Create 5 diverse queries for each destination to ensure a wide variety of aspects
    clean_name = dest_name.replace('_', ' ').title()
    return [
        f"{clean_name} famous landmark and landscape panoramas",
        f"{clean_name} traditional culture, local streets and people",
        f"{clean_name} beautiful nature outdoors scenery macro",
        f"{clean_name} unique historical architecture and buildings",
        f"{clean_name} tourist activities sunset beautiful atmospheric"
    ]

def download_diverse_100():
    print(f"Starting highly diverse download for {len(DESTINATIONS)} destinations (100 images each)...")
    
    logging.getLogger('icrawler').setLevel(logging.ERROR)
    
    for folder in DESTINATIONS:
        save_path = f"destinations/{folder}"
        os.makedirs(save_path, exist_ok=True)
        
        # Check if already downloaded sufficiently
        existing = [f for f in os.listdir(save_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        if len(existing) >= 90:
            print(f"Skipping {folder}, already has {len(existing)} images.")
            continue
            
        print(f"\n--- Downloading diverse photos for {folder} ---")
        queries = get_diverse_queries(folder)
        
        downloaded = 0
        target_per_query = 20 # 5 queries * 20 = 100 images
        
        for q_idx, query in enumerate(queries):
            print(f"  -> Query {q_idx+1}/5: {query}")
            
            try:
                crawler = BingImageCrawler(
                    storage={"root_dir": save_path},
                    feeder_threads=1,
                    parser_threads=2,
                    downloader_threads=4
                )
                crawler.crawl(
                    keyword=query,
                    max_num=target_per_query,
                    min_size=(400, 300),
                    file_idx_offset=downloaded
                )
            except Exception as e:
                print(f"     Error crawling {query}: {e}")
                
            # Count actual downloaded files to set the next offset correctly
            files = [f for f in os.listdir(save_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
            downloaded = len(files)
            
            if downloaded >= 100:
                break
                
            time.sleep(1) # Slight pause between queries
            
        # Rename securely to 1.jpg -> 100.jpg
        files = sorted([f for f in os.listdir(save_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])
        
        for i, filename in enumerate(files[:100]):
            old_path = os.path.join(save_path, filename)
            new_path = os.path.join(save_path, f"{i+1}_tmp.jpg")
            try:
                os.rename(old_path, new_path)
            except:
                pass
                
        files = sorted([f for f in os.listdir(save_path) if f.endswith('_tmp.jpg')])
        for i, filename in enumerate(files):
            old_path = os.path.join(save_path, filename)
            new_path = os.path.join(save_path, f"{i+1}.jpg")
            try:
                os.rename(old_path, new_path)
            except:
                pass
                
        print(f"✓ Done: {folder} — {len(files)} diverse photos saved")
        time.sleep(2) # Pause between destinations to avoid rate limits

if __name__ == "__main__":
    download_diverse_100()
    print("\nAll diverse downloads complete. Run generate_embeddings.py to update AI.")
