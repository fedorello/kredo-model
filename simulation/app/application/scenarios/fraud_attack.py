"""Scenario 3 — Fraud attack (math §6.3).

A 20-account cluster does fictitious transactions among themselves. Detection
is modeled in Phase 6 only by the *absence* of confidence — the auto-score
catches obvious wash trades (same large amount, same partners) by raising
HHI in the OTHER category. Full audit-driven detection lands in later
extensions.

Doc-table reference (after detection, P should recover toward baseline):

    | event                       | S        | P       |
    |-----------------------------|----------|---------|
    | mature steady state         | 150 000  | 5.33    |
    | post-fraud (50k V minted)   | 225 000  | ~3.55   |
    | post-detection (burn 75k V) | 150 000  | 5.33    |
"""

from __future__ import annotations

from app.application.scenarios.base import (
    BootstrapMember,
    ScenarioConfig,
    build_initial_state,
)
from app.application.simulation.behavior import (
    CompositeBehavior,
    FraudClusterBehavior,
    NormalActivityBehavior,
)
from app.application.simulation.market import (
    ConstantInflowMarket,
    MarketModel,
)
from app.domain.value_objects import USDC, V, member_id


def fraud_attack_scenario(total_ticks: int = 30, seed: int = 99) -> ScenarioConfig:
    fraud_cluster = tuple(member_id(f"fraud-{i:02d}") for i in range(20))
    members = [
        *(BootstrapMember(name=f"clean-{i:03d}", balance=V(150)) for i in range(80)),
        *(BootstrapMember(name=str(mid), balance=V(150)) for mid in fraud_cluster),
    ]
    state = build_initial_state(
        members=members,
        fund_usdc=USDC(200_000),
        genesis_pool=V(100_000),
        ext_rev_annualized=USDC(50_000),
    )
    market: MarketModel = ConstantInflowMarket(
        daily_invest=USDC.zero(),
        daily_revenue=USDC("137"),
        investor_ids=(),
    )
    behavior = CompositeBehavior(
        parts=(
            NormalActivityBehavior(
                daily_join_prob=__import__("decimal").Decimal("0.0"),
                daily_tx_per_member=__import__("decimal").Decimal("0.05"),
            ),
            FraudClusterBehavior(members=fraud_cluster),
        )
    )
    return ScenarioConfig(
        name="fraud_attack",
        description="Math §6.3 — 20-account wash-trade cluster",
        seed=seed,
        total_ticks=total_ticks,
        initial_state=state,
        behavior=behavior,
        market=market,
    )
