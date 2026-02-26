"""
main.py — FastAPI backend for VibeTravel.
Four endpoints: /match, /chat, /confirm, /health
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import clip_utils
import chromadb_utils
import gemini_utils
import session_store
from fake_tbo import get_budget_tier, get_tbo_data, get_compatible_stops, get_region

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="VibeTravel API", version="1.0.0")

# Allow React dev server requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve destination photos as static files
BACKEND_DIR = Path(__file__).parent
DESTINATIONS_DIR = BACKEND_DIR / "destinations"
DESTINATIONS_DIR.mkdir(exist_ok=True)

app.mount("/destinations", StaticFiles(directory=str(DESTINATIONS_DIR)), name="destinations")


# ─── Pydantic models ─────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str
    message: str


class ConfirmRequest(BaseModel):
    session_id: str


# ─── Helper functions ─────────────────────────────────────────────────────────

async def find_best_match_async(
    query_embedding,
    budget: int,
    budget_tier: str,
    exclude_names: list[str],
    n_candidates: int = 5,
) -> Optional[dict]:
    """
    Run a ChromaDB similarity search and TBO data validation.
    Returns the best matching destination dict or None.
    """
    # Exclude by TBO ID isn't directly available — convert names to IDs from session
    candidates = chromadb_utils.query_similar_destinations(
        query_embedding=query_embedding,
        budget_tier=budget_tier,
        n_results=n_candidates,
    )

    if not candidates:
        logger.warning("No candidates returned from ChromaDB")
        return None

    # Filter excluded destinations and check TBO data
    for candidate in candidates:
        if candidate["destination"] in exclude_names:
            continue

        tbo_data = await get_tbo_data(candidate["tbo_id"], budget)
        if tbo_data is None:
            continue

        # Merge ChromaDB metadata with TBO data
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


# ─── Endpoint 1: POST /itineraries ───────────────────────────────────────────

# Budget split fractions per journey type
_BUDGET_SPLITS = {
    "1-stop": [1.0],
    "2-stop": [0.55, 0.45],
    "3-stop": [0.45, 0.35, 0.20],
}

_JOURNEY_LABELS = {
    "1-stop": "Quick Escape",
    "2-stop": "Weekend Explorer",
    "3-stop": "Grand Tour",
}


# Fallback photos for destinations not in the limited ChromaDB sample
_FALLBACK_PHOTOS = {
    "Jaisalmer": "https://images.unsplash.com/photo-1599818817477-90c74b99813b?q=80&w=2672&auto=format&fit=crop", # Proper desert/fort photo
    "Udaipur": "https://images.unsplash.com/photo-1585136917228-a4f62be0e7c7?q=80&w=2670&auto=format&fit=crop",
    "Leh-Ladakh": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?q=80&w=2670&auto=format&fit=crop",
    "Alleppey": "https://images.unsplash.com/photo-1621689444225-0698c4af00f1?q=80&w=2670&auto=format&fit=crop",
    "Ooty": "https://images.unsplash.com/photo-1622279457486-7e72a7c17e55?q=80&w=2670&auto=format&fit=crop",
    "Rishikesh": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?q=80&w=2670&auto=format&fit=crop",
    "Shimla": "https://images.unsplash.com/photo-1595815771614-ade9d652a65d?q=80&w=2670&auto=format&fit=crop",
    "Agra": "https://images.unsplash.com/photo-1564507592224-200543666925?q=80&w=2670&auto=format&fit=crop",
}

@app.post("/itineraries")
async def build_itineraries(
    photo: UploadFile = File(...),
    budget: int = Form(...),
    travel_dates: Optional[str] = Form(None),
):
    """
    Called when user clicks 'Find My Journey'.
    Runs CLIP → ChromaDB → TBO for 3 geographically-constrained journey options
    (1-stop, 2-stop, 3-stop). Hides options the budget cannot support.
    Returns all valid itineraries + a session_id for the best one.
    """
    logger.info(f"POST /itineraries | budget={budget} | filename={photo.filename}")

    # 1. Read and embed the uploaded photo
    image_bytes = await photo.read()
    try:
        import io
        from PIL import Image as PILImage
        pil_image = PILImage.open(io.BytesIO(image_bytes)).convert("RGB")
        user_embedding = clip_utils.get_image_embedding(pil_image)
    except Exception as e:
        logger.error(f"CLIP embedding failed: {e}")
        raise HTTPException(status_code=422, detail=f"Could not process image: {e}")

    # 2. Determine budget tier and vibe tags
    budget_tier = get_budget_tier(budget)
    vibe_tags = clip_utils.get_image_vibes(pil_image)

    # 3. Pull top-N candidates from ChromaDB (need enough for 3 stops)
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

    # 4. Anchor = best candidate
    anchor_candidate = candidates[0]
    anchor_tbo_id = anchor_candidate["tbo_id"]
    anchor_region = get_region(anchor_tbo_id)

    # 5. Find geographically compatible additional stop IDs
    compatible_ids = get_compatible_stops(anchor_tbo_id, exclude_ids=[], n=2)

    # 6. Build a pool of resolved TBO stop data (anchor + up to 2 companions)
    # We assign per-stop budgets based on max split (3-stop) to check feasibility
    all_stop_ids = [anchor_tbo_id] + compatible_ids
    stop_budgets_3 = [int(budget * f) for f in _BUDGET_SPLITS["3-stop"]]

    resolved_stops: list[dict] = []  # fully resolved stop dicts
    for i, tbo_id in enumerate(all_stop_ids):
        per_stop_budget = stop_budgets_3[i] if i < len(stop_budgets_3) else int(budget * 0.20)
        tbo_data = await get_tbo_data(tbo_id, per_stop_budget)
        if tbo_data is None:
            # Try the next best same-region candidate
            for cand in candidates[1:]:
                if cand["tbo_id"] in [s["tbo_id"] for s in resolved_stops] + [anchor_tbo_id]:
                    continue
                if get_region(cand["tbo_id"]) == anchor_region:
                    tbo_data = await get_tbo_data(cand["tbo_id"], per_stop_budget)
                    if tbo_data:
                        tbo_id = cand["tbo_id"]
                        break
        if tbo_data:
            # Find matching photo from chromadb candidates
            photo_path = next(
                (c["photo"] for c in candidates if c["tbo_id"] == tbo_id),
                None
            )
            if not photo_path:
                dest_meta = chromadb_utils.get_destination_by_id(tbo_id)
                if dest_meta and "photo" in dest_meta:
                    photo_path = dest_meta["photo"]
                else:
                    # Fallback to specific destination photos or generic placeholder
                    dest_name = tbo_data.get("destination", "")
                    photo_path = _FALLBACK_PHOTOS.get(
                        dest_name, 
                        "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?q=80&w=2670&auto=format&fit=crop" # Generic lake/boat, safer than snow
                    )
            resolved_stops.append({
                "destination": tbo_data["destination"],
                "tbo_id": tbo_id,
                "photo": photo_path,
                "price_per_person": tbo_data["price_per_person"],
                "hotels": tbo_data["hotels"],
                "flight_min_fare": tbo_data.get("flight_min_fare"),
                "tagline": tbo_data.get("tagline", ""),
                "best_season": tbo_data.get("best_season", ""),
            })

    if not resolved_stops:
        raise HTTPException(
            status_code=400,
            detail="Could not resolve any destinations within your budget.",
        )

    # 7. Build itinerary options — only include types with enough resolved stops
    #    and whose total price is ≤ budget
    itineraries = []
    for journey_type, fractions in _BUDGET_SPLITS.items():
        n_stops = len(fractions)
        if len(resolved_stops) < n_stops:
            continue  # not enough geo-compatible stops resolved

        stops_for_type = resolved_stops[:n_stops]
        per_stop_budgets = [int(budget * f) for f in fractions]

        # Recalculate realistic total: sum of cheapest hotel at each stop
        total_price = 0
        stop_data_for_type = []
        for idx, stop in enumerate(stops_for_type):
            # Scale price to per-stop budget allocated
            allocated = per_stop_budgets[idx]
            price = min(stop["price_per_person"], allocated)
            total_price += price
            stop_data_for_type.append({**stop, "price_per_person": price, "allocated_budget": allocated})

        # Hide if total price exceeds budget
        if total_price > budget:
            logger.info(f"Hiding {journey_type} itinerary: total ₹{total_price:,} > budget ₹{budget:,}")
            continue

        itineraries.append({
            "type": journey_type,
            "label": _JOURNEY_LABELS[journey_type],
            "stops": stop_data_for_type,
            "total_price": total_price,
            "region": anchor_region,
            "stop_count": n_stops,
        })

    if not itineraries:
        raise HTTPException(
            status_code=400,
            detail="No itinerary options fit within your budget. Try increasing your budget.",
        )

    # 8. Generate Gemini explanation for the best (most stops) option
    best_itinerary = itineraries[-1]  # most stops = last = best value
    try:
        explanation = gemini_utils.generate_itinerary_explanation(
            stops=best_itinerary["stops"],
            vibe_tags=vibe_tags,
        )
        # Apply the personalized narratives to all stops in all itineraries
        stop_narratives = explanation.get("stop_narratives", {})
        for it in itineraries:
            for s in it["stops"]:
                # Only override if we generated a specific narrative for this destination
                if s["destination"] in stop_narratives:
                    s["tagline"] = stop_narratives[s["destination"]]
                    
    except Exception as e:
        logger.warning(f"Gemini itinerary explanation failed (using fallback): {e}")
        stop_names = " → ".join(s["destination"] for s in best_itinerary["stops"])
        explanation = {
            "match_reasons": ["scenic journey", "diverse landscapes", "cultural richness"],
            "itinerary_narrative": f"A wonderful journey through {stop_names}.",
            "conversation_opener": f"We've found a great {best_itinerary['type']} journey for you through {stop_names}! What would you like to know?",
            "stop_narratives": {}
        }

    # 9. Create session for the best itinerary (user can start chat from any option)
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

    # 10. Return all valid itineraries + session + explanation
    return {
        "session_id": session_id,
        "itineraries": itineraries,
        "vibe_tags": vibe_tags,
        "match_reasons": explanation["match_reasons"],
        "itinerary_narrative": explanation.get("itinerary_narrative", ""),
        "conversation_opener": explanation["conversation_opener"],
        "region": anchor_region,
    }


# ─── Endpoint 2: POST /chat ───────────────────────────────────────────────────

@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Process a user chat message and return Gemini's response.
    May trigger a new destination search if the user wants a different vibe.
    """
    logger.info(f"POST /chat | session={request.session_id}")

    session = session_store.get_session(request.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Add user message to history
    session_store.add_message(request.session_id, "user", request.message)

    # Extract any preferences from user message (simple keyword extraction)
    msg_lower = request.message.lower()
    preference_keywords = {
        "beach": "prefers beach",
        "mountain": "prefers mountains",
        "snow": "prefers snowy destination",
        "heritage": "interested in heritage",
        "peaceful": "wants peaceful/quiet destination",
        "adventure": "wants adventure activities",
        "romantic": "looking for romantic destination",
        "budget": "budget-conscious",
        "luxury": "interested in luxury",
    }
    for keyword, pref in preference_keywords.items():
        if keyword in msg_lower:
            session_store.add_preference(request.session_id, pref)

    # Get fresh session state for Gemini
    session = session_store.get_session(request.session_id)

    # Generate Gemini response
    try:
        gemini_result = gemini_utils.generate_chat_response(session)
    except Exception as e:
        logger.error(f"Gemini chat failed: {e}")
        gemini_result = {
            "message": "I had a small hiccup! Could you tell me more about what vibe you're looking for in your destination?",
            "action": "ask_question",
            "updated_filters": {"must_have": [], "must_not_have": [], "vibe_adjustment": ""},
        }

    action = gemini_result.get("action", "ask_question")
    ai_message = gemini_result.get("message", "")
    updated_filters = gemini_result.get("updated_filters", {})

    # Add AI response to history
    session_store.add_message(request.session_id, "assistant", ai_message)

    updated_match = None

    # If Gemini wants to search again, run a new ChromaDB query
    if action == "search_again":
        # Mark current destination as rejected
        current_match_name = session["current_match"]
        session_store.add_rejected_destination(request.session_id, current_match_name)

        # Refresh session
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
            # Generate new match explanation
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
            # No new match found within budget — stay with current and inform user
            action = "ask_question"
            ai_message = "I couldn't find another destination within your budget that matches that preference. Would you like to adjust your budget or explore a different type of vibe?"

    elif action == "confirm_booking":
        session_store.confirm_session(request.session_id)

    return {
        "message": ai_message,
        "action": action,
        "updated_match": updated_match,
    }


# ─── Endpoint 3: POST /confirm ────────────────────────────────────────────────

@app.post("/confirm")
async def confirm_booking(request: ConfirmRequest):
    """
    Returns the final destination card for the booking screen.
    """
    logger.info(f"POST /confirm | session={request.session_id}")

    session = session_store.get_session(request.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    session_store.confirm_session(request.session_id)

    return {
        "matched_destination": session["current_match"],
        "destination_photo": session["current_photo"],
        "price_per_person": session["current_price"],
        "hotels": session["current_hotels"],
        "match_reasons": session.get("match_reasons", []),
        "travel_dates": session.get("travel_dates"),
        "budget": session["budget"],
    }


# ─── Endpoint 4: GET /health ──────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    try:
        count = chromadb_utils.get_collection_count()
        return {"status": "ok", "destinations_loaded": count}
    except Exception as e:
        return {"status": "ok", "destinations_loaded": 0, "note": str(e)}


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
