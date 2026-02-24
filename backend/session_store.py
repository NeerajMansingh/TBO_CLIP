"""
session_store.py — In-memory session state management.
No database required — all state lives in a Python dictionary for the hackathon.
"""

from __future__ import annotations

import uuid
from typing import Optional


# Global session storage: {session_id: session_dict}
_sessions: dict[str, dict] = {}


def create_session(
    original_embedding: list[float],
    budget: int,
    budget_tier: str,
    travel_dates: Optional[str],
    current_match: str,
    current_tbo_id: str,
    current_price: int,
    current_hotels: list[dict],
    current_photo: str,
    match_reasons: list[str],
    conversation_opener: str,
    vibe_tags: list[str],
) -> str:
    """
    Create a new session and return its ID.

    Args:
        original_embedding: CLIP vector of the user's uploaded photo
        budget: User budget in INR
        budget_tier: 'budget', 'mid-range', or 'premium'
        travel_dates: Travel date string (or None)
        current_match: Name of the initially matched destination
        current_tbo_id: TBO ID of the initial match
        current_price: Price per person of the initial match
        current_hotels: List of hotel dicts for the initial match
        current_photo: Relative path to the destination hero photo
        match_reasons: List of 3 reason strings
        conversation_opener: First AI message in chat
        vibe_tags: Top vibe keywords from CLIP zero-shot classification

    Returns:
        New session ID string
    """
    session_id = str(uuid.uuid4())[:8]  # Short IDs for demo friendliness

    _sessions[session_id] = {
        "original_embedding": original_embedding,
        "budget": budget,
        "budget_tier": budget_tier,
        "travel_dates": travel_dates,
        "current_match": current_match,
        "current_tbo_id": current_tbo_id,
        "current_price": current_price,
        "current_hotels": current_hotels,
        "current_photo": current_photo,
        "match_reasons": match_reasons,
        "vibe_tags": vibe_tags,
        "rejected_destinations": [],
        "user_preferences": [],
        "conversation_history": [
            {"role": "assistant", "content": conversation_opener}
        ],
        "confirmed": False,
    }

    return session_id


def get_session(session_id: str) -> Optional[dict]:
    """Retrieve session by ID. Returns None if not found."""
    return _sessions.get(session_id)


def add_message(session_id: str, role: str, content: str) -> None:
    """
    Append a message to the conversation history.

    Args:
        session_id: Session identifier
        role: 'user' or 'assistant'
        content: Message text
    """
    session = _sessions.get(session_id)
    if session:
        session["conversation_history"].append({"role": role, "content": content})


def update_match(
    session_id: str,
    new_match: str,
    new_tbo_id: str,
    new_price: int,
    new_hotels: list[dict],
    new_photo: str,
    new_match_reasons: list[str],
) -> None:
    """Update the current matched destination in a session."""
    session = _sessions.get(session_id)
    if session:
        session["current_match"] = new_match
        session["current_tbo_id"] = new_tbo_id
        session["current_price"] = new_price
        session["current_hotels"] = new_hotels
        session["current_photo"] = new_photo
        session["match_reasons"] = new_match_reasons


def add_rejected_destination(session_id: str, destination_name: str) -> None:
    """Mark a destination as rejected so it won't be returned again."""
    session = _sessions.get(session_id)
    if session and destination_name not in session["rejected_destinations"]:
        session["rejected_destinations"].append(destination_name)


def add_preference(session_id: str, preference: str) -> None:
    """Add a user preference string to the session."""
    session = _sessions.get(session_id)
    if session and preference not in session["user_preferences"]:
        session["user_preferences"].append(preference)


def confirm_session(session_id: str) -> None:
    """Mark a session as confirmed/booked."""
    session = _sessions.get(session_id)
    if session:
        session["confirmed"] = True


def list_active_sessions() -> list[str]:
    """Return all active session IDs."""
    return list(_sessions.keys())
