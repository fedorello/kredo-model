"""Withdrawal queue: delay and discount when fund coverage is low.

ARCHITECTURE §15.2 / math §7.3:

When ρ = F/(P·S) drops below ρ*, Convert calls do not execute
immediately. The delay (in days) and the discount (price reduction)
both scale with how far below ρ* coverage has fallen.

We use a simple linear schedule:

    delay(ρ)    = 0                     if ρ ≥ ρ*
                = 30 · (1 − ρ/ρ*)       if 0 ≤ ρ < ρ*

    discount(ρ) = same as PricingService.discount_factor.

The 30-day cap matches the 1–30 day window noted in math §7.3. Operations
add the resulting delay to ``requested_at`` to produce ``execute_at``
on the queue entry.
"""

from __future__ import annotations

from decimal import Decimal

from app.domain.parameters import ClubParameters

_MAX_DELAY_DAYS = 30


class WithdrawalQueueService:
    """Compute queue delays for Convert requests."""

    def __init__(self, params: ClubParameters) -> None:
        self._params = params

    def delay_days(self, coverage: Decimal) -> int:
        """Return the delay in days before this Convert should execute."""
        if coverage < 0:
            raise ValueError(f"coverage must be non-negative, got {coverage}")
        rho_star = self._params.rho_min
        if coverage >= rho_star or rho_star <= 0:
            return 0
        ratio = Decimal(1) - coverage / rho_star
        return int((Decimal(_MAX_DELAY_DAYS) * ratio).to_integral_value())

    def execute_at(self, coverage: Decimal, requested_at: int) -> int:
        return requested_at + self.delay_days(coverage)
