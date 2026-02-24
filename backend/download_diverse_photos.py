from icrawler.builtin import BingImageCrawler
import os
import time
import shutil
import logging

# 4 diverse queries per destination to capture the full vibe
destinations = {
    "goa": ["goa beach pristine landscape", "goa portuguese church architecture", "goa vibrant nightlife", "goa spice plantation nature"],
    "andaman": ["andaman radhanagar beach white sand", "andaman cellular jail port blair", "andaman scuba diving vibrant coral reef", "andaman mangrove forest kayak"],
    "kovalam": ["kovalam lighthouse beach sunset", "kovalam ayurveda resort massage", "kovalam sea waves rocks", "kovalam luxury beach resort aerial"],
    "varkala": ["varkala red cliff beach wide shot", "varkala janardanaswamy ancient temple", "varkala cafe cliff view aesthetic", "varkala surf sunset palm trees"],
    "pondicherry": ["pondicherry yellow french town street", "pondicherry auroville matri mandir golden globe", "pondicherry promenade beach rock", "pondicherry aesthetic cafe culture"],
    "manali": ["manali snow mountains rohtang pass", "manali hadimba temple wooden architecture", "manali solang valley adventure sports", "manali old town cafes cozy"],
    "kasol": ["kasol parvati river pine trees", "kasol pine forest trek trail", "kasol hippie cafe culture vibrant", "kasol kheerganga mountain views"],
    "coorg": ["coorg coffee plantation estate green", "coorg abbey falls water waterfall", "coorg madikeri fort history", "coorg misty green hills landscape"],
    "munnar": ["munnar tea gardens rolling landscape", "munnar anamudi peak mist", "munnar mattupetty dam water", "munnar eravikulam national park nilgiri tahr"],
    "darjeeling": ["darjeeling toy train himalayan railway", "darjeeling kanchenjunga sunrise tiger hill", "darjeeling tea estate workers", "darjeeling peace pagoda mall road"],
    "spiti": ["spiti valley key monastery white architecture", "spiti chandratal lake blue water", "spiti barren mountains winding road", "spiti langza buddha statue landscape"],
    "jaipur": ["jaipur hawa mahal pink city street", "jaipur amer fort magnificent architecture", "jaipur jal mahal lake palace", "jaipur colorful bazaar market shopping"],
    "varanasi": ["varanasi dashashwamedh ghat evening aarti crowds", "varanasi kashi vishwanath temple interior gold", "varanasi ganges sunrise boat ride peaceful", "varanasi narrow ancient streets sadhu"],
    "hampi": ["hampi virupaksha temple stone chariot", "hampi giant boulders tungabhadra river", "hampi lotus mahal indo-islamic architecture", "hampi sunset point matanga hill panoramic"],
    "mysore": ["mysore palace night illumination grand", "mysore chamundeshwari temple hilltop", "mysore brindavan gardens fountains", "mysore devaraja market silk spices"],
    "jodhpur": ["jodhpur mehrangarh fort majestic towering", "jodhpur blue city houses panoramic alley", "jodhpur umaid bhawan palace luxury", "jodhpur jaswant thada white marble memorial"],
    "chikmagalur": ["chikmagalur mullayanagiri peak trek landscape", "chikmagalur hebbe falls forest", "chikmagalur coffee estates lush green", "chikmagalur bhadra wildlife sanctuary safari"],
    "wayanad": ["wayanad chembra peak heart shaped lake", "wayanad edakkal caves petroglyphs", "wayanad banasura sagar dam water", "wayanad lush tea estates dense forest"],
    "alleppey": ["alleppey traditional houseboat backwaters", "alleppey village canoe narrow canal", "alleppey lush green paddy fields", "alleppey marari beach serene calm"],
    "jaisalmer": ["jaisalmer golden fort sandstone architecture", "jaisalmer sam sand dunes camel safari sunset", "jaisalmer patwon ki haveli carved facades", "jaisalmer gadisar lake sunset pavilions"],
    "ziro": ["ziro valley paddy fields pine hills", "ziro apatani tribe culture face tattoos", "ziro talley valley wildlife sanctuary", "ziro music festival fields tents"],
    "udaipur": ["udaipur city palace lake pichola grand", "udaipur taj lake palace white marble water", "udaipur saheliyon ki bari garden fountains", "udaipur jagmandir island sunset romantic"],
    "leh": ["leh pangong tso lake crystal blue water", "leh thiksey monastery mountain backdrop", "leh nubra valley sand dunes bactrian camel", "leh magnetic hill barren road landscape"],
    "rishikesh": ["rishikesh lakshman jhula suspension bridge ganges", "rishikesh triveni ghat evening aarti lamps", "rishikesh river rafting adventure whitewater", "rishikesh yoga ashram peaceful meditation"],
    "ooty": ["ooty botanical gardens vibrant flowers", "ooty nilgiri mountain railway toy train crossing", "ooty lake boating pedal boats", "ooty tea factory landscape slope"],
    "kerala_hills": ["kerala vagamon pine forest serene", "kerala ponmudi misty winding hills", "kerala silent valley national park wilderness", "kerala high altitude tea estate viewpoints"],
    "shimla": ["shimla mall road church square bustling", "shimla jakhu temple giant hanuman statue", "shimla snow covered mountains winter landscape", "shimla viceregal lodge colonial architecture"],
    "mahabaleshwar": ["mahabaleshwar pratapgad fort historical", "mahabaleshwar venna lake boating scenic", "mahabaleshwar elephant's head point rocks", "mahabaleshwar mapro garden strawberries fresh"],
    "agra": ["agra taj mahal white marble symmetrical", "agra fort red sandstone massive walls", "agra fatehpur sikri buland darwaza grand", "agra mehtab bagh sunset views taj"],
    "shillong": ["shillong elephant falls multi tiered", "shillong umiam lake expansive water", "shillong ward's lake bridge botanical", "shillong living root bridge meghalaya forest"]
}

print("Cleaning up existing photos for strictly diverse fetch...")
shutil.rmtree("destinations", ignore_errors=True)

logging.getLogger('icrawler').setLevel(logging.WARNING)

for folder, queries in destinations.items():
    save_path = f"destinations/{folder}"
    os.makedirs(save_path, exist_ok=True)
    
    print(f"Downloading diverse photos for {folder}...")
    
    downloaded = 0
    # Fetch exactly 2 images per query for the 4 queries
    for query in queries:
        crawler = BingImageCrawler(
            storage={"root_dir": save_path},
            feeder_threads=1,
            parser_threads=1,
            downloader_threads=2
        )
        crawler.crawl(
            keyword=query,
            max_num=2,
            min_size=(400, 300),
            file_idx_offset=downloaded
        )
        
        # Count actual downloaded files
        files = [f for f in os.listdir(save_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        downloaded = len(files)
        if downloaded >= 8:
            break
            
    # Rename securely to 1.jpg -> 8.jpg
    files = sorted([f for f in os.listdir(save_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])
    
    for i, filename in enumerate(files[:8]):
        old_path = os.path.join(save_path, filename)
        new_path = os.path.join(save_path, f"{i+1}_tmp.jpg")
        os.rename(old_path, new_path)
        
    files = sorted([f for f in os.listdir(save_path) if f.endswith('_tmp.jpg')])
    for i, filename in enumerate(files):
        old_path = os.path.join(save_path, filename)
        new_path = os.path.join(save_path, f"{i+1}.jpg")
        os.rename(old_path, new_path)
    
    print(f"Done: {folder} — {min(len(files), 8)} diverse photos saved")
    time.sleep(1)

print("All diverse downloads complete.")
