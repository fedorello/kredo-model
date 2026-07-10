"""Credit limit as a function of reputation.

Formula (math §2.1):

    L(r) = L0 · (1 + α · ln(1 + r))

Logarithmic growth caps the maximum loss any single member can cause —
even at r = 10000, L is only ≈ 5.6 × the new-member limit. This is the
deliberate trade-off between rewarding tenure and limiting blast radius.
"""

from __future__ import annotations

from decimal import Decimal

from app.domain.parameters import ClubParameters
from app.domain.value_objects import R, V


class CreditLimitService:
    """Compute the maximum credit (negative balance) allowed for a member."""

    def __init__(self, params: ClubParameters) -> None:
        self._params = params

    def compute(self, reputation: R) -> V:
        # Decimal.ln() returns a correctly-rounded natural logarithm,
        # bypassing float entirely. ln(1+r) is well-defined for r ≥ 0.
        ln_arg = Decimal(1) + reputation.root
        log_term = ln_arg.ln() if ln_arg > 1 else Decimal(0)
        factor = Decimal(1) + self._params.alpha * log_term
        return self._params.L0 * factor
