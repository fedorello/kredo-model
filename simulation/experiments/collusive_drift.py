"""Kredo v2 — collusive price-drift detection (improvements/05).

Exercises :class:`DriftDetectorService` on synthetic category-price streams:

* the two-window rule fixes a covert-drift speed limit ``v* = κσ/137.5``;
* a drift below ``v*`` stays undetected but takes years to double a price
  (economically pointless), while a drift above ``v*`` is flagged;
* CUSUM additionally catches a small-step drift a windowed mean would smooth.

Deterministic: a seeded PRNG generates the noise so the run is reproducible.

Run: ``python -m experiments.collusive_drift`` from ``simulation/``.
"""

from __future__ import annotations

import json
import random
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.domain.services.drift_detector import DriftDetectorService  # noqa: E402

_BASE_PRICE = Decimal("100")
_NOISE_SIGMA = Decimal("10")
_KAPPA = Decimal("1.5")
_LONG_DAYS = 365
_SHORT_DAYS = 90
_SEED = 23


def _series(drift_per_day: Decimal, days: int, rng: random.Random) -> list[Decimal]:
    """Noisy prices around a mean drifting linearly from the base price."""
    out: list[Decimal] = []
    for t in range(days):
        mean = _BASE_PRICE + drift_per_day * Decimal(t)
        noise = Decimal(str(round(rng.gauss(0, float(_NOISE_SIGMA)), 4)))
        out.append(mean + noise)
    return out


def _evaluate(detector: DriftDetectorService, drift: Decimal, rng: random.Random) -> dict:  # type: ignore[type-arg]
    prices = _series(drift, _LONG_DAYS, rng)
    long_window = prices
    short_window = prices[-_SHORT_DAYS:]
    flagged = detector.two_window_flag(short_window, long_window)
    return {
        "drift_per_day": str(drift),
        "flagged": flagged,
        "steady_state_separation": str(detector.steady_state_separation(drift)),
        "days_to_double_price": str(detector.days_to_double(drift, _BASE_PRICE)),
    }


def main() -> None:
    detector = DriftDetectorService(
        short_window_days=_SHORT_DAYS,
        long_window_days=_LONG_DAYS,
        kappa=_KAPPA,
    )
    v_star = detector.max_undetected_drift_per_day(_NOISE_SIGMA)
    rng = random.Random(_SEED)

    slow = _evaluate(detector, (v_star / 2).quantize(Decimal("0.0001")), rng)
    fast = _evaluate(detector, (v_star * 2).quantize(Decimal("0.0001")), rng)

    # CUSUM catches a small-step drift below the two-window steady separation.
    step_prices = _series(v_star / 2, _LONG_DAYS, rng)
    cusum_flag = detector.cusum_flag(
        step_prices,
        anchor=_BASE_PRICE,
        slack=_NOISE_SIGMA / 2,
        threshold=Decimal(5) * _NOISE_SIGMA,
    )

    results = {
        "kappa": str(_KAPPA),
        "sigma_long": str(_NOISE_SIGMA),
        "v_star_per_day": str(v_star),
        "slow_drift_half_v_star": slow,
        "fast_drift_double_v_star": fast,
        "cusum_flag_on_slow_drift": cusum_flag,
    }

    print(f"=== Two-window drift detector (κ={_KAPPA}, σ={_NOISE_SIGMA}) ===")
    print(f"  v* (covert speed limit): {float(v_star):.4f} V/day")
    print(f"  slow drift {float(slow['drift_per_day']):.4f}/day: flagged={slow['flagged']}, "
          f"doubling takes {float(slow['days_to_double_price']):.0f} days "
          f"(~{float(slow['days_to_double_price'])/365:.1f} years)")
    print(f"  fast drift {float(fast['drift_per_day']):.4f}/day: flagged={fast['flagged']}, "
          f"separation {float(fast['steady_state_separation']):.1f} > κσ={float(_KAPPA*_NOISE_SIGMA):.1f}")
    print(f"  CUSUM on slow drift: flagged={cusum_flag}")

    out = Path("../results/collusive_drift.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2))
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
