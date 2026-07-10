"""Kredo v2 — Sybil-defense analysis (improvements/03).

Governance events are out of scope for the simulation engine (see
voting.py), so the three Sybil defenses are exercised here at the service
level, using the *real* domain services:

* **Diversity-weighted voting** (``VotingService`` + ``ConcentrationMonitor``):
  a wash cluster trading within itself gets HHI → 1 → D → floor, so its
  votes are scaled down. We compute how many fake identities are needed to
  reach a reputation majority, with and without the D-weight.

* **Reputation decay** (``ReputationDecayService``): an idle fleet's voting
  weight melts with the inactivity half-life.

* **Vouching with slashing** (``VouchingService``): the per-identity attack
  cost once each fake must be vouched for by real members who are slashed on
  fraud.

Run: ``python -m experiments.sybil_attack`` from ``simulation/``.
"""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.domain.services.concentration import ConcentrationMonitor  # noqa: E402
from app.domain.services.reputation_decay import ReputationDecayService  # noqa: E402
from app.domain.services.voting import VotingService  # noqa: E402
from app.domain.services.vouching import VouchingService  # noqa: E402
from app.domain.parameters import ClubParameters  # noqa: E402
from app.domain.value_objects import R, V, member_id  # noqa: E402

_HONEST_N = 1000
_HONEST_R = R(100)
_FAKE_R = R("0.5")
_THETA = Decimal("0.5")


def _honest_counterparty_hhi() -> Decimal:
    """An honest member trades evenly across 10 counterparties."""
    monitor = ConcentrationMonitor()
    volumes = {member_id(f"cp-{i}"): V(10) for i in range(10)}
    return monitor.hhi(volumes)


def _fake_counterparty_hhi() -> Decimal:
    """A fake account trades only with its single cluster partner."""
    monitor = ConcentrationMonitor()
    return monitor.hhi({member_id("cluster-partner"): V(10)})


def diversity_defense() -> dict:  # type: ignore[type-arg]
    """How many fakes reach a reputation majority, with vs without D-weight?"""
    voting = VotingService()
    honest_hhi = _honest_counterparty_hhi()
    fake_hhi = _fake_counterparty_hhi()

    honest_power_plain = _HONEST_N * voting.voting_power(_HONEST_R)
    honest_power_weighted = _HONEST_N * voting.diversity_weighted_power(_HONEST_R, honest_hhi)

    fake_unit_plain = voting.voting_power(_FAKE_R)
    fake_unit_weighted = voting.diversity_weighted_power(_FAKE_R, fake_hhi)

    # Majority: k · fake_unit > θ/(1−θ) · honest_power  (share > θ).
    def fakes_needed(honest_power: Decimal, fake_unit: Decimal) -> Decimal:
        return (_THETA / (Decimal(1) - _THETA)) * honest_power / fake_unit

    return {
        "honest_members": _HONEST_N,
        "honest_avg_reputation": str(_HONEST_R.root),
        "honest_counterparty_hhi": str(honest_hhi),
        "fake_counterparty_hhi": str(fake_hhi),
        "honest_diversity_weight": str(voting.diversity_weight(honest_hhi)),
        "fake_diversity_weight": str(voting.diversity_weight(fake_hhi)),
        "fakes_needed_plain_sqrt": str(fakes_needed(honest_power_plain, fake_unit_plain)),
        "fakes_needed_with_diversity": str(
            fakes_needed(honest_power_weighted, fake_unit_weighted)
        ),
    }


def decay_defense() -> dict:  # type: ignore[type-arg]
    """Voting weight of an idle account as inactivity grows (T½ = 180 d)."""
    service = ReputationDecayService(ClubParameters(reputation_half_life_days=180))
    return {
        "half_life_days": 180,
        "grace_days": 30,
        "retained_reputation_fraction": {
            str(days): str(service.factor(days)) for days in (30, 90, 180, 365, 730)
        },
    }


def vouching_defense() -> dict:  # type: ignore[type-arg]
    """Per-identity cost and total attack cost under vouching + slashing."""
    service = VouchingService()
    voting = VotingService()
    # Target: a reputation majority of the honest community's √R total.
    honest_total = _HONEST_N * voting.voting_power(_HONEST_R)
    target_votes = (_THETA / (Decimal(1) - _THETA)) * honest_total
    # Illustrative external prices.
    reputation_price = Decimal("1.0")  # USD per R point (proxy for earning cost)
    detection = Decimal("0.5")  # probation-window detection probability
    per_identity = service.identity_cost(detection, reputation_price)
    total = service.attack_cost(target_votes, _FAKE_R, detection, reputation_price)
    return {
        "required_vouchers_m": service.policy.required_vouchers,
        "reputation_stake_sigmaR": str(service.policy.reputation_stake.root),
        "collateral_stake_sigmaV": str(service.policy.collateral_stake.root),
        "detection_probability": str(detection),
        "per_identity_cost_usd": str(per_identity),
        "target_votes": str(target_votes),
        "total_attack_cost_usd": str(total),
    }


def main() -> None:
    out = Path("../results/sybil_attack.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    results = {
        "diversity_defense": diversity_defense(),
        "decay_defense": decay_defense(),
        "vouching_defense": vouching_defense(),
    }

    d = results["diversity_defense"]
    print("=== Diversity-weighted voting ===")
    print(f"  honest D={d['honest_diversity_weight']}, fake D={d['fake_diversity_weight']}")
    print(f"  fakes for majority: plain √R = {float(d['fakes_needed_plain_sqrt']):.0f}, "
          f"with D-weight = {float(d['fakes_needed_with_diversity']):.0f}")

    dec = results["decay_defense"]
    print("\n=== Reputation decay (T½=180d) — retained fraction ===")
    for days, frac in dec["retained_reputation_fraction"].items():
        print(f"  {days:>4} idle days: {float(frac):.3f}")

    v = results["vouching_defense"]
    print("\n=== Vouching with slashing ===")
    print(f"  per-identity cost: ${float(v['per_identity_cost_usd']):.2f}")
    print(f"  total attack cost for majority: ${float(v['total_attack_cost_usd']):,.0f}")

    out.write_text(json.dumps(results, indent=2))
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
