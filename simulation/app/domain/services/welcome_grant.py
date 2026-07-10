"""Welcome grant size — adaptively limited by Genesis Pool depth.

Math §3.5:

    g₀(t) = min(g₀_target, GenesisPool / E[NewMembers])

If new members arrive faster than the Pool can be replenished, the per-
member grant shrinks but never goes negative. This is the
``no subsidies from nowhere`` rule.
"""

from __future__ import annotations

from decimal import Decimal

from app.domain.parameters import ClubParameters
from app.domain.value_objects import V


class WelcomeGrantService:
    """Compute the V grant given to a newly-joining member."""

    def __init__(self, params: ClubParameters) -> None:
        self._params = params

    def grant(self, genesis_pool_balance: V, expected_new_members: int) -> V:
        """Return the grant size, ≤ ``params.g0`` and ≤ Genesis Pool ÷ expected.

        Args:
            genesis_pool_balance: current balance in the Genesis Pool.
            expected_new_members: members the club expects in the upcoming window.
                Pass ``1`` if you don't know — that gives the most generous bound
                (whole pool to one member).
        """
        if genesis_pool_balance.is_negative():
            raise ValueError("Genesis Pool balance must be non-negative")
        if expected_new_members <= 0:
            raise ValueError("expected_new_members must be positive")
        per_capita = V(genesis_pool_balance.root / Decimal(expected_new_members))
        return min(self._params.g0, per_capita)
