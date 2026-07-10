"""Scenario 4 — Bank run (math §6.4).

Mature steady state, then 30 % of members request Convert simultaneously.
Without protection F empties; with the withdrawal queue + discount, the
queue absorbs the wave at increasingly punitive prices, recovering ρ.

Architecture §15 / math §7.3 give the linear discount schedule:
``P_actual = P · min(1, ρ/ρ*)`` with ρ* = 0.3 by default.
"""

from __future__ import annotations

from decimal import Decimal

from app.application.scenarios.base import (
    BootstrapMember,
    ScenarioConfig,
    build_initial_state,
)
from app.application.simulation.behavior import (
    BankRunBehavior,
    BehaviorModel,
)
from app.application.simulation.market import (
    ConstantInflowMarket,
    MarketModel,
)
from app.domain.parameters import ClubParameters
from app.domain.value_objects import USDC, V


def bank_run_scenario(
    total_ticks: int = 90,
    seed: int = 7,
    trigger_tick: int = 60,
    fraction: Decimal = Decimal("0.3"),
) -> ScenarioConfig:
    """Mature state, run on day ``trigger_tick``."""
    # Mature setup — 100 members holding 150 V each.
    members = [BootstrapMember(name=f"member-{i:03d}", balance=V(150)) for i in range(100)]
    state = build_initial_state(
        members=members,
        fund_usdc=USDC(200_000),
        genesis_pool=V(100_000),
        ext_rev_annualized=USDC(50_000),
        parameters=ClubParameters(),
        # Past lock-up so Convert succeeds at trigger_tick.
        pre_locked_until=0,
    )
    behavior: BehaviorModel = BankRunBehavior(trigger_tick=trigger_tick, fraction=fraction)
    market: MarketModel = ConstantInflowMarket(
        daily_invest=USDC.zero(),
        daily_revenue=USDC("137"),
        investor_ids=(),
    )
    return ScenarioConfig(
        name="bank_run",
        description="Math §6.4 — 30 % of members Convert at trigger_tick",
        seed=seed,
        total_ticks=total_ticks,
        initial_state=state,
        behavior=behavior,
        market=market,
    )
