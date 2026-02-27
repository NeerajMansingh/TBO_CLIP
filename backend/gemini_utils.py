"""
gemini_utils.py — All Gemini API interactions for VibeTravel.
Handles match explanation generation and conversation management.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-flash"
_gemini_client: genai.GenerativeModel | None = None


def get_gemini_model() -> genai.GenerativeModel:
    """Initialise Gemini API client once."""
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        genai.configure(api_key=api_key)
        _gemini_client = genai.GenerativeModel(GEMINI_MODEL)
        logger.info(f"Gemini model '{GEMINI_MODEL}' initialised")
    return _gemini_client


def _extract_json(text: str) -> dict:
    """
    Extract JSON from Gemini's response, handling markdown code blocks.
    """
    # Try to strip markdown code fences
    code_block = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if code_block:
        text = code_block.group(1).strip()
    else:
        text = text.strip()

    # Handle cases where Gemini wraps in extra text
    json_start = text.find("{")
    json_end = text.rfind("}") + 1
    if json_start != -1 and json_end > json_start:
        text = text[json_start:json_end]

    return json.loads(text)


def generate_match_explanation(
    destination_name: str,
    vibe_tags: list[str],
) -> dict[str, Any]:
    """
    Generate match reasons and conversation opener for the initial /match response.
    Retries once on 429 rate-limit errors (waits 35s as suggested by Gemini).
    """
    model = get_gemini_model()

    prompt = f"""A user has uploaded a travel inspiration photo. Based on the visual characteristics of the photo, it has been matched to {destination_name}.

The photo appears to show: {", ".join(vibe_tags)}.

Return a JSON with exactly this structure and nothing else:
{{
  "match_reasons": ["reason 1", "reason 2", "reason 3"],
  "conversation_opener": "A single natural sentence that acknowledges the user's photo vibe and asks one opening question to start the conversation"
}}

Keep each match reason to 3-5 words. Keep the conversation opener to one sentence maximum. Be warm and specific about the destination."""

    for attempt in range(2):  # try twice: once fresh, once after 429 retry
        try:
            response = model.generate_content(prompt)
            raw_text = response.text
            result = _extract_json(raw_text)
            return {
                "match_reasons": result.get("match_reasons", ["scenic location", "beautiful atmosphere", "popular destination"]),
                "conversation_opener": result.get("conversation_opener", f"Your photo matched {destination_name}! What aspect of the destination excites you most?"),
            }
        except Exception as e:
            err_str = str(e)
            if "429" in err_str and attempt == 0:
                logger.warning("Gemini 429 rate limit hit — waiting 35s before retry...")
                time.sleep(35)
                continue
            logger.warning(f"Gemini match explanation failed: {e}")
            break

    return {
        "match_reasons": [vibe_tags[0] if vibe_tags else "scenic", "beautiful landscape", "unique atmosphere"],
        "conversation_opener": f"Your photo has a wonderful vibe that matches {destination_name}! Is the visual feel of the landscape the most important factor for you?",
    }


def generate_itinerary_explanation(
    stops: list[dict],
    vibe_tags: list[str],
) -> dict[str, Any]:
    """
    Generate match reasons and a conversation opener for a multi-stop itinerary.
    stops: list of dicts with 'destination' key.
    """
    model = get_gemini_model()
    stop_names = [s["destination"] for s in stops]
    stop_list_str = " → ".join(stop_names)
    n = len(stops)

    prompt = f"""A user uploaded a travel inspiration photo. Based on its visual style ({', '.join(vibe_tags)}), we matched them with a {n}-stop Indian itinerary: {stop_list_str}.

Return ONLY this JSON (no extra text):
{{
  "match_reasons": ["3–5 word reason 1", "3–5 word reason 2", "3–5 word reason 3"],
  "itinerary_narrative": "One warm, evocative sentence describing the full journey arc (e.g. 'Start with the beaches of Goa, then lose yourself in Hampi's ruins, before unwinding in Mysore's royal gardens.')",
  "conversation_opener": "One friendly sentence acknowledging the photo vibe and kicking off a chat about the itinerary.",
  "stop_narratives": {{
{",".join([f'    "{name}": "One short, highly specific, and evocative sentence explaining why this specific stop fits the requested vibe"' for name in stop_names])}
  }},
  "stop_itineraries": {{
{",".join([f'    "{name}": [{{ "day": 1, "title": "Day 1 Concept", "description": "1 sentence" }}, {{ "day": 2, "title": "Day 2 Concept", "description": "1 sentence" }}, {{ "day": 3, "title": "Day 3 Concept", "description": "1 sentence" }}]' for name in stop_names])}
  }}
}}"""

    for attempt in range(2):
        try:
            response = model.generate_content(prompt)
            result = _extract_json(response.text)
            return {
                "match_reasons": result.get("match_reasons", ["scenic journey", "diverse landscapes", "cultural richness"]),
                "itinerary_narrative": result.get("itinerary_narrative", f"A beautiful journey through {stop_list_str}."),
                "conversation_opener": result.get("conversation_opener", f"Your photo perfectly matches a {n}-stop journey through {stop_list_str}! Which stop excites you most?"),
                "stop_narratives": result.get("stop_narratives", {}),
                "stop_itineraries": result.get("stop_itineraries", {})
            }
        except Exception as e:
            err_str = str(e)
            if "429" in err_str and attempt == 0:
                logger.warning("Gemini 429 rate limit — waiting 35s...")
                import time; time.sleep(35)
                continue
            logger.warning(f"Gemini itinerary explanation failed: {e}")
            break

    # Fallback response when rate limit or API fails completely
    fallback_itineraries = {}
    for name in stop_names:
        fallback_itineraries[name] = [
            {"day": 1, "title": "Arrival & Exploration", "description": f"Settle into {name} and explore local highlights."},
            {"day": 2, "title": "Immersive Vibe", "description": f"Dive deep into the {vibe_tags[0] if vibe_tags else 'local'} culture and landscapes."},
            {"day": 3, "title": "Relax & Depart", "description": "Enjoy a slow morning before continuing your journey."}
        ]

    return {
        "match_reasons": ["scenic journey", "diverse landscapes", "cultural richness"],
        "itinerary_narrative": f"An unforgettable journey through {stop_list_str}.",
        "conversation_opener": f"We've designed a stunning {n}-stop journey for you through {stop_list_str}! What would you like to know first?",
        "stop_narratives": {},
        "stop_itineraries": fallback_itineraries,
    }


SYSTEM_PROMPT_TEMPLATE = """You are a travel assistant for VibeTravel. You are helping the user plan their trip.

Rules:
1. Be helpful, warm, and conversational. Keep responses under 4 sentences.
2. The user has a {stop_count}-stop itinerary: {itinerary_summary}. Discuss all stops when relevant.
3. You CAN discuss hotels, prices, and features from the session state to convince them to book.
4. If the user dislikes the itinerary, return action "search_again" with updated_filters.
5. When the user is ready to book, return action "confirm_booking".

Session state:
- Budget: ₹{budget:,}
- Photo vibe: {vibe_tags}
- Itinerary type: {itinerary_label} ({itinerary_type})
- Itinerary stops:
{itinerary_stops_detail}
- Rejected destinations: {rejected_destinations}
- Preferences: {user_preferences}
- Conversation:
{conversation_history}

Respond ONLY as JSON:
{{
  "message": "Your helpful response",
  "action": "ask_question",
  "updated_filters": {{
    "must_have": [],
    "must_not_have": [],
    "vibe_adjustment": ""
  }}
}}

action must be exactly one of: "ask_question", "search_again", "confirm_booking".
"""


def generate_chat_response(session: dict) -> dict[str, Any]:
    """
    Generate the next chat response from Gemini for a conversation turn.
    Retries once on 429 rate-limit errors.
    """
    model = get_gemini_model()

    convo_lines = []
    for msg in session.get("conversation_history", []):
        role = "Assistant" if msg["role"] == "assistant" else "User"
        convo_lines.append(f"{role}: {msg['content']}")
    conversation_history = "\n".join(convo_lines) if convo_lines else "[No conversation yet]"

    rejected = session.get("rejected_destinations", [])
    prefs = session.get("user_preferences", [])

    try:
        budget_val = int(session.get('budget', 0))
    except (ValueError, TypeError):
        budget_val = 0

    # Build itinerary-aware context
    itinerary_stops = session.get("itinerary_stops", [])
    if not itinerary_stops:
        # Backward-compat: wrap single match as a 1-stop itinerary
        itinerary_stops = [{
            "destination": session.get("current_match", "Unknown"),
            "hotels": session.get("current_hotels", []),
            "price_per_person": session.get("current_price", 0),
        }]

    stop_count = len(itinerary_stops)
    itinerary_summary = " → ".join(s.get("destination", "?") for s in itinerary_stops)

    stop_lines = []
    for i, s in enumerate(itinerary_stops, 1):
        hotels_brief = "; ".join(
            f"{h.get('name','?')} (₹{h.get('price_per_night',0):,.0f}/night)"
            for h in s.get("hotels", [])[:2]
        )
        stop_lines.append(
            f"  Stop {i}: {s.get('destination','?')} | ₹{s.get('price_per_person',0):,} | Hotels: {hotels_brief or 'TBD'}"
        )
    itinerary_stops_detail = "\n".join(stop_lines) or "  No stops available."

    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        budget=budget_val,
        vibe_tags=", ".join(session.get("vibe_tags", [])),
        stop_count=stop_count,
        itinerary_summary=itinerary_summary,
        itinerary_label=session.get("itinerary_label", "Quick Escape"),
        itinerary_type=session.get("itinerary_type", "1-stop"),
        itinerary_stops_detail=itinerary_stops_detail,
        rejected_destinations=", ".join(rejected) if rejected else "None",
        user_preferences=", ".join(prefs) if prefs else "None specified yet",
        conversation_history=conversation_history,
    )

    for attempt in range(2):
        try:
            response = model.generate_content(prompt)
            raw_text = response.text
            result = _extract_json(raw_text)
            return {
                "message": result.get("message", "I'd love to help you find the perfect destination! What's most important to you?"),
                "action": result.get("action", "ask_question"),
                "updated_filters": result.get("updated_filters", {
                    "must_have": [],
                    "must_not_have": [],
                    "vibe_adjustment": "",
                }),
            }
        except Exception as e:
            err_str = str(e)
            if "429" in err_str and attempt == 0:
                logger.warning("Gemini 429 rate limit hit — waiting 35s before retry...")
                time.sleep(35)
                continue
            logger.warning(f"Gemini chat response failed: {e}")
            break

    return {
        "message": "I want to make sure I find the perfect destination for you. Could you tell me what's most important — the type of landscape, the activities, or the overall vibe?",
        "action": "ask_question",
        "updated_filters": {"must_have": [], "must_not_have": [], "vibe_adjustment": ""},
    }
