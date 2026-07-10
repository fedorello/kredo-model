"""Monte Carlo: N seeds × 4 baseline scenarios.

Outputs JSON with pass/fail rate, percentiles of price/supply, and
typical failure modes.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.application.simulation import SimulationEngine  # noqa: E402
from app.infrastructure.random import StdRandomProvider  # noqa: E402

from experiments.criteria import evaluate  # noqa: E402
from experiments.light_scenarios import (  # noqa: E402
    light_bank_run,
    light_fraud_attack,
    light_mature_steady,
    light_normal_growth,
)


SCENARIOS = {
    "normal_growth": lambda seed, ticks: light_normal_growth(total_ticks=ticks, seed=seed),
    "mature_steady": lambda seed, ticks: light_mature_steady(total_ticks=ticks, seed=seed),
    "fraud_attack": lambda seed, ticks: light_fraud_attack(total_ticks=ticks, seed=seed),
    "bank_run": lambda seed, ticks: light_bank_run(total_ticks=ticks, seed=seed),
}


def run_one(scenario_name: str, seed: int, ticks: int) -> dict:  # type: ignore[type-arg]
    cfg = SCENARIOS[scenario_name](seed, ticks)
    rng = StdRandomProvider(seed=seed)
    engine = SimulationEngine(rng=rng)
    t0 = time.perf_counter()
    result = engine.run(
        cfg.initial_state,
        total_ticks=cfg.total_ticks,
        seed=cfg.seed,
        behavior=cfg.behavior,
        market=cfg.market,
        snapshot_every=cfg.snapshot_every,
    )
    elapsed = time.perf_counter() - t0
    verdict = evaluate(result)
    return {
        "scenario": scenario_name,
        "seed": seed,
        "ticks": ticks,
        "elapsed_s": round(elapsed, 3),
        "economically_stable": verdict.economically_stable,
        "invariants_clean": verdict.invariants_clean,
        "failures": list(verdict.failures),
        "final_price": str(verdict.final_price),
        "min_price": str(verdict.min_price),
        "coverage_ok_ratio": str(verdict.coverage_ok_ratio),
        "max_frozen_ratio": str(verdict.max_frozen_ratio),
        "violation_tick_ratio": str(verdict.violation_tick_ratio),
        "final_supply": str(verdict.final_supply),
        "invariant_violations": result.invariant_violations,
    }


def aggregate(rows: list[dict]) -> dict:  # type: ignore[type-arg]
    by_scenario: dict[str, list[dict]] = {}  # type: ignore[type-arg]
    for r in rows:
        by_scenario.setdefault(r["scenario"], []).append(r)
    summary: dict[str, dict] = {}  # type: ignore[type-arg]
    for sc, items in by_scenario.items():
        prices = [Decimal(i["final_price"]) for i in items]
        econ_count = sum(1 for i in items if i["economically_stable"])
        clean_count = sum(1 for i in items if i["invariants_clean"])
        fail_counter: dict[str, int] = {}
        for i in items:
            for f in i["failures"]:
                code = f.split()[0]
                fail_counter[code] = fail_counter.get(code, 0) + 1
        summary[sc] = {
            "runs": len(items),
            "economically_stable": econ_count,
            "economic_rate": f"{econ_count / len(items):.2%}",
            "invariants_clean": clean_count,
            "invariants_clean_rate": f"{clean_count / len(items):.2%}",
            "price_p50": str(statistics.median(prices)),
            "price_min": str(min(prices)),
            "price_max": str(max(prices)),
            "median_elapsed_s": statistics.median(i["elapsed_s"] for i in items),
            "failure_modes": fail_counter,
        }
    return summary


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=30)
    p.add_argument("--ticks", type=int, default=60)
    p.add_argument("--out", default="../results/monte_carlo.json")
    args = p.parse_args()

    rows: list[dict] = []  # type: ignore[type-arg]
    print(f"Running {args.seeds} seeds × {len(SCENARIOS)} scenarios × {args.ticks} ticks")
    for sc in SCENARIOS:
        for seed in range(1, args.seeds + 1):
            row = run_one(sc, seed, args.ticks)
            rows.append(row)
            econ = "✓" if row["economically_stable"] else "✗"
            clean = "✓" if row["invariants_clean"] else "✗"
            print(
                f"  [E:{econ}|I:{clean}] {sc} seed={seed:3d} t={row['elapsed_s']:.2f}s "
                f"price={row['final_price']:>10s} viol={row['invariant_violations']}"
            )

    summary = aggregate(rows)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps({"summary": summary, "rows": rows}, indent=2, default=str)
    )
    print()
    print("=== SUMMARY ===")
    for sc, stats in summary.items():
        print(
            f"  {sc:15s} econ={stats['economic_rate']:>7s} "
            f"({stats['economically_stable']}/{stats['runs']}) "
            f"clean={stats['invariants_clean_rate']:>7s} "
            f"price_p50={stats['price_p50']:>10s} "
            f"failures={stats['failure_modes']}"
        )
    print(f"\nFull results: {out_path}")


if __name__ == "__main__":
    main()
