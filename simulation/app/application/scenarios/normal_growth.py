"""Scenario 1 — Normal growth (math §6.1).

Bootstrap:
    100 members each with V(100) welcome grant
    F = 10 000 USDC, S = 10 000 V (matches grants)
    Price = 1.0 USDC/V
    +20 members/month
    4 transactions/month/member, average 50 V
    Default rate ~5 %
    ExtRev grows from 0 to ~2 000 USDC/month over the year
    Investment ~5 000 USDC/month

Doc-table reference (P falls because emission outpaces ExtRev growth):

    | month | members | S       | F      | ExtRev | P    |
    |-------|---------|---------|--------|--------|------|
    | 0     | 100     | 10 000  | 10 000 |     0  | 1.00 |
    | 12    | 340     | 175 200 | 93 200 | 24 000 | 0.53 |
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
    CompositeMarket as _Composite,
)
from app.application.simulation.market import (
    ConstantInflowMarket,
    GrowthMarket,
    MarketModel,
)
from app.domain.value_objects import USDC, MemberKind, V, member_id


def _build_members() -> list[BootstrapMember]:
    return [BootstrapMember(name=f"founder-{i:03d}", balance=V(100)) for i in range(100)]


def _market(investor_count: int = 5) -> MarketModel:
    """Investment + growing external revenue.

    daily_invest ≈ 5 000 USDC / 30 days = 167 USDC/day across investors.
    daily_revenue grows from ~0 to 67 USDC/day (≈ 2 000/month) over 365 days.
    """
    investor_ids = tuple(member_id(f"investor-{i}") for i in range(investor_count))
    investments = ConstantInflowMarket(
        daily_invest=USDC("167"),
        daily_revenue=USDC.zero(),
        investor_ids=investor_ids,
    )
    revenue_growth = GrowthMarket(
        initial_revenue=USDC("1"),
        daily_growth_rate=Decimal("0.0117"),  # ≈ 35 % monthly compound
    )
    return _Composite(parts=(investments, revenue_growth))


def _behavior() -> BehaviorModel:
    return NormalActivityBehavior(
        daily_join_prob=Decimal("0.65"),  # ~20 / 30 days
        daily_tx_per_member=Decimal("0.13"),  # 4 / 30 days
        avg_amount=V(50),
    )


def normal_growth_scenario(total_ticks: int = 365, seed: int = 42) -> ScenarioConfig:
    state = build_initial_state(
        members=[
            *_build_members(),
            *(
                BootstrapMember(
                    name=f"investor-{i}",
                    balance=V(100),
                    kind=MemberKind.INVESTOR,
                )
                for i in range(5)
            ),
        ],
        fund_usdc=USDC(10_000),
        genesis_pool=V(50_000),  # capacity for newcomers
    )
    return ScenarioConfig(
        name="normal_growth",
        description="Math §6.1 — 100→340 members, growing ExtRev, defaults 5 %",
        seed=seed,
        total_ticks=total_ticks,
        initial_state=state,
        behavior=_behavior(),
        market=_market(),
    )
