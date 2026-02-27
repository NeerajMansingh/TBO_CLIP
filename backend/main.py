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
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
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

    anchor_candidate = candidates[0]
    anchor_tbo_id = anchor_candidate["tbo_id"]
    anchor_region = get_region(anchor_tbo_id)
    compatible_ids = get_compatible_stops(anchor_tbo_id, exclude_ids=[], n=2)
    all_stop_ids = [anchor_tbo_id] + compatible_ids

    resolved_stops = await _resolve_stops(
        all_stop_ids, budget, candidates, anchor_region,
        BUDGET_SPLITS["3-stop"],
    )

    if not resolved_stops:
        raise HTTPException(
            status_code=400,
            detail="Could not resolve any destinations within your budget.",
        )

    itineraries = _build_itinerary_options(resolved_stops, budget, anchor_region)
    if not itineraries:
        raise HTTPException(
            status_code=400,
            detail="No itinerary options fit within your budget. Try increasing your budget.",
        )

    best_itinerary = itineraries[-1]
    try:
        explanation = gemini_utils.generate_itinerary_explanation(
            stops=best_itinerary["stops"],
            vibe_tags=vibe_tags,
        )
        stop_narratives = explanation.get("stop_narratives", {})
        stop_itineraries = explanation.get("stop_itineraries", {})
        for it in itineraries:
            for s in it["stops"]:
                if s["destination"] in stop_narratives:
                    s["tagline"] = stop_narratives[s["destination"]]
                if s["destination"] in stop_itineraries:
                    s["itinerary"] = stop_itineraries[s["destination"]]
    except Exception as e:
        logger.warning(f"Gemini explanation failed: {e}")
        stop_names = " → ".join(s["destination"] for s in best_itinerary["stops"])
        explanation = {
            "match_reasons": ["scenic journey", "diverse landscapes", "cultural richness"],
            "itinerary_narrative": f"A wonderful journey through {stop_names}.",
            "conversation_opener": f"We've found a great {best_itinerary['type']} journey for you! What would you like to know?",
            "stop_narratives": {},
        }

    # Add route justification
    route_justification = gemini_utils.generate_route_justification(
        best_itinerary["stops"], anchor_region
    )

    first_stop = best_itinerary["stops"][0]
    session_id = session_store.create_session(
        original_embedding=user_embedding,
        budget=budget,
        budget_tier=budget_tier,
        travel_dates=travel_dates,
        current_match=first_stop["destination"],
        current_tbo_id=first_stop["tbo_id"],
        current_price=first_stop["price_per_person"],
        current_hotels=first_stop["hotels"],
        current_photo=first_stop["photo"],
        match_reasons=explanation["match_reasons"],
        conversation_opener=explanation["conversation_opener"],
        vibe_tags=vibe_tags,
        itinerary_stops=best_itinerary["stops"],
        itinerary_type=best_itinerary["type"],
        itinerary_label=best_itinerary["label"],
        itinerary_region=best_itinerary["region"],
        itinerary_total_price=best_itinerary["total_price"],
    )

    return {
        "session_id": session_id,
        "itineraries": itineraries,
        "vibe_tags": vibe_tags,
        "match_reasons": explanation["match_reasons"],
        "itinerary_narrative": explanation.get("itinerary_narrative", ""),
        "conversation_opener": explanation["conversation_opener"],
        "route_justification": route_justification,
        "region": anchor_region,
    }


# ─── Endpoint 2: POST /search (new — text-based) ─────────────────────────────

@app.post("/search")
async def text_search(request: SearchRequest):
    """
    Text/NLP-based itinerary search — no image required.

    Parses the natural language query with Gemini, maps it to ChromaDB
    destinations via text embedding, and returns itinerary options.
    """
    logger.info(f"POST /search | query='{request.query}' | budget={request.budget}")

    validate_search_request(
        query=request.query,
        budget=request.budget,
        duration_days=request.duration_days,
    )

    # Parse NLP query
    parsed = gemini_utils.parse_search_query(request.query)
    effective_budget = parsed.get("budget") or request.budget
    effective_month = parsed.get("travel_month") or request.travel_month
    effective_vibes = parsed.get("vibes") or (request.vibes or [])
    duration_days = parsed.get("duration_days") or request.duration_days

    # Build a composite text prompt for ChromaDB embedding
    search_parts = [request.query]
    if effective_vibes:
        search_parts.append(", ".join(effective_vibes))
    if parsed.get("region"):
        search_parts.append(parsed["region"])
    composite_query = " ".join(search_parts)

    budget_tier = get_budget_tier(effective_budget)

    # Embed the text query and search ChromaDB
    user_embedding = clip_utils.get_text_embedding(composite_query)

    candidates = chromadb_utils.query_similar_destinations(
        query_embedding=user_embedding,
        budget_tier=budget_tier,
        n_results=10,
    )

    if not candidates:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "No matching destinations found for your query.",
                "hint": "Try broadening your search — e.g. mention a region, vibe, or adjust your budget.",
            },
        )

    anchor_candidate = candidates[0]
    anchor_tbo_id = anchor_candidate["tbo_id"]
    anchor_region = get_region(anchor_tbo_id)
    compatible_ids = get_compatible_stops(anchor_tbo_id, exclude_ids=[], n=2)

    resolved_stops = await _resolve_stops(
        [anchor_tbo_id] + compatible_ids,
        effective_budget,
        candidates,
        anchor_region,
        BUDGET_SPLITS["3-stop"],
    )

    if not resolved_stops:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Could not find destinations within your budget.",
                "hint": "Try increasing your budget or searching for a different region.",
            },
        )

    itineraries = _build_itinerary_options(resolved_stops, effective_budget, anchor_region)
    if not itineraries:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "No complete itinerary fits your budget.",
                "hint": "Try a higher budget, fewer stops, or a less expensive region.",
            },
        )

    best_itinerary = itineraries[-1]
    try:
        explanation = gemini_utils.generate_itinerary_explanation(
            stops=best_itinerary["stops"],
            vibe_tags=effective_vibes or ["travel", "exploration"],
        )
        for it in itineraries:
            for s in it["stops"]:
                if s["destination"] in explanation.get("stop_narratives", {}):
                    s["tagline"] = explanation["stop_narratives"][s["destination"]]
                if s["destination"] in explanation.get("stop_itineraries", {}):
                    s["itinerary"] = explanation["stop_itineraries"][s["destination"]]
    except Exception as e:
        logger.warning(f"Explanation failed for text search: {e}")
        explanation = {
            "match_reasons": ["great destination", "fits your budget", "matches your vibe"],
            "itinerary_narrative": f"A curated journey for your query: '{request.query}'.",
            "conversation_opener": "We've found great options for your trip! What would you like to know?",
        }

    route_justification = gemini_utils.generate_route_justification(
        best_itinerary["stops"], anchor_region
    )

    first_stop = best_itinerary["stops"][0]
    session_id = session_store.create_session(
        original_embedding=user_embedding,
        budget=effective_budget,
        budget_tier=budget_tier,
        travel_dates=effective_month,
        current_match=first_stop["destination"],
        current_tbo_id=first_stop["tbo_id"],
        current_price=first_stop["price_per_person"],
        current_hotels=first_stop["hotels"],
        current_photo=first_stop["photo"],
        match_reasons=explanation["match_reasons"],
        conversation_opener=explanation["conversation_opener"],
        vibe_tags=effective_vibes or ["travel"],
        itinerary_stops=best_itinerary["stops"],
        itinerary_type=best_itinerary["type"],
        itinerary_label=best_itinerary["label"],
        itinerary_region=best_itinerary["region"],
        itinerary_total_price=best_itinerary["total_price"],
        duration_days=duration_days,
    )

    return {
        "session_id": session_id,
        "itineraries": itineraries,
        "vibe_tags": effective_vibes,
        "parsed_query": parsed,
        "match_reasons": explanation["match_reasons"],
        "itinerary_narrative": explanation.get("itinerary_narrative", ""),
        "conversation_opener": explanation["conversation_opener"],
        "route_justification": route_justification,
        "region": anchor_region,
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


# ─── Endpoint 4: POST /chat (upgraded) ───────────────────────────────────────

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


# ─── Endpoint 8: GET /health (original) ──────────────────────────────────────

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
