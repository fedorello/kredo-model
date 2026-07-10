"""Activity multiplier for quarterly dividend distribution.

ARCHITECTURE §2.6 v2:

    multiplier_i = clip(0.3 + 0.7 · (contrib_i / mean_active_contrib),
                        activity_min, activity_max)

The minimum of 0.3 means a passive holder still gets *some* dividend
(this preserves the system's appeal to investors). The maximum (~1.7)
caps how much an extremely active member can earn over the average.
"""

from __future__ import annotations

from decimal import Decimal

from app.domain.parameters import ClubParameters
from app.domain.value_objects import V


class ActivityMultiplierService:
    """Compute the activity-weighted dividend multiplier."""

    def __init__(self, params: ClubParameters) -> None:
        self._params = params

    def multiplier(
        self,
        member_contribution: V,
        mean_active_contribution: V,
    ) -> Decimal:
        """Return the clipped multiplier in ``[activity_min, activity_max]``."""
        if member_contribution.is_negative() or mean_active_contribution.is_negative():
            raise ValueError("contributions must be non-negative")
        if mean_active_contribution.is_zero():
            return self._params.activity_min
        ratio = member_contribution.root / mean_active_contribution.root
        raw = Decimal("0.3") + Decimal("0.7") * ratio
        return max(self._params.activity_min, min(self._params.activity_max, raw))
