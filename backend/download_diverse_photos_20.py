from icrawler.builtin import BingImageCrawler
import os
import time
import shutil
import logging

# 5 diverse queries per destination, downloading 4 images each = 20 total per destination
destinations = {
    "goa": ["goa beach pristine landscape", "goa portuguese church architecture", "goa vibrant nightlife", "goa spice plantation nature", "goa local food market vibrant"],
    "andaman": ["andaman radhanagar beach white sand", "andaman cellular jail port blair", "andaman scuba diving vibrant coral reef", "andaman mangrove forest kayak", "andaman tropical island aerial view"],
    "kovalam": ["kovalam lighthouse beach sunset", "kovalam ayurveda resort massage", "kovalam sea waves rocks", "kovalam luxury beach resort aerial", "kovalam local fishing boats landscape"],
    "varkala": ["varkala red cliff beach wide shot", "varkala janardanaswamy ancient temple", "varkala cafe cliff view aesthetic", "varkala surf sunset palm trees", "varkala beach shacks evening"],
    "pondicherry": ["pondicherry yellow french town street", "pondicherry auroville matri mandir golden globe", "pondicherry promenade beach rock", "pondicherry aesthetic cafe culture", "pondicherry churches colonial architecture"],
    "manali": ["manali snow mountains rohtang pass", "manali hadimba temple wooden architecture", "manali solang valley adventure sports", "manali old town cafes cozy", "manali pine forest landscape winter"],
    "kasol": ["kasol parvati river pine trees", "kasol pine forest trek trail", "kasol hippie cafe culture vibrant", "kasol kheerganga mountain views", "kasol camping tents riverside"],
    "coorg": ["coorg coffee plantation estate green", "coorg abbey falls water waterfall", "coorg madikeri fort history", "coorg misty green hills landscape", "coorg homestay traditional architecture"],
    "munnar": ["munnar tea gardens rolling landscape", "munnar anamudi peak mist", "munnar mattupetty dam water", "munnar eravikulam national park nilgiri tahr", "munnar spice garden lush green"],
    "darjeeling": ["darjeeling toy train himalayan railway", "darjeeling kanchenjunga sunrise tiger hill", "darjeeling tea estate workers", "darjeeling peace pagoda mall road", "darjeeling colonial monastery architecture"],
    "spiti": ["spiti valley key monastery white architecture", "spiti chandratal lake blue water", "spiti barren mountains winding road", "spiti langza buddha statue landscape", "spiti high altitude desert raw nature"],
    "jaipur": ["jaipur hawa mahal pink city street", "jaipur amer fort magnificent architecture", "jaipur jal mahal lake palace", "jaipur colorful bazaar market shopping", "jaipur rajasthani food thali rich"],
    "varanasi": ["varanasi dashashwamedh ghat evening aarti crowds", "varanasi kashi vishwanath temple interior gold", "varanasi ganges sunrise boat ride peaceful", "varanasi narrow ancient streets sadhu", "varanasi silk weaving colorful traditional"],
    "hampi": ["hampi virupaksha temple stone chariot", "hampi giant boulders tungabhadra river", "hampi lotus mahal indo-islamic architecture", "hampi sunset point matanga hill panoramic", "hampi ruins ancient market street"],
    "mysore": ["mysore palace night illumination grand", "mysore chamundeshwari temple hilltop", "mysore brindavan gardens fountains", "mysore devaraja market silk spices", "mysore traditional dasara elephants grand"],
    "jodhpur": ["jodhpur mehrangarh fort majestic towering", "jodhpur blue city houses panoramic alley", "jodhpur umaid bhawan palace luxury", "jodhpur jaswant thada white marble memorial", "jodhpur desert camp rajasthani culture"],
    "chikmagalur": ["chikmagalur mullayanagiri peak trek landscape", "chikmagalur hebbe falls forest", "chikmagalur coffee estates lush green", "chikmagalur bhadra wildlife sanctuary safari", "chikmagalur homestay nature misty mountains"],
    "wayanad": ["wayanad chembra peak heart shaped lake", "wayanad edakkal caves petroglyphs", "wayanad banasura sagar dam water", "wayanad lush tea estates dense forest", "wayanad elephants wildlife sanctuary"],
    "alleppey": ["alleppey traditional houseboat backwaters", "alleppey village canoe narrow canal", "alleppey lush green paddy fields", "alleppey marari beach serene calm", "alleppey snake boat race energetic"],
    "jaisalmer": ["jaisalmer golden fort sandstone architecture", "jaisalmer sam sand dunes camel safari sunset", "jaisalmer patwon ki haveli carved facades", "jaisalmer gadisar lake sunset pavilions", "jaisalmer desert festival cultural colorful"],
    "ziro": ["ziro valley paddy fields pine hills", "ziro apatani tribe culture face tattoos", "ziro talley valley wildlife sanctuary", "ziro music festival fields tents", "ziro village bamboo houses traditional"],
    "udaipur": ["udaipur city palace lake pichola grand", "udaipur taj lake palace white marble water", "udaipur saheliyon ki bari garden fountains", "udaipur jagmandir island sunset romantic", "udaipur vintage car museum royal heritage"],
    "leh": ["leh pangong tso lake crystal blue water", "leh thiksey monastery mountain backdrop", "leh nubra valley sand dunes bactrian camel", "leh magnetic hill barren road landscape", "leh ladakh traditional food momos thukpa"],
    "rishikesh": ["rishikesh lakshman jhula suspension bridge ganges", "rishikesh triveni ghat evening aarti lamps", "rishikesh river rafting adventure whitewater", "rishikesh yoga ashram peaceful meditation", "rishikesh beatles ashram ruins graffiti"],
    "ooty": ["ooty botanical gardens vibrant flowers", "ooty nilgiri mountain railway toy train crossing", "ooty lake boating pedal boats", "ooty tea factory landscape slope", "ooty doddabetta peak viewpoint misty"],
    "kerala_hills": ["kerala vagamon pine forest serene", "kerala ponmudi misty winding hills", "kerala silent valley national park wilderness", "kerala high altitude tea estate viewpoints", "kerala hill station treehouse lush green"],
    "shimla": ["shimla mall road church square bustling", "shimla jakhu temple giant hanuman statue", "shimla snow covered mountains winter landscape", "shimla viceregal lodge colonial architecture", "shimla kuaifri winter sports snow adventure"],
    "mahabaleshwar": ["mahabaleshwar pratapgad fort historical", "mahabaleshwar venna lake boating scenic", "mahabaleshwar elephant's head point rocks", "mahabaleshwar mapro garden strawberries fresh", "mahabaleshwar lush green valleys landscape panoramic"],
    "agra": ["agra taj mahal white marble symmetrical", "agra fort red sandstone massive walls", "agra fatehpur sikri buland darwaza grand", "agra mehtab bagh sunset views taj", "agra street food chaat colorful vibrant"],
    "shillong": ["shillong elephant falls multi tiered", "shillong umiam lake expansive water", "shillong ward's lake bridge botanical", "shillong living root bridge meghalaya forest", "shillong lewduh dawki river crystal clear water"]
}

print("Cleaning up existing photos for strictly diverse fetch...")
shutil.rmtree("destinations", ignore_errors=True)

logging.getLogger('icrawler').setLevel(logging.WARNING)

IMAGES_PER_DESTINATION = 20
IMAGES_PER_QUERY = IMAGES_PER_DESTINATION // 5  # 5 queries per destination -> 4 images each

for folder, queries in destinations.items():
    save_path = f"destinations/{folder}"
    os.makedirs(save_path, exist_ok=True)
    
    print(f"Downloading {IMAGES_PER_DESTINATION} diverse photos for {folder}...")
    
    downloaded = 0
    
    for query in queries:
        crawler = BingImageCrawler(
            storage={"root_dir": save_path},
            feeder_threads=1,
            parser_threads=1,
            downloader_threads=4
        )
        # Fetch 4 diverse images per query to easily hit 20 total
        crawler.crawl(
            keyword=query,
            max_num=IMAGES_PER_QUERY + 2, # Request a few extra in case some fail to download
            min_size=(400, 300),
            file_idx_offset=downloaded
        )
        
        # Count actual downloaded files
        # Give them completely unique temp names to prevent BingCrawler from overwriting
        for file in os.listdir(save_path):
            if file.startswith("000"):
                os.rename(os.path.join(save_path, file), os.path.join(save_path, f"temp_{downloaded}_{file}"))

        files = [f for f in os.listdir(save_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        downloaded = len(files)
        
        if downloaded >= IMAGES_PER_DESTINATION:
            break
            
    # Rename securely to 1.jpg -> 20.jpg
    files = sorted([f for f in os.listdir(save_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])
    
    # Cap at 20
    for i, filename in enumerate(files[:IMAGES_PER_DESTINATION]):
        old_path = os.path.join(save_path, filename)
        new_path = os.path.join(save_path, f"{i+1}.jpg")
        os.rename(old_path, new_path)
    
    # Delete any extras over 20
    for filename in files[IMAGES_PER_DESTINATION:]:
        os.remove(os.path.join(save_path, filename))
        
    final_count = min(len(files), IMAGES_PER_DESTINATION)
    print(f"Done: {folder} — {final_count} diverse photos saved")
    time.sleep(1)

print("All diverse downloads complete.")
