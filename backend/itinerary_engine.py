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


# ── Activity-based Itinerary Builder ──────────────────────────────────────────

STYLE_MULTIPLIERS = {
    "backpacker": 0.6,
    "balanced": 1.0,
    "comfort": 1.5,
    "luxury": 2.5,
}


class ActivityItineraryBuilder:
    """
    Builds day-by-day itinerary options from user-selected activities.
    """

    def score_activities(
        self,
        activities: List[Dict],
        budget_remaining: float,
    ) -> List[Dict]:
        """Score each activity by popularity + budget fit + category diversity."""
        seen_categories = set()
        scored = []
        for act in activities:
            pop_score = act.get("popularity", 50) / 100.0 * 0.4
            cost = act.get("cost", 0)
            budget_fit = max(0, 1.0 - cost / max(budget_remaining, 1)) * 0.3
            cat = act.get("category", "")
            diversity = 0.1 if cat not in seen_categories else 0.0
            seen_categories.add(cat)
            total = pop_score + budget_fit + diversity + 0.2  # base 0.2
            scored.append({**act, "_score": total})
        return sorted(scored, key=lambda a: a["_score"], reverse=True)

    def build_day_schedule(
        self,
        activities: List[Dict],
        duration_days: int,
    ) -> List[Dict]:
        """Fill morning/afternoon/evening slots per day."""
        days = []
        slot_idx = 0

        # Preferred time mapping
        time_pref = {
            "morning": ["adventure", "culture", "nature", "wellness"],
            "afternoon": ["food", "shopping", "culture"],
            "evening": ["nightlife", "food", "nature"],
        }

        for d in range(1, duration_days + 1):
            slots = []
            if d == 1:
                slots.append({
                    "id": f"slot_{d}_0",
                    "time": "morning",
                    "locked": True,
                    "activity": {
                        "id": f"_arrive_{d}",
                        "name": "Arrive & Check-in",
                        "emoji": "✈️",
                        "duration_hrs": 2,
                        "cost": 0,
                        "category": "fixed",
                        "time_of_day": "morning",
                    },
                })
                for t_idx, time_slot in enumerate(["afternoon", "evening"]):
                    if slot_idx < len(activities):
                        slots.append({
                            "id": f"slot_{d}_{t_idx + 1}",
                            "time": time_slot,
                            "locked": False,
                            "activity": activities[slot_idx],
                        })
                        slot_idx += 1
                    else:
                        slots.append({
                            "id": f"slot_{d}_{t_idx + 1}",
                            "time": time_slot,
                            "locked": False,
                            "activity": None,
                        })
            elif d == duration_days:
                for t_idx, time_slot in enumerate(["morning"]):
                    if slot_idx < len(activities):
                        slots.append({
                            "id": f"slot_{d}_{t_idx}",
                            "time": time_slot,
                            "locked": False,
                            "activity": activities[slot_idx],
                        })
                        slot_idx += 1
                    else:
                        slots.append({
                            "id": f"slot_{d}_{t_idx}",
                            "time": time_slot,
                            "locked": False,
                            "activity": None,
                        })
                slots.append({
                    "id": f"slot_{d}_depart",
                    "time": "afternoon",
                    "locked": True,
                    "activity": {
                        "id": f"_depart_{d}",
                        "name": "Check-out & Departure",
                        "emoji": "🛫",
                        "duration_hrs": 2,
                        "cost": 0,
                        "category": "fixed",
                        "time_of_day": "afternoon",
                    },
                })
            else:
                for t_idx, time_slot in enumerate(["morning", "afternoon", "evening"]):
                    if slot_idx < len(activities):
                        slots.append({
                            "id": f"slot_{d}_{t_idx}",
                            "time": time_slot,
                            "locked": False,
                            "activity": activities[slot_idx],
                        })
                        slot_idx += 1
                    else:
                        slots.append({
                            "id": f"slot_{d}_{t_idx}",
                            "time": time_slot,
                            "locked": False,
                            "activity": None,
                        })

            label = "Arrival Day" if d == 1 else ("Departure Day" if d == duration_days else f"Day {d}")
            days.append({"day": d, "label": label, "slots": slots})

        return days

    def generate_options(
        self,
        selected_activities: List[Dict],
        all_activities: List[Dict],
        duration_days: int,
        budget: int,
        travel_style: str,
        hotel_cost: int,
        flight_cost: int,
    ) -> List[Dict]:
        """Generate 3 itinerary package options."""
        scored = self.score_activities(selected_activities, budget)

        # Option A: Quick Escape (60% of activities, more rest)
        count_a = max(2, int(len(scored) * 0.6))
        acts_a = scored[:count_a]
        days_a = self.build_day_schedule(acts_a, duration_days)
        cost_a = sum(a.get("cost", 0) for a in acts_a)
        hotel_a = int(hotel_cost * 0.8)  # slightly cheaper
        total_a = hotel_a + flight_cost + cost_a
        buffer_a = int(total_a * 0.1)

        # Option B: Best Balance (80%, recommended)
        count_b = max(2, int(len(scored) * 0.8))
        acts_b = scored[:count_b]
        days_b = self.build_day_schedule(acts_b, duration_days)
        cost_b = sum(a.get("cost", 0) for a in acts_b)
        hotel_b = hotel_cost
        total_b = hotel_b + flight_cost + cost_b
        buffer_b = int(total_b * 0.1)

        # Option C: Full Immersion (100% + suggest extras)
        acts_c = list(scored)
        # Add 2 extras from all_activities not already selected
        selected_ids = {a["id"] for a in scored}
        extras = [a for a in all_activities if a["id"] not in selected_ids][:2]
        acts_c.extend(extras)
        days_c = self.build_day_schedule(acts_c, duration_days)
        cost_c = sum(a.get("cost", 0) for a in acts_c)
        hotel_c = int(hotel_cost * 1.3)  # slightly premium
        total_c = hotel_c + flight_cost + cost_c
        buffer_c = int(total_c * 0.1)

        # Pool = all activities NOT in the schedule
        def get_pool(scheduled_acts, all_dest_acts):
            sched_ids = {a["id"] for a in scheduled_acts}
            return [a for a in all_dest_acts if a["id"] not in sched_ids]

        return [
            {
                "id": "option_a",
                "label": "Quick Escape",
                "tagline": "Relaxed pace, key highlights",
                "days": days_a,
                "activities": acts_a,
                "pool": get_pool(acts_a, all_activities),
                "hotel_cost": hotel_a,
                "flight_cost": flight_cost,
                "activity_cost": cost_a,
                "buffer": buffer_a,
                "total_cost": total_a + buffer_a,
                "highlights": [a["name"] for a in acts_a[:4]],
                "recommended": False,
            },
            {
                "id": "option_b",
                "label": "Best Balance",
                "tagline": "Perfectly paced, nothing missed",
                "days": days_b,
                "activities": acts_b,
                "pool": get_pool(acts_b, all_activities),
                "hotel_cost": hotel_b,
                "flight_cost": flight_cost,
                "activity_cost": cost_b,
                "buffer": buffer_b,
                "total_cost": total_b + buffer_b,
                "highlights": [a["name"] for a in acts_b[:4]],
                "recommended": True,
            },
            {
                "id": "option_c",
                "label": "Full Immersion",
                "tagline": "Every experience, packed in",
                "days": days_c,
                "activities": acts_c,
                "pool": get_pool(acts_c, all_activities),
                "hotel_cost": hotel_c,
                "flight_cost": flight_cost,
                "activity_cost": cost_c,
                "buffer": buffer_c,
                "total_cost": total_c + buffer_c,
                "highlights": [a["name"] for a in acts_c[:4]],
                "recommended": False,
            },
        ]


activity_builder = ActivityItineraryBuilder()

# Module-level singleton
route_optimizer = RouteOptimizer()
