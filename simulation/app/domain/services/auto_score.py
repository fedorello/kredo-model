"""Auto-score: how surprising is the declared price for its category?

Math §3.1:

    z = |amount - μ_c| / σ_c

    s_a = 1                              if z ≤ 1
        = exp(−(z − 1)² / 2)             if z > 1

A price within one standard deviation of the category mean is fully
trusted. Beyond that, trust falls off as a Gaussian — at z=2 score≈0.61,
at z=3 score≈0.14, at z=4 score≈0.01. Far-out prices require active
review (which is what the operations layer triggers).
"""

from __future__ import annotations

from app.domain.parameters import CategoryParams
from app.domain.value_objects import Confidence, V


class AutoScoreCalculator:
    """Compute the auto-score component of confidence(τ)."""

    def compute(self, amount: V, category_params: CategoryParams) -> Confidence:
        sigma = category_params.sigma
        if sigma <= 0:
            raise ValueError(f"category sigma must be positive, got {sigma}")
        z = abs(amount.root - category_params.mu) / sigma
        if z <= 1:
            return Confidence.one()
        diff = z - 1
        # Decimal.exp() is correctly-rounded; use it for full precision.
        return Confidence((-(diff * diff) / 2).exp())
