"""
session_store.py — In-memory session state management.
No database required — all state lives in a Python dictionary.

Upgraded to support itinerary edit history, day allocation per stop,
and transport modes per leg.
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
    itinerary_stops: Optional[list[dict]] = None,
    itinerary_type: Optional[str] = None,
    itinerary_label: Optional[str] = None,
    itinerary_region: Optional[str] = None,
    itinerary_total_price: Optional[int] = None,
    duration_days: Optional[int] = None,
) -> str:
    """
    Create a new session and return its ID.

    Returns:
        New session ID string
    """
    session_id = str(uuid.uuid4())[:8]  # Short IDs for demo friendliness

    n_stops = len(itinerary_stops) if itinerary_stops else 1

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
        # Itinerary fields
        "itinerary_stops": itinerary_stops or [],
        "itinerary_type": itinerary_type or "1-stop",
        "itinerary_label": itinerary_label or "Quick Escape",
        "itinerary_region": itinerary_region or "",
        "itinerary_total_price": itinerary_total_price or current_price,
        # New: per-leg metadata
        "leg_transport_modes": {i: "flight" for i in range(n_stops)},
        "days_per_stop": {i: 2 for i in range(n_stops)},
        "duration_days": duration_days,
        # Edit history for undo / audit trail
        "edit_history": [],
    }

    return session_id


def get_session(session_id: str) -> Optional[dict]:
    """Retrieve session by ID. Returns None if not found."""
    return _sessions.get(session_id)


def add_message(session_id: str, role: str, content: str) -> None:
    """Append a message to the conversation history."""
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


def update_itinerary(
    session_id: str,
    new_stops: list[dict],
    itinerary_type: str,
    itinerary_label: str,
    itinerary_region: str,
    itinerary_total_price: int,
) -> None:
    """Replace the full itinerary stops for a session."""
    session = _sessions.get(session_id)
    if session:
        session["itinerary_stops"] = new_stops
        session["itinerary_type"] = itinerary_type
        session["itinerary_label"] = itinerary_label
        session["itinerary_region"] = itinerary_region
        session["itinerary_total_price"] = itinerary_total_price
        # Reset per-leg metadata
        n = len(new_stops)
        session["leg_transport_modes"] = {i: "flight" for i in range(n)}
        session["days_per_stop"] = {i: 2 for i in range(n)}
        # Keep backward-compat fields pointed at stop 1
        if new_stops:
            s = new_stops[0]
            session["current_match"] = s.get("destination", session["current_match"])
            session["current_tbo_id"] = s.get("tbo_id", session["current_tbo_id"])
            session["current_price"] = s.get("price_per_person", session["current_price"])
            session["current_hotels"] = s.get("hotels", session["current_hotels"])
            session["current_photo"] = s.get("photo", session["current_photo"])


def update_leg(
    session_id: str,
    leg_index: int,
    transport_mode: Optional[str] = None,
    days_at_stop: Optional[int] = None,
) -> None:
    """Update transport mode or day count for a specific leg/stop."""
    session = _sessions.get(session_id)
    if session:
        if transport_mode is not None:
            session["leg_transport_modes"][leg_index] = transport_mode.lower()
        if days_at_stop is not None:
            session["days_per_stop"][leg_index] = days_at_stop


def reorder_stops(session_id: str, new_order: list[str]) -> None:
    """
    Reorder session itinerary stops by destination name list.
    new_order: list of destination names in the desired order.
    """
    session = _sessions.get(session_id)
    if not session:
        return

    current = session.get("itinerary_stops", [])
    name_to_stop = {s.get("destination", "").lower(): s for s in current}
    reordered = [name_to_stop[n.lower()] for n in new_order if n.lower() in name_to_stop]

    record_edit(session_id, "reorder_stops", {
        "old_order": [s.get("destination") for s in current],
        "new_order": new_order,
    })

    session["itinerary_stops"] = reordered
    # Reset leg metadata for new order
    n = len(reordered)
    session["leg_transport_modes"] = {i: "flight" for i in range(n)}
    session["days_per_stop"] = {i: 2 for i in range(n)}


def record_edit(session_id: str, edit_type: str, params: dict) -> None:
    """Record an edit to the session's edit history."""
    session = _sessions.get(session_id)
    if session:
        session["edit_history"].append({"type": edit_type, "params": params})


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
