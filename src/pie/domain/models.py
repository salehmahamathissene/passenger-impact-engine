from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Segment(StrEnum):
    BUSINESS = "business"
    LEISURE = "leisure"


class DisruptionType(StrEnum):
    DELAY = "delay"
    CANCEL = "cancel"


@dataclass(frozen=True)
class Passenger:
    id: str
    segment: Segment
    fare_paid: float
    refundable: bool


@dataclass(frozen=True)
class EligibilityContext:
    # EU261 applicability signals (kept explicit for correctness/audit)
    carrier_is_eu: bool
    dep_in_eu: bool
    arr_in_eu: bool
    distance_km: int

    def is_eu261_applicable(self) -> bool:
        # Simplified, explicit applicability:
        # - If departure is in EU => applicable regardless of carrier
        # - Else if arrival is in EU and carrier is EU => applicable
        if self.dep_in_eu:
            return True
        if self.arr_in_eu and self.carrier_is_eu:
            return True
        return False


@dataclass(frozen=True)
class DisruptionEvent:
    dtype: DisruptionType
    delay_minutes: int = 0
    cause: str = "unknown"


@dataclass(frozen=True)
class CompensationOutcome:
    cash_comp_eur: float
    care_cost_eur: float
    rebooking_cost_eur: float
    refund_cost_eur: float
    total_cost_eur: float
    note: str | None = None
