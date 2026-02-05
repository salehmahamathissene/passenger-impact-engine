from __future__ import annotations

from dataclasses import dataclass

from pie.domain.entitlements import Entitlement
from pie.domain.models import (
    CompensationOutcome,
    DisruptionEvent,
    DisruptionType,
    EligibilityContext,
    Passenger,
)


@dataclass(frozen=True)
class EU261Config:
    # care costs
    meal_cost: float
    hotel_cost_per_night: float
    ground_transport_cost: float

    # disruption economics
    refund_rate: float  # probability-ish approximation used for expected refund cost
    rebooking_cost_mean: float
    rebooking_cost_std: float  # used elsewhere; rule doesn't sample

    # policy simplification knobs
    assume_hotel_if_delay_over_minutes: int = 240  # 4h
    assume_hotel_if_cancel: bool = True


def _distance_band(distance_km: int) -> str:
    if distance_km <= 1500:
        return "short"
    if distance_km <= 3500:
        return "medium"
    return "long"


def _cash_compensation_eur(distance_km: int, dtype: DisruptionType, delay_minutes: int) -> float:
    """
    Simplified EU261 cash compensation structure:
    - Cancellation => compensation by distance band (baseline)
    - Delay => compensation if delay >= threshold (band-specific)
    Thresholds (simplified): short >= 120m, medium >= 180m, long >= 240m
    Amounts: short 250, medium 400, long 600
    """
    band = _distance_band(distance_km)
    amount = {"short": 250.0, "medium": 400.0, "long": 600.0}[band]

    if dtype == DisruptionType.CANCEL:
        return amount

    # delay
    threshold = {"short": 120, "medium": 180, "long": 240}[band]
    return amount if delay_minutes >= threshold else 0.0


def assess_eu261(
    passenger: Passenger,
    ctx: EligibilityContext,
    event: DisruptionEvent,
    cfg: EU261Config,
    sampled_rebooking_cost_eur: float,
) -> CompensationOutcome:
    # If not applicable => zero EU261 cash comp; we still may have operational costs but keep v0.1 strict.
    if not ctx.is_eu261_applicable():
        return CompensationOutcome(
            cash_comp_eur=0.0,
            care_cost_eur=0.0,
            rebooking_cost_eur=0.0,
            refund_cost_eur=0.0,
            total_cost_eur=0.0,
            note="EU261 not applicable",
        )

    cash = _cash_compensation_eur(ctx.distance_km, event.dtype, event.delay_minutes)

    # Care costs (simplified, auditable)
    care = 0.0
    if event.dtype == DisruptionType.CANCEL and cfg.assume_hotel_if_cancel:
        care += cfg.hotel_cost_per_night + cfg.meal_cost + cfg.ground_transport_cost
    elif event.dtype == DisruptionType.DELAY:
        care += cfg.meal_cost  # assume meal for delays in general
        if event.delay_minutes >= cfg.assume_hotel_if_delay_over_minutes:
            care += cfg.hotel_cost_per_night + cfg.ground_transport_cost

    # Refund expected cost approximation:
    refund = passenger.fare_paid if passenger.refundable else passenger.fare_paid * cfg.refund_rate

    # Rebooking cost is sampled by simulator (keeps rule pure)
    rebook = max(0.0, sampled_rebooking_cost_eur)

    total = cash + care + refund + rebook

    return CompensationOutcome(
        cash_comp_eur=cash,
        care_cost_eur=care,
        rebooking_cost_eur=rebook,
        refund_cost_eur=refund,
        total_cost_eur=total,
        note=None,
    )
def assess_passenger_eu261(
    *,
    passenger,
    ctx,
    cfg: EU261Config,
    distance_km: int,
    delay_minutes: int,
    is_cancelled: bool,
    extraordinary: bool,
    sampled_rebooking_cost_eur: float,
) -> Entitlement:
    """
    Returns per-passenger entitlement with rule references.
    NOTE: v0.2 keeps a strict simplified scope (cash comp only when applicable).
    """

    # Not applicable => no EU261 cash comp in v0.2
    if not ctx.is_eu261_applicable():
        return Entitlement(
            passenger_id=passenger.id,
            eligible=False,
            reason="Not EU261 applicable (scope)",
            cash_comp_eur=0.0,
            cash_comp_rule="EU261:N/A",
            care_cost_eur=0.0,
            care_rule="EU261:N/A",
            rebook_cost_eur=0.0,
            rebook_rule="EU261:N/A",
        )

    if extraordinary:
        # extraordinary circumstances block cash compensation (simplified)
        return Entitlement(
            passenger_id=passenger.id,
            eligible=False,
            reason="Extraordinary circumstances (cash comp excluded)",
            cash_comp_eur=0.0,
            cash_comp_rule="EU261:Art5(3)",
            care_cost_eur=0.0,
            care_rule="EU261:N/A",
            rebook_cost_eur=0.0,
            rebook_rule="EU261:N/A",
        )

    # Determine eligibility threshold (simplified):
    eligible = is_cancelled or (delay_minutes >= cfg.delay_threshold_minutes)

    if not eligible:
        return Entitlement(
            passenger_id=passenger.id,
            eligible=False,
            reason="Below compensation threshold",
            cash_comp_eur=0.0,
            cash_comp_rule="EU261:Art7",
            care_cost_eur=0.0,
            care_rule="EU261:N/A",
            rebook_cost_eur=0.0,
            rebook_rule="EU261:N/A",
        )

    # Distance bands (Art 7):
    if distance_km <= 1500:
        cash = cfg.comp_band_0_1500_eur
        rule = "EU261:Art7(1)(a)"
    elif distance_km <= 3500:
        cash = cfg.comp_band_1500_3500_eur
        rule = "EU261:Art7(1)(b)"
    else:
        cash = cfg.comp_band_3500_plus_eur
        rule = "EU261:Art7(1)(c)"

    # Optional business logic: refundable fares reduce exposure (example)
    # Keep it deterministic and explicit:
    if passenger.refundable:
        cash = cash * cfg.refundable_cash_multiplier

    return Entitlement(
        passenger_id=passenger.id,
        eligible=True,
        reason="Eligible for cash compensation",
        cash_comp_eur=float(cash),
        cash_comp_rule=rule,
        care_cost_eur=0.0,
        care_rule="EU261:Art9(NOT_MODELED_YET)",
        rebook_cost_eur=float(sampled_rebooking_cost_eur),
        rebook_rule="EU261:Art8(SIMPLIFIED)",
    )
