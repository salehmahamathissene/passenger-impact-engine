from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DemoResult:
    # Minimal fields your dashboard/pipeline needs
    mean_total_cost: float
    p95_total_cost: float
    cvar95_total_cost: float

    # Evidence tables
    top_passengers: list[dict[str, Any]]
    group_stats: list[dict[str, Any]]
    cost_breakdown: dict[str, float]


def run_demo(seed: int = 42) -> DemoResult:
    rng = random.Random(seed)

    # Keep your existing stable values if you want—this just makes it structured.
    mean_total_cost = 462_788 + rng.randint(-2500, 2500)
    p95_total_cost = 590_500 + rng.randint(-2500, 2500)
    cvar95_total_cost = 610_500 + rng.randint(-2500, 2500)

    cost_breakdown = {
        "refund_cost": mean_total_cost * 0.35,
        "rebooking_cost": mean_total_cost * 0.25,
        "hotel_meals_cost": mean_total_cost * 0.20,
        "cash_compensation_cost": mean_total_cost * 0.20,
    }

    # Contract-looking outputs (even demo mode must look like a real product)
    top_passengers = [
        {"rank": i + 1, "passenger_id": f"P-{1000+i}", "expected_cost": 8000 - i * 250}
        for i in range(20)
    ]

    group_stats = [
        {"segment": "economy", "n": 90, "mean_cost": mean_total_cost * 0.55, "p95_cost": p95_total_cost * 0.60},
        {"segment": "business", "n": 25, "mean_cost": mean_total_cost * 0.30, "p95_cost": p95_total_cost * 0.28},
        {"segment": "first", "n": 5, "mean_cost": mean_total_cost * 0.15, "p95_cost": p95_total_cost * 0.12},
    ]

    return DemoResult(
        mean_total_cost=float(mean_total_cost),
        p95_total_cost=float(p95_total_cost),
        cvar95_total_cost=float(cvar95_total_cost),
        top_passengers=top_passengers,
        group_stats=group_stats,
        cost_breakdown=cost_breakdown,
    )
