"""
gemini_utils.py — All Gemini API interactions for VibeTravel.
Handles match explanation generation, conversation management,
NLP query parsing, and structured itinerary modification via chat.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

from google import genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.0-flash"
_gemini_client: genai.Client | None = None

def get_gemini_model() -> genai.Client:
    """Initialise Gemini API client once."""
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        _gemini_client = genai.Client(api_key=api_key)
        logger.info(f"Gemini client initialized. Targeting '{GEMINI_MODEL}'")
    return _gemini_client


def _extract_json(text: str) -> dict:
    """Extract JSON from Gemini's response, handling markdown code blocks."""
    code_block = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if code_block:
        text = code_block.group(1).strip()
    else:
        text = text.strip()

    json_start = text.find("{")
    json_end = text.rfind("}") + 1
    if json_start != -1 and json_end > json_start:
        text = text[json_start:json_end]

    return json.loads(text)


def _retry_gemini(prompt: str, max_attempts: int = 2) -> str:
    """Call Gemini with automatic 429 retry. Returns raw text."""
    client = get_gemini_model()
    for attempt in range(max_attempts):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )
            return response.text
        except Exception as e:
            err_str = str(e)
            if "429" in err_str and attempt == 0:
                logger.warning("Gemini 429 rate limit — retrying immediately...")
                continue
            raise
    raise RuntimeError("Gemini failed after retries")


# ── NLP Query Parser ──────────────────────────────────────────────────────────

def parse_search_query(query: str) -> dict[str, Any]:
    """
    Parse a natural language travel query into structured search parameters.

    Example: "5 days in Rajasthan under 20k" →
      { budget: 20000, duration_days: 5, region: "Rajasthan", vibes: [], destinations: [] }

    Returns a dict with keys: budget, duration_days, region, vibes, destinations, raw_query.
    Always returns a usable dict even on Gemini failure (graceful fallback).
    """
    prompt = f"""Parse this travel search query into structured JSON. Extract whatever information is available.

Query: "{query}"

Return ONLY this JSON (no extra text):
{{
  "budget": <integer in INR, null if not mentioned>,
  "duration_days": <integer, null if not mentioned>,
  "region": "<region name e.g. Rajasthan, Goa, Kerala, null if not mentioned>",
  "destinations": [<list of specific city/place names mentioned, empty list if none>],
  "vibes": [<list of vibe keywords: beach, mountain, adventure, luxury, budget, heritage, nature, spiritual, romantic, family, solo, empty list if none>],
  "travel_month": "<month name in English, null if not mentioned>",
  "origin_city": "<city the user is travelling from, null if not mentioned>"
}}

Rules:
- Budget: convert "20k" → 20000, "1 lakh" → 100000, "2.5L" → 250000
- Duration: "5 days" → 5, "a week" → 7, "10 nights" → 10
- Be generous in extracting vibes from context words (e.g. "historic" → heritage, "luxury resort" → luxury)
"""

    try:
        raw = _retry_gemini(prompt)
        result = _extract_json(raw)
        return {
            "budget": result.get("budget"),
            "duration_days": result.get("duration_days"),
            "region": result.get("region"),
            "destinations": result.get("destinations", []),
            "vibes": result.get("vibes", []),
            "travel_month": result.get("travel_month"),
            "origin_city": result.get("origin_city"),
            "raw_query": query,
        }
    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            logger.warning("[Gemini Quota Exceeded] Unable to parse search query via LLM. Using fallback.")
        else:
            logger.warning(f"NLP query parse failed, using fallback: {err_str[:200]}...")
        return {
            "budget": None,
            "duration_days": None,
            "region": None,
            "destinations": [],
            "vibes": [],
            "travel_month": None,
            "origin_city": None,
            "raw_query": query,
        }


# ── Match Explanation ─────────────────────────────────────────────────────────

def generate_match_explanation(
    destination_name: str,
    vibe_tags: list[str],
) -> dict[str, Any]:
    """Generate match reasons and conversation opener for a single-destination match."""
    prompt = f"""A user has uploaded a travel inspiration photo matched to {destination_name}.
The photo appears to show: {", ".join(vibe_tags)}.

Return a JSON with exactly this structure and nothing else:
{{
  "match_reasons": ["reason 1", "reason 2", "reason 3"],
  "conversation_opener": "A single natural sentence that acknowledges the user's photo vibe and asks one opening question"
}}

Keep each match reason to 3-5 words. Keep the conversation opener to one sentence. Be warm and specific."""

    try:
        raw = _retry_gemini(prompt)
        result = _extract_json(raw)
        return {
            "match_reasons": result.get("match_reasons", ["scenic location", "beautiful atmosphere", "popular destination"]),
            "conversation_opener": result.get("conversation_opener", f"Your photo matched {destination_name}! What aspect excites you most?"),
        }
    except Exception as e:
        logger.warning(f"Gemini match explanation failed: {e}")
        return {
            "match_reasons": [vibe_tags[0] if vibe_tags else "scenic", "beautiful landscape", "unique atmosphere"],
            "conversation_opener": f"Your photo has a wonderful vibe that matches {destination_name}! Shall we explore it together?",
        }


# ── Itinerary Explanation ─────────────────────────────────────────────────────

def generate_itinerary_explanation(
    stops: list[dict],
    vibe_tags: list[str],
) -> dict[str, Any]:
    """Generate match reasons and a conversation opener for a multi-stop itinerary."""
    stop_names = [s["destination"] for s in stops]
    stop_list_str = " → ".join(stop_names)
    n = len(stops)

    prompt = f"""A user uploaded a travel inspiration photo. Based on its visual style ({', '.join(vibe_tags)}), we matched them with a {n}-stop Indian itinerary: {stop_list_str}.

Return ONLY this JSON (no extra text):
{{
  "match_reasons": ["3–5 word reason 1", "3–5 word reason 2", "3–5 word reason 3"],
  "itinerary_narrative": "One warm, evocative sentence describing the full journey arc.",
  "conversation_opener": "One friendly sentence acknowledging the photo vibe and kicking off a chat about the itinerary.",
  "stop_narratives": {{
{",".join([f'    "{name}": "One short, highly specific, evocative sentence explaining why this stop fits the vibe"' for name in stop_names])}
  }},
  "stop_itineraries": {{
{",".join([f'    "{name}": [{{ "day": 1, "title": "Day 1 Concept", "description": "1 sentence" }}, {{ "day": 2, "title": "Day 2 Concept", "description": "1 sentence" }}, {{ "day": 3, "title": "Day 3 Concept", "description": "1 sentence" }}]' for name in stop_names])}
  }}
}}"""

    try:
        raw = _retry_gemini(prompt)
        result = _extract_json(raw)
        return {
            "match_reasons": result.get("match_reasons", ["scenic journey", "diverse landscapes", "cultural richness"]),
            "itinerary_narrative": result.get("itinerary_narrative", f"A beautiful journey through {stop_list_str}."),
            "conversation_opener": result.get("conversation_opener", f"Your photo perfectly matches a {n}-stop journey through {stop_list_str}! Which stop excites you most?"),
            "stop_narratives": result.get("stop_narratives", {}),
            "stop_itineraries": result.get("stop_itineraries", {}),
        }
    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            logger.warning(f"[Gemini Quota Exceeded] Unable to generate itinerary narrative. Using fallback.")
        else:
            logger.warning(f"Gemini itinerary explanation failed: {err_str[:200]}...")
            
        fallback_itineraries = {}
        for name in stop_names:
            fallback_itineraries[name] = [
                {"day": 1, "title": "Arrival & Exploration", "description": f"Settle into {name} and explore local highlights."},
                {"day": 2, "title": "Immersive Vibe", "description": f"Dive deep into the {vibe_tags[0] if vibe_tags else 'local'} culture."},
                {"day": 3, "title": "Relax & Depart", "description": "Enjoy a slow morning before continuing your journey."},
            ]
        return {
            "match_reasons": ["scenic journey", "diverse landscapes", "cultural richness"],
            "itinerary_narrative": f"An unforgettable journey through {stop_list_str}.",
            "conversation_opener": f"We've designed a stunning {n}-stop journey through {stop_list_str}! What would you like to know first?",
            "stop_narratives": {},
            "stop_itineraries": fallback_itineraries,
        }


# ── Chat Response ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = """You are an open, friendly, and completely unconstrained AI conversationalist. You are currently chatting with a user who happens to be looking at a travel app, but your primary goal is to just chat with them about WHATEVER they want.

CONVERSATION RULES:
1. You MUST reply naturally to whatever the user says. If they say "hi", say "hello there!". If they ask a joke, tell a joke. If they ask about quantum physics, explain it.
2. DO NOT force the conversation back to travel. DO NOT act like a customer service agent. DO NOT say "I want to help find the perfect destination". Just be a cool AI to chat with.
3. Only talk about their trip IF THEY SPECIFICALLY ASK ABOUT IT.
4. Keep your answers brief, human-like, and conversational (1-3 sentences unless they ask for detail).
5. NEVER repeat yourself. Every response must be new.

YOU ARE TALKING TO A USER WHO HAS CHOSEN THIS ITINERARY:
- Destination: {itinerary_summary}
- Budget: ₹{budget:,} total
- Trip: {duration_days} days | {stop_count} stop(s)
- Vibes: {vibe_tags}
- Type: {itinerary_label}

STOP DETAILS:
{itinerary_stops_detail}

LOGISTICS:
- Transport: {transport_modes}
- Days per stop: {days_per_stop}
- Not interested in: {rejected_destinations}
- User preferences: {user_preferences}

THE LAST USER MESSAGE WAS: "{last_user_message}"

FULL CONVERSATION SO FAR:
{conversation_history}

ACTIONS YOU CAN TRIGGER:
- "search_again": User wants completely different destinations
- "reorder_stops": User wants stops in different order (params: new_order as list of destination names)  
- "change_transport": Change how they travel (params: leg_index: int, mode: flight/train/bus/drive)
- "adjust_days": Change days at a stop (params: stop_index: int, days: int)
- "confirm_booking": User is ready to book

RESPOND AS VALID JSON ONLY:
{{
  "message": "A direct, specific answer to the user's LAST message — different from anything you said before",
  "action": "ask_question",
  "params": {{}},
  "updated_filters": {{
    "must_have": [],
    "must_not_have": [],
    "vibe_adjustment": ""
  }}
}}

action must be exactly one of: "ask_question", "search_again", "reorder_stops", "change_transport", "adjust_days", "confirm_booking".
"""


def generate_chat_response(session: dict) -> dict[str, Any]:
    """Generate the next chat response from Gemini for a conversation turn."""
    convo_lines = []
    last_user_message = ""
    for msg in session.get("conversation_history", []):
        role = "Assistant" if msg["role"] == "assistant" else "User"
        convo_lines.append(f"{role}: {msg['content']}")
        if msg["role"] == "user":
            last_user_message = msg["content"]
    conversation_history = "\n".join(convo_lines) if convo_lines else "[No conversation yet]"

    rejected = session.get("rejected_destinations", [])
    prefs = session.get("user_preferences", [])

    try:
        budget_val = int(session.get("budget", 0))
    except (ValueError, TypeError):
        budget_val = 0

    itinerary_stops = session.get("itinerary_stops", [])
    if not itinerary_stops:
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

    transport_modes = session.get("leg_transport_modes", {})
    days_per_stop = session.get("days_per_stop", {})
    duration_days = session.get("duration_days") or (sum(days_per_stop.values()) if days_per_stop else stop_count * 2)

    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        budget=budget_val,
        vibe_tags=", ".join(session.get("vibe_tags", [])),
        stop_count=stop_count,
        itinerary_summary=itinerary_summary,
        itinerary_label=session.get("itinerary_label", "Quick Escape"),
        duration_days=duration_days,
        itinerary_stops_detail=itinerary_stops_detail,
        transport_modes=str(transport_modes),
        days_per_stop=str(days_per_stop),
        rejected_destinations=", ".join(rejected) if rejected else "None",
        user_preferences=", ".join(prefs) if prefs else "None specified yet",
        conversation_history=conversation_history,
        last_user_message=last_user_message or "[No message yet — opening conversation]",
    )

    try:
        raw = _retry_gemini(prompt)
        logger.info(f"Raw Gemini Output: {raw}")
        result = _extract_json(raw)
        msg = result.get("message", "").strip()
        if not msg:
            msg = "I'm here! Could you tell me more about what vibe you're looking for?"
            
        return {
            "message": msg,
            "action": result.get("action", "ask_question"),
            "params": result.get("params", {}),
            "updated_filters": result.get("updated_filters", {
                "must_have": [],
                "must_not_have": [],
                "vibe_adjustment": "",
            }),
        }
    except Exception as e:
        
        err_str = str(e)
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            logger.warning("[Gemini Quota Exceeded] Unable to generate dynamic chat response. Using fallback.")
            msg = "I'm receiving too many requests right now and hit my API rate limit! Please wait a minute and try asking again."
        else:
            logger.warning(f"Generating chat response failed: {err_str[:200]}...")
            msg = "I want to help find the perfect destination for you. Could you tell me what's most important — the landscape, the activities, or the overall vibe?"

        return {
            "message": msg,
            "action": "ask_question",
            "params": {},
            "updated_filters": {"must_have": [], "must_not_have": [], "vibe_adjustment": ""},
        }


# ── Route Justification ───────────────────────────────────────────────────────

def generate_route_justification(stops: list[dict], region: str) -> str:
    """One-paragraph AI explanation of why stops are ordered this way."""
    if not stops:
        return ""
    if len(stops) == 1:
        return f"{stops[0].get('destination', '')} is perfectly chosen for your travel style."

    stop_names = [s.get("destination", "?") for s in stops]
    route_str = " → ".join(stop_names)

    prompt = f"""In exactly 2 sentences, explain why this Indian travel route is geographically smart and enjoyable: {route_str} (all within {region}).

Be specific about geography (not generic). Mention why the order makes sense for minimising backtracking or maximising experiences. Do NOT use bullet points or headers. Just 2 plain sentences."""

    try:
        return _retry_gemini(prompt).strip()
    except Exception as e:
        logger.warning(f"Route justification failed: {e}")
        return (
            f"Your route ({route_str}) has been optimised for geographic proximity within {region}. "
            "This circuit minimises travel time between stops, leaving more days for exploration."
        )
