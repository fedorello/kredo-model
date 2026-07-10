"""V4: Parameter sweep — find stability regions in (K_target, μ, δ_target, ρ_min).

Each cell of the grid runs one scenario (normal_growth) with overridden
ClubParameters and reports whether the run was stable.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.application.simulation import SimulationEngine  # noqa: E402
from app.domain.parameters import ClubParameters  # noqa: E402
from app.infrastructure.random import StdRandomProvider  # noqa: E402

from experiments.criteria import evaluate  # noqa: E402
from experiments.light_scenarios import light_normal_growth  # noqa: E402


def run(
    *,
    K_target: Decimal,
    pe_multiplier: Decimal,
    delta_target: Decimal,
    rho_min: Decimal,
    ticks: int,
    seed: int,
) -> dict:  # type: ignore[type-arg]
    base = light_normal_growth(total_ticks=ticks, seed=seed)
    overridden = ClubParameters(
        K_target=K_target,
        pe_multiplier=pe_multiplier,
        delta_target=delta_target,
        rho_min=rho_min,
    )
    state = base.initial_state.model_copy(update={"parameters": overridden})
    rng = StdRandomProvider(seed=seed)
    engine = SimulationEngine(rng=rng)
    result = engine.run(
        state,
        total_ticks=ticks,
        seed=seed,
        behavior=base.behavior,
        market=base.market,
    )
    v = evaluate(result)
    return {
        "K_target": str(K_target),
        "pe_multiplier": str(pe_multiplier),
        "delta_target": str(delta_target),
        "rho_min": str(rho_min),
        "economically_stable": v.economically_stable,
        "invariants_clean": v.invariants_clean,
        "failures": list(v.failures),
        "final_price": str(v.final_price),
        "min_price": str(v.min_price),
        "coverage_ok_ratio": str(v.coverage_ok_ratio),
        "violation_tick_ratio": str(v.violation_tick_ratio),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ticks", type=int, default=45)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--out", default="../results/parameter_sweep.json")
    args = p.parse_args()

    K_targets = [Decimal("1.0"), Decimal("1.5"), Decimal("2.0"), Decimal("2.5")]
    pe_multipliers = [Decimal("6"), Decimal("12"), Decimal("18"), Decimal("24")]
    delta_targets = [Decimal("0.02"), Decimal("0.05"), Decimal("0.10"), Decimal("0.15")]
    rho_mins = [Decimal("0.10"), Decimal("0.30"), Decimal("0.50")]

    rows: list[dict] = []  # type: ignore[type-arg]
    total = (
        len(K_targets) * len(pe_multipliers) * len(delta_targets) * len(rho_mins)
    )
    print(f"Sweeping {total} parameter combinations × {args.ticks} ticks")
    for i, (k, mu, dt, rho) in enumerate(
        itertools.product(K_targets, pe_multipliers, delta_targets, rho_mins), 1
    ):
        row = run(
            K_target=k,
            pe_multiplier=mu,
            delta_target=dt,
            rho_min=rho,
            ticks=args.ticks,
            seed=args.seed,
        )
        rows.append(row)
        econ = "✓" if row["economically_stable"] else "✗"
        clean = "✓" if row["invariants_clean"] else "✗"
        print(
            f"  [{i:3d}/{total}] [E:{econ}|I:{clean}] K={k} μ={mu} δ*={dt} ρ*={rho} "
            f"price={row['final_price']}"
        )

    econ_count = sum(1 for r in rows if r["economically_stable"])
    clean_count = sum(1 for r in rows if r["invariants_clean"])
    summary = {
        "total": total,
        "economically_stable": econ_count,
        "economic_rate": f"{econ_count / total:.2%}",
        "invariants_clean": clean_count,
        "invariants_clean_rate": f"{clean_count / total:.2%}",
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2))

    print(
        f"\n=== Economic stability: {summary['economic_rate']} "
        f"({econ_count}/{total}) | Invariants clean: "
        f"{summary['invariants_clean_rate']} ({clean_count}/{total}) ==="
    )
    print(f"Full results: {out}")


if __name__ == "__main__":
    main()
