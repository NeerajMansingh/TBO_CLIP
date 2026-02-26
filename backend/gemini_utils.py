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


SYSTEM_PROMPT_TEMPLATE = """You are a travel assistant for VibeTravel. Your job is to help the user learn about their matched destination ({current_match}) and the hotels available.

Rules you must always follow:
1. Be extremely helpful and conversational. Answer the user's questions about the destination or the specific hotels we found.
2. Keep your responses engaging but concise (under 4 sentences usually). Do not ramble.
3. You CAN and SHOULD discuss the hotels, prices, and features from the session state below to convince them to book.
4. When the user says they don't like {current_match} and want a different vibe, return the action "search_again" and specify what changed in updated_filters.
5. When the user is ready to finalize the booking for {current_match}, return the action "confirm_booking".

Current session state:
- User total budget: ₹{budget:,}
- Original photo vibe summary: {vibe_tags}
- Current matched destination: {current_match}
- Hotels found in budget:
{current_hotels}
- Destinations already rejected or ruled out: {rejected_destinations}
- User preferences expressed so far: {user_preferences}
- Conversation so far:
{conversation_history}

Respond in the following JSON format every time, and return ONLY this JSON with no extra text:
{{
  "message": "Your helpful, conversational response",
  "action": "ask_question",
  "updated_filters": {{
    "must_have": [],
    "must_not_have": [],
    "vibe_adjustment": "description of new vibe if search_again"
  }}
}}

The action field must be exactly ONE of: "ask_question", "search_again", "confirm_booking". Use "ask_question" for normal conversation.
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

    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        budget=budget_val,
        vibe_tags=", ".join(session.get("vibe_tags", [])),
        current_match=session.get("current_match", "Unknown"),
        current_hotels=json.dumps(session.get("hotels", []), indent=2),
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
