import os
import io
import json
import logging
from typing import Optional
import httpx
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

TBO_HOTEL_API_URL = "http://api.tbotechnology.in/TBOHolidays_HotelAPI"
TBO_FLIGHT_API_URL = "https://api.tektravels.com"
TBO_HOTEL_USER = os.getenv("TBO_API_USER", "Hackathon")
TBO_HOTEL_PASS = os.getenv("TBO_API_PASSWORD", "Hackathon@1234")
TBO_FLIGHT_USER = os.getenv("TBO_B2B_USER", "Hackathon")
TBO_FLIGHT_PASS = os.getenv("TBO_B2B_PASSWORD", "Hackathon@123")

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


def get_budget_tier(budget: int) -> str:
    if budget < 15000:
        return "budget"
    elif budget <= 30000:
        return "mid-range"
    return "premium"


async def _check_flight_connectivity(client: httpx.AsyncClient, dest_airport: str) -> bool:
    try:
        # 1. Auth flight API
        auth_url = f"{TBO_FLIGHT_API_URL}/Authenticate/ValidateAgency"
        auth_data = {
            "ClientId": "ApiIntegrationNew",
            "EndUserIp": "127.0.0.1",
            "TokenAgencyId": 0,
            "UserName": TBO_FLIGHT_USER,
            "Password": TBO_FLIGHT_PASS
        }
        res_auth = await client.post(auth_url, json=auth_data, timeout=7.0)
        res_auth.raise_for_status()
        auth_token = res_auth.json().get("TokenId")
        
        if not auth_token:
            return False

        # 2. Search Flight
        search_url = f"{TBO_FLIGHT_API_URL}/Search"
        # Dummy search payload to verify connectivity
        search_data = {
            "EndUserIp": "127.0.0.1",
            "TokenId": auth_token,
            "AdultCount": "1",
            "ChildCount": "0",
            "InfantCount": "0",
            "JourneyType": "1",
            "Segments": [
                {
                    "Origin": "DEL",
                    "Destination": dest_airport,
                    "FlightCabinClass": "1",
                    "PreferredDepartureTime": f"{datetime.now() + timedelta(days=30):%Y-%m-%dT%H:%M:%S}",
                    "PreferredArrivalTime": f"{datetime.now() + timedelta(days=30):%Y-%m-%dT%H:%M:%S}"
                }
            ]
        }
        
        res_search = await client.post(search_url, json=search_data, timeout=10.0)
        if res_search.json().get("Response", {}).get("Results"):
            return True
        return False
        
    except Exception as e:
        logger.warning(f"Flight search failed for {dest_airport}: {e}")
        return False


async def get_tbo_data(tbo_id: str, budget: int) -> Optional[dict]:
    """
    Search TBO's live endpoints to find actual hotel prices and availability.
    """
    dest_info = DESTINATION_MAP.get(tbo_id)
    if not dest_info:
        logger.error(f"Unknown destination ID {tbo_id}")
        return None

    checkin = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    checkout = (datetime.now() + timedelta(days=35)).strftime("%Y-%m-%d")

    # TBO Documentation says Basic Auth should be used:
    tbo_auth = (TBO_HOTEL_USER, TBO_HOTEL_PASS)

    search_payload = {
        "CheckIn": checkin,
        "CheckOut": checkout,
        "HotelCodes": dest_info["hotel_codes"],
        "GuestNationality": "IN",
        "PaxRooms": [
            {
                "Adults": 1,
                "Children": 0
            }
        ],
        "IsDetailedResponse": False
    }

    async with httpx.AsyncClient() as client:
        # Search API
        try:
            res = await client.post(f"{TBO_HOTEL_API_URL}/Search", auth=tbo_auth, json=search_payload, timeout=25.0)
            res.raise_for_status()
            data = res.json()
            
            # The API response structure: Status, HotelResult -> [ { HotelCode, TotalFare, ... } ]
            if data.get("Status", {}).get("Code") != 200:
                logger.warning(f"TBO Search failed: {data.get('Status')}")
                hotel_results = None
            else:    
                hotel_results = data.get("HotelResult", [])
            
        except Exception as e:
            logger.error(f"TBO Search exception: {e}")
            hotel_results = None

        if not hotel_results:
            logger.warning("Falling back to MOCK TBO data to ensure the demo functions.")
            # Generate realistic mock hotels based on the budget
            base_price = int(budget * 0.45)
            hotel_results = [
                {"HotelCode": hcode, "TotalFare": base_price + (i * 2500), "HotelName": f"Premium Stay {i+1} (Fallback)", "Rating": 5 if i%2==0 else 4}
                for i, hcode in enumerate(dest_info["hotel_codes"].split(","))
            ]

        # Filter and process
        valid_hotels = []
        best_price = float('inf')
        
        for hotel in hotel_results:
            total_fare = hotel.get("TotalFare", float('inf'))
            # Let's consider total fare to be for 5 nights
            price_per_night = total_fare / 5
            
            # Since budget is per person total budget (usually covering a few nights), 
            # let's map it contextually or check if total_fare fits inside the user's overall budget
            if total_fare <= budget:
                valid_hotels.append({
                    "HotelCode": hotel.get("HotelCode"),
                    "TotalFare": total_fare,
                    "price_per_night": price_per_night
                })
                best_price = min(best_price, total_fare)
                
            if len(valid_hotels) == 3:
                break
                
        if not valid_hotels:
            return None

        # Get specifics for these valid hotels
        hotel_codes = ",".join([str(h["HotelCode"]) for h in valid_hotels])
        details_payload = {
            "Hotelcodes": hotel_codes,
            "Language": "EN"
        }
        
        hotel_map = {}
        try:
            res_details = await client.post(f"{TBO_HOTEL_API_URL}/HotelDetails", auth=tbo_auth, json=details_payload, timeout=25.0)
            res_details.raise_for_status()
            det_data = res_details.json()
            
            hotel_details_list = det_data.get("HotelDetails", [])
            hotel_map = {str(d.get("HotelCode")): d for d in hotel_details_list}
            
        except Exception as e:
            logger.warning(f"TBO HotelDetails exception: {e}. Falling back to mock details.")
            # If real details failed, we will use mock details below

        final_hotels = []
        for vh in valid_hotels:
            code = str(vh["HotelCode"])
            details = hotel_map.get(code, {})
            
            # Extracts
            h_name = details.get("HotelName", f"Hotel {code}")
            
            # Rating parsing, e.g. "ThreeStar" -> 3.0
            r_str = details.get("HotelRating", "ThreeStar")
            rating = 3.0
            if "Four" in r_str: rating = 4.0
            if "Five" in r_str: rating = 5.0
            if "Two" in r_str: rating = 2.0
            if "One" in r_str: rating = 1.0
                
            images = details.get("Images", [])
            photo = images[0] if images else "https://via.placeholder.com/400x300?text=Hotel+Photo"
            
            # If real details failed or we are mocking, generate compelling mock details
            # The original code already had a fallback for h_name and photo.
            # We'll enhance it slightly based on the user's intent for "compelling mock response".
            # Note: The user's provided snippet for this part was a bit fragmented and seemed to
            # introduce new keys like 'id', 'address', 'image' which are not in the original
            # final_hotels structure. I'm adapting it to fit the existing structure.
            
            # Use existing details if available, otherwise generate mock
            hotel_name = details.get("HotelName") or f"{dest_info['name']} Grand Hotel {code[-3:]} (Fallback)"
            star_rating = rating # Use parsed rating or default 3.0
            description = details.get("Description", f"Experience the charm of {dest_info['name']} at {hotel_name}. A perfect blend of comfort and luxury.")[:200]
            image_url = (images[0] if images else None) or "https://images.unsplash.com/photo-1566073771259-6a8506099945?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
            
            final_hotels.append({
                "name": hotel_name,
                "price_per_night": vh["price_per_night"],
                "rating": star_rating,
                "photo": image_url,
                "description": description
            })

        has_flights = await _check_flight_connectivity(client, dest_info["airport"])

    return {
        "destination": dest_info["name"],
        "price_per_person": best_price, # Let's use best_price or budget calculation
        "hotels": final_hotels,
        "flight_available_from_delhi": has_flights,
        "tagline": f"Discover the magic of {dest_info['name']}",
        "best_season": "Year-round"
    }
