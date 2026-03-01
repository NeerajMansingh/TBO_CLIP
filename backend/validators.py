"""
validators.py — Centralized input validation for all API endpoints.

All validators raise HTTPException directly so they can be called
inside endpoint functions without additional try/except blocks.
"""

from __future__ import annotations

from typing import Any, List, Optional

from fastapi import HTTPException


def validate_search_request(
    query: Optional[str],
    budget: int,
    duration_days: Optional[int],
) -> None:
    """
    Validate a text-based search request.

    Raises:
        HTTPException(422): On invalid input with descriptive detail.
    """
    errors = []

    if not query and budget <= 0:
        errors.append("Either a search query or a valid budget is required.")

    if query is not None:
        if len(query.strip()) == 0 or query == "Weekend trip in India":
            errors.append("Search query cannot be empty.")
        if len(query) > 500:
            errors.append("Search query is too long (max 500 characters).")

    if budget is not None and budget < 0:
        errors.append("Budget must be a non-negative number.")

    if budget is not None and budget > 10_000_000:
        errors.append("Budget value seems unrealistically high. Please enter a valid amount in INR.")

    if duration_days is not None:
        if duration_days < 1:
            errors.append("Trip duration must be at least 1 day.")
        if duration_days > 90:
            errors.append("Trip duration cannot exceed 90 days.")

    if errors:
        raise HTTPException(
            status_code=422,
            detail={"errors": errors, "hint": "Please review your search parameters."},
        )


def validate_reorder_request(
    new_stop_names: List[str],
    session_stops: List[dict],
) -> None:
    """
    Validate a reorder request — ensure no stops are added or removed, only reordered.

    Raises:
        HTTPException(422): If the set of stop names doesn't match the session.
    """
    session_names = {s.get("destination", "").lower() for s in session_stops}
    request_names = {n.lower() for n in new_stop_names}

    if session_names != request_names:
        added = request_names - session_names
        removed = session_names - request_names
        detail_parts = []
        if added:
            detail_parts.append(f"Unknown stops: {', '.join(added)}")
        if removed:
            detail_parts.append(f"Missing stops: {', '.join(removed)}")

        raise HTTPException(
            status_code=422,
            detail={
                "errors": detail_parts,
                "hint": "Reorder must include exactly the same destinations as the current itinerary.",
            },
        )


def validate_update_leg_request(
    leg_index: int,
    transport_mode: str,
    days_at_stop: Optional[int],
    session_stops: List[dict],
) -> None:
    """
    Validate a leg update request.

    Raises:
        HTTPException(422): On invalid leg index, transport mode, or day count.
    """
    errors = []

    valid_modes = {"flight", "train", "bus", "drive", "boat"}
    if transport_mode.lower() not in valid_modes:
        errors.append(f"Invalid transport mode '{transport_mode}'. Must be one of: {', '.join(sorted(valid_modes))}.")

    if leg_index < 0 or leg_index >= len(session_stops):
        errors.append(f"Leg index {leg_index} is out of range (itinerary has {len(session_stops)} stops).")

    if days_at_stop is not None:
        if days_at_stop < 1:
            errors.append("Days at stop must be at least 1.")
        if days_at_stop > 14:
            errors.append("Days at a single stop cannot exceed 14.")

    if errors:
        raise HTTPException(
            status_code=422,
            detail={"errors": errors},
        )


def validate_session_exists(session: Any, session_id: str) -> None:
    """
    Validate that a session was found. Raises 404 if not.

    Raises:
        HTTPException(404): If session is None.
    """
    if session is None:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found. It may have expired or the ID is incorrect.",
        )


def validate_chat_message(message: str) -> None:
    """
    Validate a chat message.

    Raises:
        HTTPException(422): If the message is empty or too long.
    """
    if not message or not message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty.")
    if len(message) > 2000:
        raise HTTPException(
            status_code=422,
            detail="Message is too long (max 2000 characters).",
        )
