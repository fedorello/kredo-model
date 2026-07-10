"""Dynamic compensation rate ε.

Formula (math §5.3):

    ε(t) = max(0, min(ε_max, K* - 1 - κ · (δ_t - δ*)))

where:
    K*   — target Supply / NetVerifiedValue ratio (default 1.5)
    δ*   — target default rate (default 0.05)
    κ    — sensitivity (default 2)
    δ_t  — observed default rate over the trailing 90-day window
    ε_max — hard upper bound (default 0.95)

Reduces compensation as defaults increase, reaching zero at δ ≈ 0.30 with
default parameters, which is the system's automatic conservation mode.
"""

from __future__ import annotations

from decimal import Decimal

from app.domain.parameters import ClubParameters


class EpsilonCalculator:
    """Compute the dynamic compensation factor ε for new credit emissions."""

    def __init__(self, params: ClubParameters) -> None:
        self._params = params

    def compute(self, observed_default_rate: Decimal) -> Decimal:
        if observed_default_rate < 0:
            raise ValueError(
                f"observed default rate must be non-negative, got {observed_default_rate}"
            )
        p = self._params
        raw = p.K_target - Decimal(1) - p.kappa * (observed_default_rate - p.delta_target)
        return max(Decimal(0), min(p.epsilon_max, raw))
