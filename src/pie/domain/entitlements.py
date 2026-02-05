from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Entitlement:
    passenger_id: str
    eligible: bool
    reason: str

    # EU261 cash compensation (Article 7)
    cash_comp_eur: float
    cash_comp_rule: str  # e.g. "EU261:Art7(1)(b)"

    # Care & assistance (Article 9) — simplified initial model
    care_cost_eur: float
    care_rule: str  # e.g. "EU261:Art9"

    # Re-routing/refund operational cost (Article 8) — simplified initial model
    rebook_cost_eur: float
    rebook_rule: str  # e.g. "EU261:Art8"

    @property
    def total_cost_eur(self) -> float:
        return float(self.cash_comp_eur + self.care_cost_eur + self.rebook_cost_eur)
