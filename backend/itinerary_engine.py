"""
itinerary_engine.py — Core itinerary constraint validation and optimization engine.

Extracted from main.py and fake_tbo.py inlined logic. Provides geographic ordering,
budget allocation, feasibility validation, and dynamic recalculation.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class ItineraryError(Exception):
    """Raised when an itinerary fails validation or is logically infeasible."""
    def __init__(self, reason: str, field: Optional[str] = None):
        super().__init__(reason)
        self.reason = reason
        self.field = field


# ── Budget split fractions per journey type ───────────────────────────────────
BUDGET_SPLITS: Dict[str, List[float]] = {
    "1-stop": [1.0],
    "2-stop": [0.55, 0.45],
    "3-stop": [0.45, 0.35, 0.20],
}

JOURNEY_LABELS: Dict[str, str] = {
    "1-stop": "Quick Escape",
    "2-stop": "Weekend Explorer",
    "3-stop": "Grand Tour",
}

# Approximate minimum travel days between different regions
# (so we don't pack too many cities into too few days)
_REGION_TRAVEL_COST_DAYS: Dict[Tuple[str, str], int] = {
    ("South India", "Rajasthan"): 1,
    ("Rajasthan", "South India"): 1,
    ("North India (Hills)", "Rajasthan"): 1,
    ("Rajasthan", "North India (Hills)"): 1,
    ("South India", "North India (Hills)"): 1,
    ("North India (Hills)", "South India"): 1,
    ("North India (Plains)", "Rajasthan"): 1,
    ("Rajasthan", "North India (Plains)"): 1,
    ("Islands", "South India"): 1,
    ("South India", "Islands"): 1,
}

# Minimum days recommended per stop for a meaningful visit
MIN_DAYS_PER_STOP = 1
MAX_DAYS_PER_STOP = 7


def get_region(tbo_id: str) -> str:
    """Import and delegate to fake_tbo.get_region to avoid circular imports."""
    from fake_tbo import REGION_MAP
    return REGION_MAP.get(tbo_id, "Other")


def estimate_travel_days_between(region_a: str, region_b: str) -> int:
    """Return minimum travel days (transit) between two regions."""
    if region_a == region_b:
        return 0
    return _REGION_TRAVEL_COST_DAYS.get((region_a, region_b), 1)


class RouteOptimizer:
    """
    Core route optimization and constraint validation engine.

    All public methods raise ItineraryError on infeasibility, which the
    API layer should catch and convert to a 400 HTTPException.
    """

    def validate_route(
        self,
        stops: List[Dict],
        duration_days: int,
        budget: int,
    ) -> None:
        """
        Validate that a multi-stop route is feasible within the given constraints.

        Checks:
        - At least 1 stop
        - Budget > 0
        - Enough days for the number of stops
        - Total cost does not obviously exceed budget
        - No duplicate stops

        Raises ItineraryError if any check fails.
        """
        if not stops:
            raise ItineraryError("At least one destination is required.", field="stops")

        if budget <= 0:
            raise ItineraryError("Budget must be greater than zero.", field="budget")

        if duration_days is not None and duration_days < len(stops):
            raise ItineraryError(
                f"Trip duration ({duration_days} days) is too short for {len(stops)} stops. "
                f"Need at least {len(stops)} days (1 day per destination).",
                field="duration_days",
            )

        # Detect duplicate destinations
        destinations_seen = set()
        for s in stops:
            name = s.get("destination", "")
            if name.lower() in destinations_seen:
                raise ItineraryError(
                    f"Duplicate destination '{name}' in itinerary.", field="stops"
                )
            destinations_seen.add(name.lower())

        # Budget feasibility smoke-check: minimum spend per stop
        n = len(stops)
        split_key = f"{n}-stop" if n <= 3 else "3-stop"
        fractions = BUDGET_SPLITS.get(split_key, [1.0 / n] * n)
        for i, stop in enumerate(stops):
            frac = fractions[i] if i < len(fractions) else fractions[-1]
            allocated = int(budget * frac)
            price = stop.get("price_per_person", 0)
            flight = stop.get("flight_min_fare") or int(price * 0.35)
            combined = price + flight
            if combined > allocated:
                logger.warning(
                    f"Stop '{stop.get('destination')}': combined cost ₹{combined} "
                    f"exceeds allocated ₹{allocated}. Itinerary may be infeasible."
                )

    def optimize_stop_order(self, stops: List[Dict]) -> List[Dict]:
        """
        Re-order stops to match the logical geographic circuit order
        using the region stop order from fake_tbo.

        Stops with unknown TBO IDs (e.g., from text-based search) are appended
        at the end in their original order.
        """
        from fake_tbo import _REGION_STOP_ORDER, REGION_MAP

        if len(stops) <= 1:
            return stops

        # Group stops by region
        region_buckets: Dict[str, List[Dict]] = {}
        unknown_stops: List[Dict] = []

        for stop in stops:
            tbo_id = stop.get("tbo_id", "")
            region = REGION_MAP.get(tbo_id, "")
            if region:
                region_buckets.setdefault(region, []).append(stop)
            else:
                unknown_stops.append(stop)

        # Pick the primary region (most stops) and sort within it
        if not region_buckets:
            return stops

        primary_region = max(region_buckets, key=lambda r: len(region_buckets[r]))
        circuit_order = _REGION_STOP_ORDER.get(primary_region, [])

        ordered: List[Dict] = []
        # Append stops in circuit order
        for tbo_id in circuit_order:
            for stop in stops:
                if stop.get("tbo_id") == tbo_id and stop not in ordered:
                    ordered.append(stop)

        # Append any stops not captured by the circuit order
        for stop in stops:
            if stop not in ordered:
                ordered.append(stop)

        return ordered

    def calculate_transit_days(self, stops: List[Dict]) -> List[int]:
        """
        Calculate transit days between consecutive stops.
        Returns a list of length len(stops)-1 with days needed to travel between each pair.
        """
        if len(stops) <= 1:
            return []

        transit = []
        for i in range(len(stops) - 1):
            r_a = get_region(stops[i].get("tbo_id", ""))
            r_b = get_region(stops[i + 1].get("tbo_id", ""))
            transit.append(estimate_travel_days_between(r_a, r_b))

        return transit

    def allocate_days(self, stops: List[Dict], total_days: int) -> List[int]:
        """
        Distribute total_days across stops proportionally.
        Each stop gets at least MIN_DAYS_PER_STOP and at most MAX_DAYS_PER_STOP.
        Transit days between stops are deducted first.
        """
        if not stops:
            return []

        n = len(stops)
        transit = self.calculate_transit_days(stops)
        transit_total = sum(transit)
        available_days = max(total_days - transit_total, n)

        # Equal distribution first
        base = available_days // n
        remainder = available_days % n

        result = []
        for i in range(n):
            days = max(MIN_DAYS_PER_STOP, min(MAX_DAYS_PER_STOP, base + (1 if i < remainder else 0)))
            result.append(days)

        return result

    def recalculate_budget(
        self, stops: List[Dict], budget: int
    ) -> Tuple[List[Dict], int]:
        """
        Re-apply budget splits to a set of stops.
        Returns (updated_stops, total_allocated) where total_allocated ≤ budget.
        """
        n = len(stops)
        split_key = f"{n}-stop" if n <= 3 else "3-stop"
        fractions = BUDGET_SPLITS.get(split_key, [1.0 / n] * n)

        updated = []
        total = 0
        for i, stop in enumerate(stops):
            frac = fractions[i] if i < len(fractions) else fractions[-1]
            allocated = int(budget * frac)
            flight = stop.get("flight_min_fare") or int(stop.get("price_per_person", 0) * 0.35)
            hotel = stop.get("price_per_person", 0)
            combined = flight + hotel
            updated.append({
                **stop,
                "allocated_budget": allocated,
                "price_per_person": combined,
                "is_feasible": combined <= allocated,
            })
            total += combined

        return updated, total

    def generate_route_justification(self, stops: List[Dict], region: str) -> str:
        """
        Return a short plain-text justification of why stops are ordered this way.
        Used for display in the UI.
        """
        if not stops:
            return ""
        if len(stops) == 1:
            return f"{stops[0].get('destination', '')} is an ideal destination for your travel style."

        names = [s.get("destination", "?") for s in stops]
        route_str = " → ".join(names)

        return (
            f"Your route ({route_str}) has been optimised for geographic proximity within "
            f"{region}. This circuit minimises travel time between stops, leaving more days "
            f"for exploration at each destination."
        )


# Module-level singleton
route_optimizer = RouteOptimizer()
