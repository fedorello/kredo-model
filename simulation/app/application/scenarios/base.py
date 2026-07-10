"""Scenario primitives: ScenarioConfig + bootstrap factories."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.application.simulation.behavior import BehaviorModel
from app.application.simulation.market import MarketModel
from app.domain.entities import (
    ClubState,
    GenesisPool,
    LiquidityFund,
    Member,
)
from app.domain.parameters import ClubParameters
from app.domain.value_objects import (
    USDC,
    MemberId,
    MemberKind,
    R,
    V,
    member_id,
)


@dataclass(frozen=True, slots=True)
class ScenarioConfig:
    """A complete simulation scenario.

    The engine accepts ``(initial_state, behavior, market, total_ticks, seed)``;
    a ScenarioConfig packages all of these plus a human-readable name and
    description.
    """

    name: str
    description: str
    seed: int
    total_ticks: int
    initial_state: ClubState
    behavior: BehaviorModel
    market: MarketModel
    snapshot_every: int = 30


@dataclass(frozen=True, slots=True)
class BootstrapMember:
    """Inputs for a pre-seeded member when constructing a scenario state."""

    name: str
    balance: V
    kind: MemberKind = MemberKind.ACTIVE
    reputation: R = field(default_factory=R.zero)


def build_initial_state(
    *,
    members: list[BootstrapMember],
    fund_usdc: USDC,
    genesis_pool: V,
    ext_rev_annualized: USDC = USDC.zero(),  # noqa: B008
    parameters: ClubParameters | None = None,
    pre_locked_until: int = 0,
) -> ClubState:
    """Compose a starting ClubState from a member roster.

    ``pre_locked_until`` lets scenarios mark members as past-lock-up
    immediately so Convert doesn't reject them in tick 0.
    """
    members_dict: dict[MemberId, Member] = {}
    initial_grants = V.zero()
    for spec in members:
        mid = member_id(spec.name)
        members_dict[mid] = Member(
            id=mid,
            kind=spec.kind,
            balance=spec.balance,
            reputation=spec.reputation,
            joined_at=0,
            frozen_until=pre_locked_until if pre_locked_until > 0 else None,
        )
        if spec.balance.is_positive():
            initial_grants = initial_grants + spec.balance
    return ClubState(
        tick=0,
        members=members_dict,
        fund=LiquidityFund(balance=fund_usdc),
        genesis=GenesisPool(
            balance=genesis_pool,
            cumulative_funded=genesis_pool + initial_grants,
        ),
        ext_rev_annualized=ext_rev_annualized,
        initial_genesis_grants=initial_grants,
        parameters=parameters or ClubParameters(),
    )
