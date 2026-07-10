"""Reputation decay under inactivity (Kredo v2 — improvements/03).

A soulbound reputation that never fades lets a Sybil operator build a fleet
once and hold its votes forever. Decay ties voting weight to *sustained*
genuine activity:

    r(t) = r₀ · 2^(−max(0, Δt_inactive − grace) / T½)

where Δt_inactive is days since the member's last confirmed transaction,
``grace`` tolerates ordinary breaks, and T½ is the half-life. Maintaining
k fake identities therefore costs continuous real activity on every one —
and inter-cluster wash trading is exactly what the concentration monitor
flags.

Decay is opt-in: when ``reputation_half_life_days`` is ``None`` the factor
is always 1, so legacy runs are unaffected.
"""

from __future__ import annotations

from decimal import Decimal

from app.domain.parameters import ClubParameters


class ReputationDecayService:
    """Compute the multiplicative decay factor for an inactivity span."""

    def __init__(self, params: ClubParameters) -> None:
        self._params = params

    @property
    def enabled(self) -> bool:
        return self._params.reputation_half_life_days is not None

    def factor(self, inactive_days: int) -> Decimal:
        """``2^(−max(0, inactive_days − grace)/T½)`` — in ``(0, 1]``."""
        half_life = self._params.reputation_half_life_days
        if half_life is None:
            return Decimal(1)
        if inactive_days < 0:
            raise ValueError(f"inactive_days must be non-negative, got {inactive_days}")
        overdue = inactive_days - self._params.reputation_decay_grace_days
        if overdue <= 0:
            return Decimal(1)
        exponent = Decimal(-overdue) / Decimal(half_life)
        # 2^x = exp(x·ln2); Decimal.exp/ln are correctly rounded.
        return (exponent * Decimal(2).ln()).exp()
