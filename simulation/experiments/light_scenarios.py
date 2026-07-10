"""Lite scenarios sized for Monte Carlo / sweep runs.

Same shape as ``app.application.scenarios.*`` but with a smaller member
roster so each run finishes in under one second.
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.application.scenarios.base import (  # noqa: E402
    BootstrapMember,
    ScenarioConfig,
    build_initial_state,
)
from app.application.simulation import (  # noqa: E402
    BankRunBehavior,
    CompositeBehavior,
    CompositeMarket,
    ConstantInflowMarket,
    FraudClusterBehavior,
    GrowthMarket,
    NormalActivityBehavior,
    StagnantMarket,
)
from app.domain.value_objects import USDC, MemberKind, V, member_id  # noqa: E402


def _market_growing(investor_ids):  # type: ignore[no-untyped-def]
    return CompositeMarket(
        parts=(
            ConstantInflowMarket(
                daily_invest=USDC("50"),
                daily_revenue=USDC("0"),
                investor_ids=investor_ids,
            ),
            GrowthMarket(
                initial_revenue=USDC("1"),
                daily_growth_rate=Decimal("0.0117"),
            ),
        )
    )


def light_normal_growth(*, total_ticks: int = 30, seed: int = 1) -> ScenarioConfig:
    members = [BootstrapMember(name=f"f-{i:02d}", balance=V(100)) for i in range(20)]
    investors = [
        BootstrapMember(name=f"investor-{i}", balance=V(100), kind=MemberKind.INVESTOR)
        for i in range(3)
    ]
    state = build_initial_state(
        members=[*members, *investors],
        fund_usdc=USDC(2000),
        genesis_pool=V(10_000),
    )
    return ScenarioConfig(
        name="lite_normal_growth",
        description="20 founders + Poisson joins + growing ExtRev",
        seed=seed,
        total_ticks=total_ticks,
        initial_state=state,
        behavior=NormalActivityBehavior(
            daily_join_prob=Decimal("0.5"),
            daily_tx_per_member=Decimal("0.15"),
            avg_amount=V(50),
        ),
        market=_market_growing(tuple(member_id(f"investor-{i}") for i in range(3))),
    )


def light_mature_steady(*, total_ticks: int = 30, seed: int = 1) -> ScenarioConfig:
    members = [BootstrapMember(name=f"m-{i:03d}", balance=V(150)) for i in range(50)]
    investors = [
        BootstrapMember(name=f"investor-{i}", balance=V(100), kind=MemberKind.INVESTOR)
        for i in range(3)
    ]
    state = build_initial_state(
        members=[*members, *investors],
        fund_usdc=USDC(10_000),
        genesis_pool=V.zero(),
        ext_rev_annualized=USDC(2_500),
    )
    return ScenarioConfig(
        name="lite_mature_steady",
        description="50 members, mature P~5.33 cousin",
        seed=seed,
        total_ticks=total_ticks,
        initial_state=state,
        behavior=NormalActivityBehavior(
            daily_join_prob=Decimal("0.5"),
            daily_tx_per_member=Decimal("0.13"),
            avg_amount=V(50),
        ),
        market=ConstantInflowMarket(
            daily_invest=USDC.zero(),
            daily_revenue=USDC("7"),
            investor_ids=(),
        ),
    )


def light_fraud_attack(*, total_ticks: int = 20, seed: int = 1) -> ScenarioConfig:
    fraud_ids = tuple(member_id(f"fraud-{i:02d}") for i in range(8))
    cleans = [BootstrapMember(name=f"clean-{i:02d}", balance=V(150)) for i in range(20)]
    frauds = [BootstrapMember(name=str(mid), balance=V(150)) for mid in fraud_ids]
    state = build_initial_state(
        members=[*cleans, *frauds],
        fund_usdc=USDC(10_000),
        genesis_pool=V(2_000),
        ext_rev_annualized=USDC(2_500),
    )
    behavior = CompositeBehavior(
        parts=(
            NormalActivityBehavior(
                daily_join_prob=Decimal("0.0"),
                daily_tx_per_member=Decimal("0.05"),
            ),
            FraudClusterBehavior(members=fraud_ids),
        )
    )
    return ScenarioConfig(
        name="lite_fraud_attack",
        description="8-account fraud cluster within 28 members",
        seed=seed,
        total_ticks=total_ticks,
        initial_state=state,
        behavior=behavior,
        market=ConstantInflowMarket(
            daily_invest=USDC.zero(),
            daily_revenue=USDC("7"),
            investor_ids=(),
        ),
    )


def light_bank_run(
    *,
    total_ticks: int = 25,
    seed: int = 1,
    trigger_tick: int | None = None,
    fraction: Decimal = Decimal("0.3"),
) -> ScenarioConfig:
    members = [BootstrapMember(name=f"m-{i:02d}", balance=V(150)) for i in range(40)]
    state = build_initial_state(
        members=members,
        fund_usdc=USDC(10_000),
        genesis_pool=V.zero(),
        ext_rev_annualized=USDC(2_500),
    )
    return ScenarioConfig(
        name="lite_bank_run",
        description=f"30 % bank run on tick {trigger_tick or total_ticks // 2}",
        seed=seed,
        total_ticks=total_ticks,
        initial_state=state,
        behavior=BankRunBehavior(
            trigger_tick=trigger_tick if trigger_tick is not None else total_ticks // 2,
            fraction=fraction,
        ),
        market=ConstantInflowMarket(
            daily_invest=USDC.zero(),
            daily_revenue=USDC("7"),
            investor_ids=(),
        ),
    )


def stagnant_lite(*, total_ticks: int = 60, seed: int = 1) -> ScenarioConfig:
    cfg = light_normal_growth(total_ticks=total_ticks, seed=seed)
    return ScenarioConfig(
        name="lite_stagnant",
        description="lite normal growth, ExtRev=0 (math §10.4)",
        seed=cfg.seed,
        total_ticks=cfg.total_ticks,
        initial_state=cfg.initial_state,
        behavior=cfg.behavior,
        market=StagnantMarket(),
        snapshot_every=cfg.snapshot_every,
    )
