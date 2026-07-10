"""Vouching with slashing — endogenous identity cost (v2, improvements/03).

The corrected Sybil proposition shows √R weighting alone does not deter
splitting; the defense is the *cost of each identity* plus the dual quorum.
Vouching makes that cost endogenous: a joiner needs ``m`` existing members
to vouch, each staking reputation (and/or V). If the vouchee is proven
fraudulent within the probation window, the vouchers are slashed. An
attacker who wants ``k`` fake identities must therefore corrupt real
members rather than merely defeat a KYC provider.

Governance and joining flow are out of scope for the simulation engine
(see voting.py), so this service exposes the *economics* — the minimum
per-identity attack cost and the slashing amounts — used analytically by
the ``sybil_attack`` experiment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from app.domain.value_objects import MemberId, R, V


@dataclass(frozen=True, slots=True)
class VouchPolicy:
    """Parameters of the vouching requirement."""

    required_vouchers: int = 2
    """m — number of existing members who must vouch for a joiner."""
    reputation_stake: R = field(default_factory=lambda: R(5))
    """σ_R — reputation each voucher risks (≈ half a year of activity)."""
    collateral_stake: V = field(default_factory=lambda: V(50))
    """σ_V — V collateral each voucher risks."""
    probation_days: int = 90
    """T_v — window during which vouchee fraud slashes the vouchers."""

    def __post_init__(self) -> None:
        if self.required_vouchers <= 0:
            raise ValueError("required_vouchers must be positive")
        if self.probation_days <= 0:
            raise ValueError("probation_days must be positive")


@dataclass(frozen=True, slots=True)
class Vouch:
    """One member vouching for a joiner, with a stake at risk until expiry."""

    voucher: MemberId
    vouchee: MemberId
    reputation_stake: R
    collateral_stake: V
    expires_at: int

    def is_active(self, tick: int) -> bool:
        return tick < self.expires_at


class VouchingService:
    """Attack-cost and slashing economics of the vouching requirement."""

    def __init__(self, policy: VouchPolicy | None = None) -> None:
        self._policy = policy or VouchPolicy()

    @property
    def policy(self) -> VouchPolicy:
        return self._policy

    def identity_cost(
        self,
        detection_probability: Decimal,
        reputation_price_usd: Decimal,
        kyc_cost_usd: Decimal = Decimal(0),
    ) -> Decimal:
        """Minimum USD cost of one fake identity under vouching.

        ``c_id ≥ m · Pr[detect] · (σ_R·price_R + σ_V) + c_KYC`` — the
        expected slashing a briber must compensate each voucher for, plus
        any residual KYC cost. Rises with the probation detection
        probability, so tighter monitoring raises the price of every fake.
        """
        if not (0 <= detection_probability <= 1):
            raise ValueError("detection_probability must lie in [0, 1]")
        stake_value = self._policy.reputation_stake.root * reputation_price_usd + (
            self._policy.collateral_stake.root
        )
        return self._policy.required_vouchers * detection_probability * stake_value + kyc_cost_usd

    def attack_cost(
        self,
        target_votes: Decimal,
        base_reputation: R,
        detection_probability: Decimal,
        reputation_price_usd: Decimal,
        kyc_cost_usd: Decimal = Decimal(0),
    ) -> Decimal:
        """Total cost to reach ``target_votes`` via ``k = Q/√r₀`` identities."""
        if base_reputation.is_zero():
            raise ValueError("base_reputation must be positive")
        accounts = target_votes / base_reputation.root.sqrt()
        per_identity = self.identity_cost(
            detection_probability, reputation_price_usd, kyc_cost_usd
        )
        return accounts * per_identity

    def slash(self, vouches: tuple[Vouch, ...], tick: int) -> tuple[R, V]:
        """Total reputation and collateral slashed from active vouchers."""
        rep = R.zero()
        collateral = V.zero()
        for vouch in vouches:
            if vouch.is_active(tick):
                rep = rep.add(vouch.reputation_stake)
                collateral = collateral + vouch.collateral_stake
        return rep, collateral
