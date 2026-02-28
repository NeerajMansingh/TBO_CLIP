"""
activity_data.py — Hardcoded activity database for VibeTravel.
Used by ActivityItineraryBuilder to look up activities by ID.
"""

from __future__ import annotations

ACTIVITIES: dict[str, list[dict]] = {
    "Goa": [
        {"id": "goa_01", "name": "Parasailing at Baga Beach", "category": "adventure", "duration_hrs": 2, "cost": 1500, "time_of_day": "morning", "popularity": 95},
        {"id": "goa_02", "name": "Scuba Diving at Grande Island", "category": "adventure", "duration_hrs": 4, "cost": 3500, "time_of_day": "morning", "popularity": 88},
        {"id": "goa_03", "name": "Jet Skiing at Calangute", "category": "adventure", "duration_hrs": 1, "cost": 800, "time_of_day": "morning", "popularity": 82},
        {"id": "goa_04", "name": "Seafood Trail at Anjuna Market", "category": "food", "duration_hrs": 2, "cost": 800, "time_of_day": "evening", "popularity": 92},
        {"id": "goa_05", "name": "Spice Plantation Tour + Lunch", "category": "food", "duration_hrs": 3, "cost": 1200, "time_of_day": "afternoon", "popularity": 78},
        {"id": "goa_06", "name": "Old Goa Churches Heritage Walk", "category": "culture", "duration_hrs": 3, "cost": 500, "time_of_day": "morning", "popularity": 72},
        {"id": "goa_07", "name": "Latin Quarter Walking Tour", "category": "culture", "duration_hrs": 2, "cost": 600, "time_of_day": "afternoon", "popularity": 68},
        {"id": "goa_08", "name": "Sunset Cruise on Mandovi River", "category": "nightlife", "duration_hrs": 2, "cost": 900, "time_of_day": "evening", "popularity": 90},
        {"id": "goa_09", "name": "Tito's Lane Nightlife Crawl", "category": "nightlife", "duration_hrs": 3, "cost": 2000, "time_of_day": "evening", "popularity": 85},
        {"id": "goa_10", "name": "Dudhsagar Falls Trek", "category": "nature", "duration_hrs": 6, "cost": 2000, "time_of_day": "morning", "popularity": 85},
    ],
    "Jaipur": [
        {"id": "jai_01", "name": "Amber Fort & Sheesh Mahal", "category": "culture", "duration_hrs": 3, "cost": 700, "time_of_day": "morning", "popularity": 96},
        {"id": "jai_02", "name": "Hot Air Balloon over Jaipur", "category": "adventure", "duration_hrs": 2, "cost": 8000, "time_of_day": "morning", "popularity": 91},
        {"id": "jai_03", "name": "Block Printing Workshop", "category": "culture", "duration_hrs": 2, "cost": 1500, "time_of_day": "afternoon", "popularity": 75},
        {"id": "jai_04", "name": "Street Food Tour in Old City", "category": "food", "duration_hrs": 2, "cost": 600, "time_of_day": "afternoon", "popularity": 89},
        {"id": "jai_05", "name": "Hawa Mahal Photo Walk", "category": "culture", "duration_hrs": 1.5, "cost": 200, "time_of_day": "morning", "popularity": 94},
        {"id": "jai_06", "name": "Royal Rajasthani Dinner", "category": "food", "duration_hrs": 3, "cost": 2200, "time_of_day": "evening", "popularity": 87},
        {"id": "jai_07", "name": "Nahargarh Fort Sunset Trek", "category": "nature", "duration_hrs": 2, "cost": 300, "time_of_day": "evening", "popularity": 83},
        {"id": "jai_08", "name": "Johari Bazaar Shopping", "category": "shopping", "duration_hrs": 2, "cost": 500, "time_of_day": "afternoon", "popularity": 77},
        {"id": "jai_09", "name": "Elephant Sanctuary Visit", "category": "nature", "duration_hrs": 3, "cost": 2500, "time_of_day": "morning", "popularity": 80},
    ],
    "Manali": [
        {"id": "man_01", "name": "Solang Valley Paragliding", "category": "adventure", "duration_hrs": 2, "cost": 2500, "time_of_day": "morning", "popularity": 95},
        {"id": "man_02", "name": "River Rafting on Beas", "category": "adventure", "duration_hrs": 3, "cost": 1800, "time_of_day": "morning", "popularity": 88},
        {"id": "man_03", "name": "Rohtang Pass Snow Adventure", "category": "adventure", "duration_hrs": 6, "cost": 3000, "time_of_day": "morning", "popularity": 92},
        {"id": "man_04", "name": "Old Manali Café Hopping", "category": "food", "duration_hrs": 2, "cost": 500, "time_of_day": "afternoon", "popularity": 80},
        {"id": "man_05", "name": "Hadimba Temple Walk", "category": "culture", "duration_hrs": 2, "cost": 100, "time_of_day": "morning", "popularity": 74},
        {"id": "man_06", "name": "Jogini Waterfall Trek", "category": "nature", "duration_hrs": 3, "cost": 200, "time_of_day": "morning", "popularity": 83},
        {"id": "man_07", "name": "Stargazing at Sethan", "category": "nature", "duration_hrs": 3, "cost": 1500, "time_of_day": "evening", "popularity": 78},
        {"id": "man_08", "name": "Tibetan Market Shopping", "category": "shopping", "duration_hrs": 1.5, "cost": 300, "time_of_day": "afternoon", "popularity": 69},
    ],
    "Varanasi": [
        {"id": "var_01", "name": "Sunrise Boat Ride on Ganges", "category": "culture", "duration_hrs": 2, "cost": 500, "time_of_day": "morning", "popularity": 97},
        {"id": "var_02", "name": "Ganga Aarti at Dashashwamedh", "category": "culture", "duration_hrs": 1.5, "cost": 0, "time_of_day": "evening", "popularity": 98},
        {"id": "var_03", "name": "Silk Weaving Workshop", "category": "culture", "duration_hrs": 2, "cost": 800, "time_of_day": "afternoon", "popularity": 75},
        {"id": "var_04", "name": "Street Food Trail", "category": "food", "duration_hrs": 2, "cost": 400, "time_of_day": "morning", "popularity": 90},
        {"id": "var_05", "name": "Ramnagar Fort Heritage Visit", "category": "culture", "duration_hrs": 2, "cost": 300, "time_of_day": "afternoon", "popularity": 65},
        {"id": "var_06", "name": "Yoga at Assi Ghat", "category": "wellness", "duration_hrs": 2, "cost": 600, "time_of_day": "morning", "popularity": 82},
        {"id": "var_07", "name": "Sarnath Buddhist Trail", "category": "culture", "duration_hrs": 3, "cost": 500, "time_of_day": "morning", "popularity": 78},
        {"id": "var_08", "name": "Night Walk in the Galis", "category": "nightlife", "duration_hrs": 2, "cost": 300, "time_of_day": "evening", "popularity": 72},
    ],
    "Andaman Islands": [
        {"id": "and_01", "name": "Scuba Diving at Havelock", "category": "adventure", "duration_hrs": 4, "cost": 4500, "time_of_day": "morning", "popularity": 96},
        {"id": "and_02", "name": "Sea Walking at North Bay", "category": "adventure", "duration_hrs": 2, "cost": 3500, "time_of_day": "morning", "popularity": 85},
        {"id": "and_03", "name": "Kayaking through Mangroves", "category": "adventure", "duration_hrs": 3, "cost": 2000, "time_of_day": "morning", "popularity": 82},
        {"id": "and_04", "name": "Radhanagar Beach Sunset", "category": "nature", "duration_hrs": 2, "cost": 0, "time_of_day": "evening", "popularity": 94},
        {"id": "and_05", "name": "Cellular Jail Light Show", "category": "culture", "duration_hrs": 2, "cost": 150, "time_of_day": "evening", "popularity": 88},
        {"id": "and_06", "name": "Glass Bottom Boat", "category": "nature", "duration_hrs": 3, "cost": 1500, "time_of_day": "morning", "popularity": 79},
        {"id": "and_07", "name": "Seafood at Aberdeen Market", "category": "food", "duration_hrs": 2, "cost": 700, "time_of_day": "evening", "popularity": 83},
        {"id": "and_08", "name": "Elephant Beach Snorkeling", "category": "adventure", "duration_hrs": 3, "cost": 1800, "time_of_day": "morning", "popularity": 87},
    ],
    "UDAIPUR": [
        {"id": "udp_01", "name": "City Palace Museum Tour", "category": "culture", "duration_hrs": 3, "cost": 500, "time_of_day": "morning", "popularity": 95},
        {"id": "udp_02", "name": "Lake Pichola Sunset Cruise", "category": "nature", "duration_hrs": 1.5, "cost": 800, "time_of_day": "evening", "popularity": 93},
        {"id": "udp_03", "name": "Rooftop Dinner at Ambrai", "category": "food", "duration_hrs": 2, "cost": 2500, "time_of_day": "evening", "popularity": 90},
        {"id": "udp_04", "name": "Miniature Painting Workshop", "category": "culture", "duration_hrs": 2, "cost": 1500, "time_of_day": "afternoon", "popularity": 73},
        {"id": "udp_05", "name": "Vintage Car Museum", "category": "culture", "duration_hrs": 1.5, "cost": 400, "time_of_day": "afternoon", "popularity": 68},
        {"id": "udp_06", "name": "Cycling to Badi Lake", "category": "adventure", "duration_hrs": 3, "cost": 800, "time_of_day": "morning", "popularity": 76},
        {"id": "udp_07", "name": "Dharohar Folk Dance Show", "category": "nightlife", "duration_hrs": 1.5, "cost": 150, "time_of_day": "evening", "popularity": 84},
        {"id": "udp_08", "name": "Hathi Pol Bazaar Walk", "category": "shopping", "duration_hrs": 2, "cost": 300, "time_of_day": "afternoon", "popularity": 72},
        {"id": "udp_09", "name": "Aravalli Zipline", "category": "adventure", "duration_hrs": 2, "cost": 2000, "time_of_day": "morning", "popularity": 80},
    ],
}

# Flat lookup by activity ID
_ACTIVITY_INDEX: dict[str, dict] = {}
for _dest, _acts in ACTIVITIES.items():
    for _act in _acts:
        _ACTIVITY_INDEX[_act["id"]] = {**_act, "destination": _dest}


def get_activity_by_id(activity_id: str) -> dict | None:
    return _ACTIVITY_INDEX.get(activity_id)


def get_activities_for_destination(destination: str) -> list[dict]:
    # Try exact match, then case-insensitive
    if destination in ACTIVITIES:
        return ACTIVITIES[destination]
    for key in ACTIVITIES:
        if key.lower() == destination.lower():
            return ACTIVITIES[key]
    return []
