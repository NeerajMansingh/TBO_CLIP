/**
 * activities.js — Master Activity Bank for VibeTravel
 * Hardcoded for hackathon demo: 6 destinations, ~7-10 activities each
 */

export const ACTIVITIES = {
    "Goa": [
        // Adventure
        {
            id: "goa_01", name: "Parasailing at Baga Beach", category: "adventure",
            duration_hrs: 2, cost: 1500, time_of_day: "morning", emoji: "🪂",
            description: "Soar above the Arabian Sea with stunning coastline views",
            tags: ["beach", "thrill", "outdoor"], popularity: 95
        },
        {
            id: "goa_02", name: "Scuba Diving at Grande Island", category: "adventure",
            duration_hrs: 4, cost: 3500, time_of_day: "morning", emoji: "🤿",
            description: "Explore vibrant coral reefs and exotic marine life",
            tags: ["water", "thrill", "nature"], popularity: 88
        },
        {
            id: "goa_03", name: "Jet Skiing at Calangute", category: "adventure",
            duration_hrs: 1, cost: 800, time_of_day: "morning", emoji: "🚤",
            description: "High-speed ride across turquoise waves",
            tags: ["beach", "thrill", "water"], popularity: 82
        },
        // Food
        {
            id: "goa_04", name: "Seafood Trail at Anjuna Market", category: "food",
            duration_hrs: 2, cost: 800, time_of_day: "evening", emoji: "🦞",
            description: "Fresh catch, local spices, Goan fish curry & feni shots",
            tags: ["food", "local", "culture"], popularity: 92
        },
        {
            id: "goa_05", name: "Spice Plantation Tour + Lunch", category: "food",
            duration_hrs: 3, cost: 1200, time_of_day: "afternoon", emoji: "🌶️",
            description: "Walk through spice farms, learn about cardamom & pepper, traditional Goan lunch",
            tags: ["food", "nature", "culture"], popularity: 78
        },
        // Culture
        {
            id: "goa_06", name: "Old Goa Churches Heritage Walk", category: "culture",
            duration_hrs: 3, cost: 500, time_of_day: "morning", emoji: "⛪",
            description: "UNESCO World Heritage churches, Portuguese colonial architecture",
            tags: ["history", "architecture", "culture"], popularity: 72
        },
        {
            id: "goa_07", name: "Latin Quarter Walking Tour", category: "culture",
            duration_hrs: 2, cost: 600, time_of_day: "afternoon", emoji: "🏘️",
            description: "Colorful Portuguese houses, art galleries & hidden cafes in Fontainhas",
            tags: ["history", "architecture", "culture"], popularity: 68
        },
        // Nightlife
        {
            id: "goa_08", name: "Sunset Cruise on Mandovi River", category: "nightlife",
            duration_hrs: 2, cost: 900, time_of_day: "evening", emoji: "🚢",
            description: "Live music, Goan dance, cocktails as the sun dips into the sea",
            tags: ["sunset", "music", "romantic"], popularity: 90
        },
        {
            id: "goa_09", name: "Tito's Lane Nightlife Crawl", category: "nightlife",
            duration_hrs: 3, cost: 2000, time_of_day: "evening", emoji: "🎶",
            description: "Legendary party strip with live DJs, rooftop bars & beach clubs",
            tags: ["nightlife", "music", "party"], popularity: 85
        },
        // Nature
        {
            id: "goa_10", name: "Dudhsagar Falls Trek", category: "nature",
            duration_hrs: 6, cost: 2000, time_of_day: "morning", emoji: "🌊",
            description: "Trek through dense jungle to one of India's tallest waterfalls",
            tags: ["nature", "hiking", "waterfall"], popularity: 85
        },
    ],

    "Jaipur": [
        {
            id: "jai_01", name: "Amber Fort & Sheesh Mahal", category: "culture",
            duration_hrs: 3, cost: 700, time_of_day: "morning", emoji: "🏰",
            description: "Majestic hilltop fort with stunning mirror palace & elephant rides",
            tags: ["history", "architecture", "culture"], popularity: 96
        },
        {
            id: "jai_02", name: "Hot Air Balloon over Jaipur", category: "adventure",
            duration_hrs: 2, cost: 8000, time_of_day: "morning", emoji: "🎈",
            description: "Sunrise flight over forts, palaces, and the pink city skyline",
            tags: ["thrill", "outdoor", "exclusive"], popularity: 91
        },
        {
            id: "jai_03", name: "Block Printing Workshop", category: "culture",
            duration_hrs: 2, cost: 1500, time_of_day: "afternoon", emoji: "🎨",
            description: "Learn traditional Rajasthani block printing with local artisans",
            tags: ["culture", "art", "local"], popularity: 75
        },
        {
            id: "jai_04", name: "Street Food Tour in Old City", category: "food",
            duration_hrs: 2, cost: 600, time_of_day: "afternoon", emoji: "🥘",
            description: "Pyaaz kachori, lassi at Lassiwala, dal baati churma — the Pink City on a plate",
            tags: ["food", "local", "culture"], popularity: 89
        },
        {
            id: "jai_05", name: "Hawa Mahal Photo Walk", category: "culture",
            duration_hrs: 1.5, cost: 200, time_of_day: "morning", emoji: "🏛️",
            description: "Iconic Palace of Winds — best photos at golden hour from the rooftop cafés",
            tags: ["history", "architecture", "culture"], popularity: 94
        },
        {
            id: "jai_06", name: "Royal Rajasthani Dinner at Chokhi Dhani", category: "food",
            duration_hrs: 3, cost: 2200, time_of_day: "evening", emoji: "🍽️",
            description: "Traditional village-themed resort with folk dance, puppet shows & thali feast",
            tags: ["food", "culture", "exclusive"], popularity: 87
        },
        {
            id: "jai_07", name: "Nahargarh Fort Sunset Trek", category: "nature",
            duration_hrs: 2, cost: 300, time_of_day: "evening", emoji: "🌅",
            description: "Hike to the hilltop fort for panoramic sunset views of the entire city",
            tags: ["nature", "hiking", "sunset"], popularity: 83
        },
        {
            id: "jai_08", name: "Johari Bazaar Shopping Spree", category: "shopping",
            duration_hrs: 2, cost: 500, time_of_day: "afternoon", emoji: "💎",
            description: "Rajasthan's famous gem market — kundan jewelry, textiles & handicrafts",
            tags: ["shopping", "local", "culture"], popularity: 77
        },
        {
            id: "jai_09", name: "Elephant Sanctuary Visit", category: "nature",
            duration_hrs: 3, cost: 2500, time_of_day: "morning", emoji: "🐘",
            description: "Feed and walk rescued elephants at Elefantastic ethical sanctuary",
            tags: ["nature", "wildlife", "outdoor"], popularity: 80
        },
    ],

    "Manali": [
        {
            id: "man_01", name: "Solang Valley Paragliding", category: "adventure",
            duration_hrs: 2, cost: 2500, time_of_day: "morning", emoji: "🪂",
            description: "Tandem paraglide over the snow-capped Himalayas with breathtaking valley views",
            tags: ["thrill", "outdoor", "mountain"], popularity: 95
        },
        {
            id: "man_02", name: "River Rafting on Beas", category: "adventure",
            duration_hrs: 3, cost: 1800, time_of_day: "morning", emoji: "🚣",
            description: "Grade III rapids through forested gorges on crystal-clear Himalayan water",
            tags: ["thrill", "water", "outdoor"], popularity: 88
        },
        {
            id: "man_03", name: "Rohtang Pass Snow Adventure", category: "adventure",
            duration_hrs: 6, cost: 3000, time_of_day: "morning", emoji: "🏔️",
            description: "Snow biking, skiing, tube rides — full day in the snow at 13,000 feet",
            tags: ["thrill", "outdoor", "mountain"], popularity: 92
        },
        {
            id: "man_04", name: "Old Manali Café Hopping", category: "food",
            duration_hrs: 2, cost: 500, time_of_day: "afternoon", emoji: "☕",
            description: "Cozy hippie cafés, wood-fired pizza, Israeli food & live acoustic sessions",
            tags: ["food", "local", "culture"], popularity: 80
        },
        {
            id: "man_05", name: "Hadimba Temple & Van Vihar Walk", category: "culture",
            duration_hrs: 2, cost: 100, time_of_day: "morning", emoji: "🛕",
            description: "4th-century carved wooden temple surrounded by ancient cedar forest",
            tags: ["history", "culture", "nature"], popularity: 74
        },
        {
            id: "man_06", name: "Jogini Waterfall Trek", category: "nature",
            duration_hrs: 3, cost: 200, time_of_day: "morning", emoji: "🌲",
            description: "Gentle hike through apple orchards and pine forests to a pristine waterfall",
            tags: ["nature", "hiking", "waterfall"], popularity: 83
        },
        {
            id: "man_07", name: "Stargazing at Sethan Village", category: "nature",
            duration_hrs: 3, cost: 1500, time_of_day: "evening", emoji: "✨",
            description: "Crystal-clear Himalayan skies, bonfire, and telescopic stargazing at 9,000 ft",
            tags: ["nature", "outdoor", "romantic"], popularity: 78
        },
        {
            id: "man_08", name: "Tibetan Market Shopping", category: "shopping",
            duration_hrs: 1.5, cost: 300, time_of_day: "afternoon", emoji: "🧶",
            description: "Woollen shawls, singing bowls, prayer flags & handmade jewelry",
            tags: ["shopping", "local", "culture"], popularity: 69
        },
    ],

    "Varanasi": [
        {
            id: "var_01", name: "Sunrise Boat Ride on Ganges", category: "culture",
            duration_hrs: 2, cost: 500, time_of_day: "morning", emoji: "🛶",
            description: "Glide past 84 ghats at dawn as the city wakes with ancient hymns",
            tags: ["culture", "history", "sunset"], popularity: 97
        },
        {
            id: "var_02", name: "Ganga Aarti at Dashashwamedh", category: "culture",
            duration_hrs: 1.5, cost: 0, time_of_day: "evening", emoji: "🪔",
            description: "Mesmerizing fire ritual with thousands of oil lamps at the river's edge",
            tags: ["culture", "history", "spiritual"], popularity: 98
        },
        {
            id: "var_03", name: "Silk Weaving Workshop", category: "culture",
            duration_hrs: 2, cost: 800, time_of_day: "afternoon", emoji: "🧵",
            description: "Watch artisans weave world-famous Banarasi silk sarees on handlooms",
            tags: ["culture", "art", "local"], popularity: 75
        },
        {
            id: "var_04", name: "Street Food Trail — Kachori Gali", category: "food",
            duration_hrs: 2, cost: 400, time_of_day: "morning", emoji: "🥟",
            description: "Blue Lassi, kachori sabzi, thandai, tamatar chaat — 2,000 years of flavors",
            tags: ["food", "local", "culture"], popularity: 90
        },
        {
            id: "var_05", name: "Ramnagar Fort Heritage Visit", category: "culture",
            duration_hrs: 2, cost: 300, time_of_day: "afternoon", emoji: "🏰",
            description: "17th-century royal palace with vintage cars, weaponry and astronomical clocks",
            tags: ["history", "architecture", "culture"], popularity: 65
        },
        {
            id: "var_06", name: "Yoga & Meditation at Assi Ghat", category: "wellness",
            duration_hrs: 2, cost: 600, time_of_day: "morning", emoji: "🧘",
            description: "Sunrise yoga session overlooking the Ganges with a certified guru",
            tags: ["wellness", "spiritual", "nature"], popularity: 82
        },
        {
            id: "var_07", name: "Sarnath Buddhist Trail", category: "culture",
            duration_hrs: 3, cost: 500, time_of_day: "morning", emoji: "☸️",
            description: "Where Buddha gave his first sermon — ancient stupas, museum & deer park",
            tags: ["history", "culture", "spiritual"], popularity: 78
        },
        {
            id: "var_08", name: "Night Walk in the Galis", category: "nightlife",
            duration_hrs: 2, cost: 300, time_of_day: "evening", emoji: "🏮",
            description: "Winding alleys lit by lanterns — local chai, live music, temple bells",
            tags: ["culture", "local", "nightlife"], popularity: 72
        },
    ],

    "Andaman Islands": [
        {
            id: "and_01", name: "Scuba Diving at Havelock", category: "adventure",
            duration_hrs: 4, cost: 4500, time_of_day: "morning", emoji: "🤿",
            description: "Dive into crystal-clear waters with 30m visibility and vibrant coral walls",
            tags: ["water", "thrill", "nature"], popularity: 96
        },
        {
            id: "and_02", name: "Sea Walking at North Bay", category: "adventure",
            duration_hrs: 2, cost: 3500, time_of_day: "morning", emoji: "🚶",
            description: "Walk on the ocean floor wearing a helmet — no swimming skills needed!",
            tags: ["water", "thrill", "outdoor"], popularity: 85
        },
        {
            id: "and_03", name: "Kayaking through Mangroves", category: "adventure",
            duration_hrs: 3, cost: 2000, time_of_day: "morning", emoji: "🛶",
            description: "Paddle through bioluminescent mangrove creeks in untouched forests",
            tags: ["nature", "water", "outdoor"], popularity: 82
        },
        {
            id: "and_04", name: "Radhanagar Beach Sunset", category: "nature",
            duration_hrs: 2, cost: 0, time_of_day: "evening", emoji: "🏖️",
            description: "Asia's best beach — white sand, turquoise water, and a legendary sunset",
            tags: ["beach", "sunset", "nature"], popularity: 94
        },
        {
            id: "and_05", name: "Cellular Jail Sound & Light Show", category: "culture",
            duration_hrs: 2, cost: 150, time_of_day: "evening", emoji: "🏛️",
            description: "Haunting history of India's freedom fighters in the former colonial prison",
            tags: ["history", "culture", "architecture"], popularity: 88
        },
        {
            id: "and_06", name: "Glass Bottom Boat at Jolly Buoy", category: "nature",
            duration_hrs: 3, cost: 1500, time_of_day: "morning", emoji: "🚤",
            description: "See coral reefs and tropical fish through a transparent-bottomed boat",
            tags: ["nature", "water", "outdoor"], popularity: 79
        },
        {
            id: "and_07", name: "Fresh Seafood at Aberdeen Market", category: "food",
            duration_hrs: 2, cost: 700, time_of_day: "evening", emoji: "🦀",
            description: "Grilled lobster, crab masala, fresh-caught fish — island dining at its best",
            tags: ["food", "local"], popularity: 83
        },
        {
            id: "and_08", name: "Elephant Beach Snorkeling", category: "adventure",
            duration_hrs: 3, cost: 1800, time_of_day: "morning", emoji: "🐠",
            description: "Snorkel in shallow warm waters with schools of colorful reef fish",
            tags: ["water", "nature", "outdoor"], popularity: 87
        },
    ],

    "Udaipur": [
        {
            id: "udp_01", name: "City Palace Museum Tour", category: "culture",
            duration_hrs: 3, cost: 500, time_of_day: "morning", emoji: "🏰",
            description: "Rajasthan's largest palace complex — 11 palaces, courtyards & lake views",
            tags: ["history", "architecture", "culture"], popularity: 95
        },
        {
            id: "udp_02", name: "Lake Pichola Sunset Boat Ride", category: "nature",
            duration_hrs: 1.5, cost: 800, time_of_day: "evening", emoji: "⛵",
            description: "Golden hour cruise past Jag Mandir and the Lake Palace floating hotel",
            tags: ["sunset", "romantic", "nature"], popularity: 93
        },
        {
            id: "udp_03", name: "Rooftop Dinner at Ambrai", category: "food",
            duration_hrs: 2, cost: 2500, time_of_day: "evening", emoji: "🍷",
            description: "Lakeside fine dining with City Palace lit up across the water",
            tags: ["food", "romantic", "exclusive"], popularity: 90
        },
        {
            id: "udp_04", name: "Miniature Painting Workshop", category: "culture",
            duration_hrs: 2, cost: 1500, time_of_day: "afternoon", emoji: "🖌️",
            description: "Learn centuries-old Mewar miniature painting techniques from master artists",
            tags: ["art", "culture", "local"], popularity: 73
        },
        {
            id: "udp_05", name: "Vintage Car Museum Visit", category: "culture",
            duration_hrs: 1.5, cost: 400, time_of_day: "afternoon", emoji: "🚗",
            description: "Rolls Royces, vintage Cadillacs & solar-powered cars from the royal collection",
            tags: ["history", "culture"], popularity: 68
        },
        {
            id: "udp_06", name: "Cycling to Badi Lake", category: "adventure",
            duration_hrs: 3, cost: 800, time_of_day: "morning", emoji: "🚴",
            description: "Scenic ride through Aravalli foothills to a peaceful countryside lake",
            tags: ["outdoor", "nature", "hiking"], popularity: 76
        },
        {
            id: "udp_07", name: "Dharohar Folk Dance Show", category: "nightlife",
            duration_hrs: 1.5, cost: 150, time_of_day: "evening", emoji: "💃",
            description: "Rajasthani folk artists perform traditional dance at Bagore ki Haveli",
            tags: ["culture", "music", "local"], popularity: 84
        },
        {
            id: "udp_08", name: "Hathi Pol Bazaar Walk", category: "shopping",
            duration_hrs: 2, cost: 300, time_of_day: "afternoon", emoji: "🛍️",
            description: "Silver jewelry, bandhani textiles, leather mojaris & traditional handicrafts",
            tags: ["shopping", "local", "culture"], popularity: 72
        },
        {
            id: "udp_09", name: "Aravalli Zipline Adventure", category: "adventure",
            duration_hrs: 2, cost: 2000, time_of_day: "morning", emoji: "🪢",
            description: "Zip across ravines in the Aravalli hills with panoramic desert views",
            tags: ["thrill", "outdoor", "nature"], popularity: 80
        },
    ],
}

export const CATEGORIES = [
    { id: "adventure", label: "Adventure", emoji: "🎯", color: "#FF6B35" },
    { id: "food", label: "Food & Drink", emoji: "🍜", color: "#F7B731" },
    { id: "culture", label: "Culture", emoji: "🏛️", color: "#A55EEA" },
    { id: "nature", label: "Nature", emoji: "🌿", color: "#26de81" },
    { id: "nightlife", label: "Nightlife", emoji: "🌙", color: "#4FC3F7" },
    { id: "wellness", label: "Wellness", emoji: "🧘", color: "#FD9644" },
    { id: "shopping", label: "Shopping", emoji: "🛍️", color: "#FC5C65" },
]

/** Utility: get activities for a destination, returns empty array if unknown */
export function getActivitiesForDestination(destinationName) {
    // Try exact match first, then case-insensitive partial match
    if (ACTIVITIES[destinationName]) return ACTIVITIES[destinationName]
    const key = Object.keys(ACTIVITIES).find(
        k => k.toLowerCase() === destinationName.toLowerCase()
    )
    return key ? ACTIVITIES[key] : []
}
