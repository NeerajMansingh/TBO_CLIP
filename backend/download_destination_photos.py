"""
download_destination_photos.py — Downloads real photos for all 30 destinations.
Uses Unsplash API (free tier) or public image URLs.

Run from the backend/ directory:
    python download_destination_photos.py

This creates the destinations/ folder structure with 8 photos per destination.
Photos are downloaded from Unsplash using search queries.

Note: Requires an Unsplash access key set as UNSPLASH_ACCESS_KEY env variable.
If no API key, falls back to generating colored placeholder images with PIL.
"""

from __future__ import annotations

import io
import logging
import os
import time
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent
DESTINATIONS_DIR = SCRIPT_DIR / "destinations"

DESTINATION_QUERIES = {
    "goa": ["Goa beach India", "Goa nightlife", "Goa Portuguese church", "Goa palm trees", "Goa sunset beach", "Goa hotel resort", "North Goa beaches", "Goa water sports"],
    "andaman": ["Andaman Islands beach turquoise", "Havelock Island Andaman", "Andaman coral reef", "Neil Island beach", "Andaman clear water", "Radhanagar beach Andaman", "Andaman Islands tropical", "Andaman scuba diving"],
    "kovalam": ["Kovalam beach Kerala", "Kovalam lighthouse beach", "Kovalam sunset", "Kerala beach golden", "Kovalam Ayurveda", "Kovalam fishing boats", "South Kerala beach", "Kovalam aerial view"],
    "varkala": ["Varkala cliff beach Kerala", "Varkala cliff cafe", "Varkala beach sunset", "Varkala bohemian", "Varkala backpacker", "Kerala cliff beach yoga", "Varkala temple beach", "Varkala north cliff"],
    "pondicherry": ["Pondicherry French quarter", "Pondicherry whitewashed buildings", "Pondicherry promenade beach", "Pondicherry colonial architecture", "Pondicherry romantic cafe", "Auroville Pondicherry", "Pondicherry street", "Pondicherry church"],
    "manali": ["Manali snow mountains", "Manali Rohtang Pass snow", "Manali pine forest", "Solang Valley Manali", "Manali Himachal Pradesh", "Manali old town", "Manali river valley", "Manali Hindu temple"],
    "kasol": ["Kasol Parvati valley", "Kasol river camping", "Kasol Himachal Pradesh", "Kheerganga trek Kasol", "Kasol pine trees river", "Kasol camping backpacker", "Parvati Valley trek", "Kasol village"],
    "coorg": ["Coorg coffee plantation Karnataka", "Coorg misty hills", "Abbey Falls Coorg", "Coorg green hills", "Coorg coffee estate", "Madikeri Coorg", "Coorg wildlife", "Coorg lush valley"],
    "munnar": ["Munnar tea gardens Kerala", "Munnar misty hills", "Munnar green tea estate", "Munnar sunrise mist", "Kundala Lake Munnar", "Munnar waterfalls", "Munnar rolling hills", "Eravikulam National Park"],
    "darjeeling": ["Darjeeling tea garden Himalayas", "Darjeeling toy train", "Kanchenjunga from Darjeeling", "Darjeeling sunrise Tiger Hill", "Darjeeling colonial charm", "Darjeeling monastery", "Darjeeling market", "Darjeeling Himalayan"],
    "spiti": ["Spiti Valley monastery", "Key Monastery Spiti", "Spiti Valley river", "Spiti cold desert", "Kaza Spiti", "Spiti Valley road trip", "Chandratal Lake Spiti", "Spiti Valley landscape"],
    "jaipur": ["Jaipur Hawa Mahal", "Amber Fort Jaipur", "Jaipur pink city", "City Palace Jaipur", "Jaipur bazaar", "Nahargarh Fort Jaipur", "Jaipur elephant heritage", "Jaipur blue pottery"],
    "varanasi": ["Varanasi Ganges ghats", "Varanasi sunrise Ganga", "Varanasi ghat ceremony", "Varanasi temple", "Varanasi boats on river", "Varanasi evening aarti", "Varanasi narrow lanes", "Varanasi Hindu pilgrimage"],
    "hampi": ["Hampi ruins Karnataka", "Hampi Virupaksha temple", "Hampi boulders landscape", "Hampi ancient ruins", "Hampi sunset", "Hampi Royal Enclosure", "Hampi stone chariot", "Hampi river coracle"],
    "mysore": ["Mysore Palace illuminated", "Mysore Dasara", "Chamundeshwari temple Mysore", "Mysore palace architecture", "Mysore zoo", "Mysore market silk", "Mysore flower market", "Mysore heritage hotel"],
    "jodhpur": ["Jodhpur blue city", "Mehrangarh Fort Jodhpur", "Jodhpur blue houses", "Jodhpur Rajasthan heritage", "Jaswant Thada Jodhpur", "Jodhpur aerial view", "Jodhpur market bazaar", "Umaid Bhawan Palace Jodhpur"],
    "chikmagalur": ["Chikmagalur coffee estate Karnataka", "Mullayanagiri peak Chikmagalur", "Chikmagalur green hills", "Hebbe Falls Chikmagalur", "Chikmagalur plantation", "Chikmagalur misty morning", "Bhadra wildlife Chikmagalur", "Chikmagalur valley"],
    "wayanad": ["Wayanad Kerala jungle", "Wayanad tribal culture", "Chembra Peak Wayanad", "Wayanad waterfalls", "Banasura Sagar Dam Wayanad", "Wayanad wildlife sanctuary", "Wayanad paddy fields", "Edakkal Caves Wayanad"],
    "alleppey": ["Alleppey backwaters houseboat Kerala", "Kerala backwaters canoe", "Alleppey lake sunset", "Alappuzha houseboat", "Kerala backwaters palm trees", "Alleppey boatrace", "Punnamada Lake", "Alleppey village backwaters"],
    "jaisalmer": ["Jaisalmer desert sand dunes", "Jaisalmer Golden Fort", "Sam Sand Dunes Jaisalmer", "Jaisalmer camel safari", "Jaisalmer night sky stars", "Jaisalmer havelis", "Jaisalmer sunset dunes", "Jaisalmer Rajasthan golden"],
    "ziro": ["Ziro Valley Arunachal Pradesh", "Ziro Apatani tribal", "Ziro valley paddy rice", "Arunachal Pradesh tribal", "Ziro music festival", "Ziro village houses", "Northeast India tribal", "Ziro green valley"],
    "udaipur": ["Udaipur lake palace", "Pichola Lake Udaipur Rajasthan", "Udaipur City Palace", "Udaipur romantic lake", "Udaipur sunset", "Udaipur Fateh Sagar Lake", "Udaipur heritage hotel", "Udaipur Rajput architecture"],
    "leh": ["Leh Ladakh monastery", "Pangong Lake Ladakh", "Leh palace Himalayas", "Ladakh landscape barren", "Nubra Valley Ladakh", "Ladakh Buddhist monastery", "Magnetic Hill Ladakh", "Shanti Stupa Leh"],
    "rishikesh": ["Rishikesh Ganges river rafting", "Rishikesh ashram", "Laxman Jhula Rishikesh", "Rishikesh yoga", "Rishikesh Ganga aarti", "Rishikesh suspension bridge", "Rishikesh Himalayas", "Rishikesh beach camping"],
    "ooty": ["Ooty tea garden Nilgiris", "Ooty lake rowboating", "Ooty botanical garden", "Ooty toy train", "Doddabetta Peak Ooty", "Ooty misty hills", "Ooty colonial bungalow", "Ooty eucalyptus forest"],
    "kerala_hills": ["Kerala spice garden hills", "Kerala Ayurveda resort", "Kerala misty green hills", "Thekkady Kerala", "Periyar Wildlife Kerala", "Kerala elephant", "Kerala waterfall green", "Kerala hilltop view"],
    "shimla": ["Shimla snow Himachal Pradesh", "Shimla Mall Road colonial", "Shimla Ridge promenade", "Jakhu Temple Shimla", "Shimla apple orchard", "Kufri Shimla snow", "Shimla toy train", "Shimla mountain view"],
    "mahabaleshwar": ["Mahabaleshwar hill station Maharashtra", "Mahabaleshwar strawberry", "Mahabaleshwar Venna Lake", "Mahabaleshwar valley view", "Mahabaleshwar waterfall", "Mapro strawberry Mahabaleshwar", "Mahabaleshwar Maharashtra", "Pratapgad Fort Mahabaleshwar"],
    "agra": ["Taj Mahal Agra sunrise", "Agra Fort red sandstone", "Taj Mahal sunset reflection", "Agra Yamuna river", "Taj Mahal architecture marble", "Mehtab Bagh Agra Taj", "Fatehpur Sikri Agra", "Taj Mahal night moonlight"],
    "shillong": ["Shillong Meghalaya hills", "Umiam Lake Shillong", "Shillong Police Bazaar", "Elephant Falls Shillong", "Cherrapunji Meghalaya", "Shillong colonial", "Meghalaya root bridge living", "Shillong music culture"],
}


PLACEHOLDER_COLORS = {
    "goa": (255, 165, 80), "andaman": (64, 183, 198), "kovalam": (245, 200, 100),
    "varkala": (255, 120, 100), "pondicherry": (255, 255, 240), "manali": (180, 200, 230),
    "kasol": (150, 200, 150), "coorg": (80, 130, 80), "munnar": (100, 180, 100),
    "darjeeling": (200, 170, 130), "spiti": (180, 170, 150), "jaipur": (255, 160, 100),
    "varanasi": (210, 140, 70), "hampi": (200, 140, 80), "mysore": (180, 120, 60),
    "jodhpur": (100, 140, 200), "chikmagalur": (90, 160, 90), "wayanad": (60, 140, 70),
    "alleppey": (80, 160, 120), "jaisalmer": (240, 200, 100), "ziro": (130, 190, 120),
    "udaipur": (200, 180, 220), "leh": (140, 160, 180), "rishikesh": (100, 180, 160),
    "ooty": (170, 210, 160), "kerala_hills": (80, 160, 100), "shimla": (200, 210, 220),
    "mahabaleshwar": (160, 200, 130), "agra": (255, 220, 180), "shillong": (130, 180, 200),
}


def create_placeholder_image(destination: str, photo_num: int, color: tuple) -> Image.Image:
    """Create a colored placeholder image with text overlay."""
    width, height = 800, 600
    img = Image.new("RGB", (width, height), color)
    draw = ImageDraw.Draw(img)

    # Add gradient overlay effect
    for y in range(height):
        alpha = int(40 * (y / height))
        draw.line([(0, y), (width, y)], fill=(0, 0, 0))

    img = Image.new("RGB", (width, height), color)
    draw = ImageDraw.Draw(img)

    # Add diagonal pattern for visual interest
    for i in range(0, width + height, 40):
        draw.line([(i, 0), (0, i)], fill=tuple(max(0, c - 30) for c in color), width=2)

    # Draw destination name
    text = f"{destination.replace('_', ' ').title()}\n#{photo_num}"
    bbox = draw.textbbox((0, 0), text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    draw.text((x + 2, y + 2), text, fill=(0, 0, 0))
    draw.text((x, y), text, fill=(255, 255, 255))

    return img


def download_unsplash_photo(query: str, access_key: str) -> bytes | None:
    """Download a random photo from Unsplash for a given query."""
    try:
        response = requests.get(
            "https://api.unsplash.com/photos/random",
            params={"query": query, "orientation": "landscape"},
            headers={"Authorization": f"Client-ID {access_key}"},
            timeout=10,
        )
        if response.status_code == 200:
            photo_data = response.json()
            photo_url = photo_data["urls"]["regular"]  # 1080px width
            img_response = requests.get(photo_url, timeout=15)
            if img_response.status_code == 200:
                return img_response.content
    except Exception as e:
        logger.warning(f"Unsplash download failed for '{query}': {e}")
    return None


def main():
    unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY")
    if unsplash_key:
        logger.info(f"Unsplash API key found — will download real photos")
    else:
        logger.info("No UNSPLASH_ACCESS_KEY found — generating placeholder images")

    for dest_folder, queries in DESTINATION_QUERIES.items():
        dest_dir = DESTINATIONS_DIR / dest_folder
        dest_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Processing: {dest_folder}")
        color = PLACEHOLDER_COLORS.get(dest_folder, (150, 150, 150))

        for i, query in enumerate(queries, 1):
            photo_path = dest_dir / f"{i}.jpg"

            if photo_path.exists():
                logger.info(f"  {i}.jpg already exists, skipping")
                continue

            if unsplash_key:
                photo_bytes = download_unsplash_photo(query, unsplash_key)
                if photo_bytes:
                    with open(photo_path, "wb") as f:
                        f.write(photo_bytes)
                    logger.info(f"  ✓ Downloaded {i}.jpg")
                    time.sleep(0.5)  # Rate limit: Unsplash free = 50 req/hr
                    continue
                else:
                    logger.warning(f"  Download failed for {query}, using placeholder")

            # Fallback: generate placeholder image
            img = create_placeholder_image(dest_folder, i, color)
            img.save(photo_path, "JPEG", quality=85)
            logger.info(f"  ✓ Created placeholder {i}.jpg")

    logger.info("\n✓ All destination photos ready!")
    logger.info(f"Photos saved in: {DESTINATIONS_DIR}")


if __name__ == "__main__":
    main()
