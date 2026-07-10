"""Kredo v2 — retention channel & revenue-backed emission (improvements/01).

Two claims from improvements/01-retention-channel.md, checked on the
deterministic simulator:

1. **Survival at a constant revenue level.** With the retention channel
   (revenue → fund, ``s`` retained each quarter), a *constant* external
   revenue level — no perpetual growth — keeps the price from collapsing.
   We run a steady market and confirm the price does not fall to the floor.

2. **Graceful degradation under the currency board.** When the emission
   budget is tied to revenue (``η > 0``), a revenue *stop* halts fresh
   emission instead of letting supply keep diluting the price. We run the
   same "revenue for the first half, then nothing" market twice — with the
   cap OFF (η = 0) and ON (η = s = 0.5) — and compare how supply and price
   behave after the cutoff.

Run: ``python -m experiments.retention_analysis`` from ``simulation/``.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.application.ports.random_provider import RandomProvider  # noqa: E402
from app.application.scenarios import normal_growth_scenario  # noqa: E402
from app.application.simulation import (  # noqa: E402
    ConstantInflowMarket,
    MarketTick,
    SimulationEngine,
)
from app.domain.entities import ClubState  # noqa: E402
from app.domain.operations import RecordExternalRevenueCommand  # noqa: E402
from app.domain.parameters import ClubParameters  # noqa: E402
from app.domain.value_objects import USDC, member_id  # noqa: E402
from app.infrastructure.random import StdRandomProvider  # noqa: E402

from experiments.criteria import evaluate  # noqa: E402

_INVESTORS = tuple(member_id(f"investor-{i}") for i in range(5))


@dataclass(frozen=True, slots=True)
class PhasedRevenueMarket:
    """Constant inflows until ``stop_tick``, then a fully stagnant market."""

    active: ConstantInflowMarket
    stop_tick: int

    def commands(self, state: ClubState, tick: int, rng: RandomProvider) -> MarketTick:
        if tick >= self.stop_tick:
            return MarketTick()
        return self.active.commands(state, tick, rng)


def _with_params(base_state: ClubState, params: ClubParameters) -> ClubState:
    """Rebuild the bootstrap state with different parameters."""
    return base_state.model_copy(update={"parameters": params})


def _run(params: ClubParameters, market: object, *, ticks: int, seed: int) -> dict:  # type: ignore[type-arg]
    base = normal_growth_scenario(total_ticks=ticks, seed=seed)
    state = _with_params(base.initial_state, params)
    engine = SimulationEngine(rng=StdRandomProvider(seed=seed))
    result = engine.run(
        state,
        total_ticks=ticks,
        seed=seed,
        behavior=base.behavior,
        market=market,  # type: ignore[arg-type]
        snapshot_every=base.snapshot_every,
    )
    metrics = result.metrics
    verdict = evaluate(result)
    return {
        "economically_stable": verdict.economically_stable,
        "p_first": str(metrics[0].price_usdc_per_v),
        "p_last": str(metrics[-1].price_usdc_per_v),
        "min_price": str(verdict.min_price),
        "supply_first": str(metrics[0].supply),
        "supply_last": str(metrics[-1].supply),
        "price_series": [str(m.price_usdc_per_v) for m in metrics],
        "supply_series": [str(m.supply) for m in metrics],
    }


def survival_at_constant_revenue(*, ticks: int = 180, seed: int = 23) -> dict:  # type: ignore[type-arg]
    """Claim 1 — a constant revenue *level* (no growth) governs the long-run
    price: sweeping the level from 0 upward walks the economy from a falling
    to a rising regime (survival condition ``R ≥ (eP−λ_inv)/s`` is a level).
    """
    levels = ["0", "25", "50", "100", "200"]
    sweep = {}
    for lvl in levels:
        market = ConstantInflowMarket(
            daily_invest=USDC("100"),
            daily_revenue=USDC(lvl),
            investor_ids=_INVESTORS,
        )
        run = _run(ClubParameters(), market, ticks=ticks, seed=seed)
        p_first = float(run["p_first"])
        p_last = float(run["p_last"])
        sweep[lvl] = {
            "p_first": run["p_first"],
            "p_last": run["p_last"],
            "regime": "growth" if p_last > p_first * 1.02
            else "falling" if p_last < p_first * 0.98
            else "plateau",
            "economically_stable": run["economically_stable"],
        }
    return {"revenue_level_sweep": sweep}


def currency_board_comparison(*, ticks: int = 180, stop: int = 90, seed: int = 23) -> dict:  # type: ignore[type-arg]
    """Claim 2 — revenue stops at ``stop``; compare cap OFF vs cap ON."""
    active = ConstantInflowMarket(
        daily_invest=USDC("100"),
        daily_revenue=USDC("200"),
        investor_ids=_INVESTORS,
    )
    market = PhasedRevenueMarket(active=active, stop_tick=stop)
    off = _run(ClubParameters(), market, ticks=ticks, seed=seed)
    on = _run(
        ClubParameters(emission_budget_share=Decimal("0.5")),
        market,
        ticks=ticks,
        seed=seed,
    )
    return {"stop_tick": stop, "cap_off": off, "cap_on": on}


def main() -> None:
    out = Path("../results/retention_analysis.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    results = {
        "survival_constant_revenue": survival_at_constant_revenue(),
        "currency_board": currency_board_comparison(),
    }

    print("=== Claim 1: constant revenue LEVEL sets the regime ===")
    for lvl, r in results["survival_constant_revenue"]["revenue_level_sweep"].items():
        print(f"  revenue {lvl:>3}/day: price {r['p_first']} -> {r['p_last']}  [{r['regime']}]")

    board = results["currency_board"]
    off, on = board["cap_off"], board["cap_on"]
    stop = board["stop_tick"]
    off_s = [float(x) for x in off["supply_series"]]
    on_s = [float(x) for x in on["supply_series"]]
    print(f"\n=== Claim 2: currency board — revenue stops at tick {stop} ===")
    print(f"  cap OFF: price {off['p_first']} -> {off['p_last']}; "
          f"post-stop supply growth {off_s[-1]-off_s[stop]:+.0f}")
    print(f"  cap ON : price {on['p_first']} -> {on['p_last']}; "
          f"post-stop supply growth {on_s[-1]-on_s[stop]:+.0f}")
    print(f"  whole-run supply growth: OFF {off_s[-1]-off_s[0]:.0f} -> ON {on_s[-1]-on_s[0]:.0f}")

    out.write_text(json.dumps(results, indent=2))
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
