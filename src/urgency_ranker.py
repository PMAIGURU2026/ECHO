"""
urgency_ranker.py - Tool 4 | Owner: Luba

Adds v0.2 urgency context and finalizes gap_score to 0-100.
"""

from typing import Any


VALID_TIERS = {"high", "medium", "low"}
VALID_FLAGS = {"🔴 Act this week", "🟡 Monitor", "🟢 Not ready"}


def _urgency_context_points(hospital: dict[str, Any]) -> int:
    points = 0
    if hospital.get("medicaid_extended"):
        points += 10
    if hospital.get("racial_disparity_flag"):
        points += 15
    return min(points, 25)


def _tier_and_flag(score: float) -> tuple[str, str]:
    if score >= 70:
        return "high", "🔴 Act this week"
    if score >= 40:
        return "medium", "🟡 Monitor"
    return "low", "🟢 Not ready"


def add_urgency(hospital: dict[str, Any]) -> dict[str, Any]:
    if "gap_score" not in hospital:
        raise KeyError("gap_score is required. Run calculate_gap_score() first.")
    if "gap_breakdown" not in hospital:
        raise KeyError("gap_breakdown is required. Run calculate_gap_score() first.")

    urgency_points = _urgency_context_points(hospital)
    final_score = min(float(hospital["gap_score"]) + urgency_points, 100.0)
    tier, flag = _tier_and_flag(final_score)

    hospital["gap_score"] = final_score
    hospital["gap_breakdown"]["urgency_context"] = urgency_points
    hospital["urgency_tier"] = tier
    hospital["urgency_flag"] = flag

    if tier not in VALID_TIERS:
        raise ValueError(f"Invalid urgency_tier: {tier}")
    if flag not in VALID_FLAGS:
        raise ValueError(f"Invalid urgency_flag: {flag}")

    return hospital
