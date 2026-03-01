import asyncio
import httpx
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

TBO_HOTEL_API_URL = "http://api.tbotechnology.in/TBOHolidays_HotelAPI"

def _hotel_user() -> str:
    return os.getenv("TBO_API_USER", "Hackathon")

def _hotel_pass() -> str:
    return os.getenv("TBO_API_PASSWORD", "Hackathon@1234")

# Sample of cities to test
CITIES = {
    "Goa": "1120548,1247101,1022623,1018880",
    "Andaman": "1019685,1121001,1022512,1248000",
    "Jaipur": "1121030,1121031,1121032",
    "Mysore": "1121039,1121040,1121041",
    "Jodhpur": "1121042,1121043,1121044",
    "Jaisalmer": "1121054,1121055,1121056",
    "Udaipur": "1121060,1121061,1121062",
    "Kovalam": "1121003,1121004,1121005"
}

OFFSETS = [15, 30, 45, 60]

async def check_inventory():
    tbo_auth = (_hotel_user(), _hotel_pass())
    
    print(f"{'City':<15} | {'Date (+15d)':<12} | {'Date (+30d)':<12} | {'Date (+45d)':<12} | {'Date (+60d)':<12}")
    print("-" * 75)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for city, codes in CITIES.items():
            results = []
            for offset in OFFSETS:
                checkin = (datetime.now() + timedelta(days=offset)).strftime("%Y-%m-%d")
                checkout = (datetime.now() + timedelta(days=offset + 5)).strftime("%Y-%m-%d")
                
                payload = {
                    "CheckIn": checkin,
                    "CheckOut": checkout,
                    "HotelCodes": codes,
                    "GuestNationality": "IN",
                    "PaxRooms": [{"Adults": 1, "Children": 0}],
                    "IsDetailedResponse": False
                }
                
                try:
                    res = await client.post(f"{TBO_HOTEL_API_URL}/Search", auth=tbo_auth, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        status = data.get("Status", {}).get("Code")
                        if status == 200 and data.get("HotelResult"):
                            # Inventory exists!
                            num_hotels = len(data["HotelResult"])
                            results.append(f"{num_hotels} hotels")
                        elif status == 201:
                            results.append("Empty")
                        else:
                            results.append(f"Err {status}")
                    else:
                        results.append(f"HTTP {res.status_code}")
                except Exception as e:
                    results.append("Timeout")
            
            print(f"{city:<15} | {results[0]:<12} | {results[1]:<12} | {results[2]:<12} | {results[3]:<12}")

if __name__ == "__main__":
    asyncio.run(check_inventory())
