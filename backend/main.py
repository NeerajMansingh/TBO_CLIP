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
from fake_tbo import get_budget_tier, get_tbo_data

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


# ─── Endpoint 1: POST /match ──────────────────────────────────────────────────

@app.post("/match")
async def match_destination(
    photo: UploadFile = File(...),
    budget: int = Form(...),
    travel_dates: Optional[str] = Form(None),
):
    """
    Called when user clicks 'Find My Match'.
    Runs CLIP → ChromaDB → TBO → Gemini and returns match + conversation opener.
    """
    logger.info(f"POST /match | budget={budget} | filename={photo.filename}")

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

    # 2. Determine budget tier
    budget_tier = get_budget_tier(budget)

    # 3–6. Find best matching destination
    match = await find_best_match_async(
        query_embedding=user_embedding,
        budget=budget,
        budget_tier=budget_tier,
        exclude_names=[],
        n_candidates=5,
    )

    if match is None:
        raise HTTPException(
            status_code=400,
            detail="We couldn't find a live TBO hotel match for that budget right now. (Make sure your TBO credentials in .env are correct!)",
        )

    # 7. Get vibe tags via zero-shot CLIP classification
    vibe_tags = clip_utils.get_image_vibes(pil_image)

    # 8. Call Gemini to generate match explanation and conversation opener
    try:
        explanation = gemini_utils.generate_match_explanation(
            destination_name=match["destination"],
            vibe_tags=vibe_tags,
        )
    except Exception as e:
        logger.warning(f"Gemini explanation failed (using fallback): {e}")
        explanation = {
            "match_reasons": [vibe_tags[0] if vibe_tags else "scenic", "beautiful landscape", "unique atmosphere"],
            "conversation_opener": f"Your photo matched wonderfully with {match['destination']}! Is the landscape the most important factor for you, or more the cultural atmosphere?",
        }

    # 9. Create session
    session_id = session_store.create_session(
        original_embedding=user_embedding,
        budget=budget,
        budget_tier=budget_tier,
        travel_dates=travel_dates,
        current_match=match["destination"],
        current_tbo_id=match["tbo_id"],
        current_price=match["price_per_person"],
        current_hotels=match["hotels"],
        current_photo=match["photo"],
        match_reasons=explanation["match_reasons"],
        conversation_opener=explanation["conversation_opener"],
        vibe_tags=vibe_tags,
    )

    # 10. Return response
    return {
        "session_id": session_id,
        "matched_destination": match["destination"],
        "destination_photo": match["photo"],
        "tbo_id": match["tbo_id"],
        "price_per_person": match["price_per_person"],
        "similarity_score": match.get("similarity_score", 0.0),
        "hotels": match["hotels"],
        "flight_min_fare": match.get("flight_min_fare"),  # real TBO fare in INR
        "match_reasons": explanation["match_reasons"],
        "conversation_opener": explanation["conversation_opener"],
        "tagline": match.get("tagline", ""),
        "best_season": match.get("best_season", ""),
        "vibe_tags": vibe_tags,
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
