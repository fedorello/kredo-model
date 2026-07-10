"""V5: Stress tests — combined attacks, stagnant market.

Three runs, each demonstrating system behaviour under adversarial
conditions:

  1. Stagnant market (math §10.4): no ExtRev → price-falling regime.
  2. Fraud cluster + simultaneous bank-run.
  3. Aggressive bank run with large fraction.
"""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.application.scenarios import (  # noqa: E402
    bank_run_scenario,
    fraud_attack_scenario,
    normal_growth_scenario,
)
from app.application.scenarios.base import ScenarioConfig  # noqa: E402
from app.application.simulation import (  # noqa: E402
    BankRunBehavior,
    CompositeBehavior,
    FraudClusterBehavior,
    NormalActivityBehavior,
    SimulationEngine,
    StagnantMarket,
)
from app.domain.value_objects import member_id  # noqa: E402
from app.infrastructure.random import StdRandomProvider  # noqa: E402

from experiments.criteria import evaluate  # noqa: E402


def run_scenario(scenario: ScenarioConfig) -> dict:  # type: ignore[type-arg]
    rng = StdRandomProvider(seed=scenario.seed)
    engine = SimulationEngine(rng=rng)
    result = engine.run(
        scenario.initial_state,
        total_ticks=scenario.total_ticks,
        seed=scenario.seed,
        behavior=scenario.behavior,
        market=scenario.market,
        snapshot_every=scenario.snapshot_every,
    )
    v = evaluate(result)
    return {
        "stable": v.stable,
        "failures": list(v.failures),
        "final_price": str(v.final_price),
        "min_price": str(v.min_price),
        "coverage_ok_ratio": str(v.coverage_ok_ratio),
        "max_frozen_ratio": str(v.max_frozen_ratio),
        "violation_tick_ratio": str(v.violation_tick_ratio),
        "final_supply": str(v.final_supply),
        "invariant_violations": result.invariant_violations,
    }


def stagnant_market_run() -> dict:  # type: ignore[type-arg]
    """math §10.4: without ExtRev the price is mathematically condemned."""
    base = normal_growth_scenario(total_ticks=45, seed=11)
    cfg = ScenarioConfig(
        name=base.name,
        description="stagnant: zero ExtRev",
        seed=base.seed,
        total_ticks=base.total_ticks,
        initial_state=base.initial_state,
        behavior=base.behavior,
        market=StagnantMarket(),
        snapshot_every=base.snapshot_every,
    )
    return run_scenario(cfg)


def fraud_plus_bank_run() -> dict:  # type: ignore[type-arg]
    """Fraud cluster active throughout; bank run on day 25."""
    base = fraud_attack_scenario(total_ticks=30, seed=13)
    fraud_cluster = tuple(member_id(f"fraud-{i:02d}") for i in range(20))
    behavior = CompositeBehavior(
        parts=(
            NormalActivityBehavior(daily_join_prob=Decimal("0.0"), daily_tx_per_member=Decimal("0.05")),
            FraudClusterBehavior(members=fraud_cluster),
            BankRunBehavior(trigger_tick=25, fraction=Decimal("0.5")),
        )
    )
    cfg = ScenarioConfig(
        name="fraud_and_bankrun",
        description="combined fraud cluster + bank run",
        seed=base.seed,
        total_ticks=base.total_ticks,
        initial_state=base.initial_state,
        behavior=behavior,
        market=base.market,
        snapshot_every=base.snapshot_every,
    )
    return run_scenario(cfg)


def aggressive_bank_run() -> dict:  # type: ignore[type-arg]
    """Bank run with 70 % of members."""
    base = bank_run_scenario(total_ticks=30, seed=17, trigger_tick=20, fraction=Decimal("0.7"))
    return run_scenario(base)


def main() -> None:
    out = Path("../results/stress_tests.json")
    out.parent.mkdir(parents=True, exist_ok=True)

    cases = [
        ("stagnant_market", stagnant_market_run),
        ("fraud_plus_bank_run", fraud_plus_bank_run),
        ("aggressive_bank_run", aggressive_bank_run),
    ]
    rows: dict[str, dict] = {}  # type: ignore[type-arg]
    for name, fn in cases:
        print(f"=== {name} ===")
        rows[name] = fn()
        for k, v in rows[name].items():
            print(f"  {k}: {v}")
        print()

    out.write_text(json.dumps(rows, indent=2))
    print(f"Saved to {out}")


if __name__ == "__main__":
    main()
