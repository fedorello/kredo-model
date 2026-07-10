"""Scenario 2 — Mature steady state (math §6.2).

Bootstrap:
    1 000 members, F = 200 000 USDC, S = 150 000 V, ExtRev = 50 000/year
    P = (200k + 12·50k) / 150k = 5.33 USDC/V
    Stable growth: +30 members/month, ExtRev grows 5 %/month

Doc-table reference (price climbs because external revenue outpaces emission):

    | month | S       | F        | ExtRev | P     |
    |-------|---------|----------|--------|-------|
    | 0     | 150 000 | 200 000  | 50 000 | 5.33  |
    | 12    | 248 000 | 298 000  | 90 000 | 5.55  |
"""

from __future__ import annotations

from decimal import Decimal

from app.application.scenarios.base import (
    BootstrapMember,
    ScenarioConfig,
    build_initial_state,
)
from app.application.simulation.behavior import (
    BehaviorModel,
    NormalActivityBehavior,
)
from app.application.simulation.market import (
    CompositeMarket,
    ConstantInflowMarket,
    GrowthMarket,
    MarketModel,
)
from app.domain.value_objects import USDC, MemberKind, V, member_id


def _members(n: int = 1000) -> list[BootstrapMember]:
    return [BootstrapMember(name=f"member-{i:04d}", balance=V(150)) for i in range(n)]


def _market() -> MarketModel:
    investor_ids = tuple(member_id(f"investor-{i}") for i in range(10))
    return CompositeMarket(
        parts=(
            ConstantInflowMarket(
                daily_invest=USDC.zero(),  # mature: investment optional
                daily_revenue=USDC("137"),  # ≈ 50 000 / 365
                investor_ids=investor_ids,
            ),
            GrowthMarket(
                initial_revenue=USDC.zero(),
                daily_growth_rate=Decimal("0.00163"),  # ≈ 5 %/month
            ),
        )
    )


def _behavior() -> BehaviorModel:
    return NormalActivityBehavior(
        daily_join_prob=Decimal("1.0"),  # 30/month → ~1/day
        daily_tx_per_member=Decimal("0.13"),
        avg_amount=V(50),
    )


def mature_steady_scenario(total_ticks: int = 365, seed: int = 42) -> ScenarioConfig:
    investors = [
        BootstrapMember(name=f"investor-{i}", balance=V(100), kind=MemberKind.INVESTOR)
        for i in range(10)
    ]
    # genesis_pool=0 keeps S=150_000 so the initial price matches the
    # doc reference: (200k + 12*50k)/150k = 5.33 USDC/V.
    state = build_initial_state(
        members=[*_members(), *investors],
        fund_usdc=USDC(200_000),
        genesis_pool=V.zero(),
        ext_rev_annualized=USDC(50_000),
    )
    return ScenarioConfig(
        name="mature_steady",
        description="Math §6.2 — stable price growth from sustained ExtRev",
        seed=seed,
        total_ticks=total_ticks,
        initial_state=state,
        behavior=_behavior(),
        market=_market(),
    )
