"""Escrow distribution shares — proportional to active turnover.

Math §6.2:

    share_i = (Turnover_i + ξ) / (Σ_j Turnover_j + n·ξ)

The smoothing constant ξ guarantees every member receives at least a
small share even when their 90-day turnover is zero. Without it, a
brand-new member receives nothing on the first distribution event,
which is unfair (they may have just joined).

Distributing by turnover (not by balance) is the structural difference
between this club and a regular capitalist economy: rentiers don't
accumulate disproportionate dividend weight.
"""

from __future__ import annotations

from decimal import Decimal

from app.domain.parameters import ClubParameters
from app.domain.value_objects import MemberId, V


class DistributionService:
    """Compute escrow distribution shares across members."""

    def __init__(self, params: ClubParameters) -> None:
        self._params = params

    def shares(self, turnovers: dict[MemberId, V]) -> dict[MemberId, Decimal]:
        """Return a mapping of MemberId → share, summing to 1.

        Empty input → empty mapping (no-op for distribution).
        """
        if not turnovers:
            return {}
        xi = self._params.xi.root
        n = Decimal(len(turnovers))
        total_turnover = sum((t.root for t in turnovers.values()), Decimal(0))
        denominator = total_turnover + n * xi
        if denominator <= 0:
            # Edge case: ξ=0 and all turnovers zero. Distribute equally.
            equal_share = Decimal(1) / n
            return dict.fromkeys(turnovers, equal_share)
        return {
            member: (turnover.root + xi) / denominator for member, turnover in turnovers.items()
        }
