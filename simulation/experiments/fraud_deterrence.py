"""Kredo v2 — fraud deterrence via dynamic lock-up & audit escalation (04).

Reproduces the paper's Theorem 4–5 numbers from :class:`FraudDeterrenceService`
and shows how the two v2 levers close the deterrence gap that the default
parameters leave open (Λ = 300 V < 1/β ≈ 1642 V):

* **Baseline** (a=0.03, τ0=60, w=0): a profitable optimum survives.
* **Dynamic lock-up** (w > 0): steepens the survival decay to β' = β + w·p',
  so the default stake Λ = 300 becomes sufficient.
* **Flagged audit** (a = 0.30): 1/β_flag ≈ 140 V < 300, deterred outright.

Run: ``python -m experiments.fraud_deterrence`` from ``simulation/``.
"""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.domain.services.fraud_deterrence import FraudDeterrenceService  # noqa: E402

_N_BAR = Decimal("50")
_STAKE = Decimal("300")
_DETECTION_PER_DAY = Decimal("0.05")  # p — probability a cluster is caught per day


def _table(service: FraudDeterrenceService, stake: Decimal) -> dict:  # type: ignore[type-arg]
    thefts = [Decimal(w) for w in (500, 1000, 2500, 5000, 10000)]
    return {
        "1_over_beta": str(service.deterrence_threshold_stake()),
        "optimal_theft_W_dagger": str(service.optimal_theft(stake)),
        "max_profit": str(service.max_profit(stake)),
        "deterred": service.is_deterred(stake),
        "expected_profit_bound": {
            str(w): str(service.expected_profit_bound(w, stake)) for w in thefts
        },
    }


def baseline() -> dict:  # type: ignore[type-arg]
    """Default parameters — the open deterrence gap the paper reports."""
    service = FraudDeterrenceService(
        mean_tx_size=_N_BAR,
        audit_rate=Decimal("0.03"),
        lockup_days=60,
        detection_per_day=Decimal("0"),  # paper Table 7: audit factor only
        lockup_per_v=Decimal("0"),
    )
    return _table(service, _STAKE)


def dynamic_lockup() -> dict:  # type: ignore[type-arg]
    """Lever 1 — vesting w chosen to meet the threshold at the default stake."""
    # Required β' ≥ 1/Λ ⇒ w ≥ (1/Λ − β)/p'. Solve, then verify.
    probe = FraudDeterrenceService(
        mean_tx_size=_N_BAR,
        audit_rate=Decimal("0.03"),
        lockup_days=60,
        detection_per_day=_DETECTION_PER_DAY,
    )
    beta = probe.beta
    p_prime = (Decimal(1) / (Decimal(1) - _DETECTION_PER_DAY)).ln()
    required_w = (Decimal(1) / _STAKE - beta) / p_prime
    service = FraudDeterrenceService(
        mean_tx_size=_N_BAR,
        audit_rate=Decimal("0.03"),
        lockup_days=60,
        detection_per_day=_DETECTION_PER_DAY,
        lockup_per_v=required_w,
    )
    out = _table(service, _STAKE)
    out["required_w_days_per_v"] = str(required_w)
    out["extra_lockup_per_100v_days"] = str(required_w * 100)
    return out


def flagged_audit() -> dict:  # type: ignore[type-arg]
    """Lever 2 — a flagged cluster is audited at 30 %: deterred outright."""
    service = FraudDeterrenceService(
        mean_tx_size=_N_BAR,
        audit_rate=Decimal("0.30"),
        lockup_days=60,
        detection_per_day=Decimal("0"),
        lockup_per_v=Decimal("0"),
    )
    return _table(service, _STAKE)


def main() -> None:
    out = Path("../results/fraud_deterrence.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    results = {
        "stake": str(_STAKE),
        "baseline": baseline(),
        "dynamic_lockup": dynamic_lockup(),
        "flagged_audit": flagged_audit(),
    }

    b = results["baseline"]
    print("=== Baseline (a=0.03, Λ=300) ===")
    print(f"  1/β = {float(b['1_over_beta']):.0f} V, W† = {float(b['optimal_theft_W_dagger']):.0f} V, "
          f"max profit = {float(b['max_profit']):+.0f} V, deterred = {b['deterred']}")

    d = results["dynamic_lockup"]
    print("\n=== Dynamic lock-up (p=5%/day) ===")
    print(f"  required w = {float(d['required_w_days_per_v']):.3f} d/V "
          f"(≈ {float(d['extra_lockup_per_100v_days']):.1f} d per 100 V)")
    print(f"  max profit = {float(d['max_profit']):+.2f} V, deterred = {d['deterred']}")

    f = results["flagged_audit"]
    print("\n=== Flagged audit (a=0.30) ===")
    print(f"  1/β_flag = {float(f['1_over_beta']):.0f} V < Λ=300, "
          f"max profit = {float(f['max_profit']):+.2f} V, deterred = {f['deterred']}")

    out.write_text(json.dumps(results, indent=2))
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
