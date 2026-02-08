from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RealResult:
    mean_total_cost: float
    p95_total_cost: float
    cvar95_total_cost: float

    # Evidence
    top_passengers: list[dict[str, Any]]
    top_flights: list[dict[str, Any]]
    group_stats: list[dict[str, Any]]
    cost_breakdown: dict[str, float]

    # Audit trace (ledger rows)
    ledger_rows: list[dict[str, Any]]


def _eu261_comp(distance_km: int, delay_hours: float, cancelled: bool) -> float:
    """
    Simplified EU261-style compensation:
    - 0 if < 3 hours delay and not cancelled
    - else 250/400/600 by distance buckets
    """
    if not cancelled and delay_hours < 3.0:
        return 0.0
    if distance_km <= 1500:
        return 250.0
    if distance_km <= 3500:
        return 400.0
    return 600.0


def _duty_of_care_cost(delay_hours: float, overnight: bool, cabin: str) -> float:
    if delay_hours < 2:
        return 0.0
    meals = 15.0 + (10.0 if cabin in ("business", "first") else 0.0)
    if overnight:
        hotel = 120.0 if cabin in ("business", "first") else 80.0
        return meals + hotel
    return meals


def _rebooking_cost(distance_km: int, cabin: str) -> float:
    base = 0.11 * distance_km  # proxy: cost scales with distance
    mult = {"economy": 1.0, "business": 2.4, "first": 3.8}[cabin]
    return base * mult


def _refund_cost(ticket_price: float) -> float:
    return ticket_price


def run_real(seed: int = 42, runs: int = 500, tickets_per_flight: int = 120) -> RealResult:
    rng = random.Random(seed)

    # A small flight set that looks realistic for demo contracts
    flights = [
        {"flight_id": "FL-1001", "distance_km": 980},
        {"flight_id": "FL-2033", "distance_km": 2100},
        {"flight_id": "FL-3302", "distance_km": 4200},
        {"flight_id": "FL-4410", "distance_km": 1600},
    ]

    cabins = ["economy", "business", "first"]
    cabin_probs = [0.78, 0.18, 0.04]

    loyalties = ["none", "silver", "gold"]
    loyalty_probs = [0.70, 0.20, 0.10]

    totals: list[float] = []
    ledger_rows: list[dict[str, Any]] = []

    # accumulate mean breakdown across all runs
    agg_breakdown = {"refund_cost": 0.0, "rebooking_cost": 0.0, "hotel_meals_cost": 0.0, "cash_compensation_cost": 0.0}

    passenger_costs: dict[str, float] = {}
    flight_costs: dict[str, float] = {}
    group_costs: dict[str, list[float]] = {"economy": [], "business": [], "first": []}

    for r in range(runs):
        run_total = 0.0

        for f in flights:
            flight_total = 0.0

            # scenario generation (not “fake payload”):
            # - delay: lognormal-ish
            delay_hours = max(0.0, rng.lognormvariate(mu=0.4, sigma=0.8) - 1.0)  # many small delays, some big
            cancelled = rng.random() < 0.06  # 6% cancellation rate
            missed_connection = (delay_hours > 2.0) and (rng.random() < 0.20)

            for i in range(tickets_per_flight):
                passenger_id = f"{f['flight_id']}-P{i:03d}-R{r:04d}"

                cabin = rng.choices(cabins, weights=cabin_probs, k=1)[0]
                loyalty = rng.choices(loyalties, weights=loyalty_probs, k=1)[0]

                # ticket price proxy
                base_price = 0.09 * f["distance_km"]
                cabin_mult = {"economy": 1.0, "business": 3.0, "first": 5.0}[cabin]
                loyalty_disc = {"none": 1.0, "silver": 0.96, "gold": 0.92}[loyalty]
                ticket_price = base_price * cabin_mult * loyalty_disc

                # decision policy (simple but explainable):
                # cancel -> 60% refund, 40% rebook
                # big delay -> mostly keep + duty of care
                take_refund = cancelled and (rng.random() < 0.60)
                overnight = cancelled or (delay_hours >= 8.0)

                refund = _refund_cost(ticket_price) if take_refund else 0.0
                rebook = 0.0 if take_refund else _rebooking_cost(f["distance_km"], cabin)

                # missed connection amplifies rebooking (extra segment)
                if missed_connection and not take_refund:
                    rebook *= 1.35

                hotel_meals = _duty_of_care_cost(delay_hours, overnight=overnight, cabin=cabin)
                cash = _eu261_comp(f["distance_km"], delay_hours=delay_hours, cancelled=cancelled)

                passenger_total = refund + rebook + hotel_meals + cash
                flight_total += passenger_total
                run_total += passenger_total

                agg_breakdown["refund_cost"] += refund
                agg_breakdown["rebooking_cost"] += rebook
                agg_breakdown["hotel_meals_cost"] += hotel_meals
                agg_breakdown["cash_compensation_cost"] += cash

                passenger_costs[passenger_id] = passenger_costs.get(passenger_id, 0.0) + passenger_total
                group_costs[cabin].append(passenger_total)

                # audit trace row (this is what clients ask for: “where did it come from?”)
                ledger_rows.append(
                    {
                        "run": r,
                        "flight_id": f["flight_id"],
                        "distance_km": f["distance_km"],
                        "passenger_id": passenger_id,
                        "cabin": cabin,
                        "loyalty": loyalty,
                        "delay_hours": round(delay_hours, 2),
                        "cancelled": int(cancelled),
                        "missed_connection": int(missed_connection),
                        "refund_cost": round(refund, 2),
                        "rebooking_cost": round(rebook, 2),
                        "hotel_meals_cost": round(hotel_meals, 2),
                        "cash_compensation_cost": round(cash, 2),
                        "total_cost": round(passenger_total, 2),
                    }
                )

            flight_costs[f["flight_id"]] = flight_costs.get(f["flight_id"], 0.0) + flight_total

        totals.append(run_total)

    totals_sorted = sorted(totals)
    mean_total = sum(totals_sorted) / len(totals_sorted)

    def pct(p: float) -> float:
        idx = int(math.floor((p / 100.0) * (len(totals_sorted) - 1)))
        return totals_sorted[idx]

    p95 = pct(95.0)
    # CVaR 95 = mean of tail beyond 95th percentile
    tail = [x for x in totals_sorted if x >= p95]
    cvar95 = sum(tail) / len(tail)

    # normalize breakdown to mean-per-run
    for k in list(agg_breakdown.keys()):
        agg_breakdown[k] /= runs

    # top entities
    top_passengers = sorted(
        [{"passenger_id": pid, "expected_cost": c} for pid, c in passenger_costs.items()],
        key=lambda x: x["expected_cost"],
        reverse=True,
    )[:20]

    top_flights = sorted(
        [{"flight_id": fid, "expected_cost": c / runs} for fid, c in flight_costs.items()],
        key=lambda x: x["expected_cost"],
        reverse=True,
    )[:10]

    # group stats
    group_stats: list[dict[str, Any]] = []
    for seg, vals in group_costs.items():
        s = sorted(vals)
        if not s:
            continue
        g_mean = sum(s) / len(s)
        g_p95 = s[int(0.95 * (len(s) - 1))]
        group_stats.append({"segment": seg, "n": len(s), "mean_cost": g_mean, "p95_cost": g_p95})

    return RealResult(
        mean_total_cost=float(mean_total),
        p95_total_cost=float(p95),
        cvar95_total_cost=float(cvar95),
        top_passengers=top_passengers,
        top_flights=top_flights,
        group_stats=group_stats,
        cost_breakdown=agg_breakdown,
        ledger_rows=ledger_rows,
    )
