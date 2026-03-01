"""
main.py — FastAPI backend for VibeTravel AI Travel Platform.

Endpoints:
  POST /itineraries    — Image-based multi-city itinerary generation (original)
  POST /search         — Text/NLP-based search (new)
  GET  /destinations   — Destination catalog for autocomplete (new)
  POST /chat           — AI conversational planning (upgraded)
  POST /itinerary/reorder    — Reorder cities (new)
  POST /itinerary/update-leg — Change transport / day count (new)
  POST /confirm        — Confirm/finalize booking (original)
  GET  /health         — Health check (original)
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import clip_utils
import chromadb_utils
import gemini_utils
import session_store
from fake_tbo import (
    DESTINATION_MAP,
    REGION_MAP,
    get_budget_tier,
    get_tbo_data,
    get_compatible_stops,
    get_region,
    get_activities_for_destination,
)
from itinerary_engine import (
    BUDGET_SPLITS,
    JOURNEY_LABELS,
    ItineraryError,
    route_optimizer,
)
from validators import (
    validate_chat_message,
    validate_reorder_request,
    validate_search_request,
    validate_session_exists,
    validate_update_leg_request,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="VibeTravel API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BACKEND_DIR = Path(__file__).parent
DESTINATIONS_DIR = BACKEND_DIR / "destinations"
DESTINATIONS_DIR.mkdir(exist_ok=True)
app.mount("/destinations", StaticFiles(directory=str(DESTINATIONS_DIR)), name="destinations")


# ─── Pydantic models ──────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str
    message: str


class ConfirmRequest(BaseModel):
    session_id: str


class SearchRequest(BaseModel):
    query: str
    budget: int = 100000
    duration_days: Optional[int] = None
    travel_month: Optional[str] = None
    vibes: Optional[List[str]] = None
    origin_city: Optional[str] = None


class ReorderRequest(BaseModel):
    session_id: str
    new_stop_order: List[str]  # list of destination names in desired order


class GeneratePackagesRequest(BaseModel):
    session_id: str
    budget: Optional[int] = 100000
    travel_month: Optional[str] = "December"
    selections: dict[str, List[str]]


class UpdateLegRequest(BaseModel):
    session_id: str
    leg_index: int
    transport_mode: Optional[str] = None
    days_at_stop: Optional[int] = None


# ─── Shared helpers ───────────────────────────────────────────────────────────

_FALLBACK_PHOTOS = {
    "Jaisalmer": "destinations/jaisalmer/1.jpg",
    "Udaipur": "https://images.unsplash.com/photo-1585136917228-a4f62be0e7c7?q=80&w=2670&auto=format&fit=crop",
    "Leh-Ladakh": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?q=80&w=2670&auto=format&fit=crop",
    "Alleppey": "https://images.unsplash.com/photo-1621689444225-0698c4af00f1?q=80&w=2670&auto=format&fit=crop",
    "Ooty": "https://images.unsplash.com/photo-1622279457486-7e72a7c17e55?q=80&w=2670&auto=format&fit=crop",
    "Rishikesh": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?q=80&w=2670&auto=format&fit=crop",
    "Shimla": "https://images.unsplash.com/photo-1595815771614-ade9d652a65d?q=80&w=2670&auto=format&fit=crop",
    "Agra": "https://images.unsplash.com/photo-1564507592224-200543666925?q=80&w=2670&auto=format&fit=crop",
}

_GENERIC_PHOTO = "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?q=80&w=2670&auto=format&fit=crop"


async def find_best_match_async(
    query_embedding,
    budget: int,
    budget_tier: str,
    exclude_names: list[str],
    n_candidates: int = 5,
) -> Optional[dict]:
    """ChromaDB similarity search + TBO data validation. Returns best match or None."""
    candidates = chromadb_utils.query_similar_destinations(
        query_embedding=query_embedding,
        budget_tier=budget_tier,
        n_results=n_candidates,
    )
    if not candidates:
        return None

    for candidate in candidates:
        if candidate["destination"] in exclude_names:
            continue
        tbo_data = await get_tbo_data(candidate["tbo_id"], budget)
        if tbo_data is None:
            continue
        return {
            "destination": candidate["destination"],
            "tbo_id": candidate["tbo_id"],
            "photo": candidate["photo"],
            "similarity_score": candidate["similarity_score"],
            "price_per_person": tbo_data["price_per_person"],
            "hotels": tbo_data["hotels"],
            "flight_min_fare": tbo_data.get("flight_min_fare"),
            "tagline": tbo_data.get("tagline", ""),
            "best_season": tbo_data.get("best_season", ""),
        }
    return None


async def _resolve_stops(
    all_stop_ids: list[str],
    budget: int,
    candidates: list[dict],
    anchor_region: str,
    budget_fractions: list[float],
) -> list[dict]:
    """Resolve TBO data for a list of stop IDs, with fallback logic."""
    stop_budgets = [int(budget * f) for f in budget_fractions]
    resolved: list[dict] = []

    for i, tbo_id in enumerate(all_stop_ids):
        per_stop_budget = stop_budgets[i] if i < len(stop_budgets) else int(budget * 0.20)
        tbo_data = await get_tbo_data(tbo_id, per_stop_budget)

        if tbo_data is None:
            for cand in candidates[1:]:
                if cand["tbo_id"] in [s["tbo_id"] for s in resolved] + [all_stop_ids[0]]:
                    continue
                if get_region(cand["tbo_id"]) == anchor_region:
                    tbo_data = await get_tbo_data(cand["tbo_id"], per_stop_budget)
                    if tbo_data:
                        tbo_id = cand["tbo_id"]
                        break

        if tbo_data:
            photo_path = next(
                (c["photo"] for c in candidates if c["tbo_id"] == tbo_id), None
            )
            if not photo_path:
                dest_meta = chromadb_utils.get_destination_by_id(tbo_id)
                photo_path = (
                    dest_meta.get("photo") if dest_meta else None
                ) or _FALLBACK_PHOTOS.get(tbo_data.get("destination", ""), _GENERIC_PHOTO)

            resolved.append({
                "destination": tbo_data["destination"],
                "tbo_id": tbo_id,
                "photo": photo_path,
                "price_per_person": tbo_data["price_per_person"],
                "hotels": tbo_data["hotels"],
                "flight_min_fare": tbo_data.get("flight_min_fare"),
                "hotel_price_date_label": tbo_data.get("hotel_price_date_label"),
                "tagline": tbo_data.get("tagline", ""),
                "best_season": tbo_data.get("best_season", ""),
            })

    return resolved


def _build_itinerary_options(
    resolved_stops: list[dict],
    budget: int,
    anchor_region: str,
) -> list[dict]:
    """Build 1/2/3-stop itinerary options from resolved stops."""
    itineraries = []
    for journey_type, fractions in BUDGET_SPLITS.items():
        n_stops = len(fractions)
        if len(resolved_stops) < n_stops:
            continue

        stops_for_type = resolved_stops[:n_stops]
        per_stop_budgets = [int(budget * f) for f in fractions]

        total_price = 0
        stop_data_for_type = []
        is_feasible = True

        for idx, stop in enumerate(stops_for_type):
            allocated = per_stop_budgets[idx]
            flight_cost = stop.get("flight_min_fare") or int(stop["price_per_person"] * 0.35)
            hotel_cost = stop["price_per_person"]
            combined_cost = flight_cost + hotel_cost

            if combined_cost > allocated:
                is_feasible = False
                break

            total_price += combined_cost
            stop_data_for_type.append({
                **stop,
                "price_per_person": combined_cost,
                "allocated_budget": allocated,
            })

        if not is_feasible or total_price > budget:
            logger.info(f"Hiding {journey_type}: exceeds budget constraint.")
            continue

        itineraries.append({
            "type": journey_type,
            "label": JOURNEY_LABELS[journey_type],
            "stops": stop_data_for_type,
            "total_price": total_price,
            "region": anchor_region,
            "stop_count": n_stops,
        })

    return itineraries


# ─── Endpoint 1: POST /itineraries (original — image-based) ──────────────────

async def _enrich_itineraries_with_tbo(itineraries: list, budget: int, travel_dates: str = None) -> list:
    """Concurrently fetch TBO data for the top matched destinations to show real prices."""
    from fake_tbo import get_tbo_data
    import asyncio

    async def fetch_and_update(itin):
        if not itin.get("stops"):
            return
        stop = itin["stops"][0]
        tbo_id = stop.get("tbo_id")
        if not tbo_id:
            return
            
        try:
            # We use an 8-second timeout so we don't block the search response forever
            tbo_data = await asyncio.wait_for(get_tbo_data(tbo_id, budget, travel_dates), timeout=8.0)
            if tbo_data is not None:
                if tbo_data.get("price_per_person"):
                    stop["price_per_person"] = tbo_data["price_per_person"]
                    itin["total_price"] = tbo_data["price_per_person"]
                if tbo_data.get("hotels"):
                    stop["hotels"] = tbo_data["hotels"]
                if tbo_data.get("flight_min_fare"):
                    stop["flights"] = [{"price": tbo_data["flight_min_fare"]}]
                    stop["flight_min_fare"] = tbo_data["flight_min_fare"]
        except asyncio.TimeoutError:
            logger.warning(f"TBO enrichment timed out for {tbo_id}")
        except Exception as e:
            logger.error(f"Error enriching {tbo_id} with TBO data: {e}")

    await asyncio.gather(*(fetch_and_update(itin) for itin in itineraries))
    return itineraries


@app.post("/itineraries")
async def build_itineraries(
    photo: UploadFile = File(...),
    budget: int = Form(...),
    travel_dates: Optional[str] = Form(None),
):
    """
    Image-based multi-city itinerary generation.
    Runs CLIP → ChromaDB → TBO for 3 geographically-constrained journey options.
    """
    logger.info(f"POST /itineraries | budget={budget} | filename={photo.filename}")

    image_bytes = await photo.read()
    try:
        import io
        from PIL import Image as PILImage
        pil_image = PILImage.open(io.BytesIO(image_bytes)).convert("RGB")
        user_embedding = clip_utils.get_image_embedding(pil_image)
    except Exception as e:
        logger.error(f"CLIP embedding failed: {e}")
        raise HTTPException(status_code=422, detail=f"Could not process image: {e}")

    budget_tier = get_budget_tier(budget)
    vibe_tags = clip_utils.get_image_vibes(pil_image)

    candidates = chromadb_utils.query_similar_destinations(
        query_embedding=user_embedding,
        budget_tier=budget_tier,
        n_results=10,
    )
    if not candidates:
        raise HTTPException(
            status_code=400,
            detail="No matching destinations found. Try a different photo or budget.",
        )

    # Pick top 3 UNIQUE destinations with category diversity
    selected_cands = []
    seen_names = set()
    seen_categories = []

    # Map to _DEST_REGISTRY early to get categories
    cand_info = []
    for cand in candidates:
        name = cand["destination"]
        reg_info = next((d for d in _DEST_REGISTRY if d["name"].lower() == name.lower()), {})
        cat = reg_info.get("category", "")
        cand_info.append((cand, reg_info, cat))

    for cand, reg_info, cat in cand_info:
        name = cand["destination"]
        if name in seen_names:
            continue
        # Diversity check: if category already seen, we can still pick it but we might want to prioritize others.
        # Since candidates are pre-sorted by CLIP similarity, we'll just enforce no exact duplicates for now.
        seen_names.add(name)
        seen_categories.append(cat)
        selected_cands.append((cand, reg_info))
        if len(selected_cands) == 3:
            break

    card_labels = [
        ("#1 Best Match",   "best-match"),
        ("#2 Great Option", "runner-up"),
        ("#3 Also Consider", "third-match"),
    ]

    itineraries = []
    for rank_idx, (cand, reg_info) in enumerate(selected_cands):
        img_path = cand.get("photo") or (f"/destinations/{reg_info['folder']}/1.jpg" if reg_info.get("folder") else None)
        label, card_type = card_labels[rank_idx]

        stop_data = {
            "destination": cand["destination"],
            "tbo_id": cand["tbo_id"],
            "photo": img_path,
            "price_per_person": cand.get("price_per_person") or 15000,
            "hotels": [],
            "flights": [],
            "tagline": reg_info.get("description", "")[:150] if reg_info else "",
            "best_season": travel_dates or "Year round",
            "itinerary": [],
            "similarity_rank": rank_idx + 1,
            "category": reg_info.get("category", ""),
            "rating": reg_info.get("rating", 4.0),
            "folder": reg_info.get("folder", ""),
        }

        itineraries.append({
            "type": card_type,
            "label": label,
            "stops": [stop_data],
            "total_price": cand.get("price_per_person") or 15000,
            "stop_count": 1,
            "region": reg_info.get("folder", "India").replace("_", " ").title() if reg_info else "India",
            "similarity_rank": rank_idx + 1,
        })

    itineraries = await _enrich_itineraries_with_tbo(itineraries, budget, travel_dates)

    first_stop = itineraries[0]["stops"][0]
    session_id = session_store.create_session(
        original_embedding=user_embedding,
        budget=budget,
        budget_tier=budget_tier,
        travel_dates=travel_dates,
        current_match=first_stop["destination"],
        current_tbo_id=first_stop["tbo_id"],
        current_price=first_stop["price_per_person"],
        current_hotels=[],
        current_photo=first_stop["photo"],
        match_reasons=["visual similarity to your photo", "matches your budget"],
        conversation_opener="I found some great places matching your photo's vibe! What do you think?",
        vibe_tags=vibe_tags,
        itinerary_stops=[first_stop],
        itinerary_type=itineraries[0]["type"],
        itinerary_label=itineraries[0]["label"],
        itinerary_region=itineraries[0]["region"],
        itinerary_total_price=itineraries[0]["total_price"],
    )

    return {
        "session_id": session_id,
        "itineraries": itineraries,
        "vibe_tags": vibe_tags,
        "match_reasons": ["visual similarity", "vibe match"],
        "conversation_opener": "I found some great places matching your photo's vibe! What do you think?",
        "route_justification": "",
        "region": itineraries[0]["region"],
    }


# ─── Endpoint 2: POST /search (new — text-based) ─────────────────────────────


# ─── Fast local keyword scorer for text search ───────────────────────────────

def _score_destination_for_query(dest: dict, query_lower: str, vibes: list) -> float:
    """Score a _DEST_REGISTRY entry against a free-text query. Pure Python, no ML."""
    score = 0.0
    name = dest["name"].lower()
    desc = dest.get("description", "").lower()
    cat  = dest.get("category", "").lower()
    highlights = " ".join(dest.get("highlights", [])).lower()
    folder = dest.get("folder", "").lower()

    # Exact / partial name match — highest signal
    if name == query_lower:
        score += 100
    elif name in query_lower or query_lower in name:
        score += 60
    elif any(word in name for word in query_lower.split() if len(word) > 2):
        score += 30

    # Folder slug match
    if folder.replace("_", " ") in query_lower:
        score += 40

    # Description + highlights match
    for word in query_lower.split():
        if len(word) < 3:
            continue
        if word in desc:
            score += 5
        if word in highlights:
            score += 8

    # Category keyword matching
    cat_keywords = {
        "beach":      ["beach", "sea", "coast", "ocean", "island", "surf", "sand"],
        "adventure":  ["adventure", "trek", "hike", "ski", "rafting", "camping", "mountain"],
        "historical": ["heritage", "fort", "palace", "history", "ancient", "mughal", "temple", "monument"],
        "nature":     ["nature", "forest", "wildlife", "waterfall", "hill", "valley", "lake", "green"],
        "cultural":   ["culture", "spiritual", "pilgrimage", "art", "festival", "yoga", "ashram", "temple"],
    }
    for cat_key, keywords in cat_keywords.items():
        if cat == cat_key:
            for kw in keywords:
                if kw in query_lower:
                    score += 15
                    break

    # Vibe matching
    vibe_cat_map = {
        "Beach Vibes": "beach", "Adventure": "adventure", "Heritage & History": "historical",
        "Nature & Wildlife": "nature", "Cultural & Spiritual": "cultural",
        "Mountain Views": "adventure", "Luxury": "nature",
    }
    for vibe in (vibes or []):
        mapped_cat = vibe_cat_map.get(vibe)
        if mapped_cat and cat == mapped_cat:
            score += 20

    return score


# Build a reverse lookup: dest name → TBO id (from DESTINATION_MAP)
_NAME_TO_TBO: dict[str, str] = {}
for _tbo_id, _info in DESTINATION_MAP.items():
    _NAME_TO_TBO[_info["name"].lower()] = _tbo_id


def _local_search_ranked_results(query: str, vibes: list, budget: int, travel_month: str, parsed: dict | None = None) -> list:
    """
    Returns exactly 3 INDEPENDENT single-destination results, uniquely ranked.
    Card 1 = Best match, Card 2 = 2nd best DIFFERENT CATEGORY, Card 3 = 3rd best.
    Guarantees diversity: no two cards show the same destination.
    """
    q = query.lower().strip()

    # If Gemini parsed specific destinations, boost them heavily
    boosted_names: set = set()
    if parsed:
        for dest_name in (parsed.get("destinations") or []):
            boosted_names.add(dest_name.lower())
        region_kw = (parsed.get("region") or "").lower()
        if region_kw:
            for d in _DEST_REGISTRY:
                if (region_kw in d["name"].lower()
                        or region_kw in d["description"].lower()
                        or region_kw in d["folder"].lower()):
                    boosted_names.add(d["name"].lower())

    def base_score(d):
        s = _score_destination_for_query(d, q, vibes)
        if d["name"].lower() in boosted_names:
            s += 80
        return s

    # Score and sort all destinations
    all_scored = [(d, base_score(d)) for d in _DEST_REGISTRY]
    all_scored.sort(key=lambda x: x[1], reverse=True)

    # Pick top 3 UNIQUE destinations with category diversity
    selected: list[tuple] = []   # (dest_info, score)
    seen_names: set = set()
    seen_categories: list = []   # track category order for diversity bonus

    for d, score in all_scored:
        name = d["name"]
        if name in seen_names:
            continue

        # Apply a small diversity penalty if same category already chosen
        effective_score = score
        if d.get("category") in seen_categories:
            effective_score -= 10  # slight penalty; doesn't block, just lowers priority

        seen_names.add(name)
        seen_categories.append(d.get("category", ""))
        selected.append((d, effective_score))

        if len(selected) == 3:
            break

    # Pad to 3 if still short (e.g. registry has < 3 entries)
    remaining = [(d, s) for d, s in all_scored if d["name"] not in seen_names]
    for d, s in remaining:
        selected.append((d, s))
        if len(selected) == 3:
            break

    from load_chromadb import DESTINATION_PRICES
    card_labels = [
        ("#1 Best Match",   "best-match"),
        ("#2 Great Option", "runner-up"),
        ("#3 Also Consider", "third-match"),
    ]

    itineraries = []
    for rank_idx, (dest_info, _score) in enumerate(selected[:3]):
        tbo_id = _NAME_TO_TBO.get(dest_info["name"].lower())
        if not tbo_id:
            for k, v in _NAME_TO_TBO.items():
                if dest_info["folder"] in k.replace(" ", "_").lower() or k in dest_info["folder"]:
                    tbo_id = v
                    break
        if not tbo_id:
            tbo_id = f"LOCAL_{dest_info['folder'].upper()}"

        img_path = f"/destinations/{dest_info['folder']}/1.jpg"
        label, card_type = card_labels[rank_idx]
        
        est_price = DESTINATION_PRICES.get(dest_info["folder"], 15000)

        stop_data = {
            "destination": dest_info["name"],
            "tbo_id": tbo_id,
            "photo": img_path,
            "price_per_person": est_price,
            "hotels": [],
            "flights": [],
            "tagline": dest_info.get("description", "")[:150],
            "best_season": travel_month or "Year round",
            "itinerary": [],
            "similarity_rank": rank_idx + 1,
            "category": dest_info.get("category", ""),
            "rating": dest_info.get("rating", 4.0),
            "folder": dest_info.get("folder", ""),
        }

        itineraries.append({
            "type": card_type,
            "label": label,
            "stops": [stop_data],
            "total_price": est_price,   # Will be updated when TBO data is fetched
            "stop_count": 1,
            "region": dest_info.get("folder", "India").replace("_", " ").title(),
            "similarity_rank": rank_idx + 1,
        })

    return itineraries


# Keep backward-compat alias
_local_search_itineraries = _local_search_ranked_results



@app.get("/tbo_details")
async def get_tbo_details(tbo_id: str, budget: int = 100000, travel_date_str: str = None):
    """Fetch live TBO hotel and flight options for a specific destination."""
    from fake_tbo import get_tbo_data
    try:
        data = await get_tbo_data(tbo_id, budget, travel_date_str)
        if data:
            return data
    except Exception as e:
        logger.error(f"Failed to fetch TBO details for {tbo_id}: {e}")
    # Return empty fallback
    return {"hotels": [], "flights": [], "flight_available_from_delhi": False, "flight_min_fare": None}


@app.post("/search")
async def text_search(request: SearchRequest):
    """
    Text-based itinerary search returning 3 INDEPENDENT ranked destination results.
    Card 1 = Best match, Card 2 = 2nd best, Card 3 = 3rd best.
    Uses Gemini NLP for query understanding and local scoring for speed.
    """
    import asyncio

    logger.info(f"POST /search | query='{request.query}' | budget={request.budget}")

    validate_search_request(
        query=request.query,
        budget=request.budget,
        duration_days=request.duration_days,
    )

    effective_budget = request.budget or 100000
    effective_month  = request.travel_month or "December"
    effective_vibes  = request.vibes or []
    duration_days    = request.duration_days or 5
    origin_city      = request.origin_city or "Mumbai"

    # ── Use Gemini NLP parser to better understand query intent ─────────────
    parsed_query: dict | None = None
    try:
        async def _parse_nlp():
            return gemini_utils.parse_search_query(request.query)
        parsed_query = await asyncio.wait_for(_parse_nlp(), timeout=6.0)
        # Override effective params with parsed values if available
        if parsed_query.get("budget") and not request.budget:
            effective_budget = parsed_query["budget"]
        if parsed_query.get("travel_month"):
            effective_month = parsed_query["travel_month"]
        if parsed_query.get("vibes"):
            effective_vibes = list(set(effective_vibes + parsed_query["vibes"]))
        if parsed_query.get("duration_days") and not request.duration_days:
            duration_days = parsed_query["duration_days"]
        if parsed_query.get("origin_city"):
            origin_city = parsed_query["origin_city"]
        logger.info(f"NLP parsed: {parsed_query}")
    except Exception as e:
        logger.info(f"NLP parse skipped (timeout or error): {e}")

    # ── Return 3 independent ranked destination results ──────────────────────
    itineraries = _local_search_ranked_results(
        query=request.query,
        vibes=effective_vibes,
        budget=effective_budget,
        travel_month=effective_month,
        parsed=parsed_query,
    )

    itineraries = await _enrich_itineraries_with_tbo(itineraries, effective_budget, effective_month)

    if not itineraries:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "No matching destinations found for your query.",
                "hint": "Try searching a city name, vibe, or activity (e.g. 'Goa beaches', 'mountain trek').",
            },
        )

    best_itinerary = itineraries[0]
    first_stop = best_itinerary["stops"][0]

    # ── Gemini route justification for the top result ────────────────────────
    route_justification = ""
    try:
        async def _gemini_justification():
            return gemini_utils.generate_route_justification(
                [first_stop],
                best_itinerary["region"]
            )
        route_justification = await asyncio.wait_for(_gemini_justification(), timeout=5.0)
    except Exception:
        route_justification = (
            f"{first_stop['destination']} is a top-ranked match for your search "
            f"'{request.query}'. Explore below for flights and hotel options."
        )

    # ── Create a session for the AI chat ─────────────────────────────────────
    try:
        session_id = session_store.create_session(
            original_embedding=[0.0] * 512,
            budget=effective_budget,
            budget_tier=get_budget_tier(effective_budget),
            travel_dates=effective_month,
            current_match=first_stop["destination"],
            current_tbo_id=first_stop["tbo_id"],
            current_price=first_stop["price_per_person"],
            current_hotels=[],
            current_photo=first_stop["photo"],
            match_reasons=["top search result", "highly relevant", "matches your query"],
            conversation_opener=(
                f"Found {len(itineraries)} great destinations for '{request.query}'! "
                f"Top pick: {first_stop['destination']}. Ask me anything about these places."
            ),
            vibe_tags=effective_vibes or ["travel"],
            itinerary_stops=[s["stops"][0] for s in itineraries],
            itinerary_type=best_itinerary["type"],
            itinerary_label=best_itinerary["label"],
            itinerary_region=best_itinerary["region"],
            itinerary_total_price=best_itinerary["total_price"],
            duration_days=duration_days,
        )
    except Exception as e:
        logger.warning(f"Session creation failed (non-critical): {e}")
        session_id = "local-session-" + first_stop["destination"].lower().replace(" ", "-")

    return {
        "session_id": session_id,
        "itineraries": itineraries,
        "vibe_tags": effective_vibes,
        "parsed_query": parsed_query or {"query": request.query},
        "match_reasons": ["highly relevant", "top match", "matches your search"],
        "itinerary_narrative": (
            f"Your top 3 destination matches for '{request.query}' — "
            f"ranked by relevance from best to third-best match."
        ),
        "conversation_opener": (
            f"Found {len(itineraries)} great destinations for you! "
            f"Top pick: {first_stop['destination']}. Ask me anything!"
        ),
        "route_justification": route_justification,
        "region": best_itinerary["region"],
    }




# ─── Endpoint 3: GET /destinations (new — catalog for autocomplete) ───────────

@app.get("/destinations")
async def get_destinations():
    """Return the full destination catalog for frontend autocomplete and browse."""
    catalog = []
    for tbo_id, info in DESTINATION_MAP.items():
        region = REGION_MAP.get(tbo_id, "India")
        catalog.append({
            "tbo_id": tbo_id,
            "name": info["name"],
            "region": region,
            "airport": info.get("airport", ""),
        })
    return {"destinations": catalog, "count": len(catalog)}


# ─── Endpoint 3b: GET /nearby — folder-based, coordinate-driven ───────────────
# Every destination listed here has a physical folder under backend/destinations/.
# The folder slug is used to serve images: /destinations/<slug>/1.jpg
# We use haversine distance to find neighbors within the requested radius.

import math, os

_DESTINATIONS_DIR = os.path.join(os.path.dirname(__file__), "destinations")

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in km between two lat/lon points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# Master registry: all 100 destinations with coordinates, display name, category, description.
# folder_slug must match the actual directory name under backend/destinations/.
_DEST_REGISTRY: list[dict] = [
    {"name": "Agra",           "folder": "agra",          "lat": 27.18, "lon": 78.02, "category": "historical", "description": "Home of the Taj Mahal — UNESCO World Heritage Mughal architecture at its finest.", "highlights": ["Taj Mahal", "Agra Fort", "Fatehpur Sikri nearby"], "visit_duration": "1-2 days", "rating": 4.7},
    {"name": "Ajmer",          "folder": "ajmer",         "lat": 26.45, "lon": 74.64, "category": "cultural",   "description": "City of the revered Dargah Sharif shrine and gateway to Pushkar's holy lake.", "highlights": ["Dargah Sharif", "Pushkar nearby", "Ana Sagar Lake"], "visit_duration": "1 day", "rating": 4.2},
    {"name": "Alleppey",       "folder": "alleppey",      "lat": 9.49,  "lon": 76.33, "category": "nature",     "description": "Venice of the East — gliding on Kerala's legendary backwaters on a houseboat.", "highlights": ["houseboat stays", "backwater cruises", "Vembanad Lake"], "visit_duration": "1-2 days", "rating": 4.6},
    {"name": "Almora",         "folder": "almora",        "lat": 29.60, "lon": 79.65, "category": "nature",     "description": "Serene Kumaon hilltop town with Himalayan panoramas and ancient temples.", "highlights": ["Kasar Devi temple", "Binsar wildlife sanctuary", "Himalayan views"], "visit_duration": "1-2 days", "rating": 4.3},
    {"name": "Amritsar",       "folder": "amritsar",      "lat": 31.63, "lon": 74.87, "category": "cultural",   "description": "Spiritual heart of Sikhism — the Golden Temple draws millions with its ethereal beauty.", "highlights": ["Golden Temple", "Jallianwala Bagh", "Wagah Border ceremony"], "visit_duration": "1-2 days", "rating": 4.7},
    {"name": "Andaman Islands","folder": "andaman",       "lat": 11.74, "lon": 92.66, "category": "beach",      "description": "Crystal-clear Andaman Sea, coral reefs and pristine white-sand beaches.", "highlights": ["Radhanagar Beach", "scuba diving", "Cellular Jail"], "visit_duration": "4-5 days", "rating": 4.8},
    {"name": "Araku",          "folder": "araku",         "lat": 18.33, "lon": 82.88, "category": "nature",     "description": "Mystical valley of coffee aromas and tribal culture in the Eastern Ghats.", "highlights": ["tribal museum", "coffee estates", "Borra Caves"], "visit_duration": "1-2 days", "rating": 4.4},
    {"name": "Auli",           "folder": "auli",          "lat": 30.52, "lon": 79.56, "category": "adventure",  "description": "India's premier ski resort with Asia's longest cable car and Nanda Devi views.", "highlights": ["skiing", "cable car ride", "Nanda Devi panorama"], "visit_duration": "2-3 days", "rating": 4.5},
    {"name": "Badami",         "folder": "badami",        "lat": 15.92, "lon": 75.68, "category": "historical", "description": "6th-century Chalukya rock-cut cave temples carved into red sandstone cliffs.", "highlights": ["4 cave temples", "Chalukyan architecture", "Agastya Lake"], "visit_duration": "1 day", "rating": 4.5},
    {"name": "Bandhavgarh",    "folder": "bandhavgarh",   "lat": 23.72, "lon": 81.01, "category": "nature",     "description": "India's highest density of Bengal tigers per sq km in Madhya Pradesh.", "highlights": ["tiger safari", "White Tiger heritage", "ancient fort"], "visit_duration": "2-3 days", "rating": 4.7},
    {"name": "Belur",          "folder": "belur",         "lat": 13.16, "lon": 75.86, "category": "historical", "description": "Hoysala temple of Chennakeshava — intricate carvings spanning 103 years of artistry.", "highlights": ["Chennakeshava temple", "Hoysala sculpture", "nearby Halebidu"], "visit_duration": "Half day", "rating": 4.6},
    {"name": "Bhimbetka",      "folder": "bhimbetka",     "lat": 22.93, "lon": 77.61, "category": "historical", "description": "UNESCO rock shelters with prehistoric paintings over 30,000 years old.", "highlights": ["30,000-yr-old rock art", "UNESCO site", "forest setting"], "visit_duration": "Half day", "rating": 4.4},
    {"name": "Bhubaneswar",    "folder": "bhubaneswar",   "lat": 20.30, "lon": 85.84, "category": "historical", "description": "Temple city of India with over 700 ancient temples including the Lingaraja.", "highlights": ["Lingaraja Temple", "Udayagiri caves", "gateway to Konark"], "visit_duration": "1-2 days", "rating": 4.3},
    {"name": "Bikaner",        "folder": "bikaner",       "lat": 28.02, "lon": 73.31, "category": "historical", "description": "Walled camel city of the Thar desert, home to majestic Junagarh Fort.", "highlights": ["Junagarh Fort", "camel safari", "Karni Mata Rat Temple"], "visit_duration": "1 day", "rating": 4.2},
    {"name": "Bir Billing",    "folder": "bir_billing",   "lat": 31.96, "lon": 76.72, "category": "adventure",  "description": "World's second-best paragliding site in the Himachal valley with breathtaking thermals.", "highlights": ["paragliding", "monastery tours", "camping"], "visit_duration": "1-2 days", "rating": 4.6},
    {"name": "Bodh Gaya",      "folder": "bodh_gaya",     "lat": 24.70, "lon": 84.99, "category": "cultural",   "description": "Where the Buddha attained enlightenment — holiest site in Buddhism worldwide.", "highlights": ["Mahabodhi Temple", "Bodhi Tree", "international monasteries"], "visit_duration": "1 day", "rating": 4.7},
    {"name": "Chandigarh",     "folder": "chandigarh",    "lat": 30.73, "lon": 76.78, "category": "cultural",   "description": "Le Corbusier's planned city — the Rock Garden and Sukhna Lake are iconic.", "highlights": ["Rock Garden", "Sukhna Lake", "Rose Garden"], "visit_duration": "1 day", "rating": 4.1},
    {"name": "Chikmagalur",    "folder": "chikmagalur",   "lat": 13.32, "lon": 75.77, "category": "nature",     "description": "Birthplace of Indian coffee — misty hills, waterfalls and lush Western Ghats forests.", "highlights": ["coffee plantation tours", "Mullayanagiri peak", "Baba Budangiri"], "visit_duration": "1-2 days", "rating": 4.5},
    {"name": "Chilika",        "folder": "chilika",       "lat": 19.72, "lon": 85.32, "category": "nature",     "description": "Asia's largest coastal lagoon — winter home to 160+ migratory bird species.", "highlights": ["Irrawaddy dolphins", "migratory birds", "boat safari"], "visit_duration": "1 day", "rating": 4.4},
    {"name": "Chitrakoot",     "folder": "chitrakoot",    "lat": 25.18, "lon": 80.88, "category": "cultural",   "description": "Sacred Ramayan site where Lord Ram, Sita and Lakshman spent 11 years in exile.", "highlights": ["Kamadgiri parikrama", "Ramghat aarti", "Gupt Godavari caves"], "visit_duration": "1 day", "rating": 4.3},
    {"name": "Chittorgarh",    "folder": "chittorgarh",   "lat": 24.89, "lon": 74.64, "category": "historical", "description": "India's largest fort complex — 700 acres of Rajput valor and Padmini's sacrifice.", "highlights": ["Vijay Stambha", "Rani Padmini Palace", "Kirti Stambha"], "visit_duration": "Full day", "rating": 4.6},
    {"name": "Coorg",         "folder": "coorg",          "lat": 12.33, "lon": 75.81, "category": "nature",     "description": "Scotland of India — coffeelands, rolling hills and Abbey Falls in misty Kodagu.", "highlights": ["coffee plantations", "Abbey Falls", "Raja's Seat"], "visit_duration": "2-3 days", "rating": 4.7},
    {"name": "Dalhousie",      "folder": "dalhousie",     "lat": 32.54, "lon": 75.97, "category": "nature",     "description": "Colonial hill station with pine forests, Dhauladhar views and Victorian churches.", "highlights": ["Khajjiar meadow", "Dainkund Peak", "Subhash Baoli"], "visit_duration": "1-2 days", "rating": 4.3},
    {"name": "Darjeeling",     "folder": "darjeeling",    "lat": 27.04, "lon": 88.26, "category": "nature",     "description": "Queen of Hills — toy train, tea estates and Kanchenjunga sunrise from Tiger Hill.", "highlights": ["Tiger Hill sunrise", "Toy Train UNESCO", "Himalayan Mountaineering Institute"], "visit_duration": "2-3 days", "rating": 4.6},
    {"name": "Dharamshala",    "folder": "dharamshala",   "lat": 32.22, "lon": 76.32, "category": "cultural",   "description": "Little Lhasa — Tibetan culture, Dalai Lama's residence, and Dhauladhar trekking base.", "highlights": ["Tsuglagkhang complex", "Tibetan cuisine", "Triund trek"], "visit_duration": "2-3 days", "rating": 4.5},
    {"name": "Dwarka",         "folder": "dwarka",        "lat": 22.24, "lon": 68.97, "category": "cultural",   "description": "One of the four sacred Hindu dhams — Lord Krishna's legendary submerged city.", "highlights": ["Dwarkadhish temple", "Beyt Dwarka island", "sacred pilgrimage"], "visit_duration": "1-2 days", "rating": 4.4},
    {"name": "Gir",            "folder": "gir",           "lat": 21.13, "lon": 70.75, "category": "nature",     "description": "Last refuge of the Asiatic lion — the only wild lion population outside Africa.", "highlights": ["Asiatic lion safari", "leopard sightings", "Gir interpretation zone"], "visit_duration": "1-2 days", "rating": 4.6},
    {"name": "Goa",            "folder": "goa",           "lat": 15.49, "lon": 73.82, "category": "beach",      "description": "Sun, sand and seafood — India's party capital with Portuguese colonial charm.", "highlights": ["beach shacks", "Old Goa churches", "Dudhsagar Falls nearby"], "visit_duration": "3-5 days", "rating": 4.6},
    {"name": "Gokak",          "folder": "gokak",         "lat": 16.17, "lon": 74.82, "category": "nature",     "description": "Horseshoe waterfall where the Ghataprabha river plunges 52m — Karnataka's Niagara.", "highlights": ["Gokak Falls", "ropeway", "local handicrafts"], "visit_duration": "Half day", "rating": 4.1},
    {"name": "Gokarna",        "folder": "gokarna",       "lat": 14.55, "lon": 74.31, "category": "beach",      "description": "Offbeat beach paradise — sacred town with pristine beaches and laid-back hippie vibes.", "highlights": ["Om Beach", "Half Moon Beach", "Mahabaleshwar temple"], "visit_duration": "2-3 days", "rating": 4.5},
    {"name": "Gulmarg",        "folder": "gulmarg",       "lat": 34.05, "lon": 74.38, "category": "adventure",  "description": "Meadow of flowers — Kashmir's premier ski resort with Asia's highest gondola at 4,000m.", "highlights": ["Gondola cable car", "skiing", "Khilanmarg meadow"], "visit_duration": "1-2 days", "rating": 4.7},
    {"name": "Gwalior",        "folder": "gwalior",       "lat": 26.22, "lon": 78.18, "category": "historical", "description": "Rock fortress rising 100m above the city, called the 'Gibraltar of India'.", "highlights": ["Gwalior Fort", "Man Mandir Palace", "Tansen's Tomb"], "visit_duration": "1 day", "rating": 4.3},
    {"name": "Hampi",          "folder": "hampi",         "lat": 15.34, "lon": 76.46, "category": "historical", "description": "UNESCO site — surreal boulder landscape with ruins of the Vijayanagara Empire.", "highlights": ["Virupaksha Temple", "Stone Chariot", "Vittala Temple"], "visit_duration": "2-3 days", "rating": 4.7},
    {"name": "Haridwar",       "folder": "haridwar",      "lat": 29.94, "lon": 78.16, "category": "cultural",   "description": "Gateway to God — Ganga Aarti at Har Ki Pauri is one of India's most moving spectacles.", "highlights": ["Ganga Aarti", "Har Ki Pauri ghat", "holy dip"], "visit_duration": "1 day", "rating": 4.5},
    {"name": "Jabalpur",       "folder": "jabalpur",      "lat": 23.18, "lon": 79.94, "category": "nature",     "description": "Marble Rocks at Bhedaghat — ancient geography sculpting a surreal canyon on Narmada.", "highlights": ["Bhedaghat Marble Rocks", "Dhuandhar Falls", "night boat", "Chausath Yogini Temple"], "visit_duration": "1 day", "rating": 4.3},
    {"name": "Jaipur",         "folder": "jaipur",        "lat": 26.91, "lon": 75.79, "category": "historical", "description": "Pink City — palaces, bazaars and the Amber Fort in Rajasthan's royal capital.", "highlights": ["Amber Fort", "Hawa Mahal", "City Palace", "bazaars"], "visit_duration": "2-3 days", "rating": 4.6},
    {"name": "Jaisalmer",      "folder": "jaisalmer",     "lat": 26.91, "lon": 70.92, "category": "historical", "description": "Golden Fort city rising from the Thar Desert — living fort with locals still inside.", "highlights": ["Jaisalmer Fort", "Sam Sand Dunes", "camel safari"], "visit_duration": "2-3 days", "rating": 4.6},
    {"name": "Jim Corbett",    "folder": "jim_corbett",   "lat": 29.53, "lon": 79.25, "category": "nature",     "description": "India's oldest national park — home to Bengal tigers along the Ramganga River.", "highlights": ["tiger safaris", "elephant rides", "Ramganga river"] , "visit_duration": "2-3 days", "rating": 4.6},
    {"name": "Jodhpur",        "folder": "jodhpur",       "lat": 26.29, "lon": 73.02, "category": "historical", "description": "Blue City — Mehrangarh Fort towers over cobalt-blue lanes and bustling spice markets.", "highlights": ["Mehrangarh Fort", "blue lanes of Brahmpuri", "Umaid Bhawan Palace"], "visit_duration": "1-2 days", "rating": 4.6},
    {"name": "Kanha",          "folder": "kanha",         "lat": 22.33, "lon": 80.61, "category": "nature",     "description": "Inspiration for Kipling's Jungle Book — barasingha deer and tigers in pristine forest.", "highlights": ["tiger safari", "barasingha deer", "Jungle Book inspiration"], "visit_duration": "2-3 days", "rating": 4.7},
    {"name": "Kanyakumari",    "folder": "kanyakumari",   "lat": 8.09,  "lon": 77.55, "category": "cultural",   "description": "India's southernmost tip — watch the Indian Ocean, Arabian Sea and Bay of Bengal meet.", "highlights": ["three seas confluence", "Vivekananda Rock", "sunrise & sunset same spot"], "visit_duration": "1 day", "rating": 4.4},
    {"name": "Kargil",         "folder": "kargil",        "lat": 34.56, "lon": 76.13, "category": "adventure",  "description": "High-altitude Ladakhi town famed for the 1999 war, monasteries and apricot orchards.", "highlights": ["war memorial", "Suru Valley", "monasteries", "apricot orchards"], "visit_duration": "1-2 days", "rating": 4.1},
    {"name": "Kasol",          "folder": "kasol",         "lat": 31.99, "lon": 77.31, "category": "adventure",  "description": "Parvati Valley's trekking hub — waterfalls, Kheerganga hot springs and Kalgha forests.", "highlights": ["Kheerganga trek", "hot springs", "Malana village"], "visit_duration": "2-3 days", "rating": 4.4},
    {"name": "Kausani",        "folder": "kausani",       "lat": 29.84, "lon": 79.60, "category": "nature",     "description": "The Switzerland of India — 300km Himalayan panorama visible from Gandhi's ashram.", "highlights": ["Nanda Devi views", "Anasakti Ashram", "tea gardens"], "visit_duration": "1-2 days", "rating": 4.4},
    {"name": "Kaziranga",      "folder": "kaziranga",     "lat": 26.58, "lon": 93.17, "category": "nature",     "description": "UNESCO park with 2/3 of the world's one-horned rhinos and significant tiger density.", "highlights": ["one-horned rhino", "elephant safari", "bird watching"], "visit_duration": "2 days", "rating": 4.8},
    {"name": "Kerala Hills",   "folder": "kerala_hills",  "lat": 10.10, "lon": 77.06, "category": "nature",     "description": "Misty tea-clad hills, cardamom estates and waterfalls of the Western Ghats.", "highlights": ["tea estates", "Eravikulam National Park", "Mattupetty Dam"], "visit_duration": "2-3 days", "rating": 4.5},
    {"name": "Khajjiar",       "folder": "khajjiar",      "lat": 32.55, "lon": 76.03, "category": "nature",     "description": "Mini-Switzerland — emerald meadow fringed by deodar forests and a small lake.", "highlights": ["meadow & lake", "deodar forest", "Khajjiar temple"], "visit_duration": "Half day", "rating": 4.3},
    {"name": "Khajuraho",      "folder": "khajuraho",     "lat": 24.85, "lon": 79.93, "category": "historical", "description": "UNESCO temples famous for exquisite erotic sculptures — Chandela dynasty art at peak.", "highlights": ["UNESCO temples", "erotic sculptures", "light & sound show"], "visit_duration": "1-2 days", "rating": 4.5},
    {"name": "Kinnaur",        "folder": "kinnaur",       "lat": 31.58, "lon": 78.26, "category": "nature",     "description": "Apple orchards, Hinduism-Buddhism confluence, and ancient Kalpa cliffside villages.", "highlights": ["Kalpa apple orchards", "Nako monastery", "Spiti confluence"], "visit_duration": "2-3 days", "rating": 4.5},
    {"name": "Kodaikanal",     "folder": "kodaikanal",    "lat": 10.24, "lon": 77.48, "category": "nature",     "description": "Princess of hill stations — star-shaped lake, misty pine forests and Bryant Park.", "highlights": ["Kodai Lake", "Bryan Park", "Coaker's Walk sunset"], "visit_duration": "2 days", "rating": 4.4},
    {"name": "Konark",         "folder": "konark",        "lat": 19.89, "lon": 86.09, "category": "historical", "description": "Sun Temple of Konark — colossal stone chariot of the Sun God, a UNESCO masterpiece.", "highlights": ["Sun Temple chariot", "erotic sculptures", "Konark Dance Festival"], "visit_duration": "Half day", "rating": 4.6},
    {"name": "Kovalam",        "folder": "kovalam",       "lat": 8.40,  "lon": 76.98, "category": "beach",      "description": "Kerala's Lighthouse Beach — cliffs, calm coves and Ayurvedic resorts by the sea.", "highlights": ["Lighthouse Beach", "Ayurvedic massages", "cliff viewpoints"], "visit_duration": "2-3 days", "rating": 4.4},
    {"name": "Kumbhalgarh",    "folder": "kumbhalgarh",   "lat": 25.15, "lon": 73.58, "category": "historical", "description": "World's second-longest wall (38km) — UNESCO fortress, birthplace of Maharana Pratap.", "highlights": ["38km wall", "360° views", "light & sound show", "wildlife sanctuary"], "visit_duration": "Half day", "rating": 4.7},
    {"name": "Kutch",          "folder": "kutch",         "lat": 23.73, "lon": 70.21, "category": "cultural",   "description": "Great Rann of Kutch — world's largest salt desert glows white under the full moon.", "highlights": ["Rann Utsav festival", "white salt desert", "tribal handicrafts"], "visit_duration": "2-3 days", "rating": 4.7},
    {"name": "Lahaul",         "folder": "lahaul",        "lat": 32.57, "lon": 77.17, "category": "adventure",  "description": "Cold desert valley beyond Rohtang — Buddhist monasteries, glaciers and stark landscapes.", "highlights": ["Keylong monastery", "Chandratal Lake", "Baralacha La pass"], "visit_duration": "2-3 days", "rating": 4.5},
    {"name": "Lansdowne",      "folder": "lansdowne",     "lat": 29.84, "lon": 78.68, "category": "nature",     "description": "Peaceful Garhwal cantonment town with oak forests, Bhulla Lake and Tip-in-Top viewpoint.", "highlights": ["Tip-in-Top viewpoint", "Bhulla Lake", "oak forests", "peaceful retreat"], "visit_duration": "1-2 days", "rating": 4.2},
    {"name": "Leh",            "folder": "leh",           "lat": 34.17, "lon": 77.58, "category": "adventure",  "description": "Ancient Silk Route city at 3,500m — monasteries, moonscapes and the world's highest passes.", "highlights": ["Pangong Tso", "Khardung La", "Nubra Valley", "Buddhist monasteries"], "visit_duration": "5-7 days", "rating": 4.8},
    {"name": "Lonavala",       "folder": "lonavala",      "lat": 18.75, "lon": 73.41, "category": "nature",     "description": "Monsoon gateway from Mumbai/Pune — waterfalls, forts and misty Western Ghats valleys.", "highlights": ["Bhushi Dam", "Tiger Point", "Karla Caves", "Rajmachi trek"], "visit_duration": "1-2 days", "rating": 4.2},
    {"name": "Madurai",        "folder": "madurai",       "lat": 9.92,  "lon": 78.12, "category": "cultural",   "description": "City never sleeps — Meenakshi Amman temple's 14 gopurams painted with 33,000 sculptures.", "highlights": ["Meenakshi Amman Temple", "Thirumalai Nayakkar Palace", "floating lotus market"], "visit_duration": "1-2 days", "rating": 4.6},
    {"name": "Mahabaleshwar",  "folder": "mahabaleshwar", "lat": 17.92, "lon": 73.66, "category": "nature",     "description": "Maharashtra's queen of hill stations — strawberry farms, 5 river sources and mist-covered valleys.", "highlights": ["Venna Lake", "strawberry picking", "Arthur's Seat viewpoint"], "visit_duration": "2 days", "rating": 4.3},
    {"name": "Majuli",         "folder": "majuli",        "lat": 26.95, "lon": 94.16, "category": "cultural",   "description": "World's largest river island — Assamese Vaishnava satras, masks and river festivals.", "highlights": ["Satras (monasteries)", "mask-making tradition", "Brahmaputra sunsets"], "visit_duration": "1-2 days", "rating": 4.4},
    {"name": "Manali",         "folder": "manali",        "lat": 32.24, "lon": 77.19, "category": "adventure",  "description": "Himalayan playground — Rohtang Pass, Solang Valley and ancient Hadimba temple.", "highlights": ["Rohtang Pass", "Solang Valley", "Hadimba Temple", "paragliding"], "visit_duration": "3-5 days", "rating": 4.6},
    {"name": "Mandu",          "folder": "mandu",         "lat": 22.34, "lon": 75.40, "category": "historical", "description": "Ruined medieval city of romance — Baz Bahadur's tragic love story etched in fortress walls.", "highlights": ["Jahaz Mahal", "Hindola Mahal", "Rani Roopmati Pavilion"], "visit_duration": "1 day", "rating": 4.3},
    {"name": "Mathura",        "folder": "mathura",       "lat": 27.49, "lon": 77.67, "category": "cultural",   "description": "Birthplace of Lord Krishna — 3,000-year-old pilgrimage city & gateway to Vrindavan.", "highlights": ["Krishna Janmabhoomi temple", "Vrindavan nearby", "Holi festival"], "visit_duration": "1 day", "rating": 4.4},
    {"name": "Mount Abu",      "folder": "mount_abu",     "lat": 24.59, "lon": 72.71, "category": "nature",     "description": "Rajasthan's only hill station — Dilwara Jain temples are among India's finest.", "highlights": ["Dilwara Jain temples", "Nakki Lake", "Sunset Point"], "visit_duration": "1-2 days", "rating": 4.3},
    {"name": "Munnar",         "folder": "munnar",        "lat": 10.09, "lon": 77.06, "category": "nature",     "description": "Emerald tea terraces rolling across the Western Ghats at 1,600m altitude.", "highlights": ["tea estate tours", "Eravikulam NP", "Mattupetty Dam", "Top Station"], "visit_duration": "2-3 days", "rating": 4.5},
    {"name": "Mussoorie",      "folder": "mussoorie",     "lat": 30.45, "lon": 78.07, "category": "nature",     "description": "Queen of the Hills — Mall Road, Kempty Falls and Gangotri glacier views from Lal Tibba.", "highlights": ["Kempty Falls", "Lal Tibba viewpoint", "Cable car", "Mall Road"], "visit_duration": "1-2 days", "rating": 4.3},
    {"name": "Mysore",         "folder": "mysore",        "lat": 12.30, "lon": 76.65, "category": "historical", "description": "City of palaces — Amba Vilas's illuminated dome during Dasara is unforgettable.", "highlights": ["Mysore Palace", "Dasara festival", "Chamundi Hill"], "visit_duration": "1-2 days", "rating": 4.5},
    {"name": "Nainital",       "folder": "nainital",      "lat": 29.38, "lon": 79.46, "category": "nature",     "description": "Pear-shaped lake in an emerald Kumaon bowl — boat rides and Naina Devi temple.", "highlights": ["Naini Lake boat rides", "Naina Devi temple", "Snow View point"], "visit_duration": "1-2 days", "rating": 4.3},
    {"name": "Nalanda",        "folder": "nalanda",       "lat": 25.14, "lon": 85.44, "category": "historical", "description": "Ancient world's greatest university — Xuanzang studied here 1,500 years ago.", "highlights": ["ancient university ruins", "archaeological museum", "pilgrimage site"], "visit_duration": "Half day", "rating": 4.5},
    {"name": "Nubra Valley",   "folder": "nubra_valley",  "lat": 34.72, "lon": 77.55, "category": "adventure",  "description": "Sand dunes and Bactrian camels at 3,048m — accessed via world's highest motorable pass.", "highlights": ["double-humped camels", "sand dunes", "Diskit Monastery", "white water river"], "visit_duration": "1-2 days", "rating": 4.7},
    {"name": "Ooty",           "folder": "ooty",          "lat": 11.41, "lon": 76.70, "category": "nature",     "description": "Queen of Hill Stations — Nilgiri toy train, botanical gardens and tea estates.", "highlights": ["Nilgiri Toy Train", "Ooty Lake", "Doddabetta peak", "Rose Garden"], "visit_duration": "2 days", "rating": 4.3},
    {"name": "Orchha",         "folder": "orchha",        "lat": 25.35, "lon": 78.64, "category": "historical", "description": "Forgotten Bundela kingdom — crumbling cenotaphs, Ram Raja temple and Betwa riverside forts.", "highlights": ["Orchha Fort", "Ram Raja temple", "Betwa river cenotaphs"], "visit_duration": "1 day", "rating": 4.5},
    {"name": "Pachmarhi",      "folder": "pachmarhi",     "lat": 22.47, "lon": 78.43, "category": "nature",     "description": "Satpura's only hill station — Bee Falls, prehistoric cave paintings and dense reserve forests.", "highlights": ["Bee Falls", "Jata Shankar cave", "Satpura National Park"], "visit_duration": "2 days", "rating": 4.4},
    {"name": "Pahalgam",       "folder": "pahalgam",      "lat": 34.01, "lon": 75.32, "category": "nature",     "description": "Valley of Shepherds — Lidder River, pine forests and Amarnath Yatra base camp.", "highlights": ["Betab Valley", "Amarnath Yatra base", "horse riding", "Baisaran meadow"], "visit_duration": "2-3 days", "rating": 4.6},
    {"name": "Pangong Tso",    "folder": "pangong_tso",   "lat": 33.75, "lon": 78.70, "category": "nature",     "description": "Iconic high-altitude salt lake turning from cobalt to turquoise to magenta as light shifts.", "highlights": ["color-shifting lake", "flamingos", "camping", "3 Idiots filming location"], "visit_duration": "Overnight", "rating": 4.9},
    {"name": "Pondicherry",    "folder": "pondicherry",   "lat": 11.93, "lon": 79.83, "category": "cultural",   "description": "French Quarter with bougainvillea lanes, Auroville ashram and tranquil beach promenade.", "highlights": ["French Quarter", "Auroville", "Paradise Beach", "Aurobindo Ashram"], "visit_duration": "1-2 days", "rating": 4.4},
    {"name": "Puri",           "folder": "puri",          "lat": 19.81, "lon": 85.83, "category": "cultural",   "description": "Lord Jagannath's abode — Rath Yatra procession and the golden sands of Puri beach.", "highlights": ["Jagannath Temple", "Rath Yatra festival", "Puri Beach"], "visit_duration": "1-2 days", "rating": 4.4},
    {"name": "Pushkar",        "folder": "pushkar",       "lat": 26.49, "lon": 74.56, "category": "cultural",   "description": "World's only Brahma temple by a sacred lake — rose gardens and Camel Fair in November.", "highlights": ["Brahma Temple", "Pushkar Lake ghats", "Camel Fair"], "visit_duration": "1 day", "rating": 4.4},
    {"name": "Rameshwaram",    "folder": "rameshwaram",   "lat": 9.29,  "lon": 79.31, "category": "cultural",   "description": "Island pilgrimage — Ramanathaswamy temple's 1,200m corridors are longest in the world.", "highlights": ["Ramanathaswamy Temple", "Pamban Bridge", "Dhanushkodi ruins"], "visit_duration": "1-2 days", "rating": 4.5},
    {"name": "Ranikhet",       "folder": "ranikhet",      "lat": 29.64, "lon": 79.43, "category": "nature",     "description": "Army cantonment hill station with the highest golf course in Asia at 1,829m.", "highlights": ["Asia's highest golf course", "Jhula Devi Temple", "Himalayan views"], "visit_duration": "1-2 days", "rating": 4.2},
    {"name": "Ranthambore",    "folder": "ranthambore",   "lat": 26.01, "lon": 76.47, "category": "nature",     "description": "Rajasthan's legendary tiger reserve — tigers photographed in dramatic fort ruins.", "highlights": ["tiger safari", "Ranthambore Fort", "tigers in ruins photography"], "visit_duration": "2 days", "rating": 4.7},
    {"name": "Rishikesh",      "folder": "rishikesh",     "lat": 30.09, "lon": 78.27, "category": "adventure",  "description": "Yoga capital of the world — rafting on Ganga, Laxman Jhula and Beatles Ashram.", "highlights": ["white-water rafting", "Laxman Jhula", "Beatles Ashram", "yoga retreats"], "visit_duration": "2-3 days", "rating": 4.5},
    {"name": "Sanchi",         "folder": "sanchi",        "lat": 23.48, "lon": 77.74, "category": "historical", "description": "UNESCO Buddhist stupas built by Ashoka — unparalleled toranas and original relic preservation.", "highlights": ["Great Stupa", "Ashokan Toranas", "Buddhist pilgrimage"], "visit_duration": "Half day", "rating": 4.5},
    {"name": "Shillong",       "folder": "shillong",      "lat": 25.57, "lon": 91.88, "category": "nature",     "description": "Scotland of the East — waterfalls, living root bridges and Cherrapunji rain forest nearby.", "highlights": ["Elephant Falls", "Wards Lake", "Cherrapunji nearby", "root bridges"], "visit_duration": "2-3 days", "rating": 4.5},
    {"name": "Shimla",         "folder": "shimla",        "lat": 31.10, "lon": 77.17, "category": "nature",     "description": "Former British summer capital — the Kalka-Shimla toy train and Ridge promenade.", "highlights": ["Toy Train UNESCO", "The Ridge", "Jakhu Temple", "Kufri nearby"], "visit_duration": "2-3 days", "rating": 4.4},
    {"name": "Somnath",        "folder": "somnath",       "lat": 20.89, "lon": 70.40, "category": "cultural",   "description": "First of twelve Jyotirlingas — rebuilt seven times, now standing proud overlooking the Arabian Sea.", "highlights": ["Somnath Temple", "Arabian Sea views", "Triveni Sangam"], "visit_duration": "1 day", "rating": 4.5},
    {"name": "Sonamarg",       "folder": "sonamarg",      "lat": 34.30, "lon": 75.29, "category": "nature",     "description": "Meadow of Gold — alpine glaciers, Thajiwas glacier trek and pristine streams.", "highlights": ["Thajiwas Glacier", "pony rides", "Zoji La pass gateway"], "visit_duration": "1-2 days", "rating": 4.6},
    {"name": "Spiti",          "folder": "spiti",         "lat": 32.25, "lon": 78.07, "category": "adventure",  "description": "Cold desert mountain valley — Key Monastery perched on 4,166m with ancient Tabo murals.", "highlights": ["Key Monastery", "Tabo Caves", "Chandratal Lake", "Pin Valley NP"], "visit_duration": "3-5 days", "rating": 4.8},
    {"name": "Srinagar",       "folder": "srinagar",      "lat": 34.08, "lon": 74.79, "category": "nature",     "description": "Paradise on Earth — shikara rides on Dal Lake, Mughal gardens and saffron fields.", "highlights": ["Dal Lake shikara", "Mughal Gardens", "Gulmarg skiing", "saffron fields"], "visit_duration": "3-4 days", "rating": 4.6},
    {"name": "Sunderbans",     "folder": "sunderbans",    "lat": 21.94, "lon": 89.18, "category": "nature",     "description": "World's largest mangrove delta — swimming tigers and Irrawaddy dolphins.", "highlights": ["Royal Bengal tigers (swimming)", "mangrove ecosystem", "UNESCO biosphere"], "visit_duration": "2-3 days", "rating": 4.5},
    {"name": "Tawang",         "folder": "tawang",        "lat": 27.59, "lon": 91.86, "category": "cultural",   "description": "India's largest Buddhist monastery at 3,048m — Arunachal's mystical border gateway.", "highlights": ["Tawang Monastery", "Sela Pass", "Madhuri Lake", "Tibetan culture"], "visit_duration": "2-3 days", "rating": 4.7},
    {"name": "Tirupati",       "folder": "tirupati",      "lat": 13.63, "lon": 79.42, "category": "cultural",   "description": "Richest temple in the world — millions climb Tirumala hills to seek Lord Venkateswara's blessings.", "highlights": ["Tirupati Balaji Temple", "historic laddu prasad", "Tirumala hills"], "visit_duration": "1-2 days", "rating": 4.6},
    {"name": "Tso Moriri",     "folder": "tso_moriri",    "lat": 32.87, "lon": 78.32, "category": "nature",     "description": "Remote high-altitude lake at 4,522m — undisturbed flamingos and black-neck cranes.", "highlights": ["flamingos & black-neck cranes", "isolated nomadic villages", "pristine lake"], "visit_duration": "Overnight", "rating": 4.8},
    {"name": "Udaipur",        "folder": "udaipur",       "lat": 24.57, "lon": 73.68, "category": "historical", "description": "City of Lakes — Lake Pichola, floating City Palace and Udaipur's legendary sunsets.", "highlights": ["Lake Pichola", "City Palace", "Jag Mandir", "Lake Palace"], "visit_duration": "2-3 days", "rating": 4.7},
    {"name": "Ujjain",         "folder": "ujjain",        "lat": 23.18, "lon": 75.78, "category": "cultural",   "description": "One of seven sacred Hindu cities — Mahakaleshwar Jyotirlinga and Kumbh Mela site.", "highlights": ["Mahakaleshwar temple", "Kumbh Mela site", "Kal Bhairav temple"], "visit_duration": "1 day", "rating": 4.3},
    {"name": "Varanasi",       "folder": "varanasi",      "lat": 25.32, "lon": 83.01, "category": "cultural",   "description": "World's oldest living city — Ganga Aarti, silk weavers and the ghats of eternity.", "highlights": ["Ganga Aarti at Dashashwamedh", "boat on Ganges at sunrise", "Sarnath nearby"], "visit_duration": "2-3 days", "rating": 4.6},
    {"name": "Varkala",        "folder": "varkala",       "lat": 8.73,  "lon": 76.72, "category": "beach",      "description": "Kerala's cliff beach — laterite cliffs plunging into the Arabian Sea with Papanasam beach.", "highlights": ["cliff restaurants", "Papanasam Beach", "Janardhanaswamy Temple", "Ayurveda"], "visit_duration": "2-3 days", "rating": 4.5},
    {"name": "Wayanad",        "folder": "wayanad",       "lat": 11.60, "lon": 76.13, "category": "nature",     "description": "Tribal heartland of the Western Ghats — bamboo forests, wildlife and Edakkal cave carvings.", "highlights": ["Edakkal Caves", "Chembra Peak", "wildlife safari", "coffee estates"], "visit_duration": "2-3 days", "rating": 4.5},
    {"name": "Ziro",           "folder": "ziro",          "lat": 27.59, "lon": "93.83", "category": "nature",   "description": "Apatani tribal heartland — rolling pine hills, rice fields and the famous Ziro Music Festival.", "highlights": ["Apatani tribe", "Ziro Music Festival", "Talley Valley wildlife", "organic farming"], "visit_duration": "2-3 days", "rating": 4.6},
    
    {
        "name": "Cherrapunji",
        "folder": "cherrapunji",
        "lat": 25.2866,
        "lon": 91.7315,
        "category": "nature",
        "description": "Known as one of the wettest places on Earth, featuring living root bridges and dramatic cliffs.",
        "highlights": ["Nohkalikai Falls", "Double Decker Root Bridge", "Mawsmai Cave"],
        "visit_duration": "1-2 days",
        "rating": 4.6
    },
    {
        "name": "Dawki",
        "folder": "dawki",
        "lat": 25.1843,
        "lon": 92.0152,
        "category": "nature",
        "description": "Famous for the crystal clear Umngot river where boats appear to float in mid-air.",
        "highlights": ["Umngot River Boating", "Indo-Bangladesh Border", "Shnongpdeng Camping"],
        "visit_duration": "1 day",
        "rating": 4.5
    },
    {
        "name": "Mawsynram",
        "folder": "mawsynram",
        "lat": 25.2975,
        "lon": 91.5826,
        "category": "nature",
        "description": "The current wettest place on Earth, offering lush green landscapes and unique cave formations.",
        "highlights": ["Mawjymbuin Cave", "Khreng Khreng Viewpoint", "Hot Springs"],
        "visit_duration": "1 day",
        "rating": 4.4
    },
    {
        "name": "Gangtok",
        "folder": "gangtok",
        "lat": 27.3314,
        "lon": 88.6138,
        "category": "cultural",
        "description": "The vibrant capital of Sikkim, blending modern conveniences with deep Buddhist traditions and mountain views.",
        "highlights": ["MG Marg", "Tsomgo Lake", "Rumtek Monastery"],
        "visit_duration": "2-3 days",
        "rating": 4.7
    },
    {
        "name": "Pelling",
        "folder": "pelling",
        "lat": 27.3170,
        "lon": 88.2329,
        "category": "nature",
        "description": "A serene hill station offering the closest and most spectacular views of Mount Kanchenjunga.",
        "highlights": ["Pelling Skywalk", "Pemayangtse Monastery", "Rabdentse Ruins"],
        "visit_duration": "1-2 days",
        "rating": 4.6
    },
    {
        "name": "Zero Valley",
        "folder": "zero_valley",
        "lat": 27.5689,
        "lon": 93.8378,
        "category": "cultural",
        "description": "A World Heritage site candidate known for the Apatani tribe's unique agricultural methods and facial tattoos.",
        "highlights": ["Talley Valley", "Apatani Villages", "Ziro Music Festival"],
        "visit_duration": "2-3 days",
        "rating": 4.5
    },
    {
        "name": "Bomdila",
        "folder": "bomdila",
        "lat": 27.2645,
        "lon": 92.4159,
        "category": "cultural",
        "description": "A picturesque town in Arunachal Pradesh known for its apple orchards and Buddhist monasteries.",
        "highlights": ["Bomdila Monastery", "Apple Orchards", "Bomdila View Point"],
        "visit_duration": "1 day",
        "rating": 4.3
    },
    {
        "name": "Dirang",
        "folder": "dirang",
        "lat": 27.3592,
        "lon": 92.2458,
        "category": "nature",
        "description": "A beautiful valley town featuring hot water springs, sheep breeding farms, and an old fort.",
        "highlights": ["Dirang Dzong", "Hot Water Spring", "Sangti Valley"],
        "visit_duration": "1-2 days",
        "rating": 4.4
    },
    {
        "name": "Sivasagar",
        "folder": "sivasagar",
        "lat": 26.9826,
        "lon": 94.6425,
        "category": "historical",
        "description": "The ancient capital of the Ahom Kingdom, dotted with historic palaces, tanks, and temples.",
        "highlights": ["Rang Ghar", "Talatal Ghar", "Shiva Doul"],
        "visit_duration": "1 day",
        "rating": 4.2
    },
    {
        "name": "Guwahati",
        "folder": "guwahati",
        "lat": 26.1445,
        "lon": 91.7362,
        "category": "cultural",
        "description": "The gateway to Northeast India, famous for the Kamakhya Temple and the mighty Brahmaputra river.",
        "highlights": ["Kamakhya Temple", "River Cruise", "Umananda Island"],
        "visit_duration": "1-2 days",
        "rating": 4.5
    },
    {
        "name": "Imphal",
        "folder": "imphal",
        "lat": 24.8170,
        "lon": 93.9368,
        "category": "historical",
        "description": "The capital of Manipur, rich in war history and home to the world's only women-run market.",
        "highlights": ["Kangla Fort", "Ima Keithel Market", "War Cemetery"],
        "visit_duration": "1-2 days",
        "rating": 4.3
    },
    {
        "name": "Loktak Lake",
        "folder": "loktak_lake",
        "lat": 24.5505,
        "lon": 93.8123,
        "category": "nature",
        "description": "The largest freshwater lake in Northeast India, famous for its floating circular swamps called phumdis.",
        "highlights": ["Sendra Island", "Keibul Lamjao Park", "Boating"],
        "visit_duration": "1 day",
        "rating": 4.6
    },
    {
        "name": "Kohima",
        "folder": "kohima",
        "lat": 25.6751,
        "lon": 94.1086,
        "category": "historical",
        "description": "A hill city famous for its WWII history and the vibrant annual Hornbill Festival.",
        "highlights": ["War Cemetery", "Kisama Heritage Village", "Catholic Cathedral"],
        "visit_duration": "1-2 days",
        "rating": 4.4
    },
    {
        "name": "Dzukou Valley",
        "folder": "dzukou_valley",
        "lat": 25.5714,
        "lon": 94.0700,
        "category": "adventure",
        "description": "A trekking paradise on the Nagaland-Manipur border known for its seasonal Dzukou lilies and rolling hills.",
        "highlights": ["Valley Trek", "Camping", "Seasonal Flowers"],
        "visit_duration": "2 days",
        "rating": 4.7
    },
    {
        "name": "Aizawl",
        "folder": "aizawl",
        "lat": 23.7307,
        "lon": 92.7176,
        "category": "cultural",
        "description": "The scenic capital of Mizoram, perched on ridges overlooking lush valleys.",
        "highlights": ["Reiek Tlang", "Solomon's Temple", "Durtlang Hills"],
        "visit_duration": "1-2 days",
        "rating": 4.3
    },
    {
        "name": "Agartala",
        "folder": "agartala",
        "lat": 23.8315,
        "lon": 91.2868,
        "category": "historical",
        "description": "A laid-back capital city known for its gleaming white palaces and rich royal heritage.",
        "highlights": ["Ujjayanta Palace", "Neermahal", "Heritage Park"],
        "visit_duration": "1-2 days",
        "rating": 4.2
    },
    {
        "name": "Unakoti",
        "folder": "unakoti",
        "lat": 24.3166,
        "lon": 92.0673,
        "category": "historical",
        "description": "An ancient Shaivite pilgrimage spot featuring massive bas-relief rock carvings on a hill.",
        "highlights": ["Rock Carvings", "Giant Shiva Head", "Sitakund"],
        "visit_duration": "1 day",
        "rating": 4.5
    },
    {
        "name": "Darbhanga",
        "folder": "darbhanga",
        "lat": 26.1542,
        "lon": 85.8918,
        "category": "cultural",
        "description": "The cultural capital of Mithila, known for its royal forts, ponds, and mango groves.",
        "highlights": ["Darbhanga Fort", "Shyama Mai Temple", "Ahilya Asthan"],
        "visit_duration": "1 day",
        "rating": 4.1
    },
    {
        "name": "Rajgir",
        "folder": "rajgir",
        "lat": 25.0194,
        "lon": 85.4170,
        "category": "historical",
        "description": "An ancient city surrounded by hills, sacred to Buddhists and Jains, featuring a glass skywalk.",
        "highlights": ["Glass Bridge", "Vishwa Shanti Stupa", "Hot Springs"],
        "visit_duration": "1-2 days",
        "rating": 4.4
    },
    {
        "name": "Sasaram",
        "folder": "sasaram",
        "lat": 24.9490,
        "lon": 84.0314,
        "category": "historical",
        "description": "Home to the magnificent red sandstone mausoleum of Sher Shah Suri, set in the middle of a lake.",
        "highlights": ["Sher Shah Suri Tomb", "Rohtasgarh Fort", "Manjhar Kund"],
        "visit_duration": "1 day",
        "rating": 4.2
    },
    {
        "name": "Gaya",
        "folder": "gaya",
        "lat": 24.7914,
        "lon": 85.0002,
        "category": "cultural",
        "description": "A major Hindu pilgrimage site on the banks of the Falgu River, famous for the Pind Daan ritual.",
        "highlights": ["Vishnupad Temple", "Mangla Gauri", "Barabar Caves"],
        "visit_duration": "1 day",
        "rating": 4.3
    },
    {
        "name": "Vaishali",
        "folder": "vaishali",
        "lat": 25.9928,
        "lon": 85.1251,
        "category": "historical",
        "description": "An ancient archaeological site considered the world's first republic and Lord Mahavira's birthplace.",
        "highlights": ["Ashoka Pillar", "Buddha Stupa", "Coronation Tank"],
        "visit_duration": "1 day",
        "rating": 4.1
    },
    {
        "name": "Kolkata",
        "folder": "kolkata",
        "lat": 22.5726,
        "lon": 88.3639,
        "category": "cultural",
        "description": "The City of Joy, famous for its colonial architecture, literature, sweets, and grand festivals.",
        "highlights": ["Victoria Memorial", "Howrah Bridge", "Dakshineswar Temple"],
        "visit_duration": "2-3 days",
        "rating": 4.6
    },
    {
        "name": "Digha",
        "folder": "digha",
        "lat": 21.6266,
        "lon": 87.5074,
        "category": "beach",
        "description": "West Bengal's most popular seaside resort town featuring flat, hard beaches and casuarina plantations.",
        "highlights": ["New Digha Beach", "Marine Aquarium", "Amarabati Park"],
        "visit_duration": "1-2 days",
        "rating": 4.2
    },
    {
        "name": "Mandarmani",
        "folder": "mandarmani",
        "lat": 21.6667,
        "lon": 87.7126,
        "category": "beach",
        "description": "A developing seaside resort village known for having the longest drivable beach in India.",
        "highlights": ["Beach Drive", "Red Crabs", "Water Sports"],
        "visit_duration": "1-2 days",
        "rating": 4.3
    },
    {
        "name": "Bakkhali",
        "folder": "bakkhali",
        "lat": 21.5623,
        "lon": 88.2678,
        "category": "beach",
        "description": "A quiet deltaic island beach resort with mangrove forests and windmills.",
        "highlights": ["Henry's Island", "Crocodile Project", "Fraserganj Wind Park"],
        "visit_duration": "1-2 days",
        "rating": 4.0
    },
    {
        "name": "Santiniketan",
        "folder": "santiniketan",
        "lat": 23.6749,
        "lon": 87.6934,
        "category": "cultural",
        "description": "A university town established by Rabindranath Tagore, famous for its open-air education and art.",
        "highlights": ["Visva Bharati", "Sonajhuri Haat", "Rabindra Bhavan"],
        "visit_duration": "1-2 days",
        "rating": 4.5
    },
    {
        "name": "Murshidabad",
        "folder": "murshidabad",
        "lat": 24.1759,
        "lon": 88.2802,
        "category": "historical",
        "description": "A historical city on the Hooghly river that was once the capital of Bengal, famous for its palaces.",
        "highlights": ["Hazarduari Palace", "Katra Masjid", "Kathgola Palace"],
        "visit_duration": "1 day",
        "rating": 4.3
    },
    {
        "name": "Bishnupur",
        "folder": "bishnupur",
        "lat": 23.0678,
        "lon": 87.3168,
        "category": "historical",
        "description": "Famous for its terracotta temples, Baluchari sarees, and classical music heritage.",
        "highlights": ["Rasmancha", "Terracotta Temples", "Baluchari Weaving"],
        "visit_duration": "1 day",
        "rating": 4.4
    },
    {
        "name": "Darjeeling Tea Gardens",
        "folder": "darjeeling_tea_gardens",
        "lat": 27.0410,
        "lon": 88.2663,
        "category": "nature",
        "description": "Sprawling estates producing the 'Champagne of Teas', set against the backdrop of the Himalayas.",
        "highlights": ["Tea Plucking", "Factory Tour", "Tea Tasting"],
        "visit_duration": "1 day",
        "rating": 4.7
    },
    {
        "name": "Kalimpong",
        "folder": "kalimpong",
        "lat": 27.0594,
        "lon": 88.4695,
        "category": "nature",
        "description": "A buzzing hill station known for its panoramic valley views, Buddhist monasteries, and horticulture.",
        "highlights": ["Deolo Hill", "Durpin Monastery", "Cactus Nursery"],
        "visit_duration": "1-2 days",
        "rating": 4.4
    },
    {
        "name": "Kurseong",
        "folder": "kurseong",
        "lat": 26.8906,
        "lon": 88.2789,
        "category": "nature",
        "description": "Known as the 'Land of White Orchids', a quiet hill station with tea gardens and heritage schools.",
        "highlights": ["Eagle's Crag", "Dow Hill", "Makaibari Tea Estate"],
        "visit_duration": "1 day",
        "rating": 4.2
    },
    {
        "name": "Mirik",
        "folder": "mirik",
        "lat": 26.8931,
        "lon": 88.1795,
        "category": "nature",
        "description": "A serene tourist spot nestled in the hills, centered around the beautiful Sumendu Lake.",
        "highlights": ["Sumendu Lake", "Bokar Monastery", "Orange Orchards"],
        "visit_duration": "1 day",
        "rating": 4.3
    },
    {
        "name": "Jaldapara",
        "folder": "jaldapara",
        "lat": 26.6961,
        "lon": 89.2798,
        "category": "nature",
        "description": "A national park in the foothills of the Eastern Himalayas, home to the Indian One-Horned Rhinoceros.",
        "highlights": ["Elephant Safari", "Rhino Spotting", "Totopara Village"],
        "visit_duration": "1-2 days",
        "rating": 4.5
    },
    {
        "name": "Gorumara",
        "folder": "gorumara",
        "lat": 26.7456,
        "lon": 88.7963,
        "category": "nature",
        "description": "A medium-sized park in the Dooars region primarily known for its population of Indian Rhinoceros.",
        "highlights": ["Jatraprasad Watchtower", "Jungle Safari", "Tribal Dance"],
        "visit_duration": "1-2 days",
        "rating": 4.4
    },
    {
        "name": "Buxa",
        "folder": "buxa",
        "lat": 26.7578,
        "lon": 89.5996,
        "category": "adventure",
        "description": "A tiger reserve offering treks to a historic fort and beautiful riverbeds near the Bhutan border.",
        "highlights": ["Buxa Fort Trek", "Jayanti Riverbed", "Mahakal Cave"],
        "visit_duration": "1-2 days",
        "rating": 4.3
    },
    {
        "name": "Dooars",
        "folder": "dooars",
        "lat": 26.8000,
        "lon": 89.0000,
        "category": "nature",
        "description": "The alluvial floodplains of Northeastern India, a gateway to Bhutan famous for tea gardens and forests.",
        "highlights": ["Tea Estates", "River Streams", "Samsing"],
        "visit_duration": "2-3 days",
        "rating": 4.4
    },
    {
        "name": "Ranchi",
        "folder": "ranchi",
        "lat": 23.3441,
        "lon": 85.3096,
        "category": "nature",
        "description": "The City of Waterfalls, known for its hilly topography and numerous cascading falls.",
        "highlights": ["Hundru Falls", "Jonha Falls", "Pahari Mandir"],
        "visit_duration": "1-2 days",
        "rating": 4.2
    },
    {
        "name": "Netarhat",
        "folder": "netarhat",
        "lat": 23.4795,
        "lon": 84.2709,
        "category": "nature",
        "description": "Known as the 'Queen of Chotanagpur', a hill station famous for its pine forests and sunsets.",
        "highlights": ["Magnolia Point", "Pine Forest", "Koel View Point"],
        "visit_duration": "1-2 days",
        "rating": 4.5
    },
    {
        "name": "Betla",
        "folder": "betla",
        "lat": 23.8845,
        "lon": 84.1917,
        "category": "nature",
        "description": "One of India's first national parks, offering a mix of wildlife and historic forts within the jungle.",
        "highlights": ["Jeep Safari", "Palamau Forts", "Lodh Falls"],
        "visit_duration": "1-2 days",
        "rating": 4.3
    },
    {
        "name": "Hazaribagh",
        "folder": "hazaribagh",
        "lat": 23.9925,
        "lon": 85.3637,
        "category": "nature",
        "description": "A health resort town situated on a plateau, known for its national park and scenic lakes.",
        "highlights": ["Hazaribagh Lake", "Canary Hill", "Rajrappa Temple"],
        "visit_duration": "1 day",
        "rating": 4.1
    },
    {
        "name": "Deoghar",
        "folder": "deoghar",
        "lat": 24.4826,
        "lon": 86.6970,
        "category": "cultural",
        "description": "A major Hindu pilgrimage center housing the Baidyanath Jyotirlinga temple.",
        "highlights": ["Baidyanath Dham", "Trikut Pahar", "Naulakha Mandir"],
        "visit_duration": "1-2 days",
        "rating": 4.4
    },
    {
        "name": "Simlipal",
        "folder": "simlipal",
        "lat": 21.9322,
        "lon": 86.3400,
        "category": "nature",
        "description": "A massive tiger reserve and biosphere famous for waterfalls and lush green forests.",
        "highlights": ["Barehipani Falls", "Jungle Safari", "Joranda Falls"],
        "visit_duration": "2 days",
        "rating": 4.5
    },
    {
        "name": "Bhitarkanika",
        "folder": "bhitarkanika",
        "lat": 20.7410,
        "lon": 86.8778,
        "category": "nature",
        "description": "A unique ecosystem of mangroves known for its population of giant Saltwater Crocodiles.",
        "highlights": ["Mangrove Safari", "Crocodile Spotting", "Bird Sanctuary"],
        "visit_duration": "1 day",
        "rating": 4.6
    },
    {
        "name": "Daringbadi",
        "folder": "daringbadi",
        "lat": 19.9118,
        "lon": 84.1256,
        "category": "nature",
        "description": "Known as the 'Kashmir of Odisha', a hill station with coffee gardens and pine forests.",
        "highlights": ["Coffee Plantations", "Hill View Park", "Midubanda Waterfall"],
        "visit_duration": "1-2 days",
        "rating": 4.3
    },
    {
        "name": "Gopalpur",
        "folder": "gopalpur",
        "lat": 19.2638,
        "lon": 84.9123,
        "category": "beach",
        "description": "A quiet historical sea port town with a relaxing beach and colonial ruins.",
        "highlights": ["Gopalpur Beach", "Old Lighthouse", "Tampara Lake"],
        "visit_duration": "1-2 days",
        "rating": 4.1
    },
    {
        "name": "Chandipur",
        "folder": "chandipur",
        "lat": 21.4422,
        "lon": 87.0142,
        "category": "beach",
        "description": "Famous for its unique receding sea which vanishes up to 5km during low tide.",
        "highlights": ["Sea Walk", "Red Crabs", "Balaramgadi"],
        "visit_duration": "1 day",
        "rating": 4.3
    },
    {
        "name": "Paradip",
        "folder": "paradip",
        "lat": 20.3165,
        "lon": 86.6115,
        "category": "beach",
        "description": "A major port city with a beautiful beach and marine aquarium.",
        "highlights": ["Paradip Port", "Sea Beach", "Lighthouse"],
        "visit_duration": "1 day",
        "rating": 4.0
    },
    {
        "name": "Cuttack",
        "folder": "cuttack",
        "lat": 20.4625,
        "lon": 85.8828,
        "category": "cultural",
        "description": "The Silver City of Odisha, known for its filigree work and ancient fort ruins.",
        "highlights": ["Barabati Fort", "Maritime Museum", "Dhabaleswar Island"],
        "visit_duration": "1 day",
        "rating": 4.1
    },
    {
        "name": "Jharsuguda",
        "folder": "jharsuguda",
        "lat": 21.8549,
        "lon": 84.0049,
        "category": "nature",
        "description": "An industrial hub surrounded by natural beauty including waterfalls and ancient caves.",
        "highlights": ["Koilighughar Falls", "Vikramkhol Caves", "Ib River"],
        "visit_duration": "1 day",
        "rating": 3.9
    },
    {
        "name": "Raipur",
        "folder": "raipur",
        "lat": 21.2514,
        "lon": 81.6296,
        "category": "cultural",
        "description": "The capital of Chhattisgarh, blending urban development with tribal culture museums.",
        "highlights": ["Vivekanand Sarovar", "Purkhouti Muktangan", "Nandan Van Zoo"],
        "visit_duration": "1-2 days",
        "rating": 4.0
    },
    {
        "name": "Jagdalpur",
        "folder": "jagdalpur",
        "lat": 19.0743,
        "lon": 82.0089,
        "category": "nature",
        "description": "The tourism capital of Chhattisgarh, gateway to waterfalls, caves, and tribal history.",
        "highlights": ["Teerathgarh Falls", "Kutumsar Caves", "Anthropological Museum"],
        "visit_duration": "2 days",
        "rating": 4.5
    },
    {
        "name": "Bastar",
        "folder": "bastar",
        "lat": 19.1070,
        "lon": 81.9535,
        "category": "cultural",
        "description": "A region celebrated for its indigenous tribal culture, handicrafts, and dense forests.",
        "highlights": ["Tribal Markets", "Danteshwari Temple", "Dhokra Art"],
        "visit_duration": "1-2 days",
        "rating": 4.6
    },
    {
        "name": "Chitrakote Falls",
        "folder": "chitrakote_falls",
        "lat": 19.2045,
        "lon": 81.7018,
        "category": "nature",
        "description": "Known as the Niagara of India, the widest waterfall in the country on the Indravati river.",
        "highlights": ["Boat Ride", "Camping", "Light & Sound Show"],
        "visit_duration": "1 day",
        "rating": 4.7
    },
    {
        "name": "Sirpur",
        "folder": "sirpur",
        "lat": 21.3411,
        "lon": 82.1798,
        "category": "historical",
        "description": "An important archaeological site housing ancient brick temples and Buddhist monasteries.",
        "highlights": ["Laxman Temple", "Buddha Vihara", "Gandheshwar Temple"],
        "visit_duration": "1 day",
        "rating": 4.3
    },
    {
        "name": "Amarkantak",
        "folder": "amarkantak",
        "lat": 22.6738,
        "lon": 81.7582,
        "category": "cultural",
        "description": "A pilgrim town known as the source of the holy rivers Narmada and Sone.",
        "highlights": ["Narmada Udgam", "Kapildhara Falls", "Ancient Temples"],
        "visit_duration": "1-2 days",
        "rating": 4.4
    },
    {
        "name": "Bhedaghat",
        "folder": "bhedaghat",
        "lat": 23.1311,
        "lon": 79.8006,
        "category": "nature",
        "description": "Famous for the Marble Rocks gorge on the Narmada River and the Dhuandhar waterfall.",
        "highlights": ["Marble Rocks Boating", "Dhuandhar Falls", "Chausath Yogini"],
        "visit_duration": "1 day",
        "rating": 4.6
    },
    {
        "name": "Mandla",
        "folder": "mandla",
        "lat": 22.5977,
        "lon": 80.3708,
        "category": "historical",
        "description": "A town loop-holed by the Narmada river, known for its fort and proximity to Kanha.",
        "highlights": ["Mandla Fort", "Sahastradhara", "Rangrez Ghat"],
        "visit_duration": "1 day",
        "rating": 4.0
    },
    {
        "name": "Pench",
        "folder": "pench",
        "lat": 21.7634,
        "lon": 79.2079,
        "category": "nature",
        "description": "The inspiration for 'The Jungle Book', a national park straddling MP and Maharashtra.",
        "highlights": ["Tiger Safari", "Wolf Sanctuary", "Kohka Lake"],
        "visit_duration": "2 days",
        "rating": 4.5
    },
    {
        "name": "Panna",
        "folder": "panna",
        "lat": 24.7226,
        "lon": 80.1970,
        "category": "nature",
        "description": "Famous for its tiger reserve and the only active diamond mines in Asia.",
        "highlights": ["Tiger Safari", "Pandav Falls", "Raneh Falls"],
        "visit_duration": "1-2 days",
        "rating": 4.4
    },
    {
        "name": "Chanderi",
        "folder": "chanderi",
        "lat": 24.7196,
        "lon": 78.1318,
        "category": "historical",
        "description": "A medieval town famous for its forts, palaces, and hand-woven silk sarees.",
        "highlights": ["Chanderi Fort", "Koshak Mahal", "Saree Weaving"],
        "visit_duration": "1 day",
        "rating": 4.3
    },
    {
        "name": "Maheshwar",
        "folder": "maheshwar",
        "lat": 22.1768,
        "lon": 75.5869,
        "category": "cultural",
        "description": "A temple town on the Narmada banks, known for its massive ghats and Holkar fort.",
        "highlights": ["Ahilya Fort", "Narmada Ghats", "Maheshwari Weaving"],
        "visit_duration": "1 day",
        "rating": 4.6
    },
    {
        "name": "Omkareshwar",
        "folder": "omkareshwar",
        "lat": 22.2478,
        "lon": 76.1511,
        "category": "cultural",
        "description": "A sacred island shaped like the symbol 'Om', housing one of the 12 Jyotirlingas.",
        "highlights": ["Jyotirlinga Temple", "Island Parikrama", "Boat Ride"],
        "visit_duration": "1 day",
        "rating": 4.5
    },
    {
        "name": "Bhind",
        "folder": "bhind",
        "lat": 26.5645,
        "lon": 78.7845,
        "category": "historical",
        "description": "A district known for its rugged forts and the infamous Chambal ravines.",
        "highlights": ["Ater Fort", "Vankhandeshwar Temple", "Chambal Ravines"],
        "visit_duration": "1 day",
        "rating": 3.8
    },
    {
        "name": "Morena",
        "folder": "morena",
        "lat": 26.4947,
        "lon": 77.9940,
        "category": "historical",
        "description": "Home to incredible heritage sites including the temple that inspired the Indian Parliament.",
        "highlights": ["Bateshwar Temples", "Mitawali Temple", "Padavali Fortress"],
        "visit_duration": "1 day",
        "rating": 4.4
    },
    {
        "name": "Datia",
        "folder": "datia",
        "lat": 25.6700,
        "lon": 78.4600,
        "category": "historical",
        "description": "Known for the 7-storey Datia Palace and the powerful Peetambara Peeth temple.",
        "highlights": ["Datia Palace", "Peetambara Peeth", "Sonagiri Temples"],
        "visit_duration": "1 day",
        "rating": 4.2
    },
    {
        "name": "Shivpuri",
        "folder": "shivpuri",
        "lat": 25.4362,
        "lon": 77.6596,
        "category": "historical",
        "description": "The former summer capital of the Scindias, featuring elaborate marble cenotaphs.",
        "highlights": ["Royal Chhatris", "Madhav National Park", "George Castle"],
        "visit_duration": "1 day",
        "rating": 4.1
    },
    {
        "name": "Gokarna Beaches",
        "folder": "gokarna_beaches",
        "lat": 14.5429,
        "lon": 74.3188,
        "category": "beach",
        "description": "A temple town with a hippie vibe, known for its pristine beaches like Om and Kudle.",
        "highlights": ["Om Beach", "Beach Trek", "Mahabaleshwar Temple"],
        "visit_duration": "2-3 days",
        "rating": 4.7
    },
    {
        "name": "Dandeli",
        "folder": "dandeli",
        "lat": 15.2476,
        "lon": 74.6280,
        "category": "adventure",
        "description": "An adventure hub offering white water rafting, jungle stays, and wildlife spotting.",
        "highlights": ["River Rafting", "Jungle Safari", "Syntheri Rocks"],
        "visit_duration": "2 days",
        "rating": 4.5
    },
    {
        "name": "Murudeshwar",
        "folder": "murudeshwar",
        "lat": 14.0940,
        "lon": 74.4899,
        "category": "cultural",
        "description": "Famous for the world's second-tallest Shiva statue overlooking the Arabian Sea.",
        "highlights": ["Shiva Statue", "Gopuram Lift", "Netrani Scuba"],
        "visit_duration": "1 day",
        "rating": 4.6
    },
    {
        "name": "Udupi",
        "folder": "udupi",
        "lat": 13.3409,
        "lon": 74.7421,
        "category": "cultural",
        "description": "A coastal town famous for its Krishna temple and authentic South Indian cuisine.",
        "highlights": ["Sri Krishna Temple", "Kapu Lighthouse", "Malpe Beach"],
        "visit_duration": "1-2 days",
        "rating": 4.5
    },
    {
        "name": "Malpe",
        "folder": "malpe",
        "lat": 13.3541,
        "lon": 74.7042,
        "category": "beach",
        "description": "A major fishing port and beach known for the geological marvel of St. Mary's Island.",
        "highlights": ["St. Mary's Island", "Sea Walk", "Water Sports"],
        "visit_duration": "1 day",
        "rating": 4.4
    },
    {
        "name": "Maravanthe",
        "folder": "maravanthe",
        "lat": 13.6702,
        "lon": 74.6547,
        "category": "beach",
        "description": "Features a unique highway stretch with the ocean on one side and a river on the other.",
        "highlights": ["Highway Drive", "Sunset View", "River Boat Ride"],
        "visit_duration": "1 day",
        "rating": 4.3
    },
    {
        "name": "Mangalore",
        "folder": "mangalore",
        "lat": 12.9141,
        "lon": 74.8560,
        "category": "beach",
        "description": "A major port city known for its diverse culture, beaches, and spicy seafood.",
        "highlights": ["Panambur Beach", "St. Aloysius Chapel", "Pabba's Ice Cream"],
        "visit_duration": "1-2 days",
        "rating": 4.2
    },
    {
        "name": "Hassan",
        "folder": "hassan",
        "lat": 13.0033,
        "lon": 76.1004,
        "category": "historical",
        "description": "The architectural capital of Karnataka, base for visiting Belur and Halebidu.",
        "highlights": ["Shettyhalli Church", "Gorur Dam", "Mosale Temples"],
        "visit_duration": "1 day",
        "rating": 4.0
    },
    {
        "name": "Shravanabelagola",
        "folder": "shravanabelagola",
        "lat": 12.8570,
        "lon": 76.4883,
        "category": "historical",
        "description": "A Jain pilgrimage site famous for the massive 57-foot monolithic statue of Bahubali.",
        "highlights": ["Gommateshwara Statue", "Vindhyagiri Hill", "Chandragiri Temples"],
        "visit_duration": "1 day",
        "rating": 4.6
    },
    {
        "name": "Srirangapatna",
        "folder": "srirangapatna",
        "lat": 12.4208,
        "lon": 76.6826,
        "category": "historical",
        "description": "The historic capital of Tipu Sultan, located on an island in the Kaveri river.",
        "highlights": ["Ranganathaswamy Temple", "Summer Palace", "Gumbaz"],
        "visit_duration": "1 day",
        "rating": 4.4
    },
    {
        "name": "Bandipur",
        "folder": "bandipur",
        "lat": 11.6669,
        "lon": 76.6291,
        "category": "nature",
        "description": "One of India's best-managed tiger reserves, once the hunting ground of Mysore Maharajas.",
        "highlights": ["Tiger Safari", "Gopalaswamy Betta", "Nature Walk"],
        "visit_duration": "1-2 days",
        "rating": 4.5
    },
    {
        "name": "Nagarhole",
        "folder": "nagarhole",
        "lat": 12.0315,
        "lon": 76.1207,
        "category": "nature",
        "description": "A premier tiger reserve also known as Rajiv Gandhi National Park, rich in biodiversity.",
        "highlights": ["Kabini Safari", "Iruppu Falls", "Wildlife Spotting"],
        "visit_duration": "2 days",
        "rating": 4.6
    },
    {
        "name": "Kabini",
        "folder": "kabini",
        "lat": 11.9333,
        "lon": 76.3500,
        "category": "nature",
        "description": "Famous for its leopard sightings and the elusive Black Panther along the river.",
        "highlights": ["Boat Safari", "Black Panther Spotting", "Coracle Ride"],
        "visit_duration": "2 days",
        "rating": 4.8
    },
    {
        "name": "Wayanad Wildlife",
        "folder": "wayanad_wildlife",
        "lat": 11.6854,
        "lon": 76.3756,
        "category": "nature",
        "description": "A lush green wildlife sanctuary that is an integral part of the Nilgiri Biosphere Reserve.",
        "highlights": ["Jeep Safari", "Bamboo Rafting", "Edakkal Caves"],
        "visit_duration": "2 days",
        "rating": 4.5
    },
    {
        "name": "Silent Valley",
        "folder": "silent_valley",
        "lat": 11.1306,
        "lon": 76.4316,
        "category": "nature",
        "description": "One of the last undisturbed rain forests in India, home to the Lion-tailed Macaque.",
        "highlights": ["Rainforest Trek", "Hanging Bridge", "Sairandhri Tower"],
        "visit_duration": "1 day",
        "rating": 4.4
    },
    {
        "name": "Athirappilly",
        "folder": "athirappilly",
        "lat": 10.2847,
        "lon": 76.5689,
        "category": "nature",
        "description": "The largest waterfall in Kerala, often called the 'Niagara of India', set in dense forests.",
        "highlights": ["Waterfall View", "Vazhachal Falls", "Sholayar Dam"],
        "visit_duration": "1 day",
        "rating": 4.7
    },
    {
        "name": "Bekal",
        "folder": "bekal",
        "lat": 12.3965,
        "lon": 75.0353,
        "category": "historical",
        "description": "Home to a giant keyhole-shaped fort overlooking the Arabian Sea.",
        "highlights": ["Bekal Fort", "Bekal Beach", "Backwaters"],
        "visit_duration": "1 day",
        "rating": 4.5
    },
    {
        "name": "Kannur",
        "folder": "kannur",
        "lat": 11.8745,
        "lon": 75.3704,
        "category": "cultural",
        "description": "The land of Theyyam, looms, and lore, famous for its drive-in beach and forts.",
        "highlights": ["Drive-in Beach", "St. Angelo Fort", "Theyyam Ritual"],
        "visit_duration": "1-2 days",
        "rating": 4.4
    },
    {
        "name": "Thalassery",
        "folder": "thalassery",
        "lat": 11.7480,
        "lon": 75.4894,
        "category": "cultural",
        "description": "A historic town known for its circus heritage, cricket, and delicious biryani.",
        "highlights": ["Thalassery Fort", "Overbury's Folly", "Pier Walk"],
        "visit_duration": "1 day",
        "rating": 4.2
    },
    {
        "name": "Kozhikode",
        "folder": "kozhikode",
        "lat": 11.2588,
        "lon": 75.7804,
        "category": "cultural",
        "description": "A historic spice trade hub known for its beautiful beaches and authentic Malabar food.",
        "highlights": ["Kozhikode Beach", "Beypore Shipyard", "SM Street"],
        "visit_duration": "1-2 days",
        "rating": 4.3
    },
    {
        "name": "Palakkad",
        "folder": "palakkad",
        "lat": 10.7867,
        "lon": 76.6548,
        "category": "nature",
        "description": "The gateway to Kerala, known for its paddy fields, fort, and the Western Ghats pass.",
        "highlights": ["Palakkad Fort", "Malampuzha Dam", "Rock Garden"],
        "visit_duration": "1 day",
        "rating": 4.1
    },
    {
        "name": "Thrissur",
        "folder": "thrissur",
        "lat": 10.5276,
        "lon": 76.2144,
        "category": "cultural",
        "description": "The cultural capital of Kerala, famous for the spectacular Thrissur Pooram festival.",
        "highlights": ["Vadakkunnathan Temple", "Zoo & Museum", "Bible Tower"],
        "visit_duration": "1 day",
        "rating": 4.3
    },
    {
        "name": "Guruvayur",
        "folder": "guruvayur",
        "lat": 10.5952,
        "lon": 76.0369,
        "category": "cultural",
        "description": "One of the most sacred Hindu pilgrimage sites in Kerala, dedicated to Lord Krishna.",
        "highlights": ["Temple Darshan", "Elephant Sanctuary", "Chavakkad Beach"],
        "visit_duration": "1 day",
        "rating": 4.6
    },
    {
        "name": "Kumarakom",
        "folder": "kumarakom",
        "lat": 9.6175,
        "lon": 76.4300,
        "category": "nature",
        "description": "A cluster of islands on Vembanad Lake, famous for backwater tourism and bird watching.",
        "highlights": ["Bird Sanctuary", "Houseboat Cruise", "Village Life"],
        "visit_duration": "1-2 days",
        "rating": 4.7
    },
    {
        "name": "Munroe Island",
        "folder": "munroe_island",
        "lat": 8.9958,
        "lon": 76.6117,
        "category": "nature",
        "description": "A hidden pearl in the backwaters, offering serene canoe rides through narrow canals.",
        "highlights": ["Canoe Cruise", "Mangrove Walk", "Homestay Experience"],
        "visit_duration": "1 day",
        "rating": 4.8
    },
    {
        "name": "Varkala Cliff",
        "folder": "varkala_cliff",
        "lat": 8.7379,
        "lon": 76.7030,
        "category": "beach",
        "description": "The only place in Kerala where cliffs meet the Arabian Sea, known for its geo-heritage.",
        "highlights": ["Cliff Walk", "Papanasam Beach", "Paragliding"],
        "visit_duration": "2 days",
        "rating": 4.7
    },
    {
        "name": "Poovar",
        "folder": "poovar",
        "lat": 8.3182,
        "lon": 77.0628,
        "category": "beach",
        "description": "A beautiful island estuary where the river, lake, and sea meet.",
        "highlights": ["Estuary Cruise", "Golden Sand Beach", "Floating Cottages"],
        "visit_duration": "1 day",
        "rating": 4.4
    },
    {
        "name": "Ponmudi",
        "folder": "ponmudi",
        "lat": 8.7601,
        "lon": 77.1105,
        "category": "nature",
        "description": "A misty hill station near Trivandrum with tea gardens and winding roads.",
        "highlights": ["Golden Valley", "Hilltop Viewpoint", "Meenmutty Falls"],
        "visit_duration": "1 day",
        "rating": 4.3
    },
    {
        "name": "Courtallam",
        "folder": "courtallam",
        "lat": 8.9329,
        "lon": 77.2764,
        "category": "nature",
        "description": "Known as the 'Spa of the South' due to the medicinal properties of its waterfalls.",
        "highlights": ["Main Falls", "Five Falls", "Old Courtallam"],
        "visit_duration": "1 day",
        "rating": 4.2
    },
    {
        "name": "Kodaikanal Lake",
        "folder": "kodaikanal_lake",
        "lat": 10.2338,
        "lon": 77.4892,
        "category": "nature",
        "description": "A star-shaped man-made lake that is the centerpiece of the Kodaikanal hill station.",
        "highlights": ["Lake Boating", "Cycling", "Bryant Park"],
        "visit_duration": "1-2 days",
        "rating": 4.5
    },
    {
        "name": "Valparai",
        "folder": "valparai",
        "lat": 10.3204,
        "lon": 76.9554,
        "category": "nature",
        "description": "A pollution-free hill station surrounded by tea estates and rich wildlife.",
        "highlights": ["Tea Estates", "Aliyar Dam", "Nallamudi Viewpoint"],
        "visit_duration": "1-2 days",
        "rating": 4.4
    },
    {
        "name": "Yercaud",
        "folder": "yercaud",
        "lat": 11.7753,
        "lon": 78.2093,
        "category": "nature",
        "description": "A quiet hill station in the Shevaroy Hills, known for its lake and coffee plantations.",
        "highlights": ["Emerald Lake", "Lady's Seat", "Killiyur Falls"],
        "visit_duration": "1-2 days",
        "rating": 4.3
    },
    {
        "name": "Kolli Hills",
        "folder": "kolli_hills",
        "lat": 11.2485,
        "lon": 78.3387,
        "category": "adventure",
        "description": "A mountain range famous for its 70 hairpin bends and the Agaya Gangai waterfalls.",
        "highlights": ["Hairpin Drive", "Agaya Gangai Falls", "Arapaleeswarar Temple"],
        "visit_duration": "1 day",
        "rating": 4.1
    }
]

# Fix the one accidental string in coordinates
for _d in _DEST_REGISTRY:
    _d["lon"] = float(_d["lon"])


def _get_nearby_from_registry(dest_name: str, radius_km: float = 150.0) -> list[dict]:
    """
    Find all destinations in _DEST_REGISTRY within radius_km of dest_name.
    Returns them sorted by distance with full metadata.
    radius_km is set to 150 by default to ensure reasonable results;
    caller can request a tighter filter.
    """
    # Find the query destination in registry
    from fake_tbo import DESTINATION_MAP

    # Pre-compute reverse map: name -> tbo_id
    name_to_tbo = {v["name"].lower(): k for k, v in DESTINATION_MAP.items()}

    query = None
    name_lower = dest_name.lower()
    for d in _DEST_REGISTRY:
        if (d["name"].lower() == name_lower
                or d["folder"] == name_lower
                or d["folder"] == name_lower.replace(" ", "_")
                or name_lower in d["name"].lower()
                or d["name"].lower() in name_lower):
            query = d
            break

    if query is None:
        return []

    results = []
    for d in _DEST_REGISTRY:
        if d["folder"] == query["folder"]:
            continue  # skip self
        dist = _haversine_km(query["lat"], query["lon"], d["lat"], d["lon"])
        if dist <= radius_km:
            travel_mins = int(dist * 1.4)  # rough road-time estimate
            results.append({
                "name": d["name"],
                "folder": d["folder"],
                "distance_km": round(dist, 1),
                "description": d["description"],
                "highlights": d["highlights"],
                "travel_time_min": travel_mins,
                "category": d["category"],
                "visit_duration": d["visit_duration"],
                "rating": d["rating"],
                "tbo_id": name_to_tbo.get(d["name"].lower(), f"LOCAL_{d['folder'].upper()}"),
                # Frontend uses this to build image URL: /destinations/<folder>/1.jpg
                "image_path": f"/destinations/{d['folder']}/1.jpg",
            })

    results.sort(key=lambda x: x["distance_km"])
    return results


@app.get("/nearby")
async def get_nearby_places(destination: str, radius_km: float = 150.0):
    """
    Return all destinations from the local destinations/ folder within radius_km
    of the given destination, sorted by distance. Every result has a local
    image at /destinations/<folder>/1.jpg served by the backend static files.
    """
    logger.info(f"GET /nearby | destination={destination} radius_km={radius_km}")

    # Progressive radius: try 70km, then 150km, then 300km to always return something
    for r in [radius_km, 150.0, 300.0, 600.0]:
        places = _get_nearby_from_registry(destination, r)
        if places:
            break

    actual_radius = places[0]["distance_km"] if places else 0

    return {
        "destination": destination,
        "nearby_places": places,
        "count": len(places),
        "radius_km": radius_km,
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Process a user chat message and return Gemini's response.
    Now supports structured actions: reorder_stops, change_transport, adjust_days.
    """
    logger.info(f"POST /chat | session={request.session_id}")
    validate_chat_message(request.message)

    session = session_store.get_session(request.session_id)
    validate_session_exists(session, request.session_id)

    session_store.add_message(request.session_id, "user", request.message)

    # Extract preferences from message
    msg_lower = request.message.lower()
    preference_keywords = {
        "beach": "prefers beach",
        "mountain": "prefers mountains",
        "snow": "prefers snowy destination",
        "heritage": "interested in heritage",
        "peaceful": "wants peaceful destination",
        "adventure": "wants adventure activities",
        "romantic": "looking for romantic destination",
        "budget": "budget-conscious",
        "luxury": "interested in luxury",
        "train": "prefers train travel",
        "flight": "prefers flying",
    }
    for keyword, pref in preference_keywords.items():
        if keyword in msg_lower:
            session_store.add_preference(request.session_id, pref)

    session = session_store.get_session(request.session_id)

    try:
        gemini_result = gemini_utils.generate_chat_response(session)
    except Exception as e:
        logger.error(f"Gemini chat failed: {e}")
        gemini_result = {
            "message": "I had a small hiccup! Could you tell me more about what vibe you're looking for?",
            "action": "ask_question",
            "params": {},
            "updated_filters": {"must_have": [], "must_not_have": [], "vibe_adjustment": ""},
        }

    action = gemini_result.get("action", "ask_question")
    ai_message = gemini_result.get("message", "")
    params = gemini_result.get("params", {})
    updated_filters = gemini_result.get("updated_filters", {})

    session_store.add_message(request.session_id, "assistant", ai_message)

    updated_match = None
    action_applied = None

    if action == "search_again":
        # Full new destination search
        current_match_name = session["current_match"]
        session_store.add_rejected_destination(request.session_id, current_match_name)
        session = session_store.get_session(request.session_id)
        rejected_names = session.get("rejected_destinations", [])

        import numpy as np
        original_embedding = np.array(session["original_embedding"], dtype=np.float32)

        new_match = await find_best_match_async(
            query_embedding=original_embedding,
            budget=session["budget"],
            budget_tier=session["budget_tier"],
            exclude_names=rejected_names,
            n_candidates=8,
        )

        if new_match:
            try:
                new_explanation = gemini_utils.generate_match_explanation(
                    destination_name=new_match["destination"],
                    vibe_tags=session.get("vibe_tags", []),
                )
            except Exception:
                new_explanation = {
                    "match_reasons": ["scenic location", "beautiful landscape", "unique atmosphere"],
                    "conversation_opener": "",
                }

            session_store.update_match(
                session_id=request.session_id,
                new_match=new_match["destination"],
                new_tbo_id=new_match["tbo_id"],
                new_price=new_match["price_per_person"],
                new_hotels=new_match["hotels"],
                new_photo=new_match["photo"],
                new_match_reasons=new_explanation["match_reasons"],
            )
            updated_match = {
                "matched_destination": new_match["destination"],
                "destination_photo": new_match["photo"],
                "price_per_person": new_match["price_per_person"],
                "match_reasons": new_explanation["match_reasons"],
                "hotels": new_match["hotels"],
                "tagline": new_match.get("tagline", ""),
            }
        else:
            action = "ask_question"
            ai_message = "I couldn't find another destination within your budget. Would you like to adjust your budget or explore a different vibe?"

    elif action == "reorder_stops":
        new_order = params.get("new_order", [])
        current_stops = session.get("itinerary_stops", [])
        if new_order and len(new_order) == len(current_stops):
            session_store.reorder_stops(request.session_id, new_order)
            updated_session = session_store.get_session(request.session_id)
            action_applied = {
                "type": "reorder_stops",
                "new_stops": updated_session.get("itinerary_stops", []),
            }

    elif action == "change_transport":
        leg_index = params.get("leg_index", 0)
        mode = params.get("mode", "flight")
        session_store.update_leg(request.session_id, leg_index, transport_mode=mode)
        action_applied = {"type": "change_transport", "leg_index": leg_index, "mode": mode}

    elif action == "adjust_days":
        stop_index = params.get("stop_index", 0)
        days = params.get("days", 2)
        session_store.update_leg(request.session_id, stop_index, days_at_stop=days)
        action_applied = {"type": "adjust_days", "stop_index": stop_index, "days": days}

    elif action == "confirm_booking":
        session_store.confirm_session(request.session_id)

    return {
        "message": ai_message,
        "action": action,
        "updated_match": updated_match,
        "action_applied": action_applied,
    }


# ─── Endpoint 5: POST /itinerary/reorder (new) ───────────────────────────────

@app.post("/itinerary/reorder")
async def reorder_itinerary(request: ReorderRequest):
    """
    Reorder cities in a session's itinerary.
    Validates that no stops are added or removed — only order changes.
    Returns recalculated costs and route justification.
    """
    logger.info(f"POST /itinerary/reorder | session={request.session_id}")

    session = session_store.get_session(request.session_id)
    validate_session_exists(session, request.session_id)

    current_stops = session.get("itinerary_stops", [])
    validate_reorder_request(request.new_stop_order, current_stops)

    # Apply reorder
    session_store.reorder_stops(request.session_id, request.new_stop_order)
    updated_session = session_store.get_session(request.session_id)
    new_stops = updated_session.get("itinerary_stops", [])

    # Validate route feasibility
    try:
        route_optimizer.validate_route(
            new_stops,
            duration_days=updated_session.get("duration_days"),
            budget=updated_session["budget"],
        )
    except ItineraryError as e:
        raise HTTPException(status_code=400, detail={"error": e.reason, "field": e.field})

    # Recalculate budget allocation
    updated_stops, total_price = route_optimizer.recalculate_budget(
        new_stops, updated_session["budget"]
    )

    # Generate route justification
    region = updated_session.get("itinerary_region", "India")
    justification = gemini_utils.generate_route_justification(updated_stops, region)

    return {
        "stops": updated_stops,
        "total_price": total_price,
        "route_justification": justification,
        "leg_transport_modes": updated_session.get("leg_transport_modes", {}),
        "days_per_stop": updated_session.get("days_per_stop", {}),
    }


# ─── Endpoint 6: POST /itinerary/update-leg (new) ────────────────────────────

@app.post("/itinerary/update-leg")
async def update_leg(request: UpdateLegRequest):
    """
    Update transport mode or day count for a specific stop/leg.
    Returns updated session metadata without triggering a new TBO search.
    """
    logger.info(f"POST /itinerary/update-leg | session={request.session_id} | leg={request.leg_index}")

    session = session_store.get_session(request.session_id)
    validate_session_exists(session, request.session_id)

    current_stops = session.get("itinerary_stops", [])
    validate_update_leg_request(
        request.leg_index,
        request.transport_mode or "flight",
        request.days_at_stop,
        current_stops,
    )

    session_store.update_leg(
        request.session_id,
        request.leg_index,
        transport_mode=request.transport_mode,
        days_at_stop=request.days_at_stop,
    )
    session_store.record_edit(request.session_id, "update_leg", {
        "leg_index": request.leg_index,
        "transport_mode": request.transport_mode,
        "days_at_stop": request.days_at_stop,
    })

    updated_session = session_store.get_session(request.session_id)
    days_per_stop = updated_session.get("days_per_stop", {})
    total_days = sum(days_per_stop.values()) if days_per_stop else 0

    return {
        "leg_index": request.leg_index,
        "transport_mode": request.transport_mode,
        "days_at_stop": request.days_at_stop,
        "leg_transport_modes": updated_session.get("leg_transport_modes", {}),
        "days_per_stop": days_per_stop,
        "total_days": total_days,
    }


# ─── Endpoint 7: POST /confirm (original) ────────────────────────────────────

@app.post("/confirm")
async def confirm_booking(request: ConfirmRequest):
    """Returns the final destination card for the booking screen."""
    logger.info(f"POST /confirm | session={request.session_id}")

    session = session_store.get_session(request.session_id)
    validate_session_exists(session, request.session_id)

    session_store.confirm_session(request.session_id)

    return {
        "matched_destination": session["current_match"],
        "destination_photo": session["current_photo"],
        "price_per_person": session["current_price"],
        "hotels": session["current_hotels"],
        "match_reasons": session.get("match_reasons", []),
        "travel_dates": session.get("travel_dates"),
        "budget": session["budget"],
        "itinerary_stops": session.get("itinerary_stops", []),
        "leg_transport_modes": session.get("leg_transport_modes", {}),
        "days_per_stop": session.get("days_per_stop", {}),
        "edit_history": session.get("edit_history", []),
    }


# ─── Endpoint 8: POST /generate-packages (new) ───────────────────────────────

@app.post("/generate-packages")
async def generate_packages(request: GeneratePackagesRequest):
    """
    Takes user's selected activities across stops and generates 3 package tiers.
    Works even if the session has expired (e.g. after backend restart).
    """
    logger.info(f"POST /generate-packages | session={request.session_id}")
    
    activities_total = 0
    
    for stop_tbo_id, selected_act_ids in request.selections.items():
        avail_acts = get_activities_for_destination(stop_tbo_id)
        for act_id in selected_act_ids:
            act = next((a for a in avail_acts if a["id"] == act_id), None)
            if act:
                activities_total += act["price"]

    base_budget = request.budget or 100000
    travel_month = request.travel_month or "December"
    
    # Simple travel_month -> date parser (defaults to 15th of the month)
    from datetime import datetime
    try:
        current_year = datetime.now().year
        # Parse month name
        dt = datetime.strptime(f"{travel_month} {current_year}", "%B %Y")
        # If the generated date is in the past, bump to next year
        if dt.month < datetime.now().month:
            dt = dt.replace(year=current_year + 1)
        # Target the 15th of that month as a representative date
        travel_date_str = dt.replace(day=15).strftime("%Y-%m-%d")
    except ValueError:
        travel_date_str = None
        logger.warning(f"Could not parse travel_month '{travel_month}' into a date.")
    
    # Attempt to fetch real TBO data for accurate flight & hotel costs
    from fake_tbo import get_tbo_data
    import asyncio
    
    real_flight_cost = 0
    tbo_called = False
    
    # Track the sum of tiered hotel prices across all selected destinations
    real_hotel_tiers = {
        "budget": 0,
        "standard": 0,
        "premium": 0
    }
    
    if request.selections:
        per_stop_budget = base_budget // max(1, len(request.selections))
        for stop_tbo_id in request.selections.keys():
            if stop_tbo_id.startswith("LOCAL_"):
                continue
            
            try:
                tbo_data = await get_tbo_data(stop_tbo_id, per_stop_budget, travel_date_str)
                if tbo_data:
                    tbo_called = True
                    real_flight_cost += tbo_data.get("flight_min_fare") or 0
                    
                    tiered_prices = tbo_data.get("tiered_hotel_prices", {})
                    # For each destination, add the tiered price. If a specific tier is missing, 
                    # we will fallback using the standard multiplier logic later
                    real_hotel_tiers["budget"] += tiered_prices.get("budget") or 0
                    real_hotel_tiers["standard"] += tiered_prices.get("standard") or 0
                    real_hotel_tiers["premium"] += tiered_prices.get("premium") or 0
                        
            except Exception as e:
                logger.error(f"Error fetching TBO data for {stop_tbo_id}: {e}")

    # Calculate baseline flight cost
    if tbo_called and real_flight_cost > 0:
        base_flight_total = int(real_flight_cost)
    else:
        base_flight_total = int(base_budget * 0.3)
        
    # Calculate baseline hotel total (standard)
    if tbo_called and real_hotel_tiers["standard"] > 0:
        base_hotel_total = int(real_hotel_tiers["standard"])
    else:
        # Fallback to math estimations if TBO fails entirely or no standard hotels exist
        base_hotel_total = int(base_budget * 0.4)

    # Calculate final tiered hotel costs with graceful fallback 
    # if a specific tier was completely missing from the TBO response
    backpacker_hotel = int(real_hotel_tiers["budget"]) if real_hotel_tiers["budget"] > 0 else int(base_hotel_total * 0.6)
    balanced_hotel = base_hotel_total
    premium_hotel = int(real_hotel_tiers["premium"]) if real_hotel_tiers["premium"] > 0 else int(base_hotel_total * 1.8)
    
    packages = [
        {
            "id": "backpacker",
            "tier": "The Backpacker",
            "description": "Budget-conscious. Prioritizes activities with a simpler 2-3 star hotel stay.",
            "flight_cost": base_flight_total,
            "hotel_cost": backpacker_hotel,
            "activities_cost": activities_total,
            "total_price": base_flight_total + backpacker_hotel + activities_total,
            "hotel_rating": "2-3 Stars",
        },
        {
            "id": "balanced",
            "tier": "The Balanced Explorer",
            "description": "The golden mean. Standard 3-4 star accommodations with your full activity list.",
            "flight_cost": base_flight_total,
            "hotel_cost": balanced_hotel,
            "activities_cost": activities_total,
            "total_price": base_flight_total + balanced_hotel + activities_total,
            "hotel_rating": "3-4 Stars",
        },
        {
            "id": "premium",
            "tier": "The Premium Leisure",
            "description": "Luxury experience. Upgraded 4.5-5 star hotels. Includes all selected activities.",
            "flight_cost": base_flight_total,
            "hotel_cost": premium_hotel,
            "activities_cost": activities_total,
            "total_price": base_flight_total + premium_hotel + activities_total,
            "hotel_rating": "4.5-5 Stars",
        }
    ]
    
    return {"packages": packages}


@app.get("/activities/{tbo_id}")
async def get_activities(tbo_id: str):
    return {"activities": get_activities_for_destination(tbo_id)}


# ─── Endpoint 9: GET /health (original) ──────────────────────────────────────

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    try:
        count = chromadb_utils.get_collection_count()
        return {
            "status": "ok",
            "destinations_loaded": count,
            "api_version": "2.0.0",
            "endpoints": ["/itineraries", "/search", "/destinations", "/chat", "/itinerary/reorder", "/itinerary/update-leg", "/confirm"],
        }
    except Exception as e:
        return {"status": "ok", "destinations_loaded": 0, "note": str(e)}


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
