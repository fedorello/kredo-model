"""V6: Three regimes from math §10.3.

Math §10.4 gives the survival inequality:

    λ_rev ≥ (1/μ) · [EmissionRate · P − λ_inv]

Three runs vary λ_rev/λ_inv to demonstrate:

  Regime A  growth: λ_inv + μ·λ_rev > emission → P rises
  Regime B  stable:  inflows ≈ emission → P stable
  Regime C  falling: stagnant market → P falls (math §10.4)
"""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.application.scenarios import normal_growth_scenario  # noqa: E402
from app.application.scenarios.base import ScenarioConfig  # noqa: E402
from app.application.simulation import (  # noqa: E402
    CompositeMarket,
    ConstantInflowMarket,
    SimulationEngine,
    StagnantMarket,
)
from app.domain.value_objects import USDC, member_id  # noqa: E402
from app.infrastructure.random import StdRandomProvider  # noqa: E402

from experiments.criteria import evaluate  # noqa: E402


def run(cfg: ScenarioConfig) -> dict:  # type: ignore[type-arg]
    rng = StdRandomProvider(seed=cfg.seed)
    engine = SimulationEngine(rng=rng)
    result = engine.run(
        cfg.initial_state,
        total_ticks=cfg.total_ticks,
        seed=cfg.seed,
        behavior=cfg.behavior,
        market=cfg.market,
        snapshot_every=cfg.snapshot_every,
    )
    v = evaluate(result)
    metrics = result.metrics
    p_first = metrics[0].price_usdc_per_v if metrics else Decimal(0)
    p_last = metrics[-1].price_usdc_per_v if metrics else Decimal(0)
    return {
        "stable": v.stable,
        "failures": list(v.failures),
        "p_first": str(p_first),
        "p_last": str(p_last),
        "p_delta": str(p_last - p_first),
        "min_price": str(v.min_price),
        "violation_tick_ratio": str(v.violation_tick_ratio),
    }


def make(market_kind: str, *, ticks: int = 60, seed: int = 23) -> ScenarioConfig:
    base = normal_growth_scenario(total_ticks=ticks, seed=seed)
    investor_ids = tuple(member_id(f"investor-{i}") for i in range(5))
    if market_kind == "growth":
        market = CompositeMarket(
            parts=(
                ConstantInflowMarket(
                    daily_invest=USDC("500"),
                    daily_revenue=USDC("200"),
                    investor_ids=investor_ids,
                ),
            )
        )
    elif market_kind == "stable":
        market = ConstantInflowMarket(
            daily_invest=USDC("100"),
            daily_revenue=USDC("100"),
            investor_ids=investor_ids,
        )
    elif market_kind == "stagnant":
        market = StagnantMarket()
    else:
        raise ValueError(market_kind)
    return ScenarioConfig(
        name=f"regime_{market_kind}",
        description=f"regime {market_kind}",
        seed=seed,
        total_ticks=ticks,
        initial_state=base.initial_state,
        behavior=base.behavior,
        market=market,
        snapshot_every=base.snapshot_every,
    )


def main() -> None:
    out = Path("../results/regime_analysis.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict] = {}  # type: ignore[type-arg]
    for kind in ("growth", "stable", "stagnant"):
        print(f"=== {kind} regime ===")
        results[kind] = run(make(kind))
        for k, v in results[kind].items():
            print(f"  {k}: {v}")
        print()
    out.write_text(json.dumps(results, indent=2))
    print(f"Saved to {out}")


if __name__ == "__main__":
    main()
