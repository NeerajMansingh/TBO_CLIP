import os
import logging
from typing import Optional, List
import httpx
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

TBO_HOTEL_API_URL = "http://api.tbotechnology.in/TBOHolidays_HotelAPI"
TBO_FLIGHT_AUTH_URL = "http://Sharedapi.tektravels.com/SharedData.svc/rest/Authenticate"
TBO_FLIGHT_SEARCH_URL = "http://api.tektravels.com/BookingEngineService_Air/AirService.svc/rest/Search"


def _hotel_user() -> str:
    return os.getenv("TBO_HOTEL_USER", os.getenv("TBO_API_USER", "Hackathon"))


def _hotel_pass() -> str:
    return os.getenv("TBO_HOTEL_PASSWORD", os.getenv("TBO_API_PASSWORD", "Hackathon@1234"))


def _flight_user() -> str:
    return os.getenv("TBO_B2B_USER", "Hackathon")


def _flight_pass() -> str:
    return os.getenv("TBO_B2B_PASSWORD", "Hackathon@1234")

# We map 30 known destinations to TBO hotel codes and Airport Codes
DESTINATION_MAP = {
    "GOA_FAKE_001": {"name": "Goa", "airport": "GOI", "hotel_codes": "1120548,1247101,1022623,1018880"},
    "ANDAMAN_FAKE_002": {"name": "Andaman Islands", "airport": "IXZ", "hotel_codes": "1019685,1121001,1022512,1248000"},
    "KOVALAM_FAKE_003": {"name": "Kovalam", "airport": "TRV", "hotel_codes": "1121003,1121004,1121005"},
    "VARKALA_FAKE_004": {"name": "Varkala", "airport": "TRV", "hotel_codes": "1121006,1121007,1121008"},
    "PONDICHERRY_FAKE_005": {"name": "Pondicherry", "airport": "PNY", "hotel_codes": "1121009,1121010,1121011"},
    "MANALI_FAKE_006": {"name": "Manali", "airport": "KUU", "hotel_codes": "1121012,1121013,1121014"},
    "KASOL_FAKE_007": {"name": "Kasol", "airport": "KUU", "hotel_codes": "1121015,1121016,1121017"},
    "COORG_FAKE_008": {"name": "Coorg", "airport": "MYQ", "hotel_codes": "1121018,1121019,1121020"},
    "MUNNAR_FAKE_009": {"name": "Munnar", "airport": "COK", "hotel_codes": "1121021,1121022,1121023"},
    "DARJEELING_FAKE_010": {"name": "Darjeeling", "airport": "IXB", "hotel_codes": "1121024,1121025,1121026"},
    "SPITI_FAKE_011": {"name": "Spiti Valley", "airport": "KUU", "hotel_codes": "1121027,1121028,1121029"},
    "JAIPUR_FAKE_012": {"name": "Jaipur", "airport": "JAI", "hotel_codes": "1121030,1121031,1121032"},
    "VARANASI_FAKE_013": {"name": "Varanasi", "airport": "VNS", "hotel_codes": "1121033,1121034,1121035"},
    "HAMPI_FAKE_014": {"name": "Hampi", "airport": "VDY", "hotel_codes": "1121036,1121037,1121038"},
    "MYSORE_FAKE_015": {"name": "Mysore", "airport": "MYQ", "hotel_codes": "1121039,1121040,1121041"},
    "JODHPUR_FAKE_016": {"name": "Jodhpur", "airport": "JDH", "hotel_codes": "1121042,1121043,1121044"},
    "CHIKMAGALUR_FAKE_017": {"name": "Chikmagalur", "airport": "IXE", "hotel_codes": "1121045,1121046,1121047"},
    "WAYANAD_FAKE_018": {"name": "Wayanad", "airport": "CCJ", "hotel_codes": "1121048,1121049,1121050"},
    "ALLEPPEY_FAKE_019": {"name": "Alleppey", "airport": "COK", "hotel_codes": "1121051,1121052,1121053"},
    "JAISALMER_FAKE_020": {"name": "Jaisalmer", "airport": "JSA", "hotel_codes": "1121054,1121055,1121056"},
    "ZIRO_FAKE_021": {"name": "Ziro Valley", "airport": "IXJ", "hotel_codes": "1121057,1121058,1121059"},
    "UDAIPUR_FAKE_022": {"name": "UDAIPUR", "airport": "UDR", "hotel_codes": "1121060,1121061,1121062"},
    "LEH_FAKE_023": {"name": "Leh-Ladakh", "airport": "IXL", "hotel_codes": "1121063,1121064,1121065"},
    "RISHIKESH_FAKE_024": {"name": "Rishikesh", "airport": "DED", "hotel_codes": "1121066,1121067,1121068"},
    "OOTY_FAKE_025": {"name": "Ooty", "airport": "CJB", "hotel_codes": "1121069,1121070,1121071"},
    "KERALA_BACKWATERS_FAKE_026": {"name": "Kerala Hill Stations", "airport": "COK", "hotel_codes": "1121072,1121073,1121074"},
    "SHIMLA_FAKE_027": {"name": "Shimla", "airport": "SLV", "hotel_codes": "1121075,1121076,1121077"},
    "MAHABALESHWAR_FAKE_028": {"name": "Mahabaleshwar", "airport": "PNQ", "hotel_codes": "1121078,1121079,1121080"},
    "AGRA_FAKE_029": {"name": "Agra", "airport": "AGR", "hotel_codes": "1121081,1121082,1121083"},
    "SHILLONG_FAKE_030": {"name": "Shillong", "airport": "SHL", "hotel_codes": "1121084,1121085,1121086"}
}

# Geographic region clustering — stops within the same region make travel sense.
REGION_MAP: dict[str, str] = {
    "GOA_FAKE_001":              "West India",
    "ANDAMAN_FAKE_002":          "Islands",
    "KOVALAM_FAKE_003":          "South India",
    "VARKALA_FAKE_004":          "South India",
    "PONDICHERRY_FAKE_005":      "South India",
    "MANALI_FAKE_006":           "North India (Hills)",
    "KASOL_FAKE_007":            "North India (Hills)",
    "COORG_FAKE_008":            "South India",
    "MUNNAR_FAKE_009":           "South India",
    "DARJEELING_FAKE_010":       "Northeast & East",
    "SPITI_FAKE_011":            "North India (Hills)",
    "JAIPUR_FAKE_012":           "Rajasthan",
    "VARANASI_FAKE_013":         "North India (Plains)",
    "HAMPI_FAKE_014":            "South India",
    "MYSORE_FAKE_015":           "South India",
    "JODHPUR_FAKE_016":          "Rajasthan",
    "CHIKMAGALUR_FAKE_017":      "South India",
    "WAYANAD_FAKE_018":          "South India",
    "ALLEPPEY_FAKE_019":         "South India",
    "JAISALMER_FAKE_020":        "Rajasthan",
    "ZIRO_FAKE_021":             "Northeast & East",
    "UDAIPUR_FAKE_022":          "Rajasthan",
    "LEH_FAKE_023":              "North India (Hills)",
    "RISHIKESH_FAKE_024":        "North India (Hills)",
    "OOTY_FAKE_025":             "South India",
    "KERALA_BACKWATERS_FAKE_026": "South India",
    "SHIMLA_FAKE_027":           "North India (Hills)",
    "MAHABALESHWAR_FAKE_028":    "West India",
    "AGRA_FAKE_029":             "North India (Plains)",
    "SHILLONG_FAKE_030":         "Northeast & East",
}

# Logical stop-order within each region (rough travel circuit order)
_REGION_STOP_ORDER: dict[str, list[str]] = {
    "South India":        ["GOA_FAKE_001", "PONDICHERRY_FAKE_005", "OOTY_FAKE_025", "COORG_FAKE_008", "CHIKMAGALUR_FAKE_017", "HAMPI_FAKE_014", "MYSORE_FAKE_015", "WAYANAD_FAKE_018", "MUNNAR_FAKE_009", "ALLEPPEY_FAKE_019", "KOVALAM_FAKE_003", "VARKALA_FAKE_004", "KERALA_BACKWATERS_FAKE_026"],
    "Rajasthan":          ["JAIPUR_FAKE_012", "JODHPUR_FAKE_016", "JAISALMER_FAKE_020", "UDAIPUR_FAKE_022"],
    "North India (Hills)": ["SHIMLA_FAKE_027", "MANALI_FAKE_006", "KASOL_FAKE_007", "SPITI_FAKE_011", "RISHIKESH_FAKE_024", "LEH_FAKE_023"],
    "North India (Plains)": ["AGRA_FAKE_029", "VARANASI_FAKE_013"],
    "Northeast & East":   ["DARJEELING_FAKE_010", "SHILLONG_FAKE_030", "ZIRO_FAKE_021"],
    "West India":         ["GOA_FAKE_001", "MAHABALESHWAR_FAKE_028"],
    "Islands":            ["ANDAMAN_FAKE_002"],
}

ACTIVITIES_MAP: dict[str, list[dict]] = {
    "JAIPUR_FAKE_012": [
        {"id": "Ac_JAI_01", "name": "Amer Fort Guided Tour", "price": 1200, "duration": "Half Day", "description": "Explore the majestic Amer Fort with an expert guide. Walk through mirror-studded halls, secret passages, and enjoy panoramic views of Maota Lake and the Aravalli hills."},
        {"id": "Ac_JAI_02", "name": "Hot Air Balloon Safari", "price": 8500, "duration": "Early Morning", "description": "Soar above the Pink City at sunrise in a hot air balloon. Watch Jaipur's forts and palaces glow golden as the sun rises over the desert landscape — a truly unforgettable experience."},
        {"id": "Ac_JAI_03", "name": "Chokhi Dhani Cultural Evening", "price": 2500, "duration": "Evening", "description": "Immerse yourself in Rajasthani village culture with folk dances, puppet shows, camel rides, and an authentic multi-course Rajasthani thali dinner under the stars."},
        {"id": "Ac_JAI_04", "name": "City Palace & Jantar Mantar", "price": 1000, "duration": "Half Day", "description": "Visit the stunning City Palace complex and the UNESCO-listed Jantar Mantar astronomical observatory. Marvel at centuries-old instruments that still tell accurate time."},
        {"id": "Ac_JAI_05", "name": "Shopping in Johari Bazaar", "price": 500, "duration": "2-3 Hours", "description": "Wander through Jaipur's legendary jewellery market. Browse precious gemstones, handcrafted silver, traditional lac bangles, and block-printed textiles in vibrant lanes."},
    ],
    "UDAIPUR_FAKE_022": [
        {"id": "Ac_UDR_01", "name": "Lake Pichola Sunset Cruise", "price": 1500, "duration": "2 Hours", "description": "Glide across Lake Pichola as the sun sets behind the Aravalli hills. Pass the iconic Jag Mandir and Lake Palace, bathed in golden twilight — pure Udaipur magic."},
        {"id": "Ac_UDR_02", "name": "City Palace Guided Tour", "price": 800, "duration": "Half Day", "description": "Discover Rajasthan's largest palace complex perched on the banks of Lake Pichola. Explore ornate courtyards, mosaic peacock art, and sweeping lake views from the balconies."},
        {"id": "Ac_UDR_03", "name": "Sajjangarh Monsoon Palace", "price": 600, "duration": "3 Hours", "description": "Drive up to this hilltop palace built to watch monsoon clouds roll in. The panoramic sunset views over Udaipur's lake-dotted landscape are breathtaking."},
        {"id": "Ac_UDR_04", "name": "Ambrai Ghat Evening Walk", "price": 300, "duration": "Evening", "description": "Stroll along the atmospheric Ambrai Ghat at dusk. Watch the City Palace and Jag Mandir light up across the water while soaking in Udaipur's romantic waterfront ambiance."},
        {"id": "Ac_UDR_05", "name": "Vintage Car Museum", "price": 500, "duration": "1 Hour", "description": "Browse a curated collection of royal Rolls-Royces, Cadillacs, and Mercedes once owned by the Maharanas of Mewar — a fascinating peek into Udaipur's regal past."},
    ],
    "MYSORE_FAKE_015": [
        {"id": "Ac_MYS_01", "name": "Mysore Palace Night Tour", "price": 1000, "duration": "Evening", "description": "Witness the Mysore Palace illuminated by nearly 100,000 light bulbs every Sunday evening. The Indo-Saracenic architecture glows like a jewel against the night sky."},
        {"id": "Ac_MYS_02", "name": "Chamundi Hill Climb", "price": 400, "duration": "Morning", "description": "Climb 1,000 steps to the Chamundeshwari Temple atop Chamundi Hill. Pause at the massive Nandi Bull statue and enjoy sweeping views of Mysore city below."},
        {"id": "Ac_MYS_03", "name": "Silk Weaving Factory Visit", "price": 300, "duration": "2 Hours", "description": "Watch artisans create the famous Mysore silk sarees on traditional looms. Learn about the centuries-old craft and pick up authentic silk pieces directly from the weavers."},
        {"id": "Ac_MYS_04", "name": "Brindavan Gardens Fountain Show", "price": 600, "duration": "Evening", "description": "Experience the spectacular musical fountain show at Brindavan Gardens. Colourful water jets dance to music against a backdrop of terraced ornamental gardens."},
    ],
    "KOVALAM_FAKE_003": [
        {"id": "Ac_TRV_01", "name": "Lighthouse Beach Walk", "price": 200, "duration": "Evening", "description": "Take a relaxing evening walk along Kovalam's most iconic crescent beach. Climb the old lighthouse for stunning coastal views and watch fishermen return with the day's catch."},
        {"id": "Ac_TRV_02", "name": "Ayurvedic Spa Massage", "price": 4500, "duration": "Half Day", "description": "Indulge in a traditional Kerala Ayurvedic spa experience. Skilled therapists use warm herbal oils and time-honoured techniques to rejuvenate your body and mind."},
        {"id": "Ac_TRV_03", "name": "Sree Padmanabhaswamy Temple", "price": 1000, "duration": "2 Hours", "description": "Visit one of India's richest and most sacred temples, renowned for its Dravidian architecture. The massive reclining Vishnu idol and intricate stone carvings are awe-inspiring."},
        {"id": "Ac_TRV_04", "name": "Backwater Canoe Ride", "price": 2500, "duration": "Half Day", "description": "Drift through narrow Kerala backwater canals in a traditional dugout canoe. Glide past coconut groves, village homes, and vibrant birdlife in total serenity."},
    ],
    "GOA_FAKE_001": [
        {"id": "Ac_GOA_01", "name": "Dudhsagar Waterfalls Trek", "price": 3000, "duration": "Full Day", "description": "Trek through lush jungle trails to India's fifth-tallest waterfall. The milky-white cascade plunging 310 metres into an emerald pool is a jaw-dropping sight."},
        {"id": "Ac_GOA_02", "name": "Scuba Diving at Grand Island", "price": 4500, "duration": "Half Day", "description": "Dive into the crystal-clear waters off Grand Island. Explore vibrant coral reefs, swim alongside tropical fish, and discover an underwater world just off Goa's coast."},
        {"id": "Ac_GOA_03", "name": "Old Goa Churches Walk", "price": 800, "duration": "2 Hours", "description": "Walk through the UNESCO World Heritage churches of Old Goa. See the Basilica of Bom Jesus housing St. Francis Xavier's remains and the magnificent Sé Cathedral."},
        {"id": "Ac_GOA_04", "name": "Sunset Cruise on Mandovi", "price": 1200, "duration": "Evening", "description": "Cruise the Mandovi River as the sky turns shades of orange and purple. Enjoy live Goan music, complimentary drinks, and views of Panjim's colourful waterfront."},
        {"id": "Ac_GOA_05", "name": "Spice Plantation Tour", "price": 1500, "duration": "Half Day", "description": "Visit a working spice plantation in Goa's lush interior. Smell fresh cardamom, pepper, and vanilla, enjoy a traditional Goan lunch on banana leaves, and spot butterflies."},
    ],
    "ANDAMAN_FAKE_002": [
        {"id": "Ac_IXZ_01", "name": "Havelock Scuba Diving", "price": 6000, "duration": "Half Day", "description": "Dive into the pristine waters around Havelock Island. Explore coral gardens teeming with clownfish, parrotfish, and sea turtles in one of Asia's best dive sites."},
        {"id": "Ac_IXZ_02", "name": "Cellular Jail Sound & Light", "price": 800, "duration": "Evening", "description": "Relive India's freedom struggle through a powerful sound and light show at the historic Cellular Jail. The dramatic narration brings the stories of imprisoned revolutionaries to life."},
        {"id": "Ac_IXZ_03", "name": "Ross Island Tour", "price": 1500, "duration": "Half Day", "description": "Explore the hauntingly beautiful ruins of the former British administrative headquarters. Nature has reclaimed the colonial buildings, creating an atmospheric and photogenic landscape."},
        {"id": "Ac_IXZ_04", "name": "Sea Walk at North Bay", "price": 4000, "duration": "2 Hours", "description": "Walk on the ocean floor wearing a special helmet that lets you breathe underwater. Get face-to-face with colourful marine life without any diving experience needed."},
    ],
    "PONDICHERRY_FAKE_005": [
        {"id": "Ac_PNY_01", "name": "Auroville Matrimandir Visit", "price": 500, "duration": "Half Day", "description": "Visit the golden globe of Matrimandir, the spiritual heart of Auroville. Walk through the peaceful gardens and learn about this unique international township experiment."},
        {"id": "Ac_PNY_02", "name": "French Quarter Heritage Walk", "price": 800, "duration": "2 Hours", "description": "Stroll through Pondicherry's charming Ville Blanche with its pastel-coloured colonial buildings, bougainvillea-draped streets, and quaint French cafés."},
        {"id": "Ac_PNY_03", "name": "Paradise Beach Ferry & Chill", "price": 1000, "duration": "Half Day", "description": "Take a short boat ride to the secluded Paradise Beach. Relax on golden sands fringed by casuarina trees, swim in calm waters, and enjoy fresh seafood by the shore."},
        {"id": "Ac_PNY_04", "name": "Surfing Lesson at Serenity Beach", "price": 2500, "duration": "2 Hours", "description": "Catch your first wave at Serenity Beach with professional instructors. This beginner-friendly spot has consistent swells and a laid-back surf culture vibe."},
    ],

    "AGRA_FAKE_029": [
        {"id": "Ac_AGRA_01", "name": "Taj Mahal Sunrise Visit", "price": 1100, "duration": "2 Hours", "description": "Witness the marble mausoleum bathe in soft morning light. A breathtaking, crowd-free experience of the world wonder."},
        {"id": "Ac_AGRA_02", "name": "Agra Fort Historical Tour", "price": 600, "duration": "2 Hours", "description": "Explore the massive red sandstone fort, the main residence of the emperors of the Mughal Dynasty."},
        {"id": "Ac_AGRA_03", "name": "Mehtab Bagh Sunset View", "price": 300, "duration": "1 Hour", "description": "Enjoy a romantic sunset view of the Taj Mahal from across the Yamuna River in these moonlight gardens."},
        {"id": "Ac_AGRA_04", "name": "Fatehpur Sikri Excursion", "price": 1500, "duration": "Half Day", "description": "Visit the abandoned capital of the Mughals. See the Buland Darwaza and the tomb of Salim Chishti."},
        {"id": "Ac_AGRA_05", "name": "Agra Food Walk", "price": 800, "duration": "2 Hours", "description": "Taste the famous Petha and spicy chaat of Agra in the bustling streets of Sadar Bazaar."},
    ],
    "LOCAL_AJMER": [
        {"id": "Ac_AJMER_01", "name": "Ajmer Sharif Dargah Visit", "price": 0, "duration": "1 Hour", "description": "Seek blessings at the shrine of Sufi Saint Moinuddin Chishti. A spiritual experience filled with qawwalis."},
        {"id": "Ac_AJMER_02", "name": "Ana Sagar Lake Boating", "price": 300, "duration": "1 Hour", "description": "Relax on a boat ride in this artificial lake while enjoying views of the Daulat Bagh gardens."},
        {"id": "Ac_AJMER_03", "name": "Adhai Din Ka Jhonpra Tour", "price": 50, "duration": "45 Mins", "description": "Explore one of the oldest mosques in India, known for its unique Indo-Islamic architecture and calligraphy."},
        {"id": "Ac_AJMER_04", "name": "Taragarh Fort Trek", "price": 0, "duration": "3 Hours", "description": "Hike up to the Star Fort for panoramic views of the city. A great spot for history buffs and photographers."},
        {"id": "Ac_AJMER_05", "name": "Soniji Ki Nasiyan (Red Temple)", "price": 100, "duration": "1 Hour", "description": "Marvel at the golden chamber of this Jain temple, depicting the five auspicious events in the life of Tirthankaras."},
    ],
    "ALLEPPEY_FAKE_019": [
        {"id": "Ac_ALLEPPEY_01", "name": "Houseboat Day Cruise", "price": 6000, "duration": "Half Day", "description": "Drift through the backwaters on a traditional houseboat. Includes authentic Kerala lunch served on board."},
        {"id": "Ac_ALLEPPEY_02", "name": "Shikara Ride at Dawn", "price": 800, "duration": "1 Hour", "description": "Navigate narrow canals that houseboats can't reach. Watch village life wake up along the water's edge."},
        {"id": "Ac_ALLEPPEY_03", "name": "Alappuzha Beach Sunset", "price": 0, "duration": "1 Hour", "description": "Walk along the pier and watch the sun dip into the Arabian Sea. Visit the old lighthouse nearby."},
        {"id": "Ac_ALLEPPEY_04", "name": "Kayaking in Backwaters", "price": 1200, "duration": "2 Hours", "description": "Paddle through silent mangroves and lily-filled waters. An eco-friendly way to explore nature up close."},
        {"id": "Ac_ALLEPPEY_05", "name": "Kuttanad Village Walk", "price": 500, "duration": "2 Hours", "description": "Walk through the 'Rice Bowl of Kerala'. See farming below sea level and interact with local toddy tappers."},
    ],
    "LOCAL_ALMORA": [
        {"id": "Ac_ALMORA_01", "name": "Bright End Corner Sunset", "price": 0, "duration": "1 Hour", "description": "Watch a spectacular sunset over the Himalayan peaks. Dedicated to Swami Vivekananda who meditated here."},
        {"id": "Ac_ALMORA_02", "name": "Kasar Devi Temple Visit", "price": 0, "duration": "2 Hours", "description": "Visit this ancient temple known for its unique geomagnetic field. A hub for hippie culture and meditation."},
        {"id": "Ac_ALMORA_03", "name": "Binsar Wildlife Sanctuary Trip", "price": 800, "duration": "Half Day", "description": "Drive into the dense oak forests. Spot leopards and rare birds, and enjoy the view from Zero Point."},
        {"id": "Ac_ALMORA_04", "name": "Katarmal Sun Temple Trek", "price": 0, "duration": "3 Hours", "description": "Trek to the 9th-century Sun Temple complex. A quiet architectural marvel surrounded by cedar trees."},
        {"id": "Ac_ALMORA_05", "name": "Deer Park Picnic", "price": 50, "duration": "2 Hours", "description": "A gentle outing to see deer and leopards in enclosures. Perfect for a relaxing afternoon walk."},
    ],
    "LOCAL_AMRITSAR": [
        {"id": "Ac_AMRITSAR_01", "name": "Golden Temple Night Ceremony", "price": 0, "duration": "2 Hours", "description": "Witness the Palki Sahib ceremony. The temple glowing in gold reflection is a spiritually moving sight."},
        {"id": "Ac_AMRITSAR_02", "name": "Wagah Border Beating Retreat", "price": 0, "duration": "4 Hours", "description": "Cheer at the high-energy military ceremony at the India-Pakistan border. Experience patriotic fervor."},
        {"id": "Ac_AMRITSAR_03", "name": "Jallianwala Bagh Memorial", "price": 0, "duration": "1 Hour", "description": "Pay respects at the memorial garden commemorating the 1919 massacre. See the bullet marks on the walls."},
        {"id": "Ac_AMRITSAR_04", "name": "Partition Museum Tour", "price": 250, "duration": "2 Hours", "description": "Walk through the emotional history of the 1947 Partition. A world-class museum housed in the Town Hall."},
        {"id": "Ac_AMRITSAR_05", "name": "Amritsari Kulcha Food Tour", "price": 400, "duration": "1 Hour", "description": "Taste the legendary butter-drenched Kulchas and Lassi at a famous dhaba in the old city."},
    ],
    "LOCAL_ARAKU": [
        {"id": "Ac_ARAKU_01", "name": "Borra Caves Exploration", "price": 200, "duration": "2 Hours", "description": "Explore the deep limestone caves with million-year-old stalactites and stalagmites."},
        {"id": "Ac_ARAKU_02", "name": "Coffee Museum Visit", "price": 100, "duration": "1 Hour", "description": "Learn the history of coffee in Araku and taste the world-famous organic chocolates and coffee."},
        {"id": "Ac_ARAKU_03", "name": "Chaparai Water Cascade", "price": 50, "duration": "1 Hour", "description": "Slide down the smooth rocks of this scenic water cascade. A popular picnic spot for families."},
        {"id": "Ac_ARAKU_04", "name": "Padmapuram Gardens", "price": 60, "duration": "1 Hour", "description": "Ride the toy train through the botanical gardens. Stay in unique hanging tree-top cottages."},
        {"id": "Ac_ARAKU_05", "name": "Tribal Museum Tour", "price": 40, "duration": "1 Hour", "description": "Gain insight into the lifestyle and culture of the indigenous tribes of the Eastern Ghats."},
    ],
    "LOCAL_AULI": [
        {"id": "Ac_AULI_01", "name": "Auli Cable Car Ride", "price": 1000, "duration": "1 Hour", "description": "Take one of Asia's longest ropeways from Joshimath to Auli. Enjoy stunning 360-degree snow views."},
        {"id": "Ac_AULI_02", "name": "Gorson Bugyal Trek", "price": 0, "duration": "3 Hours", "description": "A scenic trek through alpine meadows and oak forests. Offers majestic views of Nanda Devi peak."},
        {"id": "Ac_AULI_03", "name": "Artificial Lake Visit", "price": 0, "duration": "1 Hour", "description": "Visit the world's highest man-made lake. The reflection of Nanda Devi in the water is picture-perfect."},
        {"id": "Ac_AULI_04", "name": "Skiing Lesson (Winter)", "price": 2000, "duration": "2 Hours", "description": "Learn the basics of skiing on the snowy slopes of Auli. Gear rental and instructor included."},
        {"id": "Ac_AULI_05", "name": "Camping Under Stars", "price": 2500, "duration": "Evening", "description": "Experience overnight camping in the meadows. Enjoy a bonfire and clear views of the Milky Way."},
    ],
    "LOCAL_BADAMI": [
        {"id": "Ac_BADAMI_01", "name": "Badami Cave Temples Tour", "price": 300, "duration": "2 Hours", "description": "Explore the magnificent rock-cut caves featuring Hindu and Jain deities carved into red sandstone."},
        {"id": "Ac_BADAMI_02", "name": "Bhutanatha Temple Sunset", "price": 0, "duration": "1 Hour", "description": "Watch the sunset at this temple complex by the Agastya Lake. The golden light on the rocks is magical."},
        {"id": "Ac_BADAMI_03", "name": "Badami Fort Hike", "price": 0, "duration": "2 Hours", "description": "Climb the steps to the fort for a bird's eye view of the town and the lake. See the ancient granaries."},
        {"id": "Ac_BADAMI_04", "name": "Agastya Lake Walk", "price": 0, "duration": "1 Hour", "description": "A peaceful walk around the holy lake believed to have healing powers. Great for photography."},
        {"id": "Ac_BADAMI_05", "name": "Archaeological Museum Visit", "price": 50, "duration": "45 Mins", "description": "View rare sculptures and inscriptions from the Chalukya dynasty era found in the region."},
    ],
    "LOCAL_BANDHAVGARH": [
        {"id": "Ac_BANDHAVGARH_01", "name": "Tala Zone Jeep Safari", "price": 5500, "duration": "3 Hours", "description": "The premium zone for tiger spotting. Traverse the dense forest and grasslands in an open jeep."},
        {"id": "Ac_BANDHAVGARH_02", "name": "Bandhavgarh Fort Trek", "price": 0, "duration": "2 Hours", "description": "Trek up to the ancient fort ruins (permission required). See the monolithic statue of Lord Vishnu."},
        {"id": "Ac_BANDHAVGARH_03", "name": "Baghel Museum Tour", "price": 100, "duration": "1 Hour", "description": "See the private collection of the Maharaja of Rewa, including the first stuffed white tiger."},
        {"id": "Ac_BANDHAVGARH_04", "name": "Village Visit & Craft", "price": 500, "duration": "2 Hours", "description": "Interact with the local tribal community. Watch them create traditional paintings and crafts."},
        {"id": "Ac_BANDHAVGARH_05", "name": "Nature Walk in Buffer Zone", "price": 1000, "duration": "2 Hours", "description": "A guided walking safari to observe birds, butterflies, and smaller mammals safely."},
    ],
    "LOCAL_BELUR": [
        {"id": "Ac_BELUR_01", "name": "Chennakeshava Temple Tour", "price": 0, "duration": "2 Hours", "description": "Marvel at the intricate Hoysala architecture. The carvings are so fine they look like sandalwood, not stone."},
        {"id": "Ac_BELUR_02", "name": "Yagachi Dam Water Sports", "price": 500, "duration": "2 Hours", "description": "Enjoy speed boating, jet skiing, or a banana boat ride at the scenic Yagachi backwaters."},
        {"id": "Ac_BELUR_03", "name": "Halebidu Twin Temple Trip", "price": 1000, "duration": "3 Hours", "description": "A short drive to the twin city Halebidu to see the Hoysaleswara Temple, a masterpiece of sculpture."},
        {"id": "Ac_BELUR_04", "name": "Doddagaddavalli Lakshmi Temple", "price": 0, "duration": "1 Hour", "description": "Visit the first temple built by the Hoysalas. It is unique for having four shrines and a peaceful vibe."},
        {"id": "Ac_BELUR_05", "name": "Soapstone Souvenir Shopping", "price": 0, "duration": "1 Hour", "description": "Browse local shops for statues carved from soapstone, the same material used in the ancient temples."},
    ],
    "LOCAL_BHIMBETKA": [
        {"id": "Ac_BHIMBETKA_01", "name": "Rock Shelters Tour", "price": 600, "duration": "2 Hours", "description": "Walk through the UNESCO World Heritage site. See prehistoric cave paintings dating back 30,000 years."},
        {"id": "Ac_BHIMBETKA_02", "name": "Auditorium Cave Visit", "price": 0, "duration": "30 Mins", "description": "Stand in the largest shelter at the site, which resembles a cathedral-like auditorium."},
        {"id": "Ac_BHIMBETKA_03", "name": "Zoo Rock Rock Paintings", "price": 0, "duration": "30 Mins", "description": "Examine the famous rock face depicting elephants, sambar, bison, and deer in ancient ochre."},
        {"id": "Ac_BHIMBETKA_04", "name": "Turtle Rock Viewpoint", "price": 0, "duration": "30 Mins", "description": "Hike to the natural rock formation that looks exactly like a giant turtle. Great for photos."},
        {"id": "Ac_BHIMBETKA_05", "name": "Ratapani Jungle Drive", "price": 1500, "duration": "2 Hours", "description": "Drive through the surrounding Ratapani Sanctuary. Keep an eye out for diverse bird species."},
    ],
    "LOCAL_BHUBANESWAR": [
        {"id": "Ac_BHUBANESWAR_01", "name": "Lingaraj Temple Darshan", "price": 0, "duration": "1 Hour", "description": "Visit the largest temple in the city, a masterpiece of Kalinga architecture (Entry limited to Hindus)."},
        {"id": "Ac_BHUBANESWAR_02", "name": "Udayagiri & Khandagiri Caves", "price": 200, "duration": "2 Hours", "description": "Explore ancient Jain rock-cut shelters. The Rani Gumpha (Queen's Cave) is the most impressive."},
        {"id": "Ac_BHUBANESWAR_03", "name": "Nandankanan Zoological Park", "price": 100, "duration": "3 Hours", "description": "Take a white tiger safari and visit the botanical gardens in this massive zoo nestled in a forest."},
        {"id": "Ac_BHUBANESWAR_04", "name": "Dhauli Shanti Stupa", "price": 0, "duration": "1 Hour", "description": "Visit the Peace Pagoda built where Emperor Ashoka renounced war. Enjoy views of the Daya River."},
        {"id": "Ac_BHUBANESWAR_05", "name": "Mukteshwar Temple", "price": 0, "duration": "45 Mins", "description": "Admire the 'Gem of Odisha Architecture'. Known for its exquisite stone archway (Torana)."},
    ],
    "LOCAL_BIKANER": [
        {"id": "Ac_BIKANER_01", "name": "Junagarh Fort Tour", "price": 500, "duration": "2 Hours", "description": "Explore the unconquered fort featuring palaces with gold leaf painting and glass inlays."},
        {"id": "Ac_BIKANER_02", "name": "Karni Mata Temple (Rat Temple)", "price": 0, "duration": "2 Hours", "description": "Visit the unique temple where thousands of rats are revered. Spotting a white rat is considered lucky."},
        {"id": "Ac_BIKANER_03", "name": "National Research Centre on Camel", "price": 100, "duration": "1 Hour", "description": "See different camel breeds and taste camel milk ice cream at this unique breeding farm."},
        {"id": "Ac_BIKANER_04", "name": "Rampuria Haveli Walk", "price": 0, "duration": "1 Hour", "description": "Walk through the old city to admire the red sandstone Havelis with intricate jali work."},
        {"id": "Ac_BIKANER_05", "name": "Desert Camel Safari", "price": 1200, "duration": "3 Hours", "description": "Ride a camel into the Thar desert at sunset. Includes tea and snacks on the dunes."},
    ],
    "LOCAL_BIR_BILLING": [
        {"id": "Ac_BIR_01", "name": "Tandem Paragliding", "price": 3000, "duration": "1 Hour", "description": "Fly from Billing (take-off) to Bir (landing). Experience one of the world's best paragliding sites."},
        {"id": "Ac_BIR_02", "name": "Palpung Sherabling Monastery", "price": 0, "duration": "1 Hour", "description": "Visit this massive monastery hidden in pine forests. Listen to the chanting of monks."},
        {"id": "Ac_BIR_03", "name": "Mountain Biking", "price": 500, "duration": "2 Hours", "description": "Rent a mountain bike and explore the winding roads connecting the Tibetan colony and tea gardens."},
        {"id": "Ac_BIR_04", "name": "Bir River Pool Chill", "price": 0, "duration": "2 Hours", "description": "Hike down to the riverside pools. A perfect spot for a cold dip and picnic."},
        {"id": "Ac_BIR_05", "name": "Toy Train Ride (Ahju)", "price": 50, "duration": "1 Hour", "description": "Take a short scenic ride on the Kangra Valley narrow gauge railway from nearby Ahju station."},
    ],
    "LOCAL_BODH_GAYA": [
        {"id": "Ac_BODHGAYA_01", "name": "Mahabodhi Temple Complex", "price": 0, "duration": "2 Hours", "description": "Visit the UNESCO site where Buddha attained enlightenment. See the Vajrasana (Diamond Throne)."},
        {"id": "Ac_BODHGAYA_02", "name": "Bodhi Tree Meditation", "price": 0, "duration": "1 Hour", "description": "Sit in silence under the sacred Fig tree, a direct descendant of the original tree from 500 BC."},
        {"id": "Ac_BODHGAYA_03", "name": "Great Buddha Statue", "price": 0, "duration": "30 Mins", "description": "Marvel at the 80-foot tall stone statue of Buddha in meditation pose."},
        {"id": "Ac_BODHGAYA_04", "name": "Thai Monastery Visit", "price": 0, "duration": "45 Mins", "description": "Admire the sloping gold roof and Thai architecture. A serene place for reflection."},
        {"id": "Ac_BODHGAYA_05", "name": "Dungeshwari Cave Temple", "price": 500, "duration": "2 Hours", "description": "Drive to the caves where Buddha meditated fastidiously before heading to Bodh Gaya."},
    ],
    "LOCAL_CHANDIGARH": [
        {"id": "Ac_CHANDIGARH_01", "name": "Nek Chand's Rock Garden", "price": 100, "duration": "2 Hours", "description": "Wander through a maze of sculptures made entirely from industrial and home waste."},
        {"id": "Ac_CHANDIGARH_02", "name": "Sukhna Lake Boating", "price": 400, "duration": "1 Hour", "description": "Paddle boat on the serene lake at the foothills of the Shivaliks. Great for sunset views."},
        {"id": "Ac_CHANDIGARH_03", "name": "Zakir Hussain Rose Garden", "price": 50, "duration": "1 Hour", "description": "Walk through Asia's largest rose garden featuring 1,600 different species of roses."},
        {"id": "Ac_CHANDIGARH_04", "name": "Capitol Complex Tour", "price": 0, "duration": "1 Hour", "description": "See Le Corbusier's architectural marvels (Open Hand Monument). Requires permit/ID."},
        {"id": "Ac_CHANDIGARH_05", "name": "Sector 17 Shopping", "price": 0, "duration": "2 Hours", "description": "Experience the open-air plaza. The heart of the city's shopping and dining scene."},
    ],
    "CHIKMAGALUR_FAKE_017": [
        {"id": "Ac_CHIKMAGALUR_01", "name": "Mullayanagiri Peak Trek", "price": 0, "duration": "3 Hours", "description": "Trek to the highest peak in Karnataka. Enjoy misty winds and a temple at the summit."},
        {"id": "Ac_CHIKMAGALUR_02", "name": "Coffee Plantation Walk", "price": 500, "duration": "2 Hours", "description": "Guided walk through a private estate. Learn about bean-to-cup processing and taste fresh coffee."},
        {"id": "Ac_CHIKMAGALUR_03", "name": "Hebbe Falls Jeep Ride", "price": 1200, "duration": "3 Hours", "description": "Take a bumpy forest jeep ride to reach the secluded and majestic Hebbe Falls."},
        {"id": "Ac_CHIKMAGALUR_04", "name": "Baba Budangiri Shrine", "price": 0, "duration": "2 Hours", "description": "Visit the mountain shrine revered by both Hindus and Muslims. Famous for its crescent-shaped range."},
        {"id": "Ac_CHIKMAGALUR_05", "name": "Hirekolale Lake Sunset", "price": 0, "duration": "1 Hour", "description": "A quiet, man-made lake surrounded by hills. Ideal for photography during the golden hour."},
    ],
    "LOCAL_CHILIKA": [
        {"id": "Ac_CHILIKA_01", "name": "Satapada Dolphin Watching", "price": 1500, "duration": "3 Hours", "description": "Take a boat to spot the endangered Irrawaddy Dolphins playing in the lagoon waters."},
        {"id": "Ac_CHILIKA_02", "name": "Kalijai Island Temple", "price": 1000, "duration": "2 Hours", "description": "Boat ride to the island temple of Goddess Kalijai, the presiding deity of the lake."},
        {"id": "Ac_CHILIKA_03", "name": "Nalabana Bird Sanctuary", "price": 1200, "duration": "3 Hours", "description": "A paradise for birdwatchers (Winter). Spot flamingos and migratory birds from a distance."},
        {"id": "Ac_CHILIKA_04", "name": "Sea Mouth Visit", "price": 0, "duration": "3 Hours", "description": "Journey to the point where the Chilika Lake meets the Bay of Bengal. A stunning natural confluence."},
        {"id": "Ac_CHILIKA_05", "name": "Mangalajodi Wetlands", "price": 1000, "duration": "2 Hours", "description": "Take a silent country boat ride. Get incredibly close to birds without disturbing them."},
    ],
    "LOCAL_CHITRAKOOT": [
        {"id": "Ac_CHITRAKOOT_01", "name": "Ramghat Boat Ride", "price": 200, "duration": "1 Hour", "description": "Take a boat on the Mandakini River. Watch the evening Aarti performed on the ghats."},
        {"id": "Ac_CHITRAKOOT_02", "name": "Kamadgiri Parikrama", "price": 0, "duration": "2 Hours", "description": "Perform the 5km circumambulation of the holy hill believed to be the abode of Lord Ram."},
        {"id": "Ac_CHITRAKOOT_03", "name": "Gupt Godavari Caves", "price": 50, "duration": "1 Hour", "description": "Walk through narrow caves with water flowing up to your ankles. A geological wonder."},
        {"id": "Ac_CHITRAKOOT_04", "name": "Hanuman Dhara Trek", "price": 0, "duration": "2 Hours", "description": "Climb 360 steps to see the spring falling on the idol of Hanuman. Offers great views of the town."},
        {"id": "Ac_CHITRAKOOT_05", "name": "Sati Anusuya Ashram", "price": 0, "duration": "1 Hour", "description": "Visit this serene ashram located in a dense forest area upstream of the Mandakini."},
    ],
    "LOCAL_CHITTORGARH": [
        {"id": "Ac_CHITTORGARH_01", "name": "Chittorgarh Fort Tour", "price": 500, "duration": "3 Hours", "description": "Explore Asia's largest fort complex. Hear tales of Rajput valor and Jauhar."},
        {"id": "Ac_CHITTORGARH_02", "name": "Vijay Stambh Climb", "price": 50, "duration": "45 Mins", "description": "Climb the Tower of Victory for a dizzying view of the fort and city below."},
        {"id": "Ac_CHITTORGARH_03", "name": "Padmini Palace Visit", "price": 100, "duration": "1 Hour", "description": "Visit the palace surrounded by a lotus pool, associated with the legend of Rani Padmini."},
        {"id": "Ac_CHITTORGARH_04", "name": "Gaumukh Reservoir", "price": 0, "duration": "30 Mins", "description": "Feed the fish at this sacred water tank where water flows from a cow-shaped mouth."},
        {"id": "Ac_CHITTORGARH_05", "name": "Light and Sound Show", "price": 200, "duration": "1 Hour", "description": "Watch the history of the fort come alive with lights and narration in the evening."},
    ],
    "COORG_FAKE_008": [
        {"id": "Ac_COORG_01", "name": "Dubare Elephant Camp", "price": 1000, "duration": "2 Hours", "description": "Participate in bathing and feeding elephants by the river Kaveri. A hands-on animal encounter."},
        {"id": "Ac_COORG_02", "name": "Abbey Falls Visit", "price": 50, "duration": "1 Hour", "description": "Walk through a private coffee estate to view the roaring waterfall from a hanging bridge."},
        {"id": "Ac_COORG_03", "name": "Raja's Seat Sunset", "price": 50, "duration": "1 Hour", "description": "Enjoy the sunset view that the Kings of Coorg famously loved. Surrounded by seasonal flowers."},
        {"id": "Ac_COORG_04", "name": "Talakaveri Trip", "price": 0, "duration": "3 Hours", "description": "Visit the origin of the River Kaveri atop the Brahmagiri hills. A scenic and spiritual drive."},
        {"id": "Ac_COORG_05", "name": "Golden Temple (Bylakuppe)", "price": 0, "duration": "1 Hour", "description": "Explore the Namdroling Monastery. See the 40ft golden Buddha statues and Tibetan paintings."},
    ],
    "LOCAL_DALHOUSIE": [
        {"id": "Ac_DALHOUSIE_01", "name": "Khajjiar Day Excursion", "price": 1500, "duration": "Half Day", "description": "Drive to 'Mini Switzerland'. Enjoy the green meadows, pine forests, and central lake."},
        {"id": "Ac_DALHOUSIE_02", "name": "Dainkund Peak Trek", "price": 0, "duration": "2 Hours", "description": "Easy trek to the highest point in Dalhousie. 360-degree views of the valley and mountains."},
        {"id": "Ac_DALHOUSIE_03", "name": "Panchpula Waterfall", "price": 0, "duration": "1 Hour", "description": "A nice picnic spot where five streams come together. Features a monument to freedom fighters."},
        {"id": "Ac_DALHOUSIE_04", "name": "St. John's Church", "price": 0, "duration": "30 Mins", "description": "Visit the oldest church in town. Admire the Victorian architecture and stained glass windows."},
        {"id": "Ac_DALHOUSIE_05", "name": "Kalatop Sanctuary Hike", "price": 250, "duration": "3 Hours", "description": "Walk through the dense deodar forest. Look for the Himalayan Monal and enjoy the silence."},
    ],
    "DARJEELING_FAKE_010": [
        {"id": "Ac_DARJEELING_01", "name": "Tiger Hill Sunrise", "price": 1500, "duration": "3 Hours", "description": "Wake up early to watch the sun illuminate Kanchenjunga. If lucky, spot Everest in the distance."},
        {"id": "Ac_DARJEELING_02", "name": "Toy Train Joyride", "price": 1000, "duration": "2 Hours", "description": "Ride the UNESCO heritage steam train from Darjeeling to Ghum and back. Includes the Batasia Loop."},
        {"id": "Ac_DARJEELING_03", "name": "Padmaja Naidu Zoo", "price": 100, "duration": "2 Hours", "description": "See the rare Red Panda and Snow Leopard. This is the highest altitude zoo in India."},
        {"id": "Ac_DARJEELING_04", "name": "Happy Valley Tea Estate", "price": 200, "duration": "1 Hour", "description": "Walk through the tea bushes. Watch the plucking process and buy fresh Darjeeling tea."},
        {"id": "Ac_DARJEELING_05", "name": "Japanese Peace Pagoda", "price": 0, "duration": "1 Hour", "description": "Visit the white stupa for peace of mind and excellent views of the Darjeeling landscape."},
    ],
    "LOCAL_DHARAMSHALA": [
        {"id": "Ac_DHARAMSHALA_01", "name": "HPCA Cricket Stadium", "price": 50, "duration": "45 Mins", "description": "Visit one of the world's most scenic cricket stadiums, surrounded by snow-capped Dhauladhar range."},
        {"id": "Ac_DHARAMSHALA_02", "name": "Tsuglagkhang Complex (McLeod)", "price": 0, "duration": "1 Hour", "description": "The official home of the Dalai Lama. Visit the temple, museum, and rotate the prayer wheels."},
        {"id": "Ac_DHARAMSHALA_03", "name": "Bhagsunag Waterfall", "price": 0, "duration": "1 Hour", "description": "Hike past the Shiva temple to reach the waterfall. Enjoy a coffee at the famous 'Shiva Cafe'."},
        {"id": "Ac_DHARAMSHALA_04", "name": "Norbulingka Institute", "price": 100, "duration": "2 Hours", "description": "See Tibetan artisans at work creating thangkas and wood carvings. Beautiful Japanese-style gardens."},
        {"id": "Ac_DHARAMSHALA_05", "name": "Triund Trek (Day Hike)", "price": 1500, "duration": "Full Day", "description": "A popular trek for beginners offering breathtaking views of the Dhauladhar mountains."},
    ],
    "LOCAL_DWARKA": [
        {"id": "Ac_DWARKA_01", "name": "Dwarkadhish Temple Darshan", "price": 0, "duration": "1 Hour", "description": "Worship at the main shrine of Lord Krishna. Watch the flag changing ceremony atop the shikhar."},
        {"id": "Ac_DWARKA_02", "name": "Beyt Dwarka Ferry", "price": 200, "duration": "3 Hours", "description": "Take a boat to the island believed to be Krishna's residence. Visit the old temples there."},
        {"id": "Ac_DWARKA_03", "name": "Nageshwar Jyotirlinga", "price": 0, "duration": "1 Hour", "description": "Visit one of the 12 Jyotirlingas featuring a massive statue of Lord Shiva."},
        {"id": "Ac_DWARKA_04", "name": "Rukmini Devi Temple", "price": 0, "duration": "45 Mins", "description": "Visit the temple dedicated to Krishna's wife, located 2km away from the main town due to a curse."},
        {"id": "Ac_DWARKA_05", "name": "Sudama Setu Walk", "price": 50, "duration": "30 Mins", "description": "Walk across the suspension bridge over the Gomti River for a great view of the Dwarkadhish temple."},
    ],
    "LOCAL_GIR": [
        {"id": "Ac_GIR_01", "name": "Gir Jungle Safari", "price": 4500, "duration": "3 Hours", "description": "The only place in the world to see Asiatic Lions in the wild. Book permits well in advance."},
        {"id": "Ac_GIR_02", "name": "Devalia Safari Park", "price": 500, "duration": "1 Hour", "description": "An enclosed 'interpretation zone' offering a guaranteed sighting of lions and other fauna."},
        {"id": "Ac_GIR_03", "name": "Kamleshwar Dam View", "price": 0, "duration": "1 Hour", "description": "Located inside the sanctuary, this dam is home to a large population of marsh crocodiles."},
        {"id": "Ac_GIR_04", "name": "Tribal Village Visit", "price": 300, "duration": "1 Hour", "description": "Visit the Siddi community (African origin) villages. Experience their unique culture and dance."},
        {"id": "Ac_GIR_05", "name": "Somnath Beach Trip", "price": 0, "duration": "2 Hours", "description": "Take a short drive to the nearby coast to relax after your jungle adventure."},
    ],
    "LOCAL_GOKAK": [
        {"id": "Ac_GOKAK_01", "name": "Gokak Falls View", "price": 0, "duration": "1 Hour", "description": "Known as the Niagara of India. Watch the Ghataprabha river drop 52 meters over a sandstone cliff."},
        {"id": "Ac_GOKAK_02", "name": "Suspension Bridge Walk", "price": 20, "duration": "30 Mins", "description": "Walk across the swaying 200-meter old bridge hanging high above the waterfall."},
        {"id": "Ac_GOKAK_03", "name": "Mahalingeshwara Temple", "price": 0, "duration": "45 Mins", "description": "Visit the ancient Chalukyan-style temple located near the waterfall."},
        {"id": "Ac_GOKAK_04", "name": "Yogikolla Tunnel", "price": 0, "duration": "1 Hour", "description": "A small trek to a cave temple through a narrow valley. A spiritual and scenic spot."},
        {"id": "Ac_GOKAK_05", "name": "Hidkal Dam Drive", "price": 0, "duration": "2 Hours", "description": "Drive to this massive dam nearby. Enjoy the vast expanse of water and manicured gardens."},
    ],
    "LOCAL_GOKARNA": [
        {"id": "Ac_GOKARNA_01", "name": "Om Beach Leisure", "price": 0, "duration": "2 Hours", "description": "Relax on the beach naturally shaped like the symbol 'Om'. Enjoy cafe hopping by the shore."},
        {"id": "Ac_GOKARNA_02", "name": "Mahabaleshwar Temple", "price": 0, "duration": "1 Hour", "description": "Visit the sacred temple housing the Atmalinga. A major pilgrimage site for Lord Shiva devotees."},
        {"id": "Ac_GOKARNA_03", "name": "Beach Trek (Kudle to Paradise)", "price": 0, "duration": "3 Hours", "description": "Hike across the cliff tops connecting Kudle, Om, Half Moon, and Paradise beaches. Stunning sea views."},
        {"id": "Ac_GOKARNA_04", "name": "Yana Caves Excursion", "price": 1000, "duration": "Half Day", "description": "Drive to the unique black limestone rock formations hidden in the forest. A short trek is involved."},
        {"id": "Ac_GOKARNA_05", "name": "Bio-Luminescence Spotting", "price": 0, "duration": "Evening", "description": "Visit Nirvana Beach at night (seasonal) to see the water glow with blue plankton."},
    ],
    "LOCAL_GULMARG": [
        {"id": "Ac_GULMARG_01", "name": "Gulmarg Gondola Phase 1", "price": 740, "duration": "2 Hours", "description": "Ride to Kungdoori Station. Admire the pine forests and shepherd huts from above."},
        {"id": "Ac_GULMARG_02", "name": "Gulmarg Gondola Phase 2", "price": 950, "duration": "2 Hours", "description": "Go higher to Apharwat Peak. Experience snow all year round and touch the clouds."},
        {"id": "Ac_GULMARG_03", "name": "Skiing Experience", "price": 2000, "duration": "2 Hours", "description": "Hire an instructor and ski gear. Gulmarg offers some of the best powder snow in the world."},
        {"id": "Ac_GULMARG_04", "name": "Golf Course Walk", "price": 0, "duration": "1 Hour", "description": "Walk around the highest green golf course in the world (summer only). Extremely scenic."},
        {"id": "Ac_GULMARG_05", "name": "St. Mary's Church", "price": 0, "duration": "30 Mins", "description": "Visit this Victorian-style church that looks like it belongs in a fairytale, especially when snowy."},
    ],
    "LOCAL_GWALIOR": [
        {"id": "Ac_GWALIOR_01", "name": "Gwalior Fort Tour", "price": 500, "duration": "3 Hours", "description": "Explore the 'Gibraltar of India'. Visit the Man Singh Palace with its iconic blue tiles."},
        {"id": "Ac_GWALIOR_02", "name": "Jai Vilas Palace", "price": 1500, "duration": "2 Hours", "description": "See the Scindia museum. Famous for the silver toy train that serves drinks and the massive chandelier."},
        {"id": "Ac_GWALIOR_03", "name": "Saas Bahu Temple", "price": 0, "duration": "1 Hour", "description": "Admire the intricate carvings of these twin temples (Sahastrabahu) dedicated to Vishnu."},
        {"id": "Ac_GWALIOR_04", "name": "Tansen's Tomb", "price": 0, "duration": "30 Mins", "description": "Pay homage to the legendary musician. Eating a leaf from the nearby tamarind tree is said to sweeten the voice."},
        {"id": "Ac_GWALIOR_05", "name": "Gopachal Parvat", "price": 0, "duration": "1 Hour", "description": "See the giant Jain Tirthankara statues carved into the rock face along the fort road."},
    ],
    "HAMPI_FAKE_014": [
        {"id": "Ac_HAMPI_01", "name": "Virupaksha Temple", "price": 0, "duration": "1 Hour", "description": "The only functioning ancient temple in Hampi. Meet Lakshmi, the temple elephant."},
        {"id": "Ac_HAMPI_02", "name": "Vittala Temple & Stone Chariot", "price": 600, "duration": "2 Hours", "description": "Visit the iconic Stone Chariot and the musical pillars that resonate when tapped."},
        {"id": "Ac_HAMPI_03", "name": "Coracle Ride", "price": 500, "duration": "1 Hour", "description": "Float down the Tungabhadra river in a round basket boat. See ruins from the water."},
        {"id": "Ac_HAMPI_04", "name": "Matanga Hill Sunrise", "price": 0, "duration": "2 Hours", "description": "Climb the highest point for a magical sunrise view over the entire ruin landscape."},
        {"id": "Ac_HAMPI_05", "name": "Royal Enclosure Walk", "price": 0, "duration": "2 Hours", "description": "Explore the Queen's Bath, Stepped Tank, and the Mahanavami Dibba platform."},
    ],
    "LOCAL_HARIDWAR": [
        {"id": "Ac_HARIDWAR_01", "name": "Ganga Aarti at Har Ki Pauri", "price": 0, "duration": "2 Hours", "description": "Witness the mesmerizing evening prayer with thousands of lamps floating on the Ganges."},
        {"id": "Ac_HARIDWAR_02", "name": "Mansa Devi Cable Car", "price": 150, "duration": "1 Hour", "description": "Take the ropeway to the hilltop temple. Enjoy panoramic views of the river and city."},
        {"id": "Ac_HARIDWAR_03", "name": "Chandi Devi Temple Trek", "price": 0, "duration": "2 Hours", "description": "A steep 3km trek (or ropeway) to the temple on Neel Parvat. A powerful Shakti Peeth."},
        {"id": "Ac_HARIDWAR_04", "name": "Street Food Walk", "price": 300, "duration": "1 Hour", "description": "Try the famous Aloo Puri and Halwa at Mohan Ji Puri Wale in the narrow lanes."},
        {"id": "Ac_HARIDWAR_05", "name": "Shantikunj Ashram", "price": 0, "duration": "1 Hour", "description": "Visit the headquarters of the All World Gayatri Pariwar. A very disciplined and spiritual place."},
    ],
    "LOCAL_JABALPUR": [
        {"id": "Ac_JABALPUR_01", "name": "Bhedaghat Boat Ride", "price": 500, "duration": "1 Hour", "description": "Sail between the towering Marble Rocks on the Narmada river. Best during moonlight."},
        {"id": "Ac_JABALPUR_02", "name": "Dhuandhar Falls", "price": 0, "duration": "1 Hour", "description": "Watch the 'Smoke Cascade' where the Narmada plunges down. Take the cable car for a top view."},
        {"id": "Ac_JABALPUR_03", "name": "Madan Mahal Fort", "price": 0, "duration": "1 Hour", "description": "A small hilltop fort built by the Gonds. Offers a great skyline view of Jabalpur."},
        {"id": "Ac_JABALPUR_04", "name": "Balancing Rock", "price": 0, "duration": "30 Mins", "description": "See the geological wonder where a massive rock balances precariously on another."},
        {"id": "Ac_JABALPUR_05", "name": "Chausath Yogini Temple", "price": 50, "duration": "45 Mins", "description": "Climb 108 steps to this circular temple dedicated to 64 Yoginis. One of the oldest heritage sites."},
    ],
    "JAISALMER_FAKE_020": [
        {"id": "Ac_JAISALMER_01", "name": "Jaisalmer Fort Walk", "price": 0, "duration": "2 Hours", "description": "Walk inside the 'Living Fort'. Unlike others, people still live, shop, and eat inside its walls."},
        {"id": "Ac_JAISALMER_02", "name": "Sam Sand Dunes Safari", "price": 2000, "duration": "Evening", "description": "Jeep dune bashing and camel ride at sunset. Enjoy folk dance and dinner at a desert camp."},
        {"id": "Ac_JAISALMER_03", "name": "Patwon Ki Haveli", "price": 200, "duration": "1 Hour", "description": "Explore the largest and most intricate cluster of Havelis. Admire the gold-colored stone carving."},
        {"id": "Ac_JAISALMER_04", "name": "Gadisar Lake Boating", "price": 200, "duration": "1 Hour", "description": "Pedal boat in this historic rainwater lake surrounded by temples and chhatris."},
        {"id": "Ac_JAISALMER_05", "name": "Kuldhara Ghost Village", "price": 100, "duration": "2 Hours", "description": "Visit the abandoned village. Legend says it was vacated overnight due to a curse."},
    ],
    "LOCAL_JIM_CORBETT": [
        {"id": "Ac_CORBETT_01", "name": "Jeep Safari (Dhikala)", "price": 6000, "duration": "4 Hours", "description": "The prime zone for tiger sighting. Landscapes range from grasslands to riverbeds."},
        {"id": "Ac_CORBETT_02", "name": "Corbett Waterfall", "price": 100, "duration": "1 Hour", "description": "A scenic waterfall surrounded by dense teak forest. A short walk from the road."},
        {"id": "Ac_CORBETT_03", "name": "Garjiya Devi Temple", "price": 0, "duration": "1 Hour", "description": "Visit the temple perched on a large rock in the middle of the Kosi River."},
        {"id": "Ac_CORBETT_04", "name": "Corbett Museum", "price": 100, "duration": "1 Hour", "description": "Visit Jim Corbett's heritage bungalow. See his gun, cap, and manuscripts."},
        {"id": "Ac_CORBETT_05", "name": "River Rafting (Kosi)", "price": 800, "duration": "1 Hour", "description": "Enjoy Class II rapids on the Kosi river (seasonal). Fun for beginners and families."},
    ],
    "JODHPUR_FAKE_016": [
        {"id": "Ac_JODHPUR_01", "name": "Mehrangarh Fort Tour", "price": 600, "duration": "3 Hours", "description": "One of India's largest forts. See the Phool Mahal and the museum with royal palanquins."},
        {"id": "Ac_JODHPUR_02", "name": "Jaswant Thada", "price": 50, "duration": "45 Mins", "description": "Visit the white marble cenotaph built for Maharaja Jaswant Singh II. Peaceful gardens."},
        {"id": "Ac_JODHPUR_03", "name": "Umaid Bhawan Palace Museum", "price": 100, "duration": "1 Hour", "description": "Walk through the museum part of the royal residence. See the vintage car collection."},
        {"id": "Ac_JODHPUR_04", "name": "Blue City Walk", "price": 500, "duration": "2 Hours", "description": "Guided walk through the indigo-painted lanes of Navchokiya. Perfect for Instagram."},
        {"id": "Ac_JODHPUR_05", "name": "Toorji Ka Jhalra", "price": 0, "duration": "30 Mins", "description": "See the restored ancient stepwell. The intricate geometry is a marvel of engineering."},
    ],
    "LOCAL_KANHA": [
        {"id": "Ac_KANHA_01", "name": "Kanha Jungle Safari", "price": 5500, "duration": "4 Hours", "description": "Explore the inspiration for 'The Jungle Book'. Spot Barasingha and Tigers."},
        {"id": "Ac_KANHA_02", "name": "Bamni Dadar Sunset", "price": 0, "duration": "1 Hour", "description": "Known as Sunset Point. Watch the forest turn golden from this high plateau."},
        {"id": "Ac_KANHA_03", "name": "Kanha Museum", "price": 0, "duration": "45 Mins", "description": "Located inside the park, it showcases skeletons of reptiles and tigers."},
        {"id": "Ac_KANHA_04", "name": "Nature Trail Walk", "price": 500, "duration": "2 Hours", "description": "Guided walk along the Banjaar river. Learn about animal tracks and flora."},
        {"id": "Ac_KANHA_05", "name": "Night Safari (Buffer Zone)", "price": 4000, "duration": "2 Hours", "description": "Experience the jungle at night. Look for nocturnal animals like owls and civets."},
    ],
    "LOCAL_KANYAKUMARI": [
        {"id": "Ac_KANYAKUMARI_01", "name": "Vivekananda Rock Memorial", "price": 500, "duration": "2 Hours", "description": "Ferry ride to the rock island. Meditate in the hall where Swami Vivekananda meditated."},
        {"id": "Ac_KANYAKUMARI_02", "name": "Thiruvalluvar Statue View", "price": 0, "duration": "30 Mins", "description": "Get close to the massive 133-feet stone statue of the Tamil poet Saint Thiruvalluvar."},
        {"id": "Ac_KANYAKUMARI_03", "name": "Sunset & Moonrise View", "price": 0, "duration": "1 Hour", "description": "Watch the unique spectacle of the sun setting and moon rising simultaneously (full moon days)."},
        {"id": "Ac_KANYAKUMARI_04", "name": "Kumari Amman Temple", "price": 0, "duration": "1 Hour", "description": "Visit the temple of the Virgin Goddess. The diamond nose ring is said to shine out to sea."},
        {"id": "Ac_KANYAKUMARI_05", "name": "Gandhi Mandapam", "price": 20, "duration": "30 Mins", "description": "See the memorial where sun rays fall on the exact spot of Gandhi's ashes on October 2nd."},
    ],
    "LOCAL_KARGIL": [
        {"id": "Ac_KARGIL_01", "name": "Kargil War Memorial", "price": 0, "duration": "2 Hours", "description": "Pay tribute to the heroes of the 1999 war at Dras. See the Tololing & Tiger Hill peaks."},
        {"id": "Ac_KARGIL_02", "name": "Munshi Aziz Bhat Museum", "price": 100, "duration": "1 Hour", "description": "Explore artifacts of Silk Road trade history and local culture in this private museum."},
        {"id": "Ac_KARGIL_03", "name": "Mulbekh Monastery", "price": 0, "duration": "30 Mins", "description": "See the giant rock-carved Maitreya Buddha statue standing by the highway."},
        {"id": "Ac_KARGIL_04", "name": "Hunderman Village Tour", "price": 500, "duration": "2 Hours", "description": "Visit the 'Museum of Memories' in this border village that was part of Pakistan until 1971."},
        {"id": "Ac_KARGIL_05", "name": "Suru Valley Drive", "price": 1500, "duration": "3 Hours", "description": "Scenic drive towards Panikhar. Enjoy views of Nun and Kun mountain massifs."},
    ],
    "KASOL_FAKE_007": [
        {"id": "Ac_KASOL_01", "name": "Chalal Trek", "price": 0, "duration": "1 Hour", "description": "A gentle 30-minute walk from Kasol along the Parvati river to the quiet village of Chalal."},
        {"id": "Ac_KASOL_02", "name": "Manikaran Sahib Gurudwara", "price": 0, "duration": "2 Hours", "description": "Visit the holy shrine. Cook rice in the natural hot springs and enjoy the Langar."},
        {"id": "Ac_KASOL_03", "name": "Parvati River Chill", "price": 0, "duration": "2 Hours", "description": "Find a quiet rock by the roaring river. Read a book or just listen to the water."},
        {"id": "Ac_KASOL_04", "name": "Tosh Village Trip", "price": 800, "duration": "Half Day", "description": "Drive to the last motorable point and hike up to Tosh. Famous for its hippie vibe and views."},
        {"id": "Ac_KASOL_05", "name": "Malana Village Trek", "price": 1200, "duration": "Full Day", "description": "Trek to the ancient village known for its distinct democracy and taboos (Do not touch anything)."},
    ],
    "LOCAL_KAUSANI": [
        {"id": "Ac_KAUSANI_01", "name": "Himalayan Sunrise View", "price": 0, "duration": "1 Hour", "description": "Watch the sun rise over a 300km wide panoramic view of peaks like Nanda Devi and Trishul."},
        {"id": "Ac_KAUSANI_02", "name": "Anasakti Ashram", "price": 0, "duration": "1 Hour", "description": "Visit the place where Gandhi stayed and wrote his commentary on Anasakti Yoga."},
        {"id": "Ac_KAUSANI_03", "name": "Baijnath Temple Trip", "price": 500, "duration": "2 Hours", "description": "Visit the 12th-century temple complex by the Gomti river. Feed the fish in the temple pond."},
        {"id": "Ac_KAUSANI_04", "name": "Kausani Tea Estate", "price": 100, "duration": "1 Hour", "description": "Walk through the high-altitude tea gardens. Taste and buy organic Girias tea."},
        {"id": "Ac_KAUSANI_05", "name": "Sumitranandan Pant Museum", "price": 50, "duration": "45 Mins", "description": "The birthplace of the famous Hindi poet, converted into a gallery of his literary works."},
    ],
    "LOCAL_KAZIRANGA": [
        {"id": "Ac_KAZIRANGA_01", "name": "Elephant Safari Central Range", "price": 1500, "duration": "1 Hour", "description": "Ride an elephant at dawn through the tall elephant grass. Spot the rare one-horned rhinoceros up close."},
        {"id": "Ac_KAZIRANGA_02", "name": "Jeep Safari Western Range", "price": 3500, "duration": "2 Hours", "description": "Explore the Bagori range. High chance of seeing rhinos, buffaloes, and swamp deer."},
        {"id": "Ac_KAZIRANGA_03", "name": "Orchid and Biodiversity Park", "price": 200, "duration": "2 Hours", "description": "See over 500 varieties of orchids, a bamboo garden, and enjoy a cultural dance show."},
        {"id": "Ac_KAZIRANGA_04", "name": "Tea Garden Visit", "price": 0, "duration": "1 Hour", "description": "Walk through the lush Hathikuli tea estate nearby. Try the organic pepper and tea."},
        {"id": "Ac_KAZIRANGA_05", "name": "Ethnic Village Tour", "price": 300, "duration": "1 Hour", "description": "Experience the lifestyle of the Mishing tribe. See their stilted houses and weaving."},
    ],
    "KERALA_HILLS_FAKE_026": [
        {"id": "Ac_KERALA_HILLS_01", "name": "Vagamon Pine Forest", "price": 50, "duration": "1 Hour", "description": "Walk through the misty man-made pine forest. A popular filming location for movies."},
        {"id": "Ac_KERALA_HILLS_02", "name": "Idukki Arch Dam View", "price": 50, "duration": "1 Hour", "description": "View one of Asia's highest arch dams. The sheer scale of the structure between two hills is amazing."},
        {"id": "Ac_KERALA_HILLS_03", "name": "Parunthumpara Viewpoint", "price": 0, "duration": "1 Hour", "description": "Known as Eagle Rock. Offers endless views of green valleys and tea plantations."},
        {"id": "Ac_KERALA_HILLS_04", "name": "Meadows Trek", "price": 0, "duration": "2 Hours", "description": "Roll on the velvet green grassy meadows of Vagamon. Ideally done in the late afternoon."},
        {"id": "Ac_KERALA_HILLS_05", "name": "Off-Road Jeep Safari", "price": 1500, "duration": "2 Hours", "description": "Thrilling jeep ride through rocky terrains and tea estates in the hills."},
    ],
    "LOCAL_KHAJJIAR": [
        {"id": "Ac_KHAJJIAR_01", "name": "Khajjiar Lake Picnic", "price": 0, "duration": "2 Hours", "description": "Relax on the grassy saucer-shaped meadow. The floating island in the lake is a unique sight."},
        {"id": "Ac_KHAJJIAR_02", "name": "Horse Riding", "price": 400, "duration": "30 Mins", "description": "Take a horse ride around the perimeter of the meadow through the cedar trees."},
        {"id": "Ac_KHAJJIAR_03", "name": "Khajji Nag Temple", "price": 0, "duration": "30 Mins", "description": "Visit the 12th-century temple with intricate wood carvings. Dedicated to the Serpent God."},
        {"id": "Ac_KHAJJIAR_04", "name": "Zorbing", "price": 300, "duration": "15 Mins", "description": "Roll down the green slopes inside a giant plastic ball. Fun for kids and adults."},
        {"id": "Ac_KHAJJIAR_05", "name": "Kalatop Forest Trek", "price": 0, "duration": "2 Hours", "description": "Short nature walk into the sanctuary bordering the meadow. Clean air and tall trees."},
    ],
    "LOCAL_KHAJURAHO": [
        {"id": "Ac_KHAJURAHO_01", "name": "Western Group Temples", "price": 600, "duration": "2 Hours", "description": "The main complex featuring the Kandariya Mahadev Temple. Famous for erotic and spiritual carvings."},
        {"id": "Ac_KHAJURAHO_02", "name": "Light & Sound Show", "price": 300, "duration": "1 Hour", "description": "Evening show narrated by Amitabh Bachchan (Hindi). Explains the history of the Chandela dynasty."},
        {"id": "Ac_KHAJURAHO_03", "name": "Eastern Group Temples", "price": 0, "duration": "1 Hour", "description": "Visit the Jain temples (Parsvanath, Adinath). More peaceful and less crowded."},
        {"id": "Ac_KHAJURAHO_04", "name": "Raneh Falls Excursion", "price": 1000, "duration": "2 Hours", "description": "See the 'Grand Canyon of India'. Crystalline granite rocks in multi-colors along the Ken river."},
        {"id": "Ac_KHAJURAHO_05", "name": "Archaeological Museum", "price": 50, "duration": "45 Mins", "description": "View fallen sculptures and artifacts recovered from the temple sites."},
    ],
    "LOCAL_KINNAUR": [
        {"id": "Ac_KINNAUR_01", "name": "Kalpa Kinner Kailash View", "price": 0, "duration": "1 Hour", "description": "Enjoy the majestic view of the Kinner Kailash peak and the Shivling rock which changes color."},
        {"id": "Ac_KINNAUR_02", "name": "Suicide Point Roghi", "price": 0, "duration": "30 Mins", "description": "Visit the vertical cliff drop near Kalpa. Terrifyingly deep views of the Sutlej valley."},
        {"id": "Ac_KINNAUR_03", "name": "Chitkul - The Last Village", "price": 1500, "duration": "Half Day", "description": "Drive to the last inhabited village on the Indo-Tibet border. Pristine air and wooden houses."},
        {"id": "Ac_KINNAUR_04", "name": "Kamru Fort Visit", "price": 0, "duration": "1 Hour", "description": "Climb up to this tower-like fort in Sangla. Must wear a cap/waistband provided to enter."},
        {"id": "Ac_KINNAUR_05", "name": "Sangla Valley Trout Farm", "price": 100, "duration": "1 Hour", "description": "Visit the Basteri village trout farm. Cross the wooden bridge over the Baspa river."},
    ],
    "LOCAL_KODAIKANAL": [
        {"id": "Ac_KODAIKANAL_01", "name": "Kodai Lake Boating", "price": 200, "duration": "1 Hour", "description": "Row or pedal a boat in the star-shaped man-made lake. The center of Kodaikanal tourism."},
        {"id": "Ac_KODAIKANAL_02", "name": "Coaker's Walk", "price": 50, "duration": "45 Mins", "description": "A paved pedestrian path on the edge of steep slopes. Great views of the plains on a clear day."},
        {"id": "Ac_KODAIKANAL_03", "name": "Pillar Rocks Viewpoint", "price": 20, "duration": "30 Mins", "description": "See the three giant granite boulders standing vertically shoulder-to-shoulder."},
        {"id": "Ac_KODAIKANAL_04", "name": "Bryant Park Flower Show", "price": 50, "duration": "1 Hour", "description": "Wander through the botanical garden. Best visited during the summer flower bloom."},
        {"id": "Ac_KODAIKANAL_05", "name": "Guna Caves (Devil's Kitchen)", "price": 20, "duration": "1 Hour", "description": "Walk through the exposed tree roots to see the caves made famous by the movie 'Guna'."},
    ],
    "LOCAL_KONARK": [
        {"id": "Ac_KONARK_01", "name": "Sun Temple Tour", "price": 40, "duration": "2 Hours", "description": "Explore the 13th-century UNESCO site designed as a colossal chariot. Admire the intricate stone wheels."},
        {"id": "Ac_KONARK_02", "name": "Chandrabhaga Beach", "price": 0, "duration": "1 Hour", "description": "A clean, Blue Flag certified beach. Famous for its religious significance and sunrise."},
        {"id": "Ac_KONARK_03", "name": "Konark Interpretation Centre", "price": 50, "duration": "45 Mins", "description": "Learn about the history and fallen structure of the temple through interactive exhibits."},
        {"id": "Ac_KONARK_04", "name": "Marine Drive Eco Retreat", "price": 0, "duration": "1 Hour", "description": "Drive along the scenic coastal road connecting Konark and Puri."},
        {"id": "Ac_KONARK_05", "name": "ASI Museum", "price": 10, "duration": "30 Mins", "description": "See the original sculptures and fallen parts of the Sun Temple preserved here."},
    ],
    "LOCAL_KUMBHALGARH": [
        {"id": "Ac_KUMBHALGARH_01", "name": "Great Wall of India Walk", "price": 50, "duration": "2 Hours", "description": "Walk on the second longest continuous wall in the world. The fort walls are 36km long."},
        {"id": "Ac_KUMBHALGARH_02", "name": "Badal Mahal Visit", "price": 0, "duration": "1 Hour", "description": "Climb to the highest point of the fort, the 'Palace of Clouds'. Airy rooms and pastel colors."},
        {"id": "Ac_KUMBHALGARH_03", "name": "Light & Sound Show", "price": 150, "duration": "1 Hour", "description": "Evening show illuminating the massive fort walls. Learn the history of Rana Kumbha."},
        {"id": "Ac_KUMBHALGARH_04", "name": "Jungle Safari", "price": 1500, "duration": "2 Hours", "description": "Jeep safari in the Kumbhalgarh Wildlife Sanctuary. Chance to spot wolves and leopards."},
        {"id": "Ac_KUMBHALGARH_05", "name": "Neelkanth Mahadev Temple", "price": 0, "duration": "30 Mins", "description": "Visit the Shiva temple famous for its 6-foot high stone lingam."},
    ],
    "LOCAL_KUTCH": [
        {"id": "Ac_KUTCH_01", "name": "Rann Utsav (White Desert)", "price": 100, "duration": "3 Hours", "description": "Walk on the infinite white salt desert. Best experienced during full moon nights."},
        {"id": "Ac_KUTCH_02", "name": "Kala Dungar (Black Hill)", "price": 0, "duration": "2 Hours", "description": "Highest point in Kutch. Panoramic view of the Rann. Watch foxes being fed by priests."},
        {"id": "Ac_KUTCH_03", "name": "Bhujodi Village Craft", "price": 0, "duration": "2 Hours", "description": "Meet the weavers of Kutch. Buy authentic shawls and handicrafts directly from artisans."},
        {"id": "Ac_KUTCH_04", "name": "Aina Mahal Bhuj", "price": 50, "duration": "1 Hour", "description": "Visit the 'Palace of Mirrors'. An 18th-century palace showcasing European influence."},
        {"id": "Ac_KUTCH_05", "name": "Mandvi Beach & Palace", "price": 100, "duration": "2 Hours", "description": "Visit the Vijay Vilas Palace and relax on the pristine beach of Mandvi."},
    ],
    "LOCAL_LAHAUL": [
        {"id": "Ac_LAHAUL_01", "name": "Sissu Waterfall", "price": 0, "duration": "1 Hour", "description": "View the magnificent waterfall right across the Chandra river after exiting the Atal Tunnel."},
        {"id": "Ac_LAHAUL_02", "name": "Atal Tunnel Experience", "price": 0, "duration": "1 Hour", "description": "Drive through the world's highest single-tube tunnel. A marvel of engineering at 10,000 ft."},
        {"id": "Ac_LAHAUL_03", "name": "Keylong Monastery Visit", "price": 0, "duration": "1 Hour", "description": "Visit the Shashur or Kardang monastery. Enjoy views of the Bhaga valley."},
        {"id": "Ac_LAHAUL_04", "name": "Triloknath Temple", "price": 0, "duration": "2 Hours", "description": "A unique temple worshipped by both Hindus (as Shiva) and Buddhists (as Avalokiteshvara)."},
        {"id": "Ac_LAHAUL_05", "name": "Chandra River Confluence", "price": 0, "duration": "30 Mins", "description": "Stop at Tandi, the confluence of Chandra and Bhaga rivers which form the Chenab."},
    ],
    "LOCAL_LANSDOWNE": [
        {"id": "Ac_LANSDOWNE_01", "name": "Bhulla Tal Boat Ride", "price": 100, "duration": "1 Hour", "description": "A small, well-maintained lake maintained by the Army. Enjoy a quiet paddle boat ride."},
        {"id": "Ac_LANSDOWNE_02", "name": "Tip-n-Top Viewpoint", "price": 0, "duration": "1 Hour", "description": "The best vantage point in town. See the Garhwal Himalayan range and the valleys below."},
        {"id": "Ac_LANSDOWNE_03", "name": "Garhwal Rifles War Memorial", "price": 50, "duration": "45 Mins", "description": "Pay respects at the regimental center. Strict dress code and decorum apply."},
        {"id": "Ac_LANSDOWNE_04", "name": "St. Mary's Church", "price": 20, "duration": "30 Mins", "description": "Visit this British-era church converted into a small museum. Watch documentary on Lansdowne."},
        {"id": "Ac_LANSDOWNE_05", "name": "Tarkeshwar Mahadev Trip", "price": 1000, "duration": "3 Hours", "description": "Drive to this ancient Shiva temple surrounded by massive Deodar trees. Very peaceful."},
    ],
    "LOCAL_LEH": [
        {"id": "Ac_LEH_01", "name": "Leh Palace Visit", "price": 300, "duration": "1 Hour", "description": "Climb the 9-story dun-colored palace. Modeled on the Potala Palace in Lhasa."},
        {"id": "Ac_LEH_02", "name": "Shanti Stupa Sunset", "price": 0, "duration": "1 Hour", "description": "Drive up to the white domed stupa. The best place for a panoramic sunset view of Leh city."},
        {"id": "Ac_LEH_03", "name": "Hall of Fame Museum", "price": 100, "duration": "1 Hour", "description": "Run by the Indian Army. Learn about the wars in Ladakh and life of soldiers at Siachen."},
        {"id": "Ac_LEH_04", "name": "Magnetic Hill", "price": 0, "duration": "30 Mins", "description": "Park your car at the marked spot and watch it defy gravity by moving uphill."},
        {"id": "Ac_LEH_05", "name": "Spituk Monastery", "price": 0, "duration": "1 Hour", "description": "Visit the monastery near the airfield. Known for its giant statue of Goddess Kali."},
    ],
    "LOCAL_LONAVALA": [
        {"id": "Ac_LONAVALA_01", "name": "Tiger's Point", "price": 0, "duration": "1 Hour", "description": "Enjoy the cliff-top views. Famous for eating Maggi and Corn Pakodas in the mist."},
        {"id": "Ac_LONAVALA_02", "name": "Bhushi Dam", "price": 0, "duration": "2 Hours", "description": "Splash on the steps of the dam where water overflows (Monsoon only). Very popular spot."},
        {"id": "Ac_LONAVALA_03", "name": "Karla Caves", "price": 200, "duration": "2 Hours", "description": "Climb up to see ancient Buddhist rock-cut caves. Features a massive prayer hall (Chaitya)."},
        {"id": "Ac_LONAVALA_04", "name": "Sunil's Celebrity Wax Museum", "price": 200, "duration": "1 Hour", "description": "Take selfies with wax statues of celebrities. A fun indoor activity."},
        {"id": "Ac_LONAVALA_05", "name": "Lonavala Lake", "price": 0, "duration": "1 Hour", "description": "A serene lake on the outskirts. Good for bird watching and a quiet evening walk."},
    ],
    "LOCAL_MADURAI": [
        {"id": "Ac_MADURAI_01", "name": "Meenakshi Amman Temple", "price": 0, "duration": "2 Hours", "description": "Explore the vast temple complex with colorful gopurams. Visit the hall of 1000 pillars."},
        {"id": "Ac_MADURAI_02", "name": "Thirumalai Nayak Palace", "price": 50, "duration": "1 Hour", "description": "Admire the fusion of Dravidian and Islamic architecture. Massive pillars and courtyard."},
        {"id": "Ac_MADURAI_03", "name": "Gandhi Memorial Museum", "price": 0, "duration": "1 Hour", "description": "See the blood-stained dhoti worn by Gandhi during his assassination. Deeply historical."},
        {"id": "Ac_MADURAI_04", "name": "Mariamman Teppakulam", "price": 0, "duration": "30 Mins", "description": "Visit the huge temple tank. Famous for the Float Festival held in Jan/Feb."},
        {"id": "Ac_MADURAI_05", "name": "Alagar Koyil Trip", "price": 500, "duration": "2 Hours", "description": "Visit the Vishnu temple in the Alagar hills. Beware of the many monkeys!"},
    ],
    "MAHABALESHWAR_FAKE_028": [
        {"id": "Ac_MAHABALESHWAR_01", "name": "Arthur's Seat View", "price": 0, "duration": "1 Hour", "description": "The 'Queen of Points'. Throw a light cap into the valley and the wind blows it back up."},
        {"id": "Ac_MAHABALESHWAR_02", "name": "Strawberry Farm Visit", "price": 100, "duration": "1 Hour", "description": "Pluck fresh strawberries (seasonal) and enjoy strawberry cream at a local farm."},
        {"id": "Ac_MAHABALESHWAR_03", "name": "Venna Lake Boating", "price": 400, "duration": "1 Hour", "description": "Row boating on the misty lake. Enjoy street food like corn and carrots on the banks."},
        {"id": "Ac_MAHABALESHWAR_04", "name": "Mapro Garden", "price": 0, "duration": "1 Hour", "description": "Visit the famous jam factory. Buy squashes and enjoy their wood-fired pizza."},
        {"id": "Ac_MAHABALESHWAR_05", "name": "Pratapgad Fort Trip", "price": 1000, "duration": "3 Hours", "description": "Drive to the historic fort of Shivaji Maharaj. See the Bhavani temple and Afzal Khan's tomb."},
    ],
    "LOCAL_MAJULI": [
        {"id": "Ac_MAJULI_01", "name": "Satra (Monastery) Hopping", "price": 100, "duration": "3 Hours", "description": "Visit Kamalabari and Auniati Satras. See the celibate monks perform Sattriya dance."},
        {"id": "Ac_MAJULI_02", "name": "Mask Making at Samaguri", "price": 100, "duration": "1 Hour", "description": "Watch the master craftsmen create traditional bamboo masks for religious plays."},
        {"id": "Ac_MAJULI_03", "name": "Ferry Ride on Brahmaputra", "price": 20, "duration": "1 Hour", "description": "The lifeline of the island. Enjoy a rustic ride across the mighty river."},
        {"id": "Ac_MAJULI_04", "name": "Sunset at River Bank", "price": 0, "duration": "1 Hour", "description": "Watch the sun go down over the vast river. A serene, non-touristy experience."},
        {"id": "Ac_MAJULI_05", "name": "Cycling Village Tour", "price": 200, "duration": "2 Hours", "description": "Rent a cycle and ride through the mustard fields and Mishing tribal villages."},
    ],
    "MANALI_FAKE_006": [
        {"id": "Ac_MANALI_01", "name": "Solang Valley Adventure", "price": 1000, "duration": "3 Hours", "description": "Hub for paragliding, ATV rides, and skiing (winter). Take the ropeway for great views."},
        {"id": "Ac_MANALI_02", "name": "Hadimba Devi Temple", "price": 0, "duration": "1 Hour", "description": "Visit the wooden pagoda-style temple in the cedar forest. Dedicated to Bhima's wife."},
        {"id": "Ac_MANALI_03", "name": "Mall Road Stroll", "price": 0, "duration": "2 Hours", "description": "The heart of Manali. Shop for woolens and eat Trout fish at a local restaurant."},
        {"id": "Ac_MANALI_04", "name": "Vashisht Hot Springs", "price": 0, "duration": "1 Hour", "description": "Take a dip in the natural sulfur springs believed to have medicinal properties."},
        {"id": "Ac_MANALI_05", "name": "Old Manali Cafe Crawl", "price": 500, "duration": "Evening", "description": "Explore the hippie side of Manali. Live music, river-side cafes, and a chill vibe."},
    ],
    "LOCAL_MANDU": [
        {"id": "Ac_MANDU_01", "name": "Jahaz Mahal (Ship Palace)", "price": 200, "duration": "1 Hour", "description": "Explore the palace built between two artificial lakes, making it look like a floating ship."},
        {"id": "Ac_MANDU_02", "name": "Rani Roopmati Pavilion", "price": 100, "duration": "1 Hour", "description": "Perched on a cliff, it offers views of the Narmada river and Baz Bahadur's palace."},
        {"id": "Ac_MANDU_03", "name": "Hindola Mahal", "price": 0, "duration": "30 Mins", "description": "The 'Swinging Palace' known for its sloping walls that give an illusion of swaying."},
        {"id": "Ac_MANDU_04", "name": "Echo Point", "price": 0, "duration": "30 Mins", "description": "Shout out loud at the Echo Point near the Dai Ka Mahal and hear it reverberate."},
        {"id": "Ac_MANDU_05", "name": "Hoshang Shah's Tomb", "price": 0, "duration": "30 Mins", "description": "Visit India's first marble tomb. It is said to have inspired the design of the Taj Mahal."},
    ],
    "LOCAL_MATHURA": [
        {"id": "Ac_MATHURA_01", "name": "Krishna Janmabhoomi", "price": 0, "duration": "1 Hour", "description": "Visit the prison cell believed to be the birthplace of Lord Krishna. High security area."},
        {"id": "Ac_MATHURA_02", "name": "Dwarkadhish Temple", "price": 0, "duration": "45 Mins", "description": "Famous for its swing festival (Jhulan Yatra) and intricate Holi celebrations."},
        {"id": "Ac_MATHURA_03", "name": "Vishram Ghat Boat Ride", "price": 200, "duration": "1 Hour", "description": "Take a boat on the Yamuna. See the place where Krishna rested after killing Kansa."},
        {"id": "Ac_MATHURA_04", "name": "Kusum Sarovar", "price": 0, "duration": "1 Hour", "description": "A historic sandstone tank near Govardhan. Very photogenic and peaceful."},
        {"id": "Ac_MATHURA_05", "name": "Govardhan Hill Parikrama", "price": 0, "duration": "3 Hours", "description": "Do a part of the circumambulation of the sacred hill lifted by Lord Krishna."},
    ],
    "LOCAL_MOUNT_ABU": [
        {"id": "Ac_MOUNT_ABU_01", "name": "Dilwara Jain Temples", "price": 0, "duration": "2 Hours", "description": "World-famous for extraordinary marble stone carving. The details on the ceilings are unmatched."},
        {"id": "Ac_MOUNT_ABU_02", "name": "Nakki Lake Boating", "price": 300, "duration": "1 Hour", "description": "Paddle boat on the lake surrounded by hills. See the Toad Rock nearby."},
        {"id": "Ac_MOUNT_ABU_03", "name": "Guru Shikhar Peak", "price": 0, "duration": "2 Hours", "description": "Drive to the highest point in the Aravalli range. Visit the Dattatreya temple at the top."},
        {"id": "Ac_MOUNT_ABU_04", "name": "Sunset Point", "price": 0, "duration": "1 Hour", "description": "Join the crowds to watch the sun set behind the hills. A classic Mount Abu experience."},
        {"id": "Ac_MOUNT_ABU_05", "name": "Achalgarh Fort", "price": 0, "duration": "2 Hours", "description": "Explore the medieval fort and the Achaleshwar Mahadev temple with a Nandi made of 5 metals."},
    ],
    "MUNNAR_FAKE_009": [
        {"id": "Ac_MUNNAR_01", "name": "Tea Museum Visit", "price": 200, "duration": "1 Hour", "description": "Learn how tea is processed at the KDHP museum. Taste different tea varieties."},
        {"id": "Ac_MUNNAR_02", "name": "Eravikulam National Park", "price": 500, "duration": "3 Hours", "description": "Home to the endangered Nilgiri Tahr. Take the park bus to the Rajamalai viewpoint."},
        {"id": "Ac_MUNNAR_03", "name": "Mattupetty Dam", "price": 600, "duration": "1 Hour", "description": "Speed boating in the reservoir. Look out for wild elephants on the banks."},
        {"id": "Ac_MUNNAR_04", "name": "Top Station View", "price": 50, "duration": "2 Hours", "description": "Drive to the highest point on the Munnar-Kodaikanal road. View of the clouds below you."},
        {"id": "Ac_MUNNAR_05", "name": "Echo Point Fun", "price": 0, "duration": "30 Mins", "description": "Scream your name and hear it echo back from the surrounding hills. Scenic lake spot."},
    ],
    "LOCAL_MUSSOORIE": [
        {"id": "Ac_MUSSOORIE_01", "name": "Kempty Falls", "price": 50, "duration": "2 Hours", "description": "A massive waterfall with pools for bathing. Can be crowded, but iconic."},
        {"id": "Ac_MUSSOORIE_02", "name": "Gun Hill Ropeway", "price": 150, "duration": "1 Hour", "description": "Take the cable car to the second highest peak. View the Himalayan range through telescopes."},
        {"id": "Ac_MUSSOORIE_03", "name": "Mall Road Walk", "price": 0, "duration": "2 Hours", "description": "The social hub. Walk from Library to Picture Palace. Eat corn and shop for souvenirs."},
        {"id": "Ac_MUSSOORIE_04", "name": "Landour Bakehouse Trip", "price": 300, "duration": "2 Hours", "description": "Visit the quiet cantonment town of Landour. Eat at the historic bakery."},
        {"id": "Ac_MUSSOORIE_05", "name": "Company Garden", "price": 50, "duration": "1 Hour", "description": "A well-maintained garden with flowers, a wax museum, and a small artificial waterfall."},
    ],
    "LOCAL_NAINITAL": [
        {"id": "Ac_NAINITAL_01", "name": "Naini Lake Yachting", "price": 500, "duration": "1 Hour", "description": "Hire a yacht or paddle boat. The pear-shaped lake is the centerpiece of the town."},
        {"id": "Ac_NAINITAL_02", "name": "Naina Devi Temple", "price": 0, "duration": "30 Mins", "description": "Visit the Shakti Peeth located at the northern end of the lake. Destroyed by landslide and rebuilt."},
        {"id": "Ac_NAINITAL_03", "name": "Snow View Point Cable Car", "price": 300, "duration": "1 Hour", "description": "Take the aerial tramway for a view of Nanda Devi and Trishul peaks."},
        {"id": "Ac_NAINITAL_04", "name": "Pt. G.B. Pant High Altitude Zoo", "price": 100, "duration": "2 Hours", "description": "See the Siberian Tiger and Himalayan Bear. The zoo is located on a steep hill."},
        {"id": "Ac_NAINITAL_05", "name": "Tiffin Top Hike", "price": 0, "duration": "2 Hours", "description": "Hike or ride a pony to Dorothy's Seat. Offers a bird's eye view of Nainital town."},
    ],
    "LOCAL_NALANDA": [
        {"id": "Ac_NALANDA_01", "name": "Nalanda University Ruins", "price": 50, "duration": "2 Hours", "description": "Explore the red brick ruins of the ancient center of learning. See the stupas and monk cells."},
        {"id": "Ac_NALANDA_02", "name": "Hieun Tsang Memorial", "price": 50, "duration": "45 Mins", "description": "Dedicated to the Chinese traveler who studied here. Distinct Chinese architecture."},
        {"id": "Ac_NALANDA_03", "name": "Archaeological Museum", "price": 10, "duration": "1 Hour", "description": "See bronzes and statues discovered during the excavation of the university."},
        {"id": "Ac_NALANDA_04", "name": "Kundalpur Digambar Jain Temple", "price": 0, "duration": "1 Hour", "description": "Visit the birthplace of Lord Mahavira's disciple Gautam Swami. Beautiful white temples."},
        {"id": "Ac_NALANDA_05", "name": "Great Stupa Walk", "price": 0, "duration": "30 Mins", "description": "Walk around the iconic Sariputta Stupa, the most photographed structure in Nalanda."},
    ],
    "LOCAL_NUBRA_VALLEY": [
        {"id": "Ac_NUBRA_01", "name": "Hunder Sand Dunes Camel Ride", "price": 500, "duration": "1 Hour", "description": "Ride the double-humped Bactrian camel on the cold desert sand dunes."},
        {"id": "Ac_NUBRA_02", "name": "Diskit Monastery", "price": 50, "duration": "1 Hour", "description": "Visit the oldest monastery in the valley. See the giant 106ft Maitreya Buddha statue."},
        {"id": "Ac_NUBRA_03", "name": "Panamik Hot Springs", "price": 50, "duration": "1 Hour", "description": "Take a dip in the sulfur-rich hot springs near the Siachen glacier base camp."},
        {"id": "Ac_NUBRA_04", "name": "Turtuk Village Tour", "price": 0, "duration": "3 Hours", "description": "Visit the Balti village that was part of Pakistan until 1971. Unique culture and apricots."},
        {"id": "Ac_NUBRA_05", "name": "Shyok River Drive", "price": 0, "duration": "2 Hours", "description": "Scenic drive along the aqua-blue Shyok river. Incredible landscape photography."},
    ],
    "OOTY_FAKE_025": [
        {"id": "Ac_OOTY_01", "name": "Botanical Gardens", "price": 50, "duration": "1 Hour", "description": "Wander through 55 acres of lawns and rare trees. See the 20 million-year-old fossil tree."},
        {"id": "Ac_OOTY_02", "name": "Ooty Lake Boating", "price": 300, "duration": "1 Hour", "description": "A bustling spot for boating. Includes a mini-train and amusement park for kids."},
        {"id": "Ac_OOTY_03", "name": "Doddabetta Peak", "price": 20, "duration": "1 Hour", "description": "The highest peak in the Nilgiris. Offers a telescope house for sweeping views."},
        {"id": "Ac_OOTY_04", "name": "Rose Garden", "price": 40, "duration": "1 Hour", "description": "India's largest rose garden with thousands of varieties. Best blooming season is April-May."},
        {"id": "Ac_OOTY_05", "name": "Tea Factory and Museum", "price": 20, "duration": "45 Mins", "description": "See how tea leaves are processed into dust. Buy chocolate and tea at the exit."},
    ],
    "LOCAL_ORCHHA": [
        {"id": "Ac_ORCHHA_01", "name": "Jehangir Mahal Tour", "price": 200, "duration": "1 Hour", "description": "Explore the multi-story palace built to welcome Emperor Jehangir. Great views from the top."},
        {"id": "Ac_ORCHHA_02", "name": "Ram Raja Temple", "price": 0, "duration": "45 Mins", "description": "The only temple where Lord Ram is worshipped as a King. Watch the police guard of honor."},
        {"id": "Ac_ORCHHA_03", "name": "Betwa River Rafting", "price": 500, "duration": "1 Hour", "description": "Gentle rafting or boating on the Betwa river with views of the Chhatris (cenotaphs)."},
        {"id": "Ac_ORCHHA_04", "name": "Chaturbhuj Temple", "price": 0, "duration": "30 Mins", "description": "A massive temple with tall spires. Originally built for Lord Ram but now houses Radha-Krishna."},
        {"id": "Ac_ORCHHA_05", "name": "Chhatris by the River", "price": 20, "duration": "1 Hour", "description": "Visit the royal cenotaphs at sunset. The silhouette against the sky is iconic."},
    ],
    "LOCAL_PACHMARHI": [
        {"id": "Ac_PACHMARHI_01", "name": "Bee Falls Bath", "price": 50, "duration": "2 Hours", "description": "Trek down to the waterfall. The water stings like a bee, hence the name. Safe for bathing."},
        {"id": "Ac_PACHMARHI_02", "name": "Jata Shankar Cave", "price": 0, "duration": "1 Hour", "description": "A natural cave shrine with a Shiva Lingam under a rock resembling matted hair (Jata)."},
        {"id": "Ac_PACHMARHI_03", "name": "Dhoopgarh Sunset", "price": 0, "duration": "2 Hours", "description": "The highest point in the Satpuras. Watch the sun dip into the deep ravines."},
        {"id": "Ac_PACHMARHI_04", "name": "Pandav Caves", "price": 50, "duration": "30 Mins", "description": "Five ancient rock-cut caves where the Pandavas are believed to have stayed."},
        {"id": "Ac_PACHMARHI_05", "name": "Handi Khoh View", "price": 0, "duration": "30 Mins", "description": "View the deep, horse-shoe shaped ravine. Legend says it was created by a snake."},
    ],
    "LOCAL_PAHALGAM": [
        {"id": "Ac_PAHALGAM_01", "name": "Betaab Valley Visit", "price": 100, "duration": "1 Hour", "description": "Named after the Bollywood movie. Lush green meadows surrounded by snow-clad mountains."},
        {"id": "Ac_PAHALGAM_02", "name": "Aru Valley Drive", "price": 800, "duration": "2 Hours", "description": "A scenic drive to Aru. The starting point for many treks. Peaceful and less commercial."},
        {"id": "Ac_PAHALGAM_03", "name": "Lidder River Rafting", "price": 600, "duration": "1 Hour", "description": "White water rafting on the icy Lidder river. Available in short and long stretches."},
        {"id": "Ac_PAHALGAM_04", "name": "Baisaran (Mini Switzerland)", "price": 1000, "duration": "2 Hours", "description": "Ride a pony through the forest to reach this large grassy meadow."},
        {"id": "Ac_PAHALGAM_05", "name": "Mamal Temple", "price": 20, "duration": "30 Mins", "description": "Visit the 12th-century Shiva temple. One of the oldest in Kashmir."},
    ],
    "LOCAL_PANGONG_TSO": [
        {"id": "Ac_PANGONG_01", "name": "Pangong Lake View", "price": 0, "duration": "2 Hours", "description": "Witness the color-changing lake. It shifts from blue to green to turquoise."},
        {"id": "Ac_PANGONG_02", "name": "3 Idiots Point", "price": 0, "duration": "30 Mins", "description": "The famous yellow scooter spot from the movie. Popular for photo ops."},
        {"id": "Ac_PANGONG_03", "name": "Spangmik Village Walk", "price": 0, "duration": "1 Hour", "description": "Walk through the small village on the banks of the lake. See local life in harsh winter."},
        {"id": "Ac_PANGONG_04", "name": "Lakeside Camping", "price": 3000, "duration": "Evening", "description": "Stay in a tent near the lake (authorized zones only). Stargazing here is phenomenal."},
        {"id": "Ac_PANGONG_05", "name": "Marmot Spotting", "price": 0, "duration": "30 Mins", "description": "Spot the Himalayan Marmots on the way to the lake. They are often seen sunbathing."},
    ],
    "LOCAL_PURI": [
        {"id": "Ac_PURI_01", "name": "Jagannath Temple Darshan", "price": 0, "duration": "2 Hours", "description": "Visit one of the Char Dham pilgrimage sites. Taste the Mahaprasad (holy food)."},
        {"id": "Ac_PURI_02", "name": "Golden Beach Relax", "price": 0, "duration": "2 Hours", "description": "Blue Flag certified clean beach. Great for a morning swim or evening stroll."},
        {"id": "Ac_PURI_03", "name": "Swargadwar Market", "price": 0, "duration": "1 Hour", "description": "Shop for Sambalpuri textiles and shell handicrafts in the bustling market."},
        {"id": "Ac_PURI_04", "name": "Raghurajpur Artist Village", "price": 500, "duration": "3 Hours", "description": "Visit the heritage village where every house is an art studio for Pattachitra paintings."},
        {"id": "Ac_PURI_05", "name": "Chilika Lake Day Trip", "price": 2000, "duration": "Half Day", "description": "Drive to Satapada (50km) to see dolphins and the lake."},
    ],
    "LOCAL_PUSHKAR": [
        {"id": "Ac_PUSHKAR_01", "name": "Brahma Temple", "price": 0, "duration": "45 Mins", "description": "Visit one of the very few temples in the world dedicated to Lord Brahma."},
        {"id": "Ac_PUSHKAR_02", "name": "Pushkar Lake Aarti", "price": 0, "duration": "1 Hour", "description": "Sit on the ghats at sunset. Listen to the chanting and drums during the evening prayer."},
        {"id": "Ac_PUSHKAR_03", "name": "Camel Safari", "price": 500, "duration": "2 Hours", "description": "Ride a camel into the semi-desert surrounding the town. Best during the annual fair."},
        {"id": "Ac_PUSHKAR_04", "name": "Savitri Temple Trek", "price": 0, "duration": "2 Hours", "description": "Hike up the hill (or take the ropeway) for the best panoramic view of Pushkar town."},
        {"id": "Ac_PUSHKAR_05", "name": "Market Walk", "price": 0, "duration": "1 Hour", "description": "Explore the vibrant bazaar. Famous for rose products, silver jewelry, and hippie clothing."},
    ],
    "LOCAL_RAMESHWARAM": [
        {"id": "Ac_RAMESHWARAM_01", "name": "Ramanathaswamy Temple", "price": 0, "duration": "2 Hours", "description": "Walk through the longest corridor in the world with 1212 pillars. Bathe in the 22 holy wells."},
        {"id": "Ac_RAMESHWARAM_02", "name": "Dhanushkodi Ghost Town", "price": 1500, "duration": "3 Hours", "description": "Jeep ride to the ruined town destroyed by a cyclone. See the remains of the church and station."},
        {"id": "Ac_RAMESHWARAM_03", "name": "Pamban Bridge View", "price": 0, "duration": "30 Mins", "description": "Stop on the road bridge to see the railway bridge open up for ships (if lucky)."},
        {"id": "Ac_RAMESHWARAM_04", "name": "Agni Theertham", "price": 0, "duration": "1 Hour", "description": "The beach in front of the temple. Pilgrims take a dip here before entering the temple."},
        {"id": "Ac_RAMESHWARAM_05", "name": "Kalam National Memorial", "price": 20, "duration": "1 Hour", "description": "Visit the memorial of Dr. A.P.J. Abdul Kalam. See his personal items and replicas of rockets."},
    ],
    "LOCAL_RANIKHET": [
        {"id": "Ac_RANIKHET_01", "name": "Ranikhet Golf Course", "price": 150, "duration": "1 Hour", "description": "Visit one of the highest golf courses in Asia. Scenic meadows surrounded by pine forests."},
        {"id": "Ac_RANIKHET_02", "name": "Chaubatia Gardens", "price": 50, "duration": "2 Hours", "description": "Walk through apple and apricot orchards. Great views of Nanda Devi on clear days."},
        {"id": "Ac_RANIKHET_03", "name": "Jhula Devi Temple", "price": 0, "duration": "30 Mins", "description": "Famous for the thousands of bells tied by devotees whose wishes were granted."},
        {"id": "Ac_RANIKHET_04", "name": "Majkhali Picnic", "price": 0, "duration": "2 Hours", "description": "A quiet spot 12km away. Offers closer views of the Himalayan snowy peaks."},
        {"id": "Ac_RANIKHET_05", "name": "Haidakhan Babaji Temple", "price": 0, "duration": "1 Hour", "description": "Visit the ashram and temple. A very serene place for meditation with a valley view."},
    ],
    "LOCAL_RANTHAMBORE": [
        {"id": "Ac_RANTHAMBORE_01", "name": "Tiger Safari (Canter)", "price": 1500, "duration": "3 Hours", "description": "Join a group safari in an open bus. Affordable way to explore the core zones."},
        {"id": "Ac_RANTHAMBORE_02", "name": "Tiger Safari (Jeep)", "price": 3500, "duration": "3 Hours", "description": "Exclusive 6-seater jeep safari. Better maneuverability for tracking tigers."},
        {"id": "Ac_RANTHAMBORE_03", "name": "Ranthambore Fort", "price": 0, "duration": "2 Hours", "description": "Climb the UNESCO heritage fort inside the park. Incredible views and Langur monkeys."},
        {"id": "Ac_RANTHAMBORE_04", "name": "Trinetra Ganesh Temple", "price": 0, "duration": "1 Hour", "description": "Visit the famous temple inside the fort. Devotees send wedding invitations here."},
        {"id": "Ac_RANTHAMBORE_05", "name": "Padam Talao View", "price": 0, "duration": "30 Mins", "description": "See the largest lake in the park with the Jogi Mahal on its edge. Good for spotting deer."},
    ],
    "RISHIKESH_FAKE_024": [
        {"id": "Ac_RISHIKESH_01", "name": "White Water Rafting", "price": 1200, "duration": "3 Hours", "description": "Navigate the rapids of the Ganges (Shivpuri to Rishikesh). Adrenaline pumping action."},
        {"id": "Ac_RISHIKESH_02", "name": "Laxman Jhula Walk", "price": 0, "duration": "45 Mins", "description": "Walk across the iconic suspension bridge (or the new Bajrang Setu). Watch the river below."},
        {"id": "Ac_RISHIKESH_03", "name": "Beatles Ashram", "price": 600, "duration": "2 Hours", "description": "Explore the abandoned ashram where The Beatles stayed. famous for graffiti art."},
        {"id": "Ac_RISHIKESH_04", "name": "Triveni Ghat Aarti", "price": 0, "duration": "1 Hour", "description": "Attend the Maha Aarti on the banks of the Ganges. A spiritual musical experience."},
        {"id": "Ac_RISHIKESH_05", "name": "Bungee Jumping", "price": 3500, "duration": "1 Hour", "description": "Jump from India's highest fixed platform at Mohanchatti. Not for the faint-hearted."},
    ],
    "LOCAL_SANCHI": [
        {"id": "Ac_SANCHI_01", "name": "Sanchi Stupa No. 1", "price": 40, "duration": "1 Hour", "description": "Visit the Great Stupa commissioned by Ashoka. The four gateways (Toranas) are masterpieces."},
        {"id": "Ac_SANCHI_02", "name": "Ashoka Pillar", "price": 0, "duration": "15 Mins", "description": "See the remains of the polished sandstone pillar nearby the main stupa."},
        {"id": "Ac_SANCHI_03", "name": "Monastery 51", "price": 0, "duration": "30 Mins", "description": "Walk through the well-preserved brick walls of an ancient Buddhist monastery."},
        {"id": "Ac_SANCHI_04", "name": "Archaeological Museum", "price": 10, "duration": "45 Mins", "description": "See the famous four-lion capital (national emblem) and other artifacts found here."},
        {"id": "Ac_SANCHI_05", "name": "Udayagiri Caves Trip", "price": 500, "duration": "2 Hours", "description": "Short drive to see 5th-century Gupta era caves. Famous for the Varaha avatar sculpture."},
    ],
    "SHILLONG_FAKE_030": [
        {"id": "Ac_SHILLONG_01", "name": "Umiam Lake View", "price": 0, "duration": "1 Hour", "description": "Stop at the viewpoint for the massive Barapani lake. Scenic entrance to Shillong."},
        {"id": "Ac_SHILLONG_02", "name": "Elephant Falls", "price": 50, "duration": "1 Hour", "description": "A three-tiered waterfall. Walk down the stairs to see the bottom-most tier."},
        {"id": "Ac_SHILLONG_03", "name": "Shillong Peak", "price": 50, "duration": "1 Hour", "description": "The highest point in the city. Panoramic views of Shillong and Bangladesh plains."},
        {"id": "Ac_SHILLONG_04", "name": "Don Bosco Museum", "price": 200, "duration": "2 Hours", "description": "A 7-floor museum dedicated to the culture of all 8 North East states. A Skywalk on top."},
        {"id": "Ac_SHILLONG_05", "name": "Police Bazar Shopping", "price": 0, "duration": "2 Hours", "description": "Explore the central market. Try local street food like Momos and Jadoh."},
    ],
    "SHIMLA_FAKE_027": [
        {"id": "Ac_SHIMLA_01", "name": "The Ridge & Mall Road", "price": 0, "duration": "2 Hours", "description": "Walk the car-free zone. See the Scandal Point and Town Hall. No vehicles allowed."},
        {"id": "Ac_SHIMLA_02", "name": "Jakhu Temple Trek", "price": 0, "duration": "1 Hour", "description": "Hike to the Hanuman temple with a giant 108ft statue. Watch out for cheeky monkeys."},
        {"id": "Ac_SHIMLA_03", "name": "Christ Church", "price": 0, "duration": "30 Mins", "description": "Visit North India's second oldest church. Beautiful stained glass windows."},
        {"id": "Ac_SHIMLA_04", "name": "Kufri Fun World", "price": 500, "duration": "3 Hours", "description": "Drive to Kufri for go-karting and yak rides. Higher altitude and better snow in winter."},
        {"id": "Ac_SHIMLA_05", "name": "Toy Train Ride", "price": 50, "duration": "1 Hour", "description": "Take a short joyride from Shimla to Taradevi on the UNESCO heritage railway."},
    ],
    "LOCAL_SOMNATH": [
        {"id": "Ac_SOMNATH_01", "name": "Somnath Temple Jyotirlinga Darshan", "price": 0, "duration": "1 Hour", "description": "Visit the majestic first Jyotirlinga shrine. Experience spiritual peace by the Arabian Sea coastline."},
        {"id": "Ac_SOMNATH_02", "name": "Light & Sound Show", "price": 50, "duration": "1 Hour", "description": "Evening show in the temple precincts. Narrates the history of the temple's destruction and rebuilding."},
        {"id": "Ac_SOMNATH_03", "name": "Bhalka Tirth", "price": 0, "duration": "45 Mins", "description": "The sacred site where Lord Krishna was mistaken for a deer and hit by an arrow."},
        {"id": "Ac_SOMNATH_04", "name": "Triveni Sangam", "price": 0, "duration": "30 Mins", "description": "The confluence of three holy rivers: Hiran, Kapila, and Saraswati. A spot for rituals."},
        {"id": "Ac_SOMNATH_05", "name": "Somnath Beach", "price": 0, "duration": "1 Hour", "description": "Relax by the waves near the temple. Riding camels and horses is available."},
    ],
    "LOCAL_SONAMARG": [
        {"id": "Ac_SONAMARG_01", "name": "Thajiwas Glacier Trek", "price": 1000, "duration": "3 Hours", "description": "Trek or take a pony to the glacier. Snow remains here almost all year round."},
        {"id": "Ac_SONAMARG_02", "name": "Zoji La Pass Drive", "price": 3000, "duration": "3 Hours", "description": "Drive up to the treacherous pass connecting Kashmir to Ladakh. Spectacular rugged views."},
        {"id": "Ac_SONAMARG_03", "name": "Trout Fishing", "price": 500, "duration": "2 Hours", "description": "Try your hand at fishing in the Sindh River (Permit required). Famous for Trout."},
        {"id": "Ac_SONAMARG_04", "name": "Zero Point Snow Fun", "price": 1500, "duration": "2 Hours", "description": "Located near Zoji La. Enjoy sledging and snow bikes even in summer."},
        {"id": "Ac_SONAMARG_05", "name": "Krishansar Lake Trek", "price": 0, "duration": "Full Day", "description": "A high-altitude lake trek for fitness enthusiasts. Stunning alpine scenery."},
    ],
    "LOCAL_SPITI": [
        {"id": "Ac_SPITI_01", "name": "Key Monastery Visit", "price": 0, "duration": "1 Hour", "description": "Visit the iconic monastery perched on a conical hill. The biggest center of Buddhist learning in Spiti."},
        {"id": "Ac_SPITI_02", "name": "Chandratal Lake", "price": 0, "duration": "3 Hours", "description": "The crescent-shaped 'Moon Lake'. Camping nearby is a bucket-list experience."},
        {"id": "Ac_SPITI_03", "name": "Kibber Village", "price": 0, "duration": "1 Hour", "description": "Visit one of the highest motorable villages. Famous for Snow Leopard expeditions in winter."},
        {"id": "Ac_SPITI_04", "name": "Dhankar Monastery", "price": 0, "duration": "1 Hour", "description": "A cliff-hanging monastery overlooking the confluence of Spiti and Pin rivers."},
        {"id": "Ac_SPITI_05", "name": "Pin Valley National Park", "price": 0, "duration": "2 Hours", "description": "Drive into the cold desert national park. Contrasting green patches and rugged mountains."},
    ],
    "LOCAL_SRINAGAR": [
        {"id": "Ac_SRINAGAR_01", "name": "Dal Lake Shikara Ride", "price": 600, "duration": "1 Hour", "description": "Glide through the lake. Visit the floating market and buy flowers from boats."},
        {"id": "Ac_SRINAGAR_02", "name": "Mughal Gardens Tour", "price": 100, "duration": "2 Hours", "description": "Visit Nishat and Shalimar Baghs. Beautiful terraced lawns and fountains."},
        {"id": "Ac_SRINAGAR_03", "name": "Shankaracharya Temple", "price": 0, "duration": "1 Hour", "description": "Climb steps to the hilltop temple. Best panoramic view of Srinagar city and the lake."},
        {"id": "Ac_SRINAGAR_04", "name": "Hazratbal Shrine", "price": 0, "duration": "45 Mins", "description": "Visit the white marble mosque housing a relic of the Prophet. Feeding pigeons is popular here."},
        {"id": "Ac_SRINAGAR_05", "name": "Old City Walk (Downtown)", "price": 0, "duration": "2 Hours", "description": "Walk through the historic lanes. See the Jamia Masjid and buy copperware."},
    ],
    "LOCAL_SUNDERBANS": [
        {"id": "Ac_SUNDERBANS_01", "name": "Mangrove Boat Safari", "price": 2000, "duration": "Full Day", "description": "Cruise through the world's largest mangrove forest. Look for the Royal Bengal Tiger."},
        {"id": "Ac_SUNDERBANS_02", "name": "Sajnekhali Watch Tower", "price": 0, "duration": "1 Hour", "description": "Climb the tower for a chance to spot wildlife. Visit the turtle interpretation center."},
        {"id": "Ac_SUNDERBANS_03", "name": "Crocodile Project (Bhagabatpur)", "price": 100, "duration": "1 Hour", "description": "See estuarine crocodiles of different ages in this hatchery project."},
        {"id": "Ac_SUNDERBANS_04", "name": "Dobanki Canopy Walk", "price": 0, "duration": "30 Mins", "description": "Walk on the netted canopy bridge 20 feet above ground. Safe tiger territory viewing."},
        {"id": "Ac_SUNDERBANS_05", "name": "Village Walk", "price": 200, "duration": "1 Hour", "description": "Interact with locals. Learn about their life with the tides and the 'Bon Bibi' legend."},
    ],
    "LOCAL_TAWANG": [
        {"id": "Ac_TAWANG_01", "name": "Tawang Monastery", "price": 0, "duration": "2 Hours", "description": "India's largest monastery. See the massive library and the 18ft gilded Buddha statue."},
        {"id": "Ac_TAWANG_02", "name": "Sela Pass Stop", "price": 0, "duration": "30 Mins", "description": "Stop at 13,700ft on the way to Tawang. See the frozen Sela Lake and gate."},
        {"id": "Ac_TAWANG_03", "name": "Madhuri Lake (Sangetsar)", "price": 1500, "duration": "3 Hours", "description": "Drive to this stunning high-altitude lake. Famous for tree trunks standing in the water."},
        {"id": "Ac_TAWANG_04", "name": "Tawang War Memorial", "price": 0, "duration": "1 Hour", "description": "A stupa built to honor the martyrs of the 1962 Sino-Indian war. Very moving."},
        {"id": "Ac_TAWANG_05", "name": "Nuranang Falls", "price": 0, "duration": "1 Hour", "description": "A spectacular 100m waterfall located near Jang. Also known as Bong Bong falls."},
    ],
    "LOCAL_TIRUPATI": [
        {"id": "Ac_TIRUPATI_01", "name": "Tirumala Temple Darshan", "price": 300, "duration": "3 Hours", "description": "Visit the richest temple in the world. Waiting times vary, but the spiritual energy is immense."},
        {"id": "Ac_TIRUPATI_02", "name": "Kapila Theertham", "price": 0, "duration": "1 Hour", "description": "A Shiva temple at the base of a waterfall. A holy tank for a dip."},
        {"id": "Ac_TIRUPATI_03", "name": "Sri Govindaraja Swamy", "price": 0, "duration": "1 Hour", "description": "Visit the huge temple near the railway station with a seven-story gopuram."},
        {"id": "Ac_TIRUPATI_04", "name": "Silathoranam", "price": 0, "duration": "30 Mins", "description": "See the natural rock arch formation on Tirumala hills. Geologically rare."},
        {"id": "Ac_TIRUPATI_05", "name": "SV Zoo Park", "price": 100, "duration": "2 Hours", "description": "A large zoo designed around mythology themes. Good for families."},
    ],
    "LOCAL_TSO_MORIRI": [
        {"id": "Ac_TSO_MORIRI_01", "name": "Lake View & Walk", "price": 0, "duration": "2 Hours", "description": "A pristine high-altitude lake, less crowded than Pangong. Surrounded by snow peaks."},
        {"id": "Ac_TSO_MORIRI_02", "name": "Korzok Monastery", "price": 0, "duration": "1 Hour", "description": "Visit the 300-year-old monastery in the village on the banks of the lake."},
        {"id": "Ac_TSO_MORIRI_03", "name": "Bird Watching", "price": 0, "duration": "1 Hour", "description": "Spot migratory birds like the Bar-headed Goose and Brahminy Duck (breeding ground)."},
        {"id": "Ac_TSO_MORIRI_04", "name": "Mentok Kangri View", "price": 0, "duration": "30 Mins", "description": "Enjoy the view of the Mentok Kangri peaks towering over the lake."},
        {"id": "Ac_TSO_MORIRI_05", "name": "Nomadic Interaction", "price": 0, "duration": "1 Hour", "description": "Meet the Changpa nomads who rear Pashmina goats in this region."},
    ],
    "LOCAL_UJJAIN": [
        {"id": "Ac_UJJAIN_01", "name": "Mahakaleshwar Jyotirlinga", "price": 0, "duration": "2 Hours", "description": "Visit the south-facing Jyotirlinga. Witness the famous Bhasma Aarti (ash ritual) at dawn."},
        {"id": "Ac_UJJAIN_02", "name": "Ram Ghat", "price": 0, "duration": "1 Hour", "description": "The main bathing ghat for the Kumbh Mela. Peaceful river view in the evening."},
        {"id": "Ac_UJJAIN_03", "name": "Kal Bhairav Temple", "price": 0, "duration": "45 Mins", "description": "Visit the unique temple where liquor is offered as prasad to the deity."},
        {"id": "Ac_UJJAIN_04", "name": "Harsiddhi Temple", "price": 0, "duration": "30 Mins", "description": "A Shakti Peeth known for its two towering deepstambhs (lamp pillars) lit up at night."},
        {"id": "Ac_UJJAIN_05", "name": "Ved Shala (Observatory)", "price": 50, "duration": "45 Mins", "description": "See ancient astronomical instruments built by Raja Jai Singh II still used today."},
    ],
    "VARANASI_FAKE_013": [
        {"id": "Ac_VARANASI_01", "name": "Dashashwamedh Aarti", "price": 0, "duration": "1 Hour", "description": "Experience the grand evening ceremony. Priests perform synchronized rituals with fire lamps."},
        {"id": "Ac_VARANASI_02", "name": "Sunrise Boat Ride", "price": 400, "duration": "1 Hour", "description": "Row down the Ganges at dawn. See the ghats come alive with prayers and bathers."},
        {"id": "Ac_VARANASI_03", "name": "Kashi Vishwanath Temple", "price": 0, "duration": "2 Hours", "description": "Darshan at the Golden Temple dedicated to Lord Shiva. Walk through the new Corridor."},
        {"id": "Ac_VARANASI_04", "name": "Sarnath Excursion", "price": 500, "duration": "3 Hours", "description": "Visit the deer park where Buddha preached his first sermon. See the Dhamek Stupa."},
        {"id": "Ac_VARANASI_05", "name": "Assi Ghat Walk", "price": 0, "duration": "1 Hour", "description": "A popular cultural hub. Great for morning yoga and trying lemon tea and pizza."},
    ],
    "VARKALA_FAKE_004": [
        {"id": "Ac_VARKALA_01", "name": "Varkala Cliff Walk", "price": 0, "duration": "1 Hour", "description": "Walk along the red laterite cliffs. Lined with shops, cafes, and views of the Arabian Sea."},
        {"id": "Ac_VARKALA_02", "name": "Papanasam Beach", "price": 0, "duration": "2 Hours", "description": "Relax on the beach. A dip here is believed to wash away sins (Papanasam)."},
        {"id": "Ac_VARKALA_03", "name": "Janardanaswamy Temple", "price": 0, "duration": "45 Mins", "description": "Visit the 2000-year-old Vaishnavite temple. Often called the Varanasi of the South."},
        {"id": "Ac_VARKALA_04", "name": "Paragliding", "price": 3000, "duration": "30 Mins", "description": "Fly off the cliffs and glide over the ocean. A unique spot for coastal paragliding."},
        {"id": "Ac_VARKALA_05", "name": "Sivagiri Mutt", "price": 0, "duration": "1 Hour", "description": "Visit the ashram of social reformer Sree Narayana Guru. Located on a hill."},
    ],
    "WAYANAD_FAKE_018": [
        {"id": "Ac_WAYANAD_01", "name": "Edakkal Caves", "price": 50, "duration": "2 Hours", "description": "Trek up to see prehistoric rock carvings (petroglyphs) dating back to the Neolithic age."},
        {"id": "Ac_WAYANAD_02", "name": "Banasura Sagar Dam", "price": 500, "duration": "1 Hour", "description": "Speed boating in India's largest earth dam. Scenic islands visible in the water."},
        {"id": "Ac_WAYANAD_03", "name": "Pookode Lake", "price": 200, "duration": "1 Hour", "description": "A freshwater lake in the shape of India's map. Good for boating and spotting monkeys."},
        {"id": "Ac_WAYANAD_04", "name": "Chembra Peak Trek", "price": 1000, "duration": "4 Hours", "description": "Trek to the heart-shaped lake halfway up the peak. Requires forest permission."},
        {"id": "Ac_WAYANAD_05", "name": "Soochipara Waterfalls", "price": 50, "duration": "2 Hours", "description": "A three-tiered waterfall. Walk down through tea estates to reach the pool."},
    ],
    "LOCAL_ZIRO": [
        {"id": "Ac_ZIRO_01", "name": "Ziro Valley View", "price": 0, "duration": "1 Hour", "description": "View the golden paddy fields from the Ziro Puto hillock."},
        {"id": "Ac_ZIRO_02", "name": "Talley Valley Trek", "price": 1000, "duration": "Half Day", "description": "Trek through the wildlife sanctuary. Rich in biodiversity and fir trees."},
        {"id": "Ac_ZIRO_03", "name": "Hong Village Walk", "price": 0, "duration": "1 Hour", "description": "Walk through one of the largest villages of the Apatani tribe. See their unique facial tattoos."},
        {"id": "Ac_ZIRO_04", "name": "Tarin Fish Farm", "price": 50, "duration": "1 Hour", "description": "See the high-altitude fish farming in paddy fields, a unique practice of the Apatanis."},
        {"id": "Ac_ZIRO_05", "name": "Siddheshwar Nath Shiv Linga", "price": 0, "duration": "1 Hour", "description": "Visit the 25ft tall natural rock Shiva Linga discovered recently in the Kardo forest."},
    ],
    "CHERRAPUNJI_FAKE_101": [
        {"id": "Ac_CHERRA_01", "name": "Nohkalikai Falls View", "price": 50, "duration": "1 Hour", "description": "See the tallest plunge waterfall in India. The sheer drop into the green pool below is breathtaking."},
        {"id": "Ac_CHERRA_02", "name": "Double Decker Root Bridge Trek", "price": 0, "duration": "Full Day", "description": "A challenging trek down 3500 steps to see the unique bio-engineering marvel created by local tribes."},
        {"id": "Ac_CHERRA_03", "name": "Mawsmai Cave Exploration", "price": 100, "duration": "1 Hour", "description": "Walk through the illuminated limestone cave. Navigate narrow passages and admire the stalactites."},
        {"id": "Ac_CHERRA_04", "name": "Seven Sisters Falls", "price": 0, "duration": "30 Mins", "description": "View the seven-segmented waterfall cascading down the limestone cliffs, best seen during monsoon."},
        {"id": "Ac_CHERRA_05", "name": "Arwah Cave Walk", "price": 50, "duration": "1 Hour", "description": "A scenic walk through a fossil-rich cave. Spot ancient fossils on the walls and enjoy the valley view."},
    ],
    "DAWKI_FAKE_102": [
        {"id": "Ac_DAWKI_01", "name": "Umngot River Boat Ride", "price": 800, "duration": "1 Hour", "description": "Glide on the crystal-clear waters of the Umngot River where boats appear to float on air."},
        {"id": "Ac_DAWKI_02", "name": "Shnongpdeng Camping", "price": 1500, "duration": "Evening", "description": "Camp by the riverside in tents. Enjoy a bonfire and the sound of the flowing river under the stars."},
        {"id": "Ac_DAWKI_03", "name": "Snorkeling in Umngot", "price": 1000, "duration": "1 Hour", "description": "Swim in the transparent waters to see the riverbed rocks and fish clearly. Gear provided."},
        {"id": "Ac_DAWKI_04", "name": "Indo-Bangla Border View", "price": 0, "duration": "30 Mins", "description": "Visit the friendship gate at Tamabil. See the zero point between India and Bangladesh."},
        {"id": "Ac_DAWKI_05", "name": "Dawki Suspension Bridge", "price": 0, "duration": "30 Mins", "description": "Walk or drive across the British-era suspension bridge for a panoramic view of the river."},
    ],
    "MAWSYNRAM_FAKE_103": [
        {"id": "Ac_MAWSYNRAM_01", "name": "Mawjymbuin Cave", "price": 50, "duration": "1 Hour", "description": "Visit the cave famous for the natural stone Shiv Linga formed by a stalagmite."},
        {"id": "Ac_MAWSYNRAM_02", "name": "Wettest Place on Earth Sign", "price": 0, "duration": "30 Mins", "description": "Take a photo at the meteorological station marking the highest rainfall in the world."},
        {"id": "Ac_MAWSYNRAM_03", "name": "Khreng Khreng Viewpoint", "price": 0, "duration": "1 Hour", "description": "Enjoy the dramatic views of the deep valleys and winding roads of the East Khasi Hills."},
        {"id": "Ac_MAWSYNRAM_04", "name": "Symper Rock Trek", "price": 0, "duration": "2 Hours", "description": "A short hike to a massive dome-shaped rock. Offers 360-degree views of the surrounding hills."},
        {"id": "Ac_MAWSYNRAM_05", "name": "Jakrem Hot Springs", "price": 50, "duration": "2 Hours", "description": "Drive to the nearby sulfur hot springs believed to have medicinal properties."},
    ],
    "GANGTOK_FAKE_104": [
        {"id": "Ac_GANGTOK_01", "name": "Tsomgo Lake Excursion", "price": 1000, "duration": "Half Day", "description": "Visit the glacial lake at 12,310 ft. Ride a yak on the snow-covered banks (seasonal)."},
        {"id": "Ac_GANGTOK_02", "name": "MG Marg Stroll", "price": 0, "duration": "2 Hours", "description": "Walk the vehicle-free promenade. The heart of Gangtok with benches, flowers, and shops."},
        {"id": "Ac_GANGTOK_03", "name": "Gangtok Ropeway", "price": 120, "duration": "30 Mins", "description": "Take a cable car ride over the city. Get a bird's eye view of the town and Kanchenjunga."},
        {"id": "Ac_GANGTOK_04", "name": "Rumtek Monastery", "price": 50, "duration": "2 Hours", "description": "Explore one of the most significant monasteries in Sikkim. See the Golden Stupa."},
        {"id": "Ac_GANGTOK_05", "name": "Nathula Pass Visit", "price": 3000, "duration": "Full Day", "description": "Visit the Indo-China border trading post. Requires a special permit and prior booking."},
    ],
    "PELLING_FAKE_105": [
        {"id": "Ac_PELLING_01", "name": "Pelling Skywalk", "price": 100, "duration": "1 Hour", "description": "Walk on the glass-bottomed bridge leading to the giant Chenrezig statue. Thrilling views."},
        {"id": "Ac_PELLING_02", "name": "Pemayangtse Monastery", "price": 50, "duration": "1 Hour", "description": "Visit one of the oldest monasteries in Sikkim. Famous for its wooden seven-tiered model of heaven."},
        {"id": "Ac_PELLING_03", "name": "Rabdentse Ruins", "price": 50, "duration": "1 Hour", "description": "Walk through the forest to the ruins of the second capital of Sikkim. Great history and views."},
        {"id": "Ac_PELLING_04", "name": "Kanchenjunga Falls", "price": 20, "duration": "1 Hour", "description": "A perennial waterfall that is a great spot for photography and a quick snack."},
        {"id": "Ac_PELLING_05", "name": "Singshore Bridge", "price": 0, "duration": "1 Hour", "description": "Walk across the second-highest suspension bridge in Asia. The depth below is dizzying."},
    ],
    "ZERO_VALLEY_FAKE_106": [
        {"id": "Ac_ZERO_01", "name": "Apatani Village Walk", "price": 500, "duration": "2 Hours", "description": "Walk through Hong or Hari village. Meet the Apatani people famous for facial tattoos and nose plugs."},
        {"id": "Ac_ZERO_02", "name": "Paddy Field Fish Farm", "price": 0, "duration": "1 Hour", "description": "Observe the unique practice of rearing fish in paddy fields along with rice cultivation."},
        {"id": "Ac_ZERO_03", "name": "Ziro Puto Viewpoint", "price": 0, "duration": "1 Hour", "description": "Hike up the hillock where independent India's first administrative centre was set up."},
        {"id": "Ac_ZERO_04", "name": "Talley Valley Trek", "price": 1500, "duration": "Half Day", "description": "Trek into the wildlife sanctuary. A biodiversity hotspot with dense bamboo and ferns."},
        {"id": "Ac_ZERO_05", "name": "Meghna Cave Temple", "price": 0, "duration": "1 Hour", "description": "Visit the ancient rock temple surrounded by a dense forest. 5000-year-old history."},
    ],
    "BOMDILA_FAKE_107": [
        {"id": "Ac_BOMDILA_01", "name": "Bomdila Monastery", "price": 0, "duration": "1 Hour", "description": "Visit the GRL Monastery. Colorful interiors and a great view of the town below."},
        {"id": "Ac_BOMDILA_02", "name": "Apple Orchard Visit", "price": 100, "duration": "1 Hour", "description": "Walk through sprawling apple orchards (seasonal). Buy fresh apples at cheap rates."},
        {"id": "Ac_BOMDILA_03", "name": "Bomdila View Point", "price": 0, "duration": "1 Hour", "description": "See the panoramic view of the West Kameng valley and Nechipu Pass."},
        {"id": "Ac_BOMDILA_04", "name": "Craft Centre and Museum", "price": 50, "duration": "1 Hour", "description": "See local artisans weaving carpets and making masks. Buy authentic souvenirs."},
        {"id": "Ac_BOMDILA_05", "name": "R.R. Hill", "price": 0, "duration": "1 Hour", "description": "Bomdila's highest point. On clear days, you can see the roads leading to Bhutan and Tawang."},
    ],
    "DIRANG_FAKE_108": [
        {"id": "Ac_DIRANG_01", "name": "Dirang Dzong (Fort)", "price": 0, "duration": "1 Hour", "description": "Explore the 17th-century fort/jail. A fine example of tribal architecture on a hillock."},
        {"id": "Ac_DIRANG_02", "name": "Hot Water Spring", "price": 50, "duration": "1 Hour", "description": "Take a dip in the sulfur-rich hot springs located near the river. Very relaxing."},
        {"id": "Ac_DIRANG_03", "name": "Sangti Valley Drive", "price": 1000, "duration": "3 Hours", "description": "Drive to this picturesque valley. Home to Black-necked cranes in winter."},
        {"id": "Ac_DIRANG_04", "name": "Yak Research Centre", "price": 50, "duration": "1 Hour", "description": "Visit the National Research Centre on Yak. See these high-altitude animals up close."},
        {"id": "Ac_DIRANG_05", "name": "Thupsung Dhargye Monastery", "price": 0, "duration": "1 Hour", "description": "A relatively new but majestic monastery with a huge prayer hall and garden."},
    ],
    "SIVASAGAR_FAKE_109": [
        {"id": "Ac_SIVASAGAR_01", "name": "Rang Ghar", "price": 50, "duration": "1 Hour", "description": "Visit the 'Colosseum of the East'. An ancient two-story sports pavilion of Ahom kings."},
        {"id": "Ac_SIVASAGAR_02", "name": "Shiva Doul", "price": 0, "duration": "45 Mins", "description": "Worship at the massive Shiva temple, topped with a pure gold dome (Kalash)."},
        {"id": "Ac_SIVASAGAR_03", "name": "Talatal Ghar", "price": 50, "duration": "1 Hour", "description": "Explore the palace with underground tunnels (now sealed) used as secret exit routes."},
        {"id": "Ac_SIVASAGAR_04", "name": "Joysagar Tank", "price": 0, "duration": "1 Hour", "description": "Walk around the largest man-made pond in India. A peaceful spot for sunsets."},
        {"id": "Ac_SIVASAGAR_05", "name": "Kareng Ghar", "price": 50, "duration": "1 Hour", "description": "Visit the multi-storied royal palace at Gargaon. An architectural marvel of the Ahom era."},
    ],
    "GUWAHATI_FAKE_110": [
        {"id": "Ac_GUWAHATI_01", "name": "Kamakhya Temple", "price": 0, "duration": "3 Hours", "description": "Visit the famous Shakti Peeth on Nilachal Hill. The ambition of every tantric devotee."},
        {"id": "Ac_GUWAHATI_02", "name": "Brahmaputra River Cruise", "price": 500, "duration": "2 Hours", "description": "Enjoy a sunset dinner cruise on the mighty river. Live music and cultural shows included."},
        {"id": "Ac_GUWAHATI_03", "name": "Umananda Island", "price": 200, "duration": "2 Hours", "description": "Take a ferry to the smallest inhabited river island. Visit the Shiva temple and spot Golden Langurs."},
        {"id": "Ac_GUWAHATI_04", "name": "Pobitora Wildlife Sanctuary", "price": 1500, "duration": "Half Day", "description": "Day trip to see the highest density of one-horned rhinos. Closer than Kaziranga."},
        {"id": "Ac_GUWAHATI_05", "name": "Srimanta Sankaradeva Kalakshetra", "price": 100, "duration": "2 Hours", "description": "A cultural complex showcasing the art, dance, and history of Assam. Light and sound show available."},
    ],
    "IMPHAL_FAKE_111": [
        {"id": "Ac_IMPHAL_01", "name": "Kangla Fort", "price": 50, "duration": "2 Hours", "description": "Explore the ancient capital of Manipur. See the ruins, temples, and the moat."},
        {"id": "Ac_IMPHAL_02", "name": "Ima Keithel (Mother's Market)", "price": 0, "duration": "1 Hour", "description": "Visit the world's only market run entirely by women. Buy handloom and fresh produce."},
        {"id": "Ac_IMPHAL_03", "name": "Imphal War Cemetery", "price": 0, "duration": "45 Mins", "description": "A beautifully maintained Commonwealth cemetery honoring soldiers of the Battle of Imphal."},
        {"id": "Ac_IMPHAL_04", "name": "Manipur State Museum", "price": 20, "duration": "1 Hour", "description": "Learn about Manipuri culture, royal history, and tribal lifestyles."},
        {"id": "Ac_IMPHAL_05", "name": "Shree Govindajee Temple", "price": 0, "duration": "45 Mins", "description": "Visit the historic Vaishnavite temple. Famous for its twin gold domes and large congregation hall."},
    ],
    "LOKTAK_LAKE_FAKE_112": [
        {"id": "Ac_LOKTAK_01", "name": "Sendra Island View", "price": 50, "duration": "1 Hour", "description": "Get the best panoramic view of the lake and its floating biomass (phumdis) from the hillock."},
        {"id": "Ac_LOKTAK_02", "name": "Keibul Lamjao National Park", "price": 200, "duration": "2 Hours", "description": "Visit the world's only floating national park. Spot the endangered Sangai dancing deer."},
        {"id": "Ac_LOKTAK_03", "name": "Boating on Phumdis", "price": 500, "duration": "1 Hour", "description": "Take a boat ride through the floating vegetation. Walk on a Phumdi to feel it bounce."},
        {"id": "Ac_LOKTAK_04", "name": "Karang Island Trip", "price": 100, "duration": "1 Hour", "description": "Visit the first cashless island in India located in the middle of the lake."},
        {"id": "Ac_LOKTAK_05", "name": "Fishermen Village Tour", "price": 300, "duration": "1 Hour", "description": "Observe the unique lifestyle of fishermen who live in huts built on the floating biomass."},
    ],
    "KOHIMA_FAKE_113": [
        {"id": "Ac_KOHIMA_01", "name": "Kohima War Cemetery", "price": 0, "duration": "1 Hour", "description": "Visit the site of the Battle of Tennis Court. The epitaph here is world-famous."},
        {"id": "Ac_KOHIMA_02", "name": "Kisama Heritage Village", "price": 50, "duration": "2 Hours", "description": "The venue of the Hornbill Festival. See traditional Morung huts of all Naga tribes."},
        {"id": "Ac_KOHIMA_03", "name": "Khonoma Green Village", "price": 500, "duration": "Half Day", "description": "Drive to Asia's first green village. Learn about their unique conservation and farming methods."},
        {"id": "Ac_KOHIMA_04", "name": "Kohima Cathedral", "price": 0, "duration": "30 Mins", "description": "Visit the Catholic church with a unique semicircular architecture and large wooden crucifix."},
        {"id": "Ac_KOHIMA_05", "name": "Nagaland State Museum", "price": 20, "duration": "1 Hour", "description": "See dioramas of Naga life, colorful costumes, and ancestral weaponry."},
    ],
    "DZUKOU_VALLEY_FAKE_114": [
        {"id": "Ac_DZUKOU_01", "name": "Dzukou Valley Trek", "price": 1000, "duration": "Full Day", "description": "Trek through bamboo brush to reach the rolling green valley. A paradise for hikers."},
        {"id": "Ac_DZUKOU_02", "name": "Valley of Flowers", "price": 0, "duration": "2 Hours", "description": "Explore the valley floor covered in seasonal lilies (monsoon). Pristine and untouched."},
        {"id": "Ac_DZUKOU_03", "name": "Ghost Cave Exploration", "price": 0, "duration": "1 Hour", "description": "A small cave used as a shelter by trekkers. Adds a bit of mystery to the valley."},
        {"id": "Ac_DZUKOU_04", "name": "Camping in Valley", "price": 1500, "duration": "Evening", "description": "Stay overnight in a tent or the guest house. The sunrise over the valley is magical."},
        {"id": "Ac_DZUKOU_05", "name": "Frozen River Walk", "price": 0, "duration": "1 Hour", "description": "In winter, the stream freezes over. Walking near the crystal ice is a unique experience."},
    ],
    "AIZAWL_FAKE_115": [
        {"id": "Ac_AIZAWL_01", "name": "Reiek Tlang Trek", "price": 0, "duration": "3 Hours", "description": "Hike to the peak for a stunning view of the surrounding Mizo hills and valleys."},
        {"id": "Ac_AIZAWL_02", "name": "Solomon's Temple", "price": 0, "duration": "1 Hour", "description": "Visit the massive white church built with marble. A major architectural landmark."},
        {"id": "Ac_AIZAWL_03", "name": "Mizoram State Museum", "price": 20, "duration": "1 Hour", "description": "View rare photographs, textiles, and archaeological objects of the Mizo tribes."},
        {"id": "Ac_AIZAWL_04", "name": "Durtlang Hills Drive", "price": 500, "duration": "1 Hour", "description": "Drive up for the best aerial view of Aizawl city which looks like a glittering necklace at night."},
        {"id": "Ac_AIZAWL_05", "name": "KV Paradise", "price": 50, "duration": "45 Mins", "description": "Known as the Taj Mahal of Mizoram. A marble mausoleum built by a husband for his wife."},
    ],
    "AGARTALA_FAKE_116": [
        {"id": "Ac_AGARTALA_01", "name": "Ujjayanta Palace", "price": 50, "duration": "2 Hours", "description": "Explore the royal palace and its museum. The white structure with Mughal gardens is stunning."},
        {"id": "Ac_AGARTALA_02", "name": "Neermahal Water Palace", "price": 500, "duration": "3 Hours", "description": "Drive to Melaghar and take a boat to the palace built in the middle of Rudrasagar Lake."},
        {"id": "Ac_AGARTALA_03", "name": "Sepahijala Wildlife Sanctuary", "price": 100, "duration": "2 Hours", "description": "Spot the Spectacled Monkey and Clouded Leopard. Enjoy boating in the zoo lake."},
        {"id": "Ac_AGARTALA_04", "name": "Heritage Park", "price": 20, "duration": "1 Hour", "description": "Walk through miniature replicas of all major tourist spots of Tripura in one garden."},
        {"id": "Ac_AGARTALA_05", "name": "Akhaura Border Retreat", "price": 0, "duration": "1 Hour", "description": "Witness the flag-lowering ceremony at the India-Bangladesh border, similar to Wagah."},
    ],
    "UNAKOTI_FAKE_117": [
        {"id": "Ac_UNAKOTI_01", "name": "Bas-Relief Carvings View", "price": 50, "duration": "2 Hours", "description": "Marvel at the massive rock-cut sculptures of Shiva and Ganesha dating back to the 7th century."},
        {"id": "Ac_UNAKOTI_02", "name": "Unakotiswara Kal Bhairav", "price": 0, "duration": "30 Mins", "description": "See the central 30-foot high head of Shiva carved into the hill face."},
        {"id": "Ac_UNAKOTI_03", "name": "Hill Trekking", "price": 0, "duration": "1 Hour", "description": "Climb the stairs connecting the various rock carvings scattered across the lush green hill."},
        {"id": "Ac_UNAKOTI_04", "name": "Sitakund Waterfall", "price": 0, "duration": "30 Mins", "description": "A stream that flows over the rock carvings, adding to the mystic beauty of the site."},
        {"id": "Ac_UNAKOTI_05", "name": "Annual Mela (Fair)", "price": 0, "duration": "2 Hours", "description": "If visiting in April, experience the Ashokastami Mela with thousands of pilgrims."},
    ],
    "DARBHANGA_FAKE_118": [
        {"id": "Ac_DARBHANGA_01", "name": "Darbhanga Fort", "price": 0, "duration": "1 Hour", "description": "Walk around the massive walls of the Raj Qila. Experience the grandeur of the Darbhanga Raj."},
        {"id": "Ac_DARBHANGA_02", "name": "Shyama Mai Temple", "price": 0, "duration": "45 Mins", "description": "Visit the Kali temple built on the funeral pyre of the Maharaja. A spiritual hub."},
        {"id": "Ac_DARBHANGA_03", "name": "Ahilya Asthan", "price": 0, "duration": "1 Hour", "description": "Visit the legendary site associated with the Ramayana where Ahilya was liberated."},
        {"id": "Ac_DARBHANGA_04", "name": "Kusheshwar Asthan Bird Sanctuary", "price": 500, "duration": "Half Day", "description": "A winter paradise for bird watchers. Spot migratory Siberian cranes in the wetlands."},
        {"id": "Ac_DARBHANGA_05", "name": "Mithila Art Shopping", "price": 0, "duration": "1 Hour", "description": "Buy authentic Madhubani paintings directly from local artists in the nearby villages."},
    ],
    "RAJGIR_FAKE_119": [
        {"id": "Ac_RAJGIR_01", "name": "Glass Bridge Walk", "price": 250, "duration": "1 Hour", "description": "Walk on the transparent glass skywalk amidst five hills. A thrilling modern attraction."},
        {"id": "Ac_RAJGIR_02", "name": "Vishwa Shanti Stupa Ropeway", "price": 100, "duration": "1 Hour", "description": "Take the single-seater ropeway to the Peace Pagoda atop Ratnagiri Hill."},
        {"id": "Ac_RAJGIR_03", "name": "Gridhakuta (Vulture's Peak)", "price": 0, "duration": "1 Hour", "description": "Visit the site where Buddha delivered many sermons. A significant Buddhist pilgrimage spot."},
        {"id": "Ac_RAJGIR_04", "name": "Cyclopean Wall", "price": 0, "duration": "30 Mins", "description": "See the remains of the ancient stone wall that once encircled the city of Rajgir."},
        {"id": "Ac_RAJGIR_05", "name": "Brahmakund Hot Springs", "price": 0, "duration": "1 Hour", "description": "Bathe in the hot water springs located at the foot of Vaibhav Hill. Sacred to Hindus."},
    ],
    "SASARAM_FAKE_120": [
        {"id": "Ac_SASARAM_01", "name": "Sher Shah Suri Tomb", "price": 25, "duration": "1 Hour", "description": "Visit the Indo-Islamic masterpiece. A red sandstone mausoleum standing in the middle of a lake."},
        {"id": "Ac_SASARAM_02", "name": "Rohtasgarh Fort Trek", "price": 500, "duration": "Half Day", "description": "Trek up to one of the largest forts in India. Offers stunning views of the Son River valley."},
        {"id": "Ac_SASARAM_03", "name": "Manjhar Kund Waterfall", "price": 0, "duration": "2 Hours", "description": "Picnic at the waterfall. Especially beautiful and full during the rainy season."},
        {"id": "Ac_SASARAM_04", "name": "Tara Chandi Temple", "price": 0, "duration": "45 Mins", "description": "Visit the Shakti Peeth located in a cave on the hill. A major pilgrimage site."},
        {"id": "Ac_SASARAM_05", "name": "Dhua Kund", "price": 0, "duration": "1 Hour", "description": "Visit the waterfall nearby Manjhar Kund. The water creates a misty 'smoke' effect."},
    ],
    "GAYA_FAKE_121": [
        {"id": "Ac_GAYA_01", "name": "Vishnupad Temple", "price": 0, "duration": "1 Hour", "description": "Visit the temple on the Falgu riverbank featuring a 40cm long footprint of Lord Vishnu."},
        {"id": "Ac_GAYA_02", "name": "Pind Daan Ritual", "price": 500, "duration": "2 Hours", "description": "Perform the sacred ritual for ancestors (optional). The main reason pilgrims visit Gaya."},
        {"id": "Ac_GAYA_03", "name": "Mangla Gauri Temple", "price": 0, "duration": "45 Mins", "description": "Climb up to this Shakti Peeth. Offers a nice view of the city from the hilltop."},
        {"id": "Ac_GAYA_04", "name": "Dungeshwari Cave Temples", "price": 300, "duration": "2 Hours", "description": "Visit the Mahakala caves where Buddha meditated before enlightenment. 12km from town."},
        {"id": "Ac_GAYA_05", "name": "Barabar Caves Day Trip", "price": 1000, "duration": "Half Day", "description": "Explore the oldest surviving rock-cut caves in India. Famous for their polished echoes."},
    ],
    "VAISHALI_FAKE_122": [
        {"id": "Ac_VAISHALI_01", "name": "Ashoka Pillar", "price": 20, "duration": "45 Mins", "description": "See the single lion capital pillar built by Emperor Ashoka. Very well preserved."},
        {"id": "Ac_VAISHALI_02", "name": "Buddha Stupa I & II", "price": 20, "duration": "1 Hour", "description": "Visit the excavation site containing one-eighth of the sacred ashes of Lord Buddha."},
        {"id": "Ac_VAISHALI_03", "name": "Vishwa Shanti Stupa", "price": 0, "duration": "30 Mins", "description": "Visit the modern white Peace Pagoda built by the Japanese adjacent to the tank."},
        {"id": "Ac_VAISHALI_04", "name": "Abhishek Pushkarni", "price": 0, "duration": "30 Mins", "description": "See the coronation tank. Legend says Lichchavi kings were anointed with its water."},
        {"id": "Ac_VAISHALI_05", "name": "Archaeological Museum", "price": 10, "duration": "1 Hour", "description": "View antiquities found in the region, including terracotta figurines and coins."},
    ],
    "KOLKATA_FAKE_123": [
        {"id": "Ac_KOLKATA_01", "name": "Victoria Memorial Tour", "price": 50, "duration": "2 Hours", "description": "Explore the white marble grandeur of the British era. Walk through the sprawling gardens."},
        {"id": "Ac_KOLKATA_02", "name": "Dakshineswar Kali Temple", "price": 0, "duration": "2 Hours", "description": "Visit the famous temple on the Hooghly banks. Associated with Ramakrishna Paramahansa."},
        {"id": "Ac_KOLKATA_03", "name": "Howrah Bridge Ferry", "price": 20, "duration": "1 Hour", "description": "Take a local ferry from Howrah to Millennium Park. Best view of the iconic cantilever bridge."},
        {"id": "Ac_KOLKATA_04", "name": "Park Street Food Walk", "price": 800, "duration": "2 Hours", "description": "Taste the legendary Kati Rolls and visit historic bakeries like Flurys."},
        {"id": "Ac_KOLKATA_05", "name": "Kumartuli Clay Walk", "price": 0, "duration": "1 Hour", "description": "Walk through the potters' colony. Watch artisans sculpt idols of Goddess Durga from clay."},
    ],
    "DIGHA_FAKE_124": [
        {"id": "Ac_DIGHA_01", "name": "New Digha Beach Fun", "price": 0, "duration": "2 Hours", "description": "Enjoy the sea breeze on the man-made beach. Safer for swimming than Old Digha."},
        {"id": "Ac_DIGHA_02", "name": "Marine Aquarium", "price": 20, "duration": "1 Hour", "description": "Visit the largest marine aquarium in India. See sharks, rays, and sea snakes."},
        {"id": "Ac_DIGHA_03", "name": "Amarabati Park", "price": 20, "duration": "1 Hour", "description": "A relaxing park with a lake and ropeway ride. Good for families and kids."},
        {"id": "Ac_DIGHA_04", "name": "Mohana Fish Market", "price": 0, "duration": "1 Hour", "description": "Visit the estuary market early morning. Watch the massive catch of fish being auctioned."},
        {"id": "Ac_DIGHA_05", "name": "Biswa Bangla Park", "price": 0, "duration": "1 Hour", "description": "Stroll through the beautified park at Old Digha. Enjoy the fountain and sea view."},
    ],
    "MANDARMANI_FAKE_125": [
        {"id": "Ac_MANDARMANI_01", "name": "Beach Bike Ride", "price": 300, "duration": "30 Mins", "description": "Ride an ATV on the long, hard-packed sand beach. A signature Mandarmani activity."},
        {"id": "Ac_MANDARMANI_02", "name": "Red Crab Spotting", "price": 0, "duration": "1 Hour", "description": "Walk to the quieter parts of the beach to see thousands of red ghost crabs crawling."},
        {"id": "Ac_MANDARMANI_03", "name": "Water Sports", "price": 800, "duration": "1 Hour", "description": "Try jet skiing or a banana boat ride in the Bay of Bengal waters."},
        {"id": "Ac_MANDARMANI_04", "name": "Mohana Delta View", "price": 0, "duration": "1 Hour", "description": "Walk to the end of the beach where the river meets the sea. Great fishing boats view."},
        {"id": "Ac_MANDARMANI_05", "name": "Resort Leisure", "price": 0, "duration": "Evening", "description": "Relax at a sea-facing resort. Mandarmani is known for luxury resorts right on the beach."},
    ],
    "BAKKHALI_FAKE_126": [
        {"id": "Ac_BAKKHALI_01", "name": "Henry's Island", "price": 20, "duration": "1 Hour", "description": "Walk through the mangrove forests and fisheries project. Climb the watchtower for views."},
        {"id": "Ac_BAKKHALI_02", "name": "Crocodile Breeding Centre", "price": 10, "duration": "45 Mins", "description": "See estuarine crocodiles of all sizes at the Bhagabatpur project nearby."},
        {"id": "Ac_BAKKHALI_03", "name": "Fraserganj Wind Park", "price": 0, "duration": "30 Mins", "description": "Visit the area with massive windmills. A unique landscape of beach and turbines."},
        {"id": "Ac_BAKKHALI_04", "name": "Jambu Dweep Boat Ride", "price": 500, "duration": "2 Hours", "description": "Take a boat towards the isolated island (landing is restricted). Scenic sea journey."},
        {"id": "Ac_BAKKHALI_05", "name": "Bishalakshmi Temple", "price": 0, "duration": "30 Mins", "description": "A small, quaint temple right on the beach. Popular with locals."},
    ],
    "SANTINIKETAN_FAKE_127": [
        {"id": "Ac_SANTINIKETAN_01", "name": "Visva Bharati Campus", "price": 0, "duration": "2 Hours", "description": "Walk through Tagore's university. See the open-air classrooms under the trees."},
        {"id": "Ac_SANTINIKETAN_02", "name": "Upasana Griha (Prayer Hall)", "price": 0, "duration": "30 Mins", "description": "Visit the stunning prayer hall made of colored Belgian glass. Also known as Kanch Mandir."},
        {"id": "Ac_SANTINIKETAN_03", "name": "Sonajhuri Haat", "price": 0, "duration": "2 Hours", "description": "Experience the Saturday market in the forest. Buy handicrafts and listen to Baul singers."},
        {"id": "Ac_SANTINIKETAN_04", "name": "Rabindra Bhavan Museum", "price": 50, "duration": "1 Hour", "description": "See personal items, manuscripts, and the Nobel Prize replica of Rabindranath Tagore."},
        {"id": "Ac_SANTINIKETAN_05", "name": "Kopai River Bank", "price": 0, "duration": "1 Hour", "description": "Sit by the small winding river that inspired many of Tagore's poems."},
    ],
    "MURSHIDABAD_FAKE_128": [
        {"id": "Ac_MURSHIDABAD_01", "name": "Hazarduari Palace", "price": 25, "duration": "2 Hours", "description": "Explore the 'Palace with a Thousand Doors'. Now a museum with weapons and oil paintings."},
        {"id": "Ac_MURSHIDABAD_02", "name": "Katra Masjid", "price": 0, "duration": "45 Mins", "description": "Visit the old mosque with massive domes. The tomb of Murshid Quli Khan is under the stairs."},
        {"id": "Ac_MURSHIDABAD_03", "name": "Kathgola Palace", "price": 50, "duration": "1 Hour", "description": "See the garden palace of a wealthy merchant. Famous for its secret tunnels and Jain temple."},
        {"id": "Ac_MURSHIDABAD_04", "name": "Nizamat Imambara", "price": 0, "duration": "30 Mins", "description": "View the largest Imambara in India (exterior view mostly) opposite the palace."},
        {"id": "Ac_MURSHIDABAD_05", "name": "Motijheel Park", "price": 20, "duration": "1 Hour", "description": "Relax at the oxbow lake park. Historically the residence of Ghaseti Begum."},
    ],
    "BISHNUPUR_FAKE_129": [
        {"id": "Ac_BISHNUPUR_01", "name": "Rasmancha Visit", "price": 25, "duration": "1 Hour", "description": "Visit the unique pyramid-like structure used for the Ras festival. A masterpiece of brick architecture."},
        {"id": "Ac_BISHNUPUR_02", "name": "Terracotta Temples Tour", "price": 0, "duration": "2 Hours", "description": "See the intricate terracotta carvings on Jor Bangla and Madan Mohan temples."},
        {"id": "Ac_BISHNUPUR_03", "name": "Baluchari Saree Weaving", "price": 0, "duration": "1 Hour", "description": "Watch weavers create silk sarees depicting scenes from the Ramayana on the borders."},
        {"id": "Ac_BISHNUPUR_04", "name": "Dalmadal Cannon", "price": 0, "duration": "15 Mins", "description": "See the massive iron cannon. Legend says Lord Madan Mohan fired it to protect the city."},
        {"id": "Ac_BISHNUPUR_05", "name": "Acharya Jogesh Chandra Museum", "price": 10, "duration": "1 Hour", "description": "View local art, manuscripts, and music instruments relating to the Bishnupur Gharana."},
    ],
    "DARJEELING_TEA_GARDENS_FAKE_130": [
        {"id": "Ac_DARJ_TEA_01", "name": "Tea Plucking Experience", "price": 500, "duration": "2 Hours", "description": "Dress like a local worker and try your hand at plucking the 'two leaves and a bud'."},
        {"id": "Ac_DARJ_TEA_02", "name": "Tea Factory Tour", "price": 200, "duration": "1 Hour", "description": "Watch the withering, rolling, and drying process of the world's most famous tea."},
        {"id": "Ac_DARJ_TEA_03", "name": "Tea Tasting Session", "price": 300, "duration": "1 Hour", "description": "Learn to distinguish between First Flush, Second Flush, and Autumn Flush teas."},
        {"id": "Ac_DARJ_TEA_04", "name": "Garden Picnic", "price": 0, "duration": "2 Hours", "description": "Enjoy a quiet picnic amidst the rolling green bushes with a view of the mountains."},
        {"id": "Ac_DARJ_TEA_05", "name": "Homestay in Estate", "price": 2000, "duration": "Full Day", "description": "Stay in a bungalow within the tea estate. Wake up to the smell of fresh tea."},
    ],
    "KALIMPONG_FAKE_131": [
        {"id": "Ac_KALIMPONG_01", "name": "Deolo Hill Park", "price": 50, "duration": "2 Hours", "description": "Visit the highest point in town. Beautiful gardens and paragliding take-off site."},
        {"id": "Ac_KALIMPONG_02", "name": "Durpin Monastery", "price": 0, "duration": "1 Hour", "description": "Spin the prayer wheels at Zang Dhok Palri Phodang. Great views of Kanchenjunga."},
        {"id": "Ac_KALIMPONG_03", "name": "Pine View Cactus Nursery", "price": 20, "duration": "1 Hour", "description": "See the largest collection of exotic cacti in Asia. A treat for plant lovers."},
        {"id": "Ac_KALIMPONG_04", "name": "Morgan House", "price": 0, "duration": "30 Mins", "description": "See the colonial stone cottage (now a hotel) famous for ghost stories and architecture."},
        {"id": "Ac_KALIMPONG_05", "name": "Haat Bazar", "price": 0, "duration": "1 Hour", "description": "Explore the local market on Wed/Sat. Farmers sell cheese, pickles, and orchids."},
    ],
    "KURSEONG_FAKE_132": [
        {"id": "Ac_KURSEONG_01", "name": "Eagle's Crag Viewpoint", "price": 0, "duration": "1 Hour", "description": "Hike to the viewpoint for a sweeping view of the Teesta valley and plains."},
        {"id": "Ac_KURSEONG_02", "name": "Dow Hill Forest Walk", "price": 0, "duration": "2 Hours", "description": "Walk through the misty pine forest. Known for its 'haunted' Death Road."},
        {"id": "Ac_KURSEONG_03", "name": "Netaji Subhash Chandra Bose Museum", "price": 20, "duration": "1 Hour", "description": "Visit the house where Netaji was interned. See his furniture and letters."},
        {"id": "Ac_KURSEONG_04", "name": "Makaibari Tea Estate", "price": 200, "duration": "2 Hours", "description": "Tour the world's first tea factory. Famous for its organic and biodynamic tea."},
        {"id": "Ac_KURSEONG_05", "name": "Toy Train Station", "price": 0, "duration": "30 Mins", "description": "Watch the steam train pass through the town market. The tracks run right on the road."},
    ],
    "MIRIK_FAKE_133": [
        {"id": "Ac_MIRIK_01", "name": "Sumendu Lake Boating", "price": 200, "duration": "1 Hour", "description": "Paddle boat on the serene lake. Cross the arched footbridge (Indreni Pull)."},
        {"id": "Ac_MIRIK_02", "name": "Bokar Monastery", "price": 0, "duration": "1 Hour", "description": "Visit the peaceful monastery on top of a hill. Listen to the evening chants."},
        {"id": "Ac_MIRIK_03", "name": "Orange Orchard Visit", "price": 0, "duration": "1 Hour", "description": "Walk through the orange groves (seasonal). Mirik is famous for its sweet oranges."},
        {"id": "Ac_MIRIK_04", "name": "Pashupati Market Trip", "price": 500, "duration": "2 Hours", "description": "Drive to the Nepal border market. Buy imported clothes and electronics."},
        {"id": "Ac_MIRIK_05", "name": "Tingling View Point", "price": 0, "duration": "30 Mins", "description": "Stop for a view of the tea gardens spread over the slopes like a green carpet."},
    ],
    "JALDAPARA_FAKE_134": [
        {"id": "Ac_JALDAPARA_01", "name": "Elephant Safari", "price": 800, "duration": "1 Hour", "description": "Ride an elephant into the tall grasslands. The best way to spot the One-Horned Rhino."},
        {"id": "Ac_JALDAPARA_02", "name": "Jeep Safari", "price": 1500, "duration": "2 Hours", "description": "Drive through the dense forest. Look for bison, elephants, and deer."},
        {"id": "Ac_JALDAPARA_03", "name": "Totopara Village", "price": 500, "duration": "2 Hours", "description": "Visit the home of the Toto tribe, one of the most primitive and endangered tribes."},
        {"id": "Ac_JALDAPARA_04", "name": "Chilapata Forest Drive", "price": 1000, "duration": "2 Hours", "description": "Drive through the dense elephant corridor. See the ruins of Nal Rajar Garh."},
        {"id": "Ac_JALDAPARA_05", "name": "Hollong Bungalow", "price": 0, "duration": "1 Hour", "description": "Visit the salt lick outside the bungalow. Rhinos often come here at dusk (exterior view)."},
    ],
    "GORUMARA_FAKE_135": [
        {"id": "Ac_GORUMARA_01", "name": "Jatraprasad Watchtower", "price": 120, "duration": "2 Hours", "description": "Climb the tower for a panoramic view of the forest and rhinos grazing."},
        {"id": "Ac_GORUMARA_02", "name": "Jungle Safari (Jeep)", "price": 1500, "duration": "2 Hours", "description": "Explore the park in a gypsy. Spot peacocks, gaurs, and wild elephants."},
        {"id": "Ac_GORUMARA_03", "name": "Tribal Dance Show", "price": 100, "duration": "1 Hour", "description": "Watch the local tribal community perform mesmerizing folk dances in the evening."},
        {"id": "Ac_GORUMARA_04", "name": "Murti River Visit", "price": 0, "duration": "1 Hour", "description": "Walk along the stony riverbed. A great spot for birdwatching and wading."},
        {"id": "Ac_GORUMARA_05", "name": "Medla Watchtower", "price": 120, "duration": "2 Hours", "description": "Take a buffalo cart ride to reach this unique watchtower near the river."},
    ],
    "BUXA_FAKE_136": [
        {"id": "Ac_BUXA_01", "name": "Buxa Fort Trek", "price": 0, "duration": "2 Hours", "description": "Trek up to the historic fort used as a detention camp by the British. High in the hills."},
        {"id": "Ac_BUXA_02", "name": "Jayanti Riverbed", "price": 0, "duration": "2 Hours", "description": "Walk on the white pebble riverbed bordering Bhutan. The landscape is cinematic."},
        {"id": "Ac_BUXA_03", "name": "Mahakal Cave", "price": 0, "duration": "1 Hour", "description": "A limestone cave dedicated to Lord Shiva. Requires a short trek from Jayanti."},
        {"id": "Ac_BUXA_04", "name": "Pokhri Hill Trek", "price": 0, "duration": "1 Hour", "description": "Hike to a sacred pond on the hill full of large catfish and turtles."},
        {"id": "Ac_BUXA_05", "name": "Rajabhatkhawa Nature Center", "price": 50, "duration": "1 Hour", "description": "Visit the interpretation center to learn about the flora and fauna of the tiger reserve."},
    ],
    "DOOARS_FAKE_137": [
        {"id": "Ac_DOOARS_01", "name": "Tea Garden Drive", "price": 0, "duration": "1 Hour", "description": "Drive through the endless tea estates that characterize the Dooars region."},
        {"id": "Ac_DOOARS_02", "name": "Samsing & Suntalekhola", "price": 1200, "duration": "Half Day", "description": "Visit the scenic hill spots with hanging bridges and orange orchards."},
        {"id": "Ac_DOOARS_03", "name": "River Crossing", "price": 0, "duration": "1 Hour", "description": "Wade through shallow streams. The region is crisscrossed by many rivers like Teesta and Torsa."},
        {"id": "Ac_DOOARS_04", "name": "Nature Walk", "price": 0, "duration": "2 Hours", "description": "Take a guided walk on the forest fringes to spot hornbills and butterflies."},
        {"id": "Ac_DOOARS_05", "name": "Bindu Dam View", "price": 1000, "duration": "3 Hours", "description": "Visit the last village on the India-Bhutan border. See the Jaldhaka Hydel Project."},
    ],
    "RANCHI_FAKE_138": [
        {"id": "Ac_RANCHI_01", "name": "Hundru Falls", "price": 50, "duration": "2 Hours", "description": "Descend 700 steps to see the Subarnarekha river falling from 320 feet."},
        {"id": "Ac_RANCHI_02", "name": "Jonha Falls", "price": 50, "duration": "2 Hours", "description": "Visit the 'Gautam Dhara' falls. More peaceful and accessible than Hundru."},
        {"id": "Ac_RANCHI_03", "name": "Pahari Mandir", "price": 0, "duration": "1 Hour", "description": "Climb 468 steps to the Shiva temple. Get the best view of Ranchi city."},
        {"id": "Ac_RANCHI_04", "name": "Rock Garden", "price": 30, "duration": "1 Hour", "description": "Relax in the garden built from the rocks of Gonda Hill. Overlooks the Kanke Dam."},
        {"id": "Ac_RANCHI_05", "name": "Tagore Hill", "price": 0, "duration": "1 Hour", "description": "Visit the hill associated with Rabindranath Tagore's brother. A serene cultural spot."},
    ],
    "NETARHAT_FAKE_139": [
        {"id": "Ac_NETARHAT_01", "name": "Magnolia Sunset Point", "price": 0, "duration": "1 Hour", "description": "Watch a spectacular sunset. Named after a colonial girl who leaped to death here for love."},
        {"id": "Ac_NETARHAT_02", "name": "Sunrise at Koel View Point", "price": 0, "duration": "1 Hour", "description": "See the sun rise over the winding Koel river deep in the pine forest valley."},
        {"id": "Ac_NETARHAT_03", "name": "Pine Forest Walk", "price": 0, "duration": "2 Hours", "description": "Walk through the cool, fragrant pine forest. Feels like a hill station in the north."},
        {"id": "Ac_NETARHAT_04", "name": "Nashpati (Pear) Garden", "price": 0, "duration": "1 Hour", "description": "Stroll through the government pear orchards. Beautiful blooms in spring."},
        {"id": "Ac_NETARHAT_05", "name": "Upper Ghaghri Falls", "price": 0, "duration": "1 Hour", "description": "Picnic at the small but scenic waterfall located in a dense forest pocket."},
    ],
    "BETLA_FAKE_140": [
        {"id": "Ac_BETLA_01", "name": "Betla Jeep Safari", "price": 1000, "duration": "2 Hours", "description": "Explore one of India's first tiger reserves. Spot bison, elephants, and deer."},
        {"id": "Ac_BETLA_02", "name": "Palamau Forts", "price": 0, "duration": "1 Hour", "description": "Visit the ruins of two 16th-century Chero dynasty forts located deep inside the jungle."},
        {"id": "Ac_BETLA_03", "name": "Elephant Ride", "price": 400, "duration": "1 Hour", "description": "Take an elephant back ride for a higher vantage point to see wildlife."},
        {"id": "Ac_BETLA_04", "name": "Kechki Sangam", "price": 0, "duration": "1 Hour", "description": "Visit the confluence of Auranga and Koel rivers. A popular picnic spot."},
        {"id": "Ac_BETLA_05", "name": "Lodh Falls Trip", "price": 1000, "duration": "3 Hours", "description": "Drive to Jharkhand's highest waterfall. The water thunders down from 468 feet."},
    ],
    "HAZARIBAGH_FAKE_141": [
        {"id": "Ac_HAZARIBAGH_01", "name": "Hazaribagh Lake", "price": 50, "duration": "1 Hour", "description": "Boating and relaxation at the urban lake complex. Good for morning walks."},
        {"id": "Ac_HAZARIBAGH_02", "name": "Canary Hill", "price": 0, "duration": "1 Hour", "description": "Climb the watchtower on the hill for a view of the dense forests and town."},
        {"id": "Ac_HAZARIBAGH_03", "name": "Rajrappa Temple", "price": 0, "duration": "3 Hours", "description": "Visit the Chinnamasta Temple located where rivers Damodar and Bhairavi meet."},
        {"id": "Ac_HAZARIBAGH_04", "name": "Hazaribagh National Park", "price": 200, "duration": "2 Hours", "description": "A wildlife sanctuary known for Sambars and Cheetals. Scenic drive through the forest."},
        {"id": "Ac_HAZARIBAGH_05", "name": "Konar Dam", "price": 0, "duration": "2 Hours", "description": "Drive to the massive dam. A quiet place to enjoy the expanse of water."},
    ],
    "DEOGHAR_FAKE_142": [
        {"id": "Ac_DEOGHAR_01", "name": "Baidyanath Dham Darshan", "price": 0, "duration": "2 Hours", "description": "Worship at one of the 12 Jyotirlingas. The heart of Deoghar tourism."},
        {"id": "Ac_DEOGHAR_02", "name": "Trikut Pahar Ropeway", "price": 150, "duration": "2 Hours", "description": "Take the cable car to the top of the three peaks. Enjoy trekking and feeding monkeys."},
        {"id": "Ac_DEOGHAR_03", "name": "Naulakha Mandir", "price": 0, "duration": "45 Mins", "description": "Visit the temple built for 9 lakh rupees. Similar architecture to Belur Math."},
        {"id": "Ac_DEOGHAR_04", "name": "Tapovan Caves", "price": 0, "duration": "1 Hour", "description": "Explore the caves where sages famously meditated. A place of penance."},
        {"id": "Ac_DEOGHAR_05", "name": "Satsang Ashram", "price": 0, "duration": "1 Hour", "description": "Visit the holy ashram of Sri Sri Thakur Anukulchandra. Very peaceful atmosphere."},
    ],
    "SIMLIPAL_FAKE_143": [
        {"id": "Ac_SIMLIPAL_01", "name": "Barehipani Waterfall", "price": 0, "duration": "1 Hour", "description": "View the second highest waterfall in India. A two-tiered drop visible from the viewpoint."},
        {"id": "Ac_SIMLIPAL_02", "name": "Jungle Safari", "price": 1000, "duration": "Full Day", "description": "Traverse the massive biosphere reserve. Home to tigers, elephants, and melanistic tigers."},
        {"id": "Ac_SIMLIPAL_03", "name": "Joranda Falls", "price": 0, "duration": "30 Mins", "description": "See the single-drop waterfall plunging straight down a cliff."},
        {"id": "Ac_SIMLIPAL_04", "name": "Mugger Crocodile Project", "price": 50, "duration": "45 Mins", "description": "Visit the breeding center at Ramtirtha to see crocodiles."},
        {"id": "Ac_SIMLIPAL_05", "name": "Gurguria Orchidarium", "price": 0, "duration": "1 Hour", "description": "See rare wild orchids at the Gurguria nature camp inside the forest."},
    ],
    "BHITARKANIKA_FAKE_144": [
        {"id": "Ac_BHITARKANIKA_01", "name": "Mangrove Boat Safari", "price": 3000, "duration": "3 Hours", "description": "Cruise through the creeks. Spot giant Saltwater Crocodiles basking on the mud."},
        {"id": "Ac_BHITARKANIKA_02", "name": "Bird Sanctuary Trek", "price": 50, "duration": "1 Hour", "description": "Walk to the Bagagahan heronry. See thousands of nesting birds (seasonal)."},
        {"id": "Ac_BHITARKANIKA_03", "name": "Dangmal Museum", "price": 20, "duration": "30 Mins", "description": "See the skeletons of massive crocodiles and whale sharks at the interpretation center."},
        {"id": "Ac_BHITARKANIKA_04", "name": "Olive Ridley Hatchery", "price": 0, "duration": "1 Hour", "description": "Visit Gahirmatha beach (nearby) to see turtle nesting or hatchlings (seasonal)."},
        {"id": "Ac_BHITARKANIKA_05", "name": "Hunting Tower View", "price": 0, "duration": "30 Mins", "description": "Climb the ancient hunting tower used by erstwhile kings for a view of the jungle trails."},
    ],
    "DARINGBADI_FAKE_145": [
        {"id": "Ac_DARINGBADI_01", "name": "Coffee Plantation Walk", "price": 0, "duration": "1 Hour", "description": "Walk through the coffee and black pepper gardens. Known as the 'Kashmir of Odisha'."},
        {"id": "Ac_DARINGBADI_02", "name": "Hill View Park", "price": 20, "duration": "1 Hour", "description": "A landscaped garden on a hill top. Perfect for sunrise and sunset views."},
        {"id": "Ac_DARINGBADI_03", "name": "Midubanda Waterfall", "price": 0, "duration": "1 Hour", "description": "Descend 150 steps to reach this scenic waterfall hidden in the forest."},
        {"id": "Ac_DARINGBADI_04", "name": "Pine Forest Picnic", "price": 0, "duration": "1 Hour", "description": "Relax in the belt of tall pine trees planted along the road."},
        {"id": "Ac_DARINGBADI_05", "name": "Emu Farm Visit", "price": 20, "duration": "30 Mins", "description": "See the flightless Emu birds at a local private farm."},
    ],
    "GOPALPUR_FAKE_146": [
        {"id": "Ac_GOPALPUR_01", "name": "Gopalpur Beach", "price": 0, "duration": "2 Hours", "description": "Relax on the golden sands. Watch fishermen bring in their catch in traditional boats."},
        {"id": "Ac_GOPALPUR_02", "name": "Old Lighthouse", "price": 20, "duration": "45 Mins", "description": "Climb the lighthouse for a panoramic view of the coastline and the town."},
        {"id": "Ac_GOPALPUR_03", "name": "Ruined Jetty Walk", "price": 0, "duration": "30 Mins", "description": "Walk near the crumbling pillars of the ancient port jetty. Atmospheric and historic."},
        {"id": "Ac_GOPALPUR_04", "name": "Cashew Processing Unit", "price": 0, "duration": "1 Hour", "description": "Visit a local factory to see how cashew nuts are roasted and shelled."},
        {"id": "Ac_GOPALPUR_05", "name": "Tampara Lake Water Sports", "price": 500, "duration": "2 Hours", "description": "Drive to the nearby freshwater lake for jet skiing and boating."},
    ],
    "CHANDIPUR_FAKE_147": [
        {"id": "Ac_CHANDIPUR_01", "name": "Receding Sea Walk", "price": 0, "duration": "2 Hours", "description": "Walk 5km into the sea during low tide. The water vanishes and reappears twice a day."},
        {"id": "Ac_CHANDIPUR_02", "name": "Red Crab Spotting", "price": 0, "duration": "1 Hour", "description": "Watch thousands of red ghost crabs scuttle on the exposed seabed."},
        {"id": "Ac_CHANDIPUR_03", "name": "Balaramgadi Mouth", "price": 0, "duration": "1 Hour", "description": "Visit the confluence of the Budhabalanga river and the sea. Watch fishing trawlers."},
        {"id": "Ac_CHANDIPUR_04", "name": "Panchalingeswar Trip", "price": 800, "duration": "3 Hours", "description": "Drive to the hill temple where 5 Shiva Lingas are bathed by a natural stream."},
        {"id": "Ac_CHANDIPUR_05", "name": "Emami Jagannath Temple", "price": 0, "duration": "1 Hour", "description": "Visit the modern, beautifully architectural temple nearby in Balasore."},
    ],
    "PARADIP_FAKE_148": [
        {"id": "Ac_PARADIP_01", "name": "Paradip Port Drive", "price": 0, "duration": "1 Hour", "description": "Drive through the massive port area. See huge ships and cargo movement (restricted zones apply)."},
        {"id": "Ac_PARADIP_02", "name": "Paradip Beach", "price": 0, "duration": "1 Hour", "description": "A clean beach located at the confluence of the Mahanadi river and ocean."},
        {"id": "Ac_PARADIP_03", "name": "Marine Aquarium", "price": 20, "duration": "45 Mins", "description": "A small aquarium maintained by the port trust showcasing local marine life."},
        {"id": "Ac_PARADIP_04", "name": "Lighthouse Visit", "price": 10, "duration": "30 Mins", "description": "View the vast Bay of Bengal and the port infrastructure from the top."},
        {"id": "Ac_PARADIP_05", "name": "Jhankad Sarala Temple", "price": 0, "duration": "2 Hours", "description": "Visit the famous temple of Goddess Sarala, a major spiritual center of Odisha."},
    ],
    "CUTTACK_FAKE_149": [
        {"id": "Ac_CUTTACK_01", "name": "Barabati Fort Ruins", "price": 20, "duration": "1 Hour", "description": "See the moat and gate of the 14th-century fort. A stadium now sits inside."},
        {"id": "Ac_CUTTACK_02", "name": "Maritime Museum", "price": 50, "duration": "1 Hour", "description": "Learn about Odisha's ancient maritime history. Located in the old jobra workshop."},
        {"id": "Ac_CUTTACK_03", "name": "Dhabaleswar Island", "price": 200, "duration": "2 Hours", "description": "Take a boat or cross the suspension bridge to the Shiva temple on the river island."},
        {"id": "Ac_CUTTACK_04", "name": "Netaji Birthplace Museum", "price": 20, "duration": "1 Hour", "description": "Visit Janakinath Bhawan, where Subhash Chandra Bose was born."},
        {"id": "Ac_CUTTACK_05", "name": "Silver Filigree Shopping", "price": 0, "duration": "1 Hour", "description": "Shop for the famous 'Tarakasi' silver jewelry, a specialty of Cuttack."},
    ],
    "JHARSUGUDA_FAKE_150": [
        {"id": "Ac_JHARSUGUDA_01", "name": "Koilighughar Waterfall", "price": 0, "duration": "2 Hours", "description": "Picnic at the waterfall which has a Shiva Lingam submerged in the water."},
        {"id": "Ac_JHARSUGUDA_02", "name": "Vikramkhol Caves Trip", "price": 500, "duration": "3 Hours", "description": "Visit the prehistoric rock shelter containing ancient inscriptions and paintings."},
        {"id": "Ac_JHARSUGUDA_03", "name": "Pahadi Mandir", "price": 0, "duration": "1 Hour", "description": "A hilltop temple offering a view of the industrial town and surroundings."},
        {"id": "Ac_JHARSUGUDA_04", "name": "Ib River Boat Ride", "price": 200, "duration": "1 Hour", "description": "Enjoy a simple boat ride on the Ib river, a tributary of the Mahanadi."},
        {"id": "Ac_JHARSUGUDA_05", "name": "Jhadeswar Temple", "price": 0, "duration": "45 Mins", "description": "Visit the ancient Shiva temple that gave the district its name."},
    ],
    "RAIPUR_FAKE_151": [
        {"id": "Ac_RAIPUR_01", "name": "Swami Vivekanand Sarovar", "price": 0, "duration": "1 Hour", "description": "Walk around the Burha Talab lake. See the massive statue of Swami Vivekananda in the center."},
        {"id": "Ac_RAIPUR_02", "name": "Purkhouti Muktangan", "price": 50, "duration": "2 Hours", "description": "An open-air museum showcasing the rich tribal culture and sculptures of Chhattisgarh."},
        {"id": "Ac_RAIPUR_03", "name": "Nandan Van Zoo", "price": 50, "duration": "2 Hours", "description": "Go on a jungle safari bus ride to see lions and tigers in this zoo."},
        {"id": "Ac_RAIPUR_04", "name": "Ghatarani Waterfalls Trip", "price": 1000, "duration": "Half Day", "description": "Drive to the scenic waterfall and temple located in a lush green forest."},
        {"id": "Ac_RAIPUR_05", "name": "Marine Drive Telibandha", "price": 0, "duration": "1 Hour", "description": "Enjoy the evening vibe at the lakeside promenade. Street food and art installations."},
    ],
    "JAGDALPUR_FAKE_152": [
        {"id": "Ac_JAGDALPUR_01", "name": "Teerathgarh Falls", "price": 50, "duration": "2 Hours", "description": "Visit the multi-tiered waterfall inside Kanger Valley National Park."},
        {"id": "Ac_JAGDALPUR_02", "name": "Kutumsar Caves", "price": 50, "duration": "1 Hour", "description": "Descend into the deep limestone caves. See the blind cave fish (seasonal access)."},
        {"id": "Ac_JAGDALPUR_03", "name": "Bastar Palace", "price": 0, "duration": "1 Hour", "description": "See the historic seat of the Bastar royals. Visit during Dussehra for grandeur."},
        {"id": "Ac_JAGDALPUR_04", "name": "Anthropological Museum", "price": 20, "duration": "1 Hour", "description": "Learn about the diverse tribal groups of Bastar through exhibits and artifacts."},
        {"id": "Ac_JAGDALPUR_05", "name": "Dalpat Sagar Lake", "price": 0, "duration": "1 Hour", "description": "Watch the sunset at the large artificial lake. Visit the temple on the island."},
    ],
    "BASTAR_FAKE_153": [
        {"id": "Ac_BASTAR_01", "name": "Tribal Market Visit", "price": 0, "duration": "2 Hours", "description": "Visit a weekly Haat. See the barter system, cockfighting, and local produce."},
        {"id": "Ac_BASTAR_02", "name": "Danteshwari Temple", "price": 0, "duration": "1 Hour", "description": "Pay respects at one of the 52 Shakti Peeths in Dantewada."},
        {"id": "Ac_BASTAR_03", "name": "Dhokra Art Workshop", "price": 0, "duration": "1 Hour", "description": "Watch artisans create bell metal crafts using the lost-wax casting technique."},
        {"id": "Ac_BASTAR_04", "name": "Kanger Dhara", "price": 0, "duration": "1 Hour", "description": "A picnic spot inside the national park with small cascading waterfalls."},
        {"id": "Ac_BASTAR_05", "name": "Memory Pillars (Gamawada)", "price": 0, "duration": "1 Hour", "description": "See the ancient stone megaliths erected in memory of the deceased by tribes."},
    ],
    "CHITRAKOTE_FALLS_FAKE_154": [
        {"id": "Ac_CHITRAKOTE_01", "name": "Boat Ride to Falls", "price": 100, "duration": "45 Mins", "description": "Take a boat to the base of the 'Niagara of India'. Feel the spray of the Indravati river."},
        {"id": "Ac_CHITRAKOTE_02", "name": "Camping View", "price": 1000, "duration": "Evening", "description": "Stay in luxury tents on the cliff edge overlooking the falls."},
        {"id": "Ac_CHITRAKOTE_03", "name": "Trek Down to River", "price": 0, "duration": "1 Hour", "description": "Walk down the stairs to the river bank for photography and rock sitting."},
        {"id": "Ac_CHITRAKOTE_04", "name": "Light and Sound Show", "price": 50, "duration": "1 Hour", "description": "Watch the waterfall illuminated with colorful lights in the evening."},
        {"id": "Ac_CHITRAKOTE_05", "name": "Small Temple Visit", "price": 0, "duration": "30 Mins", "description": "Visit the small Shiva shrines located naturally in the caves near the falls."},
    ],
    "SIRPUR_FAKE_155": [
        {"id": "Ac_SIRPUR_01", "name": "Laxman Temple", "price": 25, "duration": "1 Hour", "description": "Admire the 7th-century brick temple. One of the finest examples of brick architecture."},
        {"id": "Ac_SIRPUR_02", "name": "Buddha Vihara", "price": 0, "duration": "1 Hour", "description": "Explore the excavated Buddhist monasteries. See the large Buddha statue."},
        {"id": "Ac_SIRPUR_03", "name": "Gandheshwar Temple", "price": 0, "duration": "45 Mins", "description": "Visit the Shiva temple on the Mahanadi banks. Full of recycled ancient sculptures."},
        {"id": "Ac_SIRPUR_04", "name": "Surang Tila", "price": 0, "duration": "30 Mins", "description": "Climb the steps of this excavated temple complex which had an earthquake-resistant design."},
        {"id": "Ac_SIRPUR_05", "name": "Sirpur Music Festival", "price": 0, "duration": "3 Hours", "description": "Attend the cultural fest (Jan/Feb) featuring classical music against heritage backdrops."},
    ],
    "AMARKANTAK_FAKE_156": [
        {"id": "Ac_AMARKANTAK_01", "name": "Narmada Udgam Temple", "price": 0, "duration": "1 Hour", "description": "Visit the holy tank which is the source of the River Narmada. White temples surround it."},
        {"id": "Ac_AMARKANTAK_02", "name": "Kapildhara Waterfalls", "price": 0, "duration": "1 Hour", "description": "See the first waterfall of the Narmada river, plunging 100 feet deep."},
        {"id": "Ac_AMARKANTAK_03", "name": "Ancient Temples of Kalachuri", "price": 0, "duration": "1 Hour", "description": "Explore the group of protected archaeological temples dating back to 1042 AD."},
        {"id": "Ac_AMARKANTAK_04", "name": "Mai Ki Bagiya", "price": 0, "duration": "45 Mins", "description": "A garden grove where Goddess Narmada is said to have plucked flowers."},
        {"id": "Ac_AMARKANTAK_05", "name": "Sonemuda Viewpoint", "price": 0, "duration": "1 Hour", "description": "Visit the origin point of the Sone River. Enjoy the valley view."},
    ],
    "BHEDAGHAT_FAKE_157": [
        {"id": "Ac_BHEDAGHAT_01", "name": "Marble Rocks Boat Ride", "price": 500, "duration": "1 Hour", "description": "Sail between towering cliffs of white marble on the Narmada. Magical by moonlight."},
        {"id": "Ac_BHEDAGHAT_02", "name": "Dhuandhar Falls", "price": 0, "duration": "1 Hour", "description": "Witness the powerful 'Smoke Cascade' where the river plunges into a gorge."},
        {"id": "Ac_BHEDAGHAT_03", "name": "Ropeway Ride", "price": 100, "duration": "30 Mins", "description": "Take the cable car across the Dhuandhar falls for an aerial perspective."},
        {"id": "Ac_BHEDAGHAT_04", "name": "Chausath Yogini Temple", "price": 50, "duration": "1 Hour", "description": "Climb 108 steps to the 10th-century circular temple dedicated to 64 Yoginis."},
        {"id": "Ac_BHEDAGHAT_05", "name": "Soapstone Shopping", "price": 0, "duration": "1 Hour", "description": "Buy intricate artifacts carved from the local soft soapstone."},
    ],
    "MANDLA_FAKE_158": [
        {"id": "Ac_MANDLA_01", "name": "Mandla Fort", "price": 0, "duration": "1 Hour", "description": "Explore the fort surrounded by the Narmada on three sides. Built by Gond kings."},
        {"id": "Ac_MANDLA_02", "name": "Sahastradhara", "price": 0, "duration": "1 Hour", "description": "See the spot where the Narmada flows through a thousand rocky channels."},
        {"id": "Ac_MANDLA_03", "name": "Rangrez Ghat", "price": 0, "duration": "1 Hour", "description": "Visit the historic ghats. A peaceful spot to watch the river flow."},
        {"id": "Ac_MANDLA_04", "name": "Garh Kalika Temple", "price": 0, "duration": "45 Mins", "description": "Visit the ancient temple within the fort complex."},
        {"id": "Ac_MANDLA_05", "name": "Hot Springs", "price": 0, "duration": "1 Hour", "description": "Take a dip in the medicinal hot springs located 18km away at Garam Pani."},
    ],
    "PENCH_FAKE_159": [
        {"id": "Ac_PENCH_01", "name": "Tiger Safari (Turia)", "price": 3000, "duration": "3 Hours", "description": "Enter the land of Mowgli. High chances of spotting tigers and leopards."},
        {"id": "Ac_PENCH_02", "name": "Night Safari (Wolf Sanctuary)", "price": 2500, "duration": "2 Hours", "description": "Explore the buffer zone at night. Look for wolves, owls, and civets."},
        {"id": "Ac_PENCH_03", "name": "Kohka Lake Sunset", "price": 0, "duration": "1 Hour", "description": "Watch the sunset at the lake. A great spot for bird watching."},
        {"id": "Ac_PENCH_04", "name": "Potters Village Visit", "price": 200, "duration": "1 Hour", "description": "Visit Pachdhar village. Watch potters make clay crafts and try the wheel yourself."},
        {"id": "Ac_PENCH_05", "name": "Nature Walk", "price": 500, "duration": "2 Hours", "description": "Guided walking safari in the buffer zone. Learn about tracks and trees."},
    ],
    "PANNA_FAKE_160": [
        {"id": "Ac_PANNA_01", "name": "Panna Tiger Safari", "price": 2500, "duration": "4 Hours", "description": "Explore the park famous for successful tiger reintroduction. Also see sloth bears."},
        {"id": "Ac_PANNA_02", "name": "Pandav Falls", "price": 50, "duration": "1 Hour", "description": "Visit the perennial waterfall and caves where Pandavas sought shelter."},
        {"id": "Ac_PANNA_03", "name": "Raneh Falls (Grand Canyon)", "price": 200, "duration": "2 Hours", "description": "See the multi-colored granite canyon carved by the Ken river. Spectacular scenery."},
        {"id": "Ac_PANNA_04", "name": "Diamond Mines Tour", "price": 100, "duration": "1 Hour", "description": "Visit Asia's only active diamond mine at Majhgaon (permission based)."},
        {"id": "Ac_PANNA_05", "name": "Ken Gharial Sanctuary", "price": 200, "duration": "1 Hour", "description": "Boat ride to see the long-snouted Gharials basking on the river banks."},
    ],
    "CHANDERI_FAKE_161": [
        {"id": "Ac_CHANDERI_01", "name": "Chanderi Fort", "price": 50, "duration": "2 Hours", "description": "Climb to the hilltop fort. Panoramic views of the town and 'Johar Smarak'."},
        {"id": "Ac_CHANDERI_02", "name": "Koshak Mahal", "price": 20, "duration": "1 Hour", "description": "Explore the 15th-century palace ruin. Impressive vaulted ceilings and arches."},
        {"id": "Ac_CHANDERI_03", "name": "Saree Weaving Tour", "price": 0, "duration": "1 Hour", "description": "Watch weavers creating the world-famous sheer Chanderi silk sarees."},
        {"id": "Ac_CHANDERI_04", "name": "Kati Ghati Gateway", "price": 0, "duration": "30 Mins", "description": "See the massive gateway cut through solid rock overnight according to legend."},
        {"id": "Ac_CHANDERI_05", "name": "Badal Mahal Gate", "price": 0, "duration": "30 Mins", "description": "The iconic gateway of Chanderi. A symbol of the town's architectural heritage."},
    ],
    "MAHESHWAR_FAKE_162": [
        {"id": "Ac_MAHESHWAR_01", "name": "Ahilya Fort Tour", "price": 0, "duration": "1 Hour", "description": "Walk through the riverside fort of Queen Ahilyabai Holkar. Serene and majestic."},
        {"id": "Ac_MAHESHWAR_02", "name": "Narmada Ghat Boat Ride", "price": 200, "duration": "1 Hour", "description": "Take a boat to Baneshwar temple in the middle of the river. Watch the sunset."},
        {"id": "Ac_MAHESHWAR_03", "name": "Rehwa Society Weaving", "price": 0, "duration": "1 Hour", "description": "Visit the weaving center inside the fort. Buy authentic Maheshwari sarees."},
        {"id": "Ac_MAHESHWAR_04", "name": "Narmada Aarti", "price": 0, "duration": "45 Mins", "description": "Witness the evening prayer on the ghats. Less crowded and more peaceful than Varanasi."},
        {"id": "Ac_MAHESHWAR_05", "name": "Royal Palace", "price": 20, "duration": "30 Mins", "description": "See the simple living quarters of the pious Queen Ahilyabai and her puja room."},
    ],
    "OMKARESHWAR_FAKE_163": [
        {"id": "Ac_OMKARESHWAR_01", "name": "Jyotirlinga Darshan", "price": 0, "duration": "2 Hours", "description": "Visit the Omkareshwar temple on the Mandhata island shaped like the symbol 'Om'."},
        {"id": "Ac_OMKARESHWAR_02", "name": "Mamleshwar Temple", "price": 0, "duration": "45 Mins", "description": "Visit the ancient temple on the mainland. Considered half of the Jyotirlinga."},
        {"id": "Ac_OMKARESHWAR_03", "name": "Parikrama Walk", "price": 0, "duration": "3 Hours", "description": "Walk the 7km path around the island. Pass by many ancient ruins and shrines."},
        {"id": "Ac_OMKARESHWAR_04", "name": "Narmada Boat Ride", "price": 100, "duration": "1 Hour", "description": "Cross the river or circle the island in a boat. View the hanging bridge."},
        {"id": "Ac_OMKARESHWAR_05", "name": "Siddhanath Temple", "price": 0, "duration": "1 Hour", "description": "Visit the 13th-century temple on the plateau. Famous for its frieze of elephants."},
    ],
    "BHIND_FAKE_164": [
        {"id": "Ac_BHIND_01", "name": "Ater Fort", "price": 0, "duration": "2 Hours", "description": "Explore the ruins of the Bhadauria kings' fort located deep in the Chambal ravines."},
        {"id": "Ac_BHIND_02", "name": "Vankhandeshwar Temple", "price": 0, "duration": "1 Hour", "description": "Visit the ancient Shiva temple believed to be founded by Prithviraj Chauhan."},
        {"id": "Ac_BHIND_03", "name": "Chambal Ravines View", "price": 0, "duration": "1 Hour", "description": "See the infamous 'Beehad' (badlands). A landscape historically known for dacoits."},
        {"id": "Ac_BHIND_04", "name": "Gohad Fort", "price": 0, "duration": "1 Hour", "description": "Visit the circular fort built by Jat kings. Known for its intricate enameling work."},
        {"id": "Ac_BHIND_05", "name": "Renuka Temple", "price": 0, "duration": "45 Mins", "description": "Visit the temple dedicated to the mother of Lord Parashurama."},
    ],
    "MORENA_FAKE_165": [
        {"id": "Ac_MORENA_01", "name": "Bateshwar Temples", "price": 0, "duration": "1 Hour", "description": "Marvel at the cluster of 200 restored sandstone temples in the forest."},
        {"id": "Ac_MORENA_02", "name": "Mitawali Temple", "price": 0, "duration": "1 Hour", "description": "Visit the circular Chausath Yogini temple said to have inspired the Indian Parliament design."},
        {"id": "Ac_MORENA_03", "name": "Padavali Fortress", "price": 20, "duration": "1 Hour", "description": "See the intricate erotic carvings and friezes at the entrance of the fortress."},
        {"id": "Ac_MORENA_04", "name": "Kakanmath Temple", "price": 0, "duration": "45 Mins", "description": "See the gravity-defying temple built without cement. Looks fragile but has stood for centuries."},
        {"id": "Ac_MORENA_05", "name": "Chambal Safari", "price": 1500, "duration": "2 Hours", "description": "Boat safari on the Chambal river. Spot Gharials, Muggers, and Gangetic Dolphins."},
    ],
    "DATIA_FAKE_166": [
        {"id": "Ac_DATIA_01", "name": "Peetambara Peeth", "price": 0, "duration": "1 Hour", "description": "Visit the powerful Shakti Peeth. A major center for Tantra practice."},
        {"id": "Ac_DATIA_02", "name": "Datia Palace (Bir Singh Palace)", "price": 50, "duration": "1 Hour", "description": "Explore the 7-story palace built entirely of stone and bricks without wood or iron."},
        {"id": "Ac_DATIA_03", "name": "Sonagiri Jain Temples", "price": 0, "duration": "2 Hours", "description": "Visit the hill covered with 77 white Jain temples. A stunning sight from a distance."},
        {"id": "Ac_DATIA_04", "name": "Unao Balaji Sun Temple", "price": 0, "duration": "1 Hour", "description": "Visit the ancient Sun temple. Believed to cure skin diseases."},
        {"id": "Ac_DATIA_05", "name": "Botanical Garden", "price": 20, "duration": "1 Hour", "description": "Relax in the well-maintained garden near the palace."},
    ],
    "SHIVPURI_FAKE_167": [
        {"id": "Ac_SHIVPURI_01", "name": "Royal Chhatris", "price": 50, "duration": "1 Hour", "description": "Admire the marble cenotaphs of the Scindia rulers facing each other across a garden."},
        {"id": "Ac_SHIVPURI_02", "name": "Madhav National Park", "price": 200, "duration": "2 Hours", "description": "Drive through the forest. See Sakhya Sagar lake and diverse birdlife."},
        {"id": "Ac_SHIVPURI_03", "name": "George Castle", "price": 0, "duration": "1 Hour", "description": "Visit the castle built for King George V (who never came) on the highest point of the park."},
        {"id": "Ac_SHIVPURI_04", "name": "Bhadaiya Kund", "price": 0, "duration": "1 Hour", "description": "Picnic at the natural spring. The water is mineral-rich and therapeutic."},
        {"id": "Ac_SHIVPURI_05", "name": "Banganga Temple", "price": 0, "duration": "30 Mins", "description": "Visit the old temple with 52 holy kunds (tanks)."},
    ],
    "GOKARNA_BEACHES_FAKE_168": [
        {"id": "Ac_GOKARNA_B_01", "name": "Om Beach Water Sports", "price": 500, "duration": "1 Hour", "description": "Enjoy banana boat rides and jet skiing on the famous Om-shaped beach."},
        {"id": "Ac_GOKARNA_B_02", "name": "Beach Trekking", "price": 0, "duration": "3 Hours", "description": "Trek the trail connecting Kudle, Om, Half Moon, and Paradise beaches."},
        {"id": "Ac_GOKARNA_B_03", "name": "Paradise Beach Camping", "price": 0, "duration": "Evening", "description": "Relax on the secluded beach (camping subject to permits). Accessible only by boat or trek."},
        {"id": "Ac_GOKARNA_B_04", "name": "Kudle Beach Sunset", "price": 0, "duration": "1 Hour", "description": "Watch the sunset at the most popular beach. Play volleyball or frisbee."},
        {"id": "Ac_GOKARNA_B_05", "name": "Phytoplankton Night Watch", "price": 0, "duration": "Evening", "description": "Look for bioluminescent plankton glowing in the waves at Nirvana beach (seasonal)."},
    ],
    "DANDELI_FAKE_169": [
        {"id": "Ac_DANDELI_01", "name": "River Rafting", "price": 1300, "duration": "2 Hours", "description": "Navigate the rapids of the Kali River. A thrilling white water experience."},
        {"id": "Ac_DANDELI_02", "name": "Jungle Safari", "price": 600, "duration": "2 Hours", "description": "Explore the Dandeli-Anshi Tiger Reserve. Look for Black Panthers and Hornbills."},
        {"id": "Ac_DANDELI_03", "name": "Syntheri Rocks", "price": 50, "duration": "1 Hour", "description": "See the massive 300ft tall monolith limestone rock with a river flowing at its base."},
        {"id": "Ac_DANDELI_04", "name": "Kayaking", "price": 300, "duration": "1 Hour", "description": "Paddle a kayak on the calm stretches of the Kali river or Supa reservoir."},
        {"id": "Ac_DANDELI_05", "name": "Natural Jacuzzi", "price": 0, "duration": "30 Mins", "description": "Sit in the rapids where the water massages your back naturally. Safe and fun."},
    ],
    "MURUDESHWAR_FAKE_170": [
        {"id": "Ac_MURUDESHWAR_01", "name": "Shiva Statue View", "price": 0, "duration": "1 Hour", "description": "Marvel at the world's second-tallest Shiva statue seated against the Arabian Sea backdrop."},
        {"id": "Ac_MURUDESHWAR_02", "name": "Gopuram Lift Ride", "price": 20, "duration": "30 Mins", "description": "Take the elevator to the top of the 20-story Raja Gopuram for a stunning aerial view."},
        {"id": "Ac_MURUDESHWAR_03", "name": "Netrani Island Scuba", "price": 4500, "duration": "Half Day", "description": "Boat trip to Pigeon Island for scuba diving. Clear waters and coral reefs."},
        {"id": "Ac_MURUDESHWAR_04", "name": "Murudeshwar Beach", "price": 0, "duration": "1 Hour", "description": "Enjoy water sports or a walk on the beach right next to the temple complex."},
        {"id": "Ac_MURUDESHWAR_05", "name": "Murudeshwar Fort", "price": 0, "duration": "45 Mins", "description": "Explore the renovated fort behind the temple believed to be from the Vijayanagara era."},
    ],
    "UDUPI_FAKE_171": [
        {"id": "Ac_UDUPI_01", "name": "Sri Krishna Temple", "price": 0, "duration": "1 Hour", "description": "View the deity through the 'Kanakana Kindi' window. Enjoy the free temple meal."},
        {"id": "Ac_UDUPI_02", "name": "Kapu Beach Lighthouse", "price": 20, "duration": "1 Hour", "description": "Climb the lighthouse at Kapu beach for a breathtaking view of the coastline at sunset."},
        {"id": "Ac_UDUPI_03", "name": "Manipal End Point", "price": 0, "duration": "1 Hour", "description": "Visit the cliff edge park overlooking the Swarna river. Great for jogging."},
        {"id": "Ac_UDUPI_04", "name": "Coin Museum Corp Bank", "price": 0, "duration": "45 Mins", "description": "See an extensive collection of currency from around the world at the Corporation Bank museum."},
        {"id": "Ac_UDUPI_05", "name": "Mattu Gulla Farm", "price": 0, "duration": "1 Hour", "description": "Visit the village famous for a special variety of eggplant (GI tagged)."},
    ],
    "MALPE_FAKE_172": [
        {"id": "Ac_MALPE_01", "name": "St. Mary's Island Ferry", "price": 300, "duration": "2 Hours", "description": "Take a boat to the island with hexagonal basalt rock formations. Geological wonder."},
        {"id": "Ac_MALPE_02", "name": "Sea Walkway", "price": 0, "duration": "45 Mins", "description": "Walk on the path built over the rocks into the sea. Great for photos."},
        {"id": "Ac_MALPE_03", "name": "Water Sports", "price": 500, "duration": "1 Hour", "description": "Parasailing and jet skiing at Malpe beach. Safe and well-organized."},
        {"id": "Ac_MALPE_04", "name": "Fishing Harbour Visit", "price": 0, "duration": "1 Hour", "description": "Watch the bustling activity of hundreds of colorful fishing boats unloading catch."},
        {"id": "Ac_MALPE_05", "name": "Beach Camel Ride", "price": 100, "duration": "15 Mins", "description": "Enjoy a short camel ride on the sands of Malpe Beach."},
    ],
    "MARAVANTHE_FAKE_173": [
        {"id": "Ac_MARAVANTHE_01", "name": "Highway Drive", "price": 0, "duration": "30 Mins", "description": "Drive on NH-66 with the Arabian Sea on one side and Souparnika River on the other."},
        {"id": "Ac_MARAVANTHE_02", "name": "Beach Sunset", "price": 0, "duration": "1 Hour", "description": "Stop by the highway to watch the sun dip into the ocean. Very scenic."},
        {"id": "Ac_MARAVANTHE_03", "name": "Boat Ride on River", "price": 200, "duration": "1 Hour", "description": "Take a local boat on the Souparnika river. See the coconut palms reflected in water."},
        {"id": "Ac_MARAVANTHE_04", "name": "Kodi Beach Walk", "price": 0, "duration": "1 Hour", "description": "Visit the nearby Kodi beach. Walk along the sea wall towards the lighthouse."},
        {"id": "Ac_MARAVANTHE_05", "name": "Maraswamy Temple", "price": 0, "duration": "30 Mins", "description": "Visit the Varaha temple located right on the river bank. Known for crocodiles (harmless)."},
    ],
    "MANGALORE_FAKE_174": [
        {"id": "Ac_MANGALORE_01", "name": "Panambur Beach", "price": 0, "duration": "2 Hours", "description": "Visit the cleanest beach in the city. Hosting kite festivals and sand sculpture events."},
        {"id": "Ac_MANGALORE_02", "name": "St. Aloysius Chapel", "price": 0, "duration": "1 Hour", "description": "Admire the stunning frescoes covering every inch of the walls and ceiling."},
        {"id": "Ac_MANGALORE_03", "name": "Mangaladevi Temple", "price": 0, "duration": "45 Mins", "description": "Visit the ancient temple from which the city gets its name. Kerala style architecture."},
        {"id": "Ac_MANGALORE_04", "name": "Pabba's Ice Cream", "price": 150, "duration": "45 Mins", "description": "Eat the legendary 'Gadbad' ice cream at Pabba's. A culinary must-do."},
        {"id": "Ac_MANGALORE_05", "name": "Tannirbhavi Beach", "price": 0, "duration": "1 Hour", "description": "A quieter beach with pine trees. Reachable by ferry from Sultan Battery."},
    ],
    "HASSAN_FAKE_175": [
        {"id": "Ac_HASSAN_01", "name": "Shettyhalli Church", "price": 0, "duration": "1 Hour", "description": "See the floating ruins of the Gothic church. It gets submerged during monsoon."},
        {"id": "Ac_HASSAN_02", "name": "Gorur Dam", "price": 0, "duration": "1 Hour", "description": "Visit the Hemavathi dam. A popular picnic spot with a garden."},
        {"id": "Ac_HASSAN_03", "name": "Hasanamba Temple", "price": 0, "duration": "1 Hour", "description": "Visit the temple that opens only for 2 weeks during Diwali. Very sacred."},
        {"id": "Ac_HASSAN_04", "name": "Maharaja Park", "price": 20, "duration": "1 Hour", "description": "A well-maintained park in the city center with tall trees and play areas."},
        {"id": "Ac_HASSAN_05", "name": "Mosale Temples", "price": 0, "duration": "1 Hour", "description": "Visit the twin Hoysala temples of Nageshwara and Chennakeshava in Mosale village."},
    ],
    "SHRAVANABELAGOLA_FAKE_176": [
        {"id": "Ac_SHRAVAN_01", "name": "Gommateshwara Climb", "price": 0, "duration": "2 Hours", "description": "Climb 650 steps to see the 57-foot monolithic statue of Bahubali. World's tallest monolith."},
        {"id": "Ac_SHRAVAN_02", "name": "Chandragiri Hill Temples", "price": 0, "duration": "1 Hour", "description": "Visit the smaller hill opposite Vindhyagiri. Has ancient basadis and Ashoka's footprints."},
        {"id": "Ac_SHRAVAN_03", "name": "Bhandari Basadi", "price": 0, "duration": "30 Mins", "description": "Visit the largest temple on the plain. Known for its symmetric architecture."},
        {"id": "Ac_SHRAVAN_04", "name": "Tyagada Kamba", "price": 0, "duration": "15 Mins", "description": "See the intricately carved pillar on Vindhyagiri hill. A masterpiece of art."},
        {"id": "Ac_SHRAVAN_05", "name": "Jain Math", "price": 0, "duration": "45 Mins", "description": "Visit the monastery to see rare palm-leaf manuscripts and wall paintings."},
    ],
    "SRIRANGAPATNA_FAKE_177": [
        {"id": "Ac_SRIRANG_01", "name": "Ranganathaswamy Temple", "price": 0, "duration": "1 Hour", "description": "Visit the massive Vishnu temple on the river island. One of the Pancharanga Kshetras."},
        {"id": "Ac_SRIRANG_02", "name": "Daria Daulat Bagh", "price": 20, "duration": "1 Hour", "description": "Explore Tipu Sultan's summer palace made of teak. Famous for vibrant murals."},
        {"id": "Ac_SRIRANG_03", "name": "Gumbaz", "price": 0, "duration": "30 Mins", "description": "Visit the mausoleum of Tipu Sultan and Hyder Ali. Beautiful dome and tiger stripes."},
        {"id": "Ac_SRIRANG_04", "name": "Sangam", "price": 0, "duration": "1 Hour", "description": "The confluence of three rivers. Take a coracle ride here."},
        {"id": "Ac_SRIRANG_05", "name": "Bailey's Dungeon", "price": 0, "duration": "30 Mins", "description": "See the underground prison where British officers were held captive."},
    ],
    "BANDIPUR_FAKE_178": [
        {"id": "Ac_BANDIPUR_01", "name": "Jeep Safari", "price": 3000, "duration": "3 Hours", "description": "Private jeep safari deep into the forest. Best for photography and tiger tracking."},
        {"id": "Ac_BANDIPUR_02", "name": "Bus Safari", "price": 350, "duration": "1 Hour", "description": "Government-run bus safari. Good for spotting elephants, gaur, and deer."},
        {"id": "Ac_BANDIPUR_03", "name": "Himavad Gopalaswamy Betta", "price": 0, "duration": "2 Hours", "description": "Drive to the misty hill peak with a temple. Highest peak in the park (access restricted sometimes)."},
        {"id": "Ac_BANDIPUR_04", "name": "Moyar Gorge View", "price": 0, "duration": "1 Hour", "description": "View the 'Mysore Ditch', a deep gorge separating Bandipur from Mudumalai."},
        {"id": "Ac_BANDIPUR_05", "name": "Nature Walk", "price": 200, "duration": "1 Hour", "description": "Guided walk in the periphery of the campus. Spot birds and butterflies."},
    ],
    "NAGARHOLE_FAKE_179": [
        {"id": "Ac_NAGARHOLE_01", "name": "Kabini Boat Safari", "price": 2000, "duration": "3 Hours", "description": "Safari on the backwaters. Famous for sighting elephants swimming and leopards."},
        {"id": "Ac_NAGARHOLE_02", "name": "Jeep Safari", "price": 1500, "duration": "2 Hours", "description": "Drive through the dense forest. High density of tigers and Asiatic wild dogs."},
        {"id": "Ac_NAGARHOLE_03", "name": "Iruppu Falls", "price": 50, "duration": "2 Hours", "description": "Visit the waterfall in the Brahmagiri range. A pilgrimage spot and scenic beauty."},
        {"id": "Ac_NAGARHOLE_04", "name": "Rameshwara Temple", "price": 0, "duration": "30 Mins", "description": "Visit the Shiva temple near the falls. Legend says it was installed by Lord Rama."},
        {"id": "Ac_NAGARHOLE_05", "name": "Kutta Viewpoint", "price": 0, "duration": "1 Hour", "description": "Drive through Kutta region. Coffee estates border the wildlife sanctuary."},
    ],
    "KABINI_FAKE_180": [
        {"id": "Ac_KABINI_01", "name": "Black Panther Safari", "price": 2500, "duration": "3 Hours", "description": "Look for 'Saya', the famous black panther of Kabini. Best chances in summer."},
        {"id": "Ac_KABINI_02", "name": "Coracle Ride", "price": 500, "duration": "1 Hour", "description": "Float on the river in a traditional round boat. Peaceful sunset experience."},
        {"id": "Ac_KABINI_03", "name": "Tribal Village Visit", "price": 300, "duration": "1 Hour", "description": "Visit the local Kuruba tribe village. Learn about their culture and forest life."},
        {"id": "Ac_KABINI_04", "name": "Nature Walk", "price": 200, "duration": "1 Hour", "description": "Walking tour with a naturalist. Identify varied bird species along the river bank."},
        {"id": "Ac_KABINI_05", "name": "Elephant Interaction", "price": 1000, "duration": "1 Hour", "description": "Visit the camp to see mahouts bathing and feeding camp elephants."},
    ],
    "WAYANAD_WILDLIFE_FAKE_181": [
        {"id": "Ac_WAYANAD_W_01", "name": "Tholpetty Jeep Safari", "price": 1500, "duration": "2 Hours", "description": "Explore the northern sanctuary. Good for spotting elephants and bison."},
        {"id": "Ac_WAYANAD_W_02", "name": "Muthanga Jeep Safari", "price": 1500, "duration": "2 Hours", "description": "Explore the southern range connecting to Bandipur. Rich in wildlife."},
        {"id": "Ac_WAYANAD_W_03", "name": "Bamboo Rafting", "price": 500, "duration": "2 Hours", "description": "Rafting at Kuruva Island (seasonal). Glide through the river surrounded by forest."},
        {"id": "Ac_WAYANAD_W_04", "name": "Pakshipathalam Trek", "price": 1000, "duration": "Full Day", "description": "Trek to the 'Bird World'. A cave deep in the forest (requires permit)."},
        {"id": "Ac_WAYANAD_W_05", "name": "Seetha Lava Kusha Temple", "price": 0, "duration": "45 Mins", "description": "Visit the temple near Pulpally associated with the Ramayana legend."},
    ],
    "SILENT_VALLEY_FAKE_182": [
        {"id": "Ac_SILENT_01", "name": "Sairandhri Safari", "price": 2500, "duration": "5 Hours", "description": "Jeep ride to the watchtower. View the untouched rainforest and Kunthi river."},
        {"id": "Ac_SILENT_02", "name": "Kunthi River Trek", "price": 0, "duration": "1 Hour", "description": "Walk down from Sairandhri to the crystal clear river. No plastic allowed."},
        {"id": "Ac_SILENT_03", "name": "Hanging Bridge Walk", "price": 0, "duration": "30 Mins", "description": "Walk on the suspension bridge over the Kunthi river. Surrounded by dense jungle."},
        {"id": "Ac_SILENT_04", "name": "Lion-Tailed Macaque Spotting", "price": 0, "duration": "2 Hours", "description": "Look for the endangered primate endemic to this valley."},
        {"id": "Ac_SILENT_05", "name": "Interpretation Centre", "price": 20, "duration": "1 Hour", "description": "Learn about the history of the 'Save Silent Valley' movement and ecology."},
    ],
    "ATHIRAPPILLY_FAKE_183": [
        {"id": "Ac_ATHIRAPPILLY_01", "name": "Waterfall View (Bottom)", "price": 50, "duration": "1 Hour", "description": "Walk down the steep path to feel the spray of the 'Niagara of India'."},
        {"id": "Ac_ATHIRAPPILLY_02", "name": "Vazhachal Falls", "price": 50, "duration": "1 Hour", "description": "Visit the cascading falls upstream. Safer for viewing than Athirappilly."},
        {"id": "Ac_ATHIRAPPILLY_03", "name": "Sholayar Dam Drive", "price": 0, "duration": "2 Hours", "description": "Drive through the rainforest to the dam. Great chance to spot Hornbills."},
        {"id": "Ac_ATHIRAPPILLY_04", "name": "Charpa Falls", "price": 0, "duration": "15 Mins", "description": "Roadside waterfall visible during monsoon. Flows right onto the road sometimes."},
        {"id": "Ac_ATHIRAPPILLY_05", "name": "Jungle Safari", "price": 1000, "duration": "2 Hours", "description": "Night or day safari through the oil palm forest and natural jungle."},
    ],
    "BEKAL_FAKE_184": [
        {"id": "Ac_BEKAL_01", "name": "Bekal Fort Tour", "price": 25, "duration": "2 Hours", "description": "Explore the largest keyhole-shaped fort in Kerala. Famous for the 'Tu Hi Re' song."},
        {"id": "Ac_BEKAL_02", "name": "Bekal Beach Park", "price": 20, "duration": "1 Hour", "description": "Relax in the park next to the fort. illuminated beautifully at night."},
        {"id": "Ac_BEKAL_03", "name": "Kappil Beach", "price": 0, "duration": "1 Hour", "description": "A secluded and clean beach nearby. Climb the Kodi cliff for a view."},
        {"id": "Ac_BEKAL_04", "name": "Valiyaparamba Backwaters", "price": 1000, "duration": "2 Hours", "description": "Houseboat cruise on the scenic backwaters. Less crowded than Alleppey."},
        {"id": "Ac_BEKAL_05", "name": "Nityanandashram Caves", "price": 0, "duration": "1 Hour", "description": "Explore the 45 hand-cut caves containing the panchaloha statue of the Swami."},
    ],
    "KANNUR_FAKE_185": [
        {"id": "Ac_KANNUR_01", "name": "Muzhappilangad Drive-in Beach", "price": 50, "duration": "1 Hour", "description": "Drive your car on the 4km stretch of hard sand beach. Asia's longest drive-in beach."},
        {"id": "Ac_KANNUR_02", "name": "St. Angelo Fort", "price": 20, "duration": "1 Hour", "description": "Visit the massive triangular laterite fort built by the Portuguese in 1505."},
        {"id": "Ac_KANNUR_03", "name": "Theyyam Performance", "price": 0, "duration": "3 Hours", "description": "Watch the divine ritual dance in a local temple (seasonal - Winter nights)."},
        {"id": "Ac_KANNUR_04", "name": "Arakkal Museum", "price": 30, "duration": "1 Hour", "description": "Visit the palace of the only Muslim royal family in Kerala. Maritime artifacts."},
        {"id": "Ac_KANNUR_05", "name": "Payyambalam Beach", "price": 0, "duration": "1 Hour", "description": "Walk on the famous beach with a flat coastline. View the 'Mother and Child' sculpture."},
    ],
    "THALASSERY_FAKE_186": [
        {"id": "Ac_THALASSERY_01", "name": "Thalassery Fort", "price": 0, "duration": "1 Hour", "description": "Explore the British fort with secret tunnels and a lighthouse."},
        {"id": "Ac_THALASSERY_02", "name": "Overbury's Folly", "price": 10, "duration": "1 Hour", "description": "Relax at the seaside park and cafe. Historic picnic spot."},
        {"id": "Ac_THALASSERY_03", "name": "Bakery History Tour", "price": 0, "duration": "1 Hour", "description": "Visit the oldest bakeries. Thalassery is the birthplace of baking in Kerala."},
        {"id": "Ac_THALASSERY_04", "name": "Thalassery Pier", "price": 0, "duration": "30 Mins", "description": "Walk on the old sea bridge extending into the Arabian Sea."},
        {"id": "Ac_THALASSERY_05", "name": "Mahe Day Trip", "price": 0, "duration": "2 Hours", "description": "Visit the French colony enclave nearby. See the St. Teresa's Shrine."},
    ],
    "KOZHIKODE_FAKE_187": [
        {"id": "Ac_KOZHIKODE_01", "name": "Kozhikode Beach", "price": 0, "duration": "1 Hour", "description": "Walk along the historic beach. See the two crumbling sea piers."},
        {"id": "Ac_KOZHIKODE_02", "name": "Beypore Shipyard", "price": 0, "duration": "1 Hour", "description": "Watch artisans build the massive wooden 'Uru' ships manually."},
        {"id": "Ac_KOZHIKODE_03", "name": "SM Street Food Walk", "price": 300, "duration": "1 Hour", "description": "Taste the famous Kozhikode Halwa and banana chips in Sweet Meat Street."},
        {"id": "Ac_KOZHIKODE_04", "name": "Mishkal Mosque", "price": 0, "duration": "30 Mins", "description": "Visit the 14th-century mosque with timber architecture. No minarets."},
        {"id": "Ac_KOZHIKODE_05", "name": "Mananchira Square", "price": 0, "duration": "1 Hour", "description": "Relax in the park built around the ancient tank of the Zamorin Mana."},
    ],
    "PALAKKAD_FAKE_188": [
        {"id": "Ac_PALAKKAD_01", "name": "Palakkad Fort", "price": 0, "duration": "1 Hour", "description": "Walk around the well-preserved granite fort built by Hyder Ali. Wide moat."},
        {"id": "Ac_PALAKKAD_02", "name": "Malampuzha Dam & Gardens", "price": 50, "duration": "2 Hours", "description": "Visit the dam, rose garden, and the massive Yakshi sculpture."},
        {"id": "Ac_PALAKKAD_03", "name": "Rock Garden", "price": 20, "duration": "1 Hour", "description": "See sculptures made from waste material. Designed by Nek Chand's student."},
        {"id": "Ac_PALAKKAD_04", "name": "Kalpathy Heritage Village", "price": 0, "duration": "1 Hour", "description": "Walk through the Brahmin agraharam. Famous for the Ratholsavam (Chariot fest)."},
        {"id": "Ac_PALAKKAD_05", "name": "Dhoni Waterfalls Trek", "price": 0, "duration": "3 Hours", "description": "A 3-hour trek through the forest to reach the waterfall (permission required)."},
    ],
    "THRISSUR_FAKE_189": [
        {"id": "Ac_THRISSUR_01", "name": "Vadakkunnathan Temple", "price": 0, "duration": "1 Hour", "description": "Admire the classic Kerala architecture of this Shiva temple. Venue of Thrissur Pooram."},
        {"id": "Ac_THRISSUR_02", "name": "Athirappilly Day Trip", "price": 1000, "duration": "Half Day", "description": "Drive to the famous waterfalls located in the district."},
        {"id": "Ac_THRISSUR_03", "name": "Thrissur Zoo & Museum", "price": 20, "duration": "2 Hours", "description": "Visit the zoo and art museum displaying wood carvings and swords."},
        {"id": "Ac_THRISSUR_04", "name": "Bible Tower", "price": 10, "duration": "45 Mins", "description": "Climb the tower of Our Lady of Dolours Basilica for a city view."},
        {"id": "Ac_THRISSUR_05", "name": "Vilangan Kunnu", "price": 10, "duration": "1 Hour", "description": "Drive to the hilltop park. Known as the Oxygen Jar of Thrissur."},
    ],
    "GURUVAYUR_FAKE_190": [
        {"id": "Ac_GURUVAYUR_01", "name": "Temple Darshan", "price": 0, "duration": "2 Hours", "description": "Visit the 'Dwarka of the South'. Dedicated to Lord Krishna."},
        {"id": "Ac_GURUVAYUR_02", "name": "Punnathur Kotta", "price": 10, "duration": "1 Hour", "description": "See over 50 elephants housed in the temple sanctuary. Watch them being fed."},
        {"id": "Ac_GURUVAYUR_03", "name": "Mammiyoor Temple", "price": 0, "duration": "30 Mins", "description": "Shiva temple that devotees must visit after Guruvayur for complete pilgrimage."},
        {"id": "Ac_GURUVAYUR_04", "name": "Chavakkad Beach", "price": 0, "duration": "1 Hour", "description": "Visit the beach where the river meets the sea. Famous for sunsets."},
        {"id": "Ac_GURUVAYUR_05", "name": "Institute of Mural Painting", "price": 0, "duration": "1 Hour", "description": "Watch students learning the ancient art of Kerala mural painting."},
    ],
    "KUMARAKOM_FAKE_191": [
        {"id": "Ac_KUMARAKOM_01", "name": "Bird Sanctuary Walk", "price": 100, "duration": "2 Hours", "description": "Walk the trail to see migratory birds like Siberian Cranes (seasonal)."},
        {"id": "Ac_KUMARAKOM_02", "name": "Houseboat Cruise", "price": 5000, "duration": "Half Day", "description": "Cruise on Vembanad Lake. Lunch served on board with local Karimeen fish."},
        {"id": "Ac_KUMARAKOM_03", "name": "Toddy Shop Visit", "price": 300, "duration": "1 Hour", "description": "Try fresh toddy and spicy duck roast at a local shop."},
        {"id": "Ac_KUMARAKOM_04", "name": "Driftwood Museum", "price": 50, "duration": "45 Mins", "description": "See unique sculptures made from driftwood collected from the Andaman seas."},
        {"id": "Ac_KUMARAKOM_05", "name": "Village Life Experience", "price": 500, "duration": "2 Hours", "description": "Try your hand at coir making and weaving coconut leaves with locals."},
    ],
    "MUNROE_ISLAND_FAKE_192": [
        {"id": "Ac_MUNROE_01", "name": "Canoe Tour", "price": 800, "duration": "2 Hours", "description": "Navigate the narrow canals in a small canoe. Duck your head under low bridges."},
        {"id": "Ac_MUNROE_02", "name": "Mangrove Walk", "price": 0, "duration": "1 Hour", "description": "Walk through the mangrove archways. A photographer's delight."},
        {"id": "Ac_MUNROE_03", "name": "Homestay Lunch", "price": 400, "duration": "1 Hour", "description": "Enjoy an authentic Kerala meal served on a banana leaf at a local home."},
        {"id": "Ac_MUNROE_04", "name": "Kallada River Fishing", "price": 0, "duration": "1 Hour", "description": "Watch locals fishing with nets or try angling yourself."},
        {"id": "Ac_MUNROE_05", "name": "Sunset Point", "price": 0, "duration": "1 Hour", "description": "Watch the sun set over the Ashtamudi Lake confluence."},
    ],
    "VARKALA_CLIFF_FAKE_193": [
        {"id": "Ac_VARKALA_C_01", "name": "North Cliff Walk", "price": 0, "duration": "1 Hour", "description": "Stroll along the cliff edge lined with bohemian cafes and shops."},
        {"id": "Ac_VARKALA_C_02", "name": "Paragliding", "price": 3500, "duration": "30 Mins", "description": "Fly from the helipad on the cliff. Float over the ocean and golden sands."},
        {"id": "Ac_VARKALA_C_03", "name": "Steps to Black Beach", "price": 0, "duration": "30 Mins", "description": "Walk down the steep steps to the secluded Black Beach."},
        {"id": "Ac_VARKALA_C_04", "name": "Sunset Yoga", "price": 500, "duration": "1 Hour", "description": "Join a yoga class on a rooftop overlooking the Arabian Sea."},
        {"id": "Ac_VARKALA_C_05", "name": "Tibetan Market Shopping", "price": 0, "duration": "1 Hour", "description": "Buy silver jewelry and singing bowls from the Tibetan shops on the cliff."},
    ],
    "POOVAR_FAKE_194": [
        {"id": "Ac_POOVAR_01", "name": "Motorboat Cruise", "price": 1500, "duration": "2 Hours", "description": "Cruise through the Neyyar river estuary. See the Golden Sand Beach."},
        {"id": "Ac_POOVAR_02", "name": "Mangrove Forest Ride", "price": 0, "duration": "30 Mins", "description": "Pass through thick mangrove forests. Spot water birds and eagles."},
        {"id": "Ac_POOVAR_03", "name": "Floating Restaurant", "price": 500, "duration": "1 Hour", "description": "Have lunch at a restaurant floating on the backwaters."},
        {"id": "Ac_POOVAR_04", "name": "Estuary Sunset", "price": 0, "duration": "1 Hour", "description": "Watch the sun set where the river, lake, and sea meet."},
        {"id": "Ac_POOVAR_05", "name": "Elephant Rock", "price": 0, "duration": "30 Mins", "description": "See the rock formation that looks like an elephant during the boat ride."},
    ],
    "PONMUDI_FAKE_195": [
        {"id": "Ac_PONMUDI_01", "name": "Golden Valley", "price": 20, "duration": "2 Hours", "description": "Relax by the Kallar river. clear water and rounded pebbles."},
        {"id": "Ac_PONMUDI_02", "name": "Meenmutty Falls Trek", "price": 200, "duration": "2 Hours", "description": "Trek through the forest to reach the waterfall (requires guide)."},
        {"id": "Ac_PONMUDI_03", "name": "Hill Top Viewpoint", "price": 0, "duration": "1 Hour", "description": "Drive to the top via 22 hairpin bends. View the mist-covered valleys."},
        {"id": "Ac_PONMUDI_04", "name": "Peppara Wildlife Sanctuary", "price": 50, "duration": "2 Hours", "description": "Visit the sanctuary on the way. Spot elephants and sambar deer."},
        {"id": "Ac_PONMUDI_05", "name": "Echo Point", "price": 0, "duration": "30 Mins", "description": "Shout out at the Echo Point and hear your voice bounce back from the hills."},
    ],
    "COURTALLAM_FAKE_196": [
        {"id": "Ac_COURTALLAM_01", "name": "Main Falls Bath", "price": 0, "duration": "1 Hour", "description": "Take a herbal bath in the massive Main Falls. Believed to cure skin ailments."},
        {"id": "Ac_COURTALLAM_02", "name": "Five Falls (Aintharuvi)", "price": 0, "duration": "1 Hour", "description": "Bathe where the water splits into five branches like a cobra's hood."},
        {"id": "Ac_COURTALLAM_03", "name": "Old Courtallam Falls", "price": 0, "duration": "1 Hour", "description": "Visit the less crowded waterfall. Steps carved into rock lead to the pool."},
        {"id": "Ac_COURTALLAM_04", "name": "Tiger Falls", "price": 0, "duration": "30 Mins", "description": "A smaller, safer waterfall suitable for children and families."},
        {"id": "Ac_COURTALLAM_05", "name": "Border Parotta Feast", "price": 200, "duration": "1 Hour", "description": "Eat the famous spicy chicken and parotta at a 'Border Shop' nearby."},
    ],
    "KODAIKANAL_LAKE_FAKE_197": [
        {"id": "Ac_KODAI_LAKE_01", "name": "Cycling around Lake", "price": 100, "duration": "1 Hour", "description": "Rent a cycle and ride on the 5km path circling the star-shaped lake."},
        {"id": "Ac_KODAI_LAKE_02", "name": "Shikara Ride", "price": 300, "duration": "1 Hour", "description": "Take a unique Shikara boat ride usually found in Kashmir."},
        {"id": "Ac_KODAI_LAKE_03", "name": "Horse Riding", "price": 200, "duration": "30 Mins", "description": "Ride a horse along the lake periphery. Popular with kids."},
        {"id": "Ac_KODAI_LAKE_04", "name": "Balloon Shooting", "price": 50, "duration": "30 Mins", "description": "Play shooting games at the stalls lining the lake entrance."},
        {"id": "Ac_KODAI_LAKE_05", "name": "Bryant Park", "price": 30, "duration": "1 Hour", "description": "Visit the botanical garden right next to the lake. Famous for the Glass House."},
    ],
    "VALPARAI_FAKE_198": [
        {"id": "Ac_VALPARAI_01", "name": "Tea Estate Drive", "price": 0, "duration": "1 Hour", "description": "Drive through the endless tea carpets. Valparai is less commercialized than Munnar."},
        {"id": "Ac_VALPARAI_02", "name": "Aliyar Dam", "price": 20, "duration": "1 Hour", "description": "Visit the park at the base of the hills. Boating available."},
        {"id": "Ac_VALPARAI_03", "name": "Nallamudi Poonjolai", "price": 0, "duration": "1 Hour", "description": "Walk through tea bushes to a viewpoint offering a view of the Anamalai Tiger Reserve."},
        {"id": "Ac_VALPARAI_04", "name": "Monkey Falls", "price": 30, "duration": "1 Hour", "description": "A roadside waterfall famous for its population of macaques."},
        {"id": "Ac_VALPARAI_05", "name": "Loam's View Point", "price": 0, "duration": "30 Mins", "description": "Stop at the 9th hairpin bend for a view of the Aliyar dam reservoir."},
    ],
    "YERCAUD_FAKE_199": [
        {"id": "Ac_YERCAUD_01", "name": "Emerald Lake Boating", "price": 200, "duration": "1 Hour", "description": "Paddle in the lake surrounded by hills and a deer park."},
        {"id": "Ac_YERCAUD_02", "name": "Lady's Seat", "price": 0, "duration": "1 Hour", "description": "View the winding ghat road and Salem city through the telescope."},
        {"id": "Ac_YERCAUD_03", "name": "Killiyur Falls Trek", "price": 0, "duration": "2 Hours", "description": "Trek down a steep path to see the waterfall overflowing from the lake."},
        {"id": "Ac_YERCAUD_04", "name": "Pagoda Point", "price": 0, "duration": "1 Hour", "description": "Visit the viewpoint with stone pyramids. Good for sunrise."},
        {"id": "Ac_YERCAUD_05", "name": "Shevaroy Temple", "price": 0, "duration": "1 Hour", "description": "Visit the cave temple at the highest point in Yercaud."},
    ],
    "KOLLI_HILLS_FAKE_200": [
        {"id": "Ac_KOLLI_01", "name": "70 Hairpin Bends Drive", "price": 0, "duration": "2 Hours", "description": "Experience the thrilling drive up the hill with 70 sharp turns."},
        {"id": "Ac_KOLLI_02", "name": "Agaya Gangai Waterfalls", "price": 0, "duration": "3 Hours", "description": "Descend 1000 steps to reach the base of the massive waterfall."},
        {"id": "Ac_KOLLI_03", "name": "Arapaleeswarar Temple", "price": 0, "duration": "45 Mins", "description": "Visit the ancient Shiva temple. The starting point for the falls trek."},
        {"id": "Ac_KOLLI_04", "name": "Seekuparai Viewpoint", "price": 0, "duration": "1 Hour", "description": "A viewpoint offering a panoramic view of the plains. Has a government resort."},
        {"id": "Ac_KOLLI_05", "name": "Botanical Garden", "price": 20, "duration": "1 Hour", "description": "Visit the garden featuring a rose garden, eco-friendly cottages, and a viewpoint."},
    ]
}


def get_activities_for_destination(tbo_id: str) -> list[dict]:
    if tbo_id in ACTIVITIES_MAP:
        return ACTIVITIES_MAP[tbo_id]

    dest = DESTINATION_MAP.get(tbo_id)
    if dest:
        name = dest["name"]
    else:
        # Handle LOCAL_ prefixed IDs (e.g. LOCAL_SUNDERBANS → Sunderbans)
        name = tbo_id.replace("LOCAL_", "").replace("_", " ").title()
        
    # Generic fallback activities for any destination
    return [
        {"id": f"Ac_{tbo_id}_01", "name": f"Highlights Tour of {name}", "price": 1500, "duration": "Half Day", "description": f"Discover the most iconic landmarks and hidden gems of {name} with a knowledgeable local guide who brings the city's story alive."},
        {"id": f"Ac_{tbo_id}_02", "name": f"Local Cuisine Tasting", "price": 2000, "duration": "Evening", "description": f"Savour the authentic flavours of {name} on a guided food trail. Sample street delicacies, traditional dishes, and local sweets at handpicked eateries."},
        {"id": f"Ac_{tbo_id}_03", "name": f"Sunset Viewpoint Visit", "price": 800, "duration": "2 Hours", "description": f"Head to the best sunset spot in {name} for golden-hour views you'll never forget. Perfect for photography and quiet reflection."},
        {"id": f"Ac_{tbo_id}_04", "name": f"Heritage Walk in {name}", "price": 1200, "duration": "Half Day", "description": f"Walk through the historic heart of {name}, exploring ancient architecture, vibrant markets, and cultural landmarks with expert commentary."},
        {"id": f"Ac_{tbo_id}_05", "name": f"Full Day Private Explorer", "price": 5000, "duration": "Full Day", "description": f"A fully customisable private day tour of {name}. Your personal guide tailors the itinerary to your interests — temples, nature, or local culture."},
    ]



def get_region(tbo_id: str) -> str:
    """Return the geographic region label for a destination TBO ID."""
    return REGION_MAP.get(tbo_id, "Other")


def get_compatible_stops(anchor_tbo_id: str, exclude_ids: list[str], n: int = 2) -> list[str]:
    """
    Return up to n additional TBO IDs from the same region as the anchor,
    in logical circuit order, excluding the anchor and any already-used IDs.
    Falls back to the nearest other region if the anchor's region has too few destinations.
    """
    region = get_region(anchor_tbo_id)
    ordered = _REGION_STOP_ORDER.get(region, [])
    excluded = set(exclude_ids) | {anchor_tbo_id}
    compatible = [tid for tid in ordered if tid not in excluded and tid in DESTINATION_MAP]
    # If region is too small, supplement from closest-feel region
    if len(compatible) < n:
        fallback_regions = {
            "Islands": "South India",
            "West India": "South India",
            "North India (Plains)": "Rajasthan",
        }
        fb_region = fallback_regions.get(region, "South India")
        fb_ordered = _REGION_STOP_ORDER.get(fb_region, [])
        for tid in fb_ordered:
            if tid not in excluded and tid in DESTINATION_MAP and tid not in compatible:
                compatible.append(tid)
            if len(compatible) >= n:
                break
    return compatible[:n]


def get_budget_tier(budget: int) -> str:
    if budget < 15000:
        return "budget"
    elif budget <= 30000:
        return "mid-range"
    return "premium"


async def _check_flight_connectivity(client: httpx.AsyncClient, dest_airport: str, travel_date: datetime = None) -> Optional[float]:
    """
    Search TBO for DEL -> dest_airport flights (real fare for this destination).
    Falls back to DEL -> BLR proxy if the destination airport has no UAT inventory.
    Returns the minimum PublishedFare (INR) for 1 adult, or None on auth failure.
    """
    FALLBACK_AIRPORT = "BLR"  # DEL->BLR confirmed: 111 flights, always available in UAT

    try:
        # 1. Authenticate
        auth_data = {
            "ClientId": "ApiIntegrationNew",
            "EndUserIp": "127.0.0.1",
            "UserName": _flight_user(),
            "Password": _flight_pass()
        }
        res_auth = await client.post(TBO_FLIGHT_AUTH_URL, json=auth_data, timeout=10.0)
        res_auth.raise_for_status()
        auth_json = res_auth.json()
        auth_token = auth_json.get("TokenId")

        if not auth_token or auth_json.get("Status") != 1:
            logger.warning(f"TBO Flight auth failed: {auth_json.get('Error')}")
            return None

        # Use the provided travel_date, or default to +30 days 
        target_date = travel_date or (datetime.now() + timedelta(days=30))
        dep_date = f"{target_date:%Y-%m-%dT00:00:00}"

        # 2. Try real destination first, fall back to proxy if no results
        airports_to_try = [dest_airport]
        if dest_airport != FALLBACK_AIRPORT:
            airports_to_try.append(FALLBACK_AIRPORT)

        for airport in airports_to_try:
            is_fallback = (airport == FALLBACK_AIRPORT and airport != dest_airport)
            search_data = {
                "EndUserIp": "127.0.0.1",
                "TokenId": auth_token,
                "AdultCount": "1",
                "ChildCount": "0",
                "InfantCount": "0",
                "JourneyType": "1",
                "Segments": [{
                    "Origin": "DEL",
                    "Destination": airport,
                    "FlightCabinClass": "1",
                    "PreferredDepartureTime": dep_date,
                    "PreferredArrivalTime": dep_date
                }]
            }
            res_search = await client.post(TBO_FLIGHT_SEARCH_URL, json=search_data, timeout=8.0)
            response_data = res_search.json().get("Response", {})

            if response_data.get("ResponseStatus") == 1 and response_data.get("Results"):
                flights = response_data["Results"][0]
                flight_options = []
                for f in flights:
                    fare_dict = f.get("Fare", {})
                    fare_val = fare_dict.get("PublishedFare")
                    currency = fare_dict.get("Currency", "INR").upper()
                    if fare_val:
                        fare = float(fare_val)
                        if currency == "USD":
                            fare *= 85.0
                        elif currency == "EUR":
                            fare *= 90.0
                        elif currency == "GBP":
                            fare *= 105.0
                            
                        # Try to extract airline name (TBO Segments format)
                        airline = "Airline"
                        try:
                            segs = f.get("Segments", [[{}]])[0]
                            airline = segs[0].get("Airline", {}).get("AirlineName", "Unknown Airline")
                        except Exception:
                            pass
                        flight_options.append({
                            "id": f.get("ResultIndex", "0"),
                            "fare": fare,
                            "airline": airline
                        })

                if flight_options:
                    # Sort by fare and take top 5
                    flight_options.sort(key=lambda x: x["fare"])
                    top_flights = flight_options[:5]
                    min_fare = top_flights[0]["fare"]
                    
                    route = f"DEL->{airport}"
                    label = f"{route} (proxy)" if is_fallback else route
                    logger.info(f"TBO flight OK: {label} | {len(flights)} flights | min fare: Rs{min_fare:.0f}")
                    return {"min_fare": min_fare, "options": top_flights}

            err = response_data.get("Error", {})
            logger.warning(
                f"TBO DEL->{airport}: ResponseStatus={response_data.get('ResponseStatus')} "
                f"ErrCode={err.get('ErrorCode', 0)} '{err.get('ErrorMessage', '')}'"
                f"{' — trying fallback' if not is_fallback and airport != FALLBACK_AIRPORT else ''}"
            )

        return None

    except Exception as e:
        logger.warning(f"Flight connectivity check failed: {e}")
        return None


# ── Hotel code cache (city lookup is expensive — cache per tbo_id) ────────────
_hotel_code_cache: dict = {}


async def _lookup_city_code(client: httpx.AsyncClient, city_name: str) -> Optional[str]:
    """Search TBO CityList for India and return the city code for the best match."""
    try:
        r = await client.post(
            f"{TBO_HOTEL_API_URL}/CityList",
            auth=(_hotel_user(), _hotel_pass()),
            json={"CountryCode": "IN"},
            timeout=6.0,
        )
        cities = r.json().get("CityList", [])
        search = city_name.lower().split("/")[0].strip()  # handle "Leh-Ladakh" → "leh"
        # Try exact word match first, then substring
        for city in cities:
            if search == city.get("Name", "").lower().split(",")[0].strip():
                return city.get("Code")
        for city in cities:
            if search in city.get("Name", "").lower():
                return city.get("Code")
    except Exception as e:
        logger.warning(f"CityList lookup failed for '{city_name}': {e}")
    return None


async def _lookup_hotel_codes(client: httpx.AsyncClient, city_code: str) -> str:
    """Return comma-separated TBO hotel codes for a given city code (first 10)."""
    try:
        r = await client.post(
            f"{TBO_HOTEL_API_URL}/TBOHotelCodeList",
            auth=(_hotel_user(), _hotel_pass()),
            json={"CityCode": city_code, "IsDetailedResponse": "false"},
            timeout=6.0,
        )
        hlist = r.json().get("HotelCodeList", [])[:10]
        codes = [
            str(h.get("TBOHotelCode", h) if isinstance(h, dict) else h)
            for h in hlist
        ]
        return ",".join(codes)
    except Exception as e:
        logger.warning(f"TBOHotelCodeList lookup failed for city {city_code}: {e}")
    return ""


async def get_tbo_data(tbo_id: str, budget: int, travel_date_str: str = None) -> Optional[dict]:
    """
    Search TBO's live endpoints to find actual hotel prices and availability.
    If travel_date_str is provided (YYYY-MM-DD), uses that date.
    Otherwise tries +30 days first; falls back to +60 days if no rooms available.
    """
    dest_info = DESTINATION_MAP.get(tbo_id)
    if not dest_info:
        logger.error(f"Unknown destination ID {tbo_id}")
        return None

    # Immediate fail-fast for local fallback destinations not present in TBO
    if str(tbo_id).startswith("LOCAL_"):
        return {"hotels": [], "flights": [], "flight_available_from_delhi": False, "flight_min_fare": None}

    tbo_auth = (_hotel_user(), _hotel_pass())
    hotel_results = None
    hotel_price_date_label = None  # Set only when using the +60 day fallback

    async with httpx.AsyncClient(follow_redirects=True) as client:

        # ── 0. Dynamically resolve real hotel codes via TBO CityList / HotelCodeList ──
        if tbo_id not in _hotel_code_cache:
            city_name = dest_info["name"]
            city_code = await _lookup_city_code(client, city_name)
            if city_code:
                dynamic_codes = await _lookup_hotel_codes(client, city_code)
                _hotel_code_cache[tbo_id] = dynamic_codes
                if dynamic_codes:
                    logger.info(f"Dynamic hotel codes for {city_name} (cityCode={city_code}): {dynamic_codes}")
                else:
                    logger.warning(f"TBOHotelCodeList returned empty for {city_name} (cityCode={city_code}) — using hardcoded fallback")
            else:
                _hotel_code_cache[tbo_id] = ""
                logger.warning(f"City '{city_name}' not found in TBO CityList — using hardcoded fallback")

        hotel_codes_to_use = _hotel_code_cache.get(tbo_id) or dest_info["hotel_codes"]

        # ── 1. Hotel Search: Determine Target Dates ────────
        target_dates = []
        parsed_travel_date = None
        
        if travel_date_str:
            try:
                parsed_travel_date = datetime.strptime(travel_date_str, "%Y-%m-%d")
                # Ensure the date is in the future
                if parsed_travel_date > datetime.now():
                    target_dates.append({
                        "checkin": parsed_travel_date.strftime("%Y-%m-%d"),
                        "checkout": (parsed_travel_date + timedelta(days=2)).strftime("%Y-%m-%d"),
                        "is_fallback": False
                    })
                else:
                    logger.warning(f"Provided travel date {travel_date_str} is in the past. Falling back to offsets.")
            except ValueError:
                logger.warning(f"Invalid travel_date format: {travel_date_str}. Expected YYYY-MM-DD. Falling back to offsets.")
        
        if not target_dates:
            target_dates = [
                {
                    "checkin": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                    "checkout": (datetime.now() + timedelta(days=32)).strftime("%Y-%m-%d"),
                    "is_fallback": False
                },
                {
                    "checkin": (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d"),
                    "checkout": (datetime.now() + timedelta(days=62)).strftime("%Y-%m-%d"),
                    "is_fallback": True
                }
            ]

        for date_info in target_dates:
            checkin = date_info["checkin"]
            checkout = date_info["checkout"]
            
            search_payload = {
                "CheckIn": checkin,
                "CheckOut": checkout,
                "HotelCodes": hotel_codes_to_use,
                "GuestNationality": "IN",
                "PaxRooms": [{"Adults": 1, "Children": 0}],
                "IsDetailedResponse": False,
                "Filters": {"Refundable": False, "NoOfRooms": 0, "MealType": 0,
                            "OrderBy": 0, "StarRating": 0, "HotelName": None},
                "ResponseTime": 15.0,
            }
            try:
                res = await client.post(
                    f"{TBO_HOTEL_API_URL}/Search",
                    auth=tbo_auth, json=search_payload, timeout=30.0
                )
                res.raise_for_status()
                data = res.json()
                
                import json
                logger.info(f"\n{'='*50}\nTBO HOTEL SEARCH RAW RESPONSE ({dest_info['name']})\n{'='*50}\n{json.dumps(data, indent=2)}\n")
                
                status_code = data.get("Status", {}).get("Code")
                if status_code == 200 and data.get("HotelResult"):
                    hotel_results = data["HotelResult"]
                    if date_info.get("is_fallback"):
                        hotel_price_date_label = f"{checkin} to {checkout}"
                    logger.info(
                        f"TBO Hotel OK for {dest_info['name']} "
                        f"({checkin}-{checkout}): {len(hotel_results)} hotels"
                    )
                    break
                else:
                    logger.warning(
                        f"TBO Hotel ({checkin}-{checkout}): Code={status_code} "
                        f"'{data.get('Status',{}).get('Description','')}'"
                        f" — retrying with later dates"
                    )
            except Exception as e:
                logger.error(f"TBO Search exception ({checkin}-{checkout}): {e}")

        if not hotel_results:
            logger.warning(
                f"TBO returned no hotel results for {dest_info['name']} on all date offsets. "
                "No hotels available — returning None."
            )
            hotel_results = []

        # ── 2. Extract prices from Rooms[0].TotalFare (real API field) ────────
        valid_hotels = []
        best_price = float("inf")

        for hotel in hotel_results:
            rooms = hotel.get("Rooms", [])
            currency = hotel.get("Currency", "INR").upper()
            if not rooms:
                continue
            try:
                total_fare = float(rooms[0].get("TotalFare", float("inf")))
                if currency == "USD":
                    total_fare *= 85.0
                elif currency == "EUR":
                    total_fare *= 90.0
                elif currency == "GBP":
                    total_fare *= 105.0
            except (TypeError, ValueError):
                total_fare = float("inf")
            if total_fare == float("inf"):
                continue
            # Price per night based on the 2-night stay window used in the local search
            price_per_night = round(total_fare / 2, 2)

            if total_fare <= float(budget):
                valid_hotels.append({
                    "HotelCode": hotel.get("HotelCode"),
                    "TotalFare": total_fare,
                    "price_per_night": price_per_night,
                })
                best_price = min(best_price, total_fare)

            if len(valid_hotels) == 20:
                break

        if not valid_hotels:
            # No real hotels within budget — signal unavailability clearly
            logger.info(f"No hotels within budget ₹{budget} for {dest_info['name']}")
            return None

        # ── 3. Fetch hotel details (name, rating, images) ────────────────────
        hotel_codes = ",".join([str(h["HotelCode"]) for h in valid_hotels])
        hotel_map: dict = {}
        try:
            res_details = await client.post(
                f"{TBO_HOTEL_API_URL}/HotelDetails",
                auth=tbo_auth,
                json={"Hotelcodes": hotel_codes, "Language": "EN"},
                timeout=30.0
            )
            res_details.raise_for_status()
            det_data = res_details.json()
            hotel_details_list = det_data.get("HotelDetails", [])
            hotel_map = {str(d.get("HotelCode")): d for d in hotel_details_list}
        except Exception as e:
            logger.warning(f"TBO HotelDetails exception: {e}. Falling back to mock details.")

        final_hotels = []
        # Track minimum prices per tier
        tiered_min_prices = {
            "budget": float("inf"),
            "standard": float("inf"),
            "premium": float("inf")
        }
        
        for vh in valid_hotels:
            code = str(vh["HotelCode"])
            details = hotel_map.get(code, {})

            # Rating
            r_val = details.get("HotelRating", "ThreeStar")
            rating = 3.0
            if isinstance(r_val, (int, float)):
                rating = float(r_val)
            elif isinstance(r_val, str):
                if "Four" in r_val or "4" in r_val: rating = 4.0
                elif "Five" in r_val or "5" in r_val: rating = 5.0
                elif "Two" in r_val or "2" in r_val: rating = 2.0
                elif "One" in r_val or "1" in r_val: rating = 1.0

            # Images
            raw_images = details.get("Images", [])
            if isinstance(raw_images, list):
                image_list: List[str] = [str(img) for img in raw_images if img]
            elif isinstance(raw_images, str) and raw_images:
                image_list = [raw_images]
            else:
                image_list = []

            hotel_name = (
                details.get("HotelName")
                or f"{dest_info['name']} Hotel {code[-3:]}"
            )
            description = str(
                details.get("Description")
                or f"Experience {dest_info['name']} at {hotel_name}."
            )[:200]
            image_url = (image_list[0] if image_list else None) or (
                "https://images.unsplash.com/photo-1566073771259-6a8506099945"
                "?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
            )

            final_hotels.append({
                "name": hotel_name,
                "price_per_night": vh["price_per_night"],
                "rating": rating,
                "photo": image_url,
                "description": description,
            })
            
            # Update tiered prices
            price = vh["price_per_night"] * 2 # Price for 2 nights
            if rating <= 3.5:
                tiered_min_prices["budget"] = min(tiered_min_prices["budget"], price)
            elif rating <= 4.5:
                # Some 4.5 might be standard, but usually premium. Let's say <= 4.0 is standard
                if rating <= 4.0:
                    tiered_min_prices["standard"] = min(tiered_min_prices["standard"], price)
                else:
                    tiered_min_prices["premium"] = min(tiered_min_prices["premium"], price)
            else:
                tiered_min_prices["premium"] = min(tiered_min_prices["premium"], price)
                
        # Clean up infinities
        tiered_hotel_prices = {
            t: (p if p != float("inf") else None) for t, p in tiered_min_prices.items()
        }

        # ── 4. Flight connectivity check (DEL -> Destination) ────────────────────
        flight_fares = {}
        dest_airport = dest_info.get("airport_code")
        if dest_airport:
            flight_fare = await _check_flight_connectivity(client, dest_airport, parsed_travel_date)
            if flight_fare:
                flight_fares["DEL"] = flight_fare

        if hotel_results:
            return {
                "destination": dest_info["name"],
                "price_per_person": min([h["price_per_night"] for h in valid_hotels], default=0) * 2,
                "hotels": valid_hotels,
                "tiered_hotel_prices": tiered_hotel_prices,
                "flight_available_from_delhi": "DEL" in flight_fares,
                "flight_min_fare": flight_fares.get("DEL"),
                "hotel_price_date_label": hotel_price_date_label,  # None = +30d, str = fallback date
                "tagline": dest_info.get("tagline", ""),
                "best_season": dest_info.get("best_season", ""),
            }

        return None
