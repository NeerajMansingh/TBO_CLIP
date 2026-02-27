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


async def _check_flight_connectivity(client: httpx.AsyncClient, dest_airport: str) -> Optional[float]:
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

        dep_date = f"{datetime.now() + timedelta(days=30):%Y-%m-%dT00:00:00}"

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
            res_search = await client.post(TBO_FLIGHT_SEARCH_URL, json=search_data, timeout=120.0)
            response_data = res_search.json().get("Response", {})

            if response_data.get("ResponseStatus") == 1 and response_data.get("Results"):
                flights = response_data["Results"][0]
                fares = [
                    float(f.get("Fare", {}).get("PublishedFare", 0))
                    for f in flights
                    if f.get("Fare", {}).get("PublishedFare")
                ]
                min_fare = min(fares) if fares else None
                if min_fare:
                    route = f"DEL->{airport}"
                    label = f"{route} (proxy)" if is_fallback else route
                    logger.info(f"TBO flight OK: {label} | {len(flights)} flights | min fare: Rs{min_fare:.0f}")
                    return min_fare

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
            timeout=20.0,
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
            timeout=20.0,
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


async def get_tbo_data(tbo_id: str, budget: int) -> Optional[dict]:
    """
    Search TBO's live endpoints to find actual hotel prices and availability.
    Tries +30 days first; falls back to +60 days if no rooms available.
    """
    dest_info = DESTINATION_MAP.get(tbo_id)
    if not dest_info:
        logger.error(f"Unknown destination ID {tbo_id}")
        return None

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

        # ── 1. Hotel Search: try +30 days first, fall back to +60 days ────────
        for day_offset in [30, 60]:
            checkin  = (datetime.now() + timedelta(days=day_offset)).strftime("%Y-%m-%d")
            checkout = (datetime.now() + timedelta(days=day_offset + 5)).strftime("%Y-%m-%d")
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
                    auth=tbo_auth, json=search_payload, timeout=25.0
                )
                res.raise_for_status()
                data = res.json()
                status_code = data.get("Status", {}).get("Code")
                if status_code == 200 and data.get("HotelResult"):
                    hotel_results = data["HotelResult"]
                    if day_offset > 30:
                        hotel_price_date_label = f"{checkin} to {checkout}"
                    logger.info(
                        f"TBO Hotel OK for {dest_info['name']} "
                        f"({checkin}-{checkout}): {len(hotel_results)} hotels"
                    )
                    break
                else:
                    logger.warning(
                        f"TBO Hotel +{day_offset}d: Code={status_code} "
                        f"'{data.get('Status',{}).get('Description','')}'"
                        f" — retrying with later dates"
                    )
            except Exception as e:
                logger.error(f"TBO Search exception (+{day_offset}d): {e}")

        if not hotel_results:
            logger.warning("Falling back to MOCK TBO data to ensure the demo functions.")
            base_price = int(budget * 0.45)
            # Mock data uses a synthetic Rooms structure so price extraction below works uniformly
            hotel_results = [
                {
                    "HotelCode": hcode,
                    "Currency": "INR",
                    "Rooms": [{"TotalFare": base_price + (i * 2500), "Name": ["Deluxe Room"], "MealType": "Room_Only"}],
                    "_mock": True
                }
                for i, hcode in enumerate(dest_info["hotel_codes"].split(","))
            ]

        # ── 2. Extract prices from Rooms[0].TotalFare (real API field) ────────
        valid_hotels = []
        best_price = float("inf")

        for hotel in hotel_results:
            rooms = hotel.get("Rooms", [])
            if not rooms:
                continue
            try:
                total_fare = float(rooms[0].get("TotalFare", float("inf")))
            except (TypeError, ValueError):
                total_fare = float("inf")
            price_per_night = total_fare / 5  # 5-night stay

            if total_fare <= float(budget):
                valid_hotels.append({
                    "HotelCode": hotel.get("HotelCode"),
                    "TotalFare": total_fare,
                    "price_per_night": price_per_night,
                    "_mock": hotel.get("_mock", False),
                })
                best_price = min(best_price, total_fare)

            if len(valid_hotels) == 3:
                break

        if not valid_hotels:
            return None

        # ── 3. Fetch hotel details (name, rating, images) ────────────────────
        hotel_codes = ",".join([str(h["HotelCode"]) for h in valid_hotels])
        hotel_map: dict = {}
        try:
            res_details = await client.post(
                f"{TBO_HOTEL_API_URL}/HotelDetails",
                auth=tbo_auth,
                json={"Hotelcodes": hotel_codes, "Language": "EN"},
                timeout=25.0
            )
            res_details.raise_for_status()
            det_data = res_details.json()
            hotel_details_list = det_data.get("HotelDetails", [])
            hotel_map = {str(d.get("HotelCode")): d for d in hotel_details_list}
        except Exception as e:
            logger.warning(f"TBO HotelDetails exception: {e}. Falling back to mock details.")

        final_hotels = []
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
                or f"{dest_info['name']} Hotel {code[-3:]} {'(Fallback)' if vh.get('_mock') else ''}"
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

        # ── 4. Flight connectivity check ──────────────────────────────────────
        flight_min_fare = await _check_flight_connectivity(client, dest_info["airport"])

    return {
        "destination": dest_info["name"],
        "price_per_person": best_price,
        "hotels": final_hotels,
        "flight_available_from_delhi": flight_min_fare is not None,
        "flight_min_fare": int(flight_min_fare) if flight_min_fare else None,
        "hotel_price_date_label": hotel_price_date_label,  # None = +30d, str = fallback date
        "tagline": f"Discover the magic of {dest_info['name']}",
        "best_season": "Year-round",
    }

