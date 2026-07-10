"""Quadratic voting (√R) and the double-quorum rule.

Math §8:

    VotingPower(m) = √R(m)
    Reputation Quorum: Σ √R · vote > θ_R · Σ √R   (default θ_R = 0.5)
    Stake Quorum:     Σ b · vote > θ_V · Σ max(0, b) (default θ_V = 0.5)

Constitutional changes raise both thresholds to 0.66.

Although this service exists in the domain, the simulator itself does
not model voting events. Operations may consult it when applying a
hypothetical parameter change embedded in a scenario, but full
governance simulation is explicitly out of scope (ARCHITECTURE §16.6).
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from app.domain.value_objects import R, V

_SIMPLE_MAJORITY = Decimal("0.5")
_CONSTITUTIONAL = Decimal("0.66")


class QuorumKind(StrEnum):
    SIMPLE = "simple"
    CONSTITUTIONAL = "constitutional"


def _threshold(kind: QuorumKind) -> Decimal:
    return _SIMPLE_MAJORITY if kind == QuorumKind.SIMPLE else _CONSTITUTIONAL


class VotingService:
    """Compute voting power and quorum decisions."""

    @staticmethod
    def voting_power(reputation: R) -> Decimal:
        """``√R``. Caps the influence of large stakeholders."""
        return reputation.root.sqrt()

    def reputation_quorum_satisfied(
        self,
        votes_for: dict[R, bool],
        kind: QuorumKind = QuorumKind.SIMPLE,
    ) -> bool:
        """True if Σ_{m: vote==True} √R(m) > θ · Σ_m √R(m).

        ``votes_for`` maps each voter's reputation to their vote (True = yes).
        Members with R = 0 contribute zero power, naturally.
        """
        total_power = sum((self.voting_power(r) for r in votes_for), Decimal(0))
        if total_power <= 0:
            return False
        yes_power = sum(
            (self.voting_power(r) for r, vote in votes_for.items() if vote),
            Decimal(0),
        )
        return yes_power > _threshold(kind) * total_power

    def stake_quorum_satisfied(
        self,
        votes_for: dict[V, bool],
        kind: QuorumKind = QuorumKind.SIMPLE,
    ) -> bool:
        """True if Σ_{m: vote==True} b(m) > θ · Σ_m max(0, b(m))."""
        total_stake = sum((b.root for b in votes_for if b.is_positive()), Decimal(0))
        if total_stake <= 0:
            return False
        yes_stake = sum(
            (b.root for b, vote in votes_for.items() if vote and b.is_positive()),
            Decimal(0),
        )
        return yes_stake > _threshold(kind) * total_stake

    def double_quorum_satisfied(
        self,
        reputation_votes: dict[R, bool],
        stake_votes: dict[V, bool],
        kind: QuorumKind = QuorumKind.SIMPLE,
    ) -> bool:
        """Both quorums must independently pass."""
        return self.reputation_quorum_satisfied(
            reputation_votes, kind
        ) and self.stake_quorum_satisfied(stake_votes, kind)
