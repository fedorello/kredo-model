"""Phase 6 — end-to-end adversary in the engine (Kredo v2).

The earlier fraud experiments checked the deterrence *formulas*. This one
runs an actual wash-trading cluster through the **real** domain operations
and measures its realised expected profit, then compares it to the
closed-form ``E[π] = q(W)·W − (1−q(W))·Λ`` (Theorem 4).

Attack, per seed:
  1. Build-up: the cluster mints ``W`` worth of V via ``n = W/N̄`` real
     ``Transact`` wash trades (collector always the provider). Each trade is
     independently audited with probability ``a`` (Bernoulli via the seeded
     RNG) — the stochastic audit at the base rate, or the escalated
     ``audit_rate_flagged`` once the intra-cluster pattern is flagged.
  2. Lock-up: the collector tries a real ``Convert``. The v2 vesting gate
     (``lockup_per_v``) blocks it until ``w·W`` days pass; each waiting tick
     the cluster is caught with per-day probability ``p``. (With ``w=0`` the
     convert is immediate — no lock-up exposure.)
  3. Outcome: escape → the ``Convert`` really pays ``W`` USDC out of the fund
     (profit ``+W``); detection → ``RemediateFraud`` really freezes the
     cluster and burns its unbacked V (restoring supply), and the attacker
     forfeits its posted stake ``Λ`` (profit ``−Λ``).

Everything is logged to ``experiments/logs/phase6_fraud.log``.

Run: ``python -m experiments.phase6_fraud`` from ``simulation/``.
"""

from __future__ import annotations

import json
import logging
import random
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.domain.entities import ClubState, LiquidityFund  # noqa: E402
from app.domain.entities.member import Member  # noqa: E402
from app.domain.operations import (  # noqa: E402
    ConvertCommand,
    ErrorCode,
    RemediateFraudCommand,
    TransactCommand,
    default_registry,
)
from app.domain.parameters import ClubParameters  # noqa: E402
from app.domain.services.fraud_deterrence import FraudDeterrenceService  # noqa: E402
from app.domain.value_objects import USDC, CategoryId, MemberKind, R, V, member_id  # noqa: E402

_LOG_PATH = ROOT / "experiments" / "logs" / "phase6_fraud.log"
_N_BAR = Decimal("50")
_STAKE = Decimal("300")  # Λ — the attacker's posted real stake (V)
_CLUSTER_SIZE = 6
_SEEDS = 30

logger = logging.getLogger("phase6")


def _setup_logging() -> None:
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.handlers.clear()
    handler = logging.FileHandler(_LOG_PATH, mode="w")
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


@dataclass(frozen=True, slots=True)
class AttackConfig:
    label: str
    audit_rate: Decimal
    lockup_per_v: Decimal
    detection_per_day: Decimal


def _params(cfg: AttackConfig) -> ClubParameters:
    # High credit limit so wash trades are never blocked (we model fraud, not
    # the credit gate); audit_rate carries the effective (possibly flagged) rate.
    return ClubParameters(
        L0=V(1_000_000),
        audit_rate=cfg.audit_rate,
        lockup_per_v=cfg.lockup_per_v,
    )


def _build_state(params: ClubParameters) -> tuple[ClubState, list, object]:  # type: ignore[type-arg]
    """Cluster of collector + borrowers, a well-funded fund (price ≈ 1)."""
    collector = member_id("fraud-collector")
    borrowers = [member_id(f"fraud-borrower-{i}") for i in range(_CLUSTER_SIZE - 1)]
    members = {}
    members[collector] = Member(
        id=collector, kind=MemberKind.ACTIVE, balance=V(0), reputation=R(1000),
        joined_at=0, frozen_until=None,
    )
    for b in borrowers:
        members[b] = Member(
            id=b, kind=MemberKind.ACTIVE, balance=V(0), reputation=R(1000),
            joined_at=0, frozen_until=None,
        )
    supply_seed = V(1000)  # a little genesis so price is well-defined
    from app.domain.entities.genesis import GenesisPool

    state = ClubState(
        tick=0,
        members=members,
        fund=LiquidityFund(balance=USDC(1_000_000)),
        genesis=GenesisPool(balance=supply_seed, cumulative_funded=supply_seed),
        initial_genesis_grants=V(0),
        parameters=params,
    )
    cluster = [collector, *borrowers]
    return state, cluster, collector


def _run_attack(seed: int, theft: Decimal, cfg: AttackConfig) -> dict:  # type: ignore[type-arg]
    rng = random.Random(seed)
    registry = default_registry()
    params = _params(cfg)
    state, cluster, collector = _build_state(params)
    n_trades = int(theft / _N_BAR)
    a = float(cfg.audit_rate)
    p = float(cfg.detection_per_day)
    borrowers = cluster[1:]

    logger.info(f"[{cfg.label}] seed={seed} W={theft} n_trades={n_trades} a={a} "
                f"w={cfg.lockup_per_v} p={p}")

    # ---- Phase 1: build-up wash trades, each audited with prob a ----
    for i in range(n_trades):
        state = state.model_copy(update={"tick": i})
        borrower = borrowers[i % len(borrowers)]
        cmd = TransactCommand(actor=collector, receiver=borrower, amount=V(_N_BAR),
                              category=CategoryId.DEV)
        res = registry.execute(state, cmd)
        if not res.succeeded:
            logger.info(f"  tick {i}: wash trade REJECTED ({res.error.code}) — aborting attack")
            return _caught(seed, cfg, theft, state, registry, cluster, i, reason="trade_rejected")
        state = res.new_state
        if rng.random() < a:
            logger.info(f"  tick {i}: AUDIT HIT on wash trade #{i + 1}/{n_trades} → detected")
            return _caught(seed, cfg, theft, state, registry, cluster, i, reason="audit")
    logger.info(f"  build-up survived all {n_trades} audits; collector balance="
                f"{state.members[collector].balance}")

    # ---- Phase 2: lock-up — try Convert; vesting gate forces the wait ----
    convert_v = state.members[collector].balance
    tick = n_trades
    lockup_ticks = 0
    while True:
        state = state.model_copy(update={"tick": tick})
        res = registry.execute(state, ConvertCommand(member=collector, amount=convert_v))
        if res.succeeded:
            extracted = _extracted_usdc(res)
            logger.info(f"  tick {tick}: CONVERT ok after {lockup_ticks} lock-up ticks — "
                        f"extracted {extracted} USDC → ESCAPED, profit=+{theft}")
            return {"seed": seed, "escaped": True, "profit": str(theft),
                    "lockup_ticks": lockup_ticks, "reason": "escaped"}
        if res.error.code != ErrorCode.LOCK_UP_ACTIVE:
            logger.info(f"  tick {tick}: convert failed ({res.error.code}) — treat as caught")
            return _caught(seed, cfg, theft, state, registry, cluster, tick, reason="convert_fail")
        # Still vesting — one more day of exposure to per-day detection.
        lockup_ticks += 1
        if rng.random() < p:
            logger.info(f"  tick {tick}: LOCK-UP DETECTION (day {lockup_ticks}) → caught")
            return _caught(seed, cfg, theft, state, registry, cluster, tick, reason="lockup")
        tick += 1
        if lockup_ticks > 5000:  # safety
            raise RuntimeError("vesting never cleared")


def _caught(seed, cfg, theft, state, registry, cluster, tick, *, reason):  # type: ignore[no-untyped-def]
    """Remediate the cluster (real freeze/burn) and book profit = −Λ."""
    res = registry.execute(state, RemediateFraudCommand(members=tuple(cluster)))
    burned = next((e for e in res.events if type(e).__name__ == "FraudRemediated"), None)
    burned_v = str(burned.burned_v) if burned else "0"
    logger.info(f"  REMEDIATED at tick {tick} ({reason}): burned unbacked V={burned_v}; "
                f"attacker forfeits stake Λ={_STAKE} → profit=−{_STAKE}")
    return {"seed": seed, "escaped": False, "profit": str(-_STAKE),
            "lockup_ticks": 0, "reason": reason}


def _extracted_usdc(res) -> str:  # type: ignore[no-untyped-def]
    ev = next((e for e in res.events if type(e).__name__ == "FundConverted"), None)
    return str(ev.usdc_paid) if ev else "0"


def _closed_form(theft: Decimal, cfg: AttackConfig) -> dict:  # type: ignore[type-arg]
    # τ0 held non-detecting (audit-only baseline); vesting carries the hazard.
    svc = FraudDeterrenceService(
        mean_tx_size=_N_BAR, audit_rate=cfg.audit_rate, lockup_days=0,
        detection_per_day=cfg.detection_per_day, lockup_per_v=cfg.lockup_per_v,
    )
    q = svc.survival_probability(theft)
    e_pi = q * theft - (Decimal(1) - q) * _STAKE
    return {"q": str(q), "expected_profit": str(e_pi)}


def _monte_carlo(theft: Decimal, cfg: AttackConfig) -> dict:  # type: ignore[type-arg]
    runs = [_run_attack(s, theft, cfg) for s in range(_SEEDS)]
    escapes = sum(1 for r in runs if r["escaped"])
    profits = [Decimal(r["profit"]) for r in runs]
    mean_profit = sum(profits, Decimal(0)) / Decimal(_SEEDS)
    q_emp = Decimal(escapes) / Decimal(_SEEDS)
    cf = _closed_form(theft, cfg)
    logger.info(f"[{cfg.label}] W={theft}: escapes={escapes}/{_SEEDS} "
                f"q_emp={float(q_emp):.4f} E[pi]_emp={float(mean_profit):+.1f}  |  "
                f"closed-form q={float(Decimal(cf['q'])):.6f} "
                f"E[pi]={float(Decimal(cf['expected_profit'])):+.1f}")
    return {
        "theft": str(theft), "escapes": escapes, "seeds": _SEEDS,
        "q_empirical": str(q_emp), "mean_profit_empirical": str(mean_profit),
        "q_closed_form": cf["q"], "expected_profit_closed_form": cf["expected_profit"],
    }


def main() -> None:
    _setup_logging()
    configs = [
        ("baseline_v1", AttackConfig("baseline_v1", audit_rate=Decimal("0.03"),
                                     lockup_per_v=Decimal("0"), detection_per_day=Decimal("0")),
         "Baseline v1 (a=0.03, no vesting) — the open gap"),
        ("v2_vesting", AttackConfig("v2_vesting", audit_rate=Decimal("0.03"),
                                    lockup_per_v=Decimal("0.053"), detection_per_day=Decimal("0.05")),
         "v2 lever 1 — dynamic lock-up only (a=0.03, w=0.053, p=0.05)"),
        ("v2_flagged", AttackConfig("v2_flagged", audit_rate=Decimal("0.30"),
                                    lockup_per_v=Decimal("0"), detection_per_day=Decimal("0")),
         "v2 lever 2 — flagged audit only (a=0.30, no vesting)"),
    ]
    thefts = [Decimal("500"), Decimal("1000"), Decimal("2500")]

    results = {"stake": str(_STAKE), "seeds": _SEEDS}
    logger.info("=== Phase 6: end-to-end fraud attack ===")
    for key, cfg, _title in configs:
        results[key] = {str(W): _monte_carlo(W, cfg) for W in thefts}

    print("=== Phase 6: end-to-end adversary vs closed form (Λ=300, 30 seeds) ===\n")
    for key, _cfg, title in configs:
        print(f"{title}")
        print(f"  {'W':>6} {'q_emp':>7} {'q_cf':>8} {'Epi_emp':>9} {'Epi_cf':>9}  verdict")
        for W in thefts:
            r = results[key][str(W)]
            emp = float(r["mean_profit_empirical"])
            cf = float(r["expected_profit_closed_form"])
            verdict = "PROFITABLE" if emp > 0 else "deterred"
            print(f"  {float(r['theft']):>6.0f} {float(r['q_empirical']):>7.3f} "
                  f"{float(r['q_closed_form']):>8.4f} {emp:>+9.1f} {cf:>+9.1f}  {verdict}")
        print()

    out = ROOT.parent / "results" / "phase6_fraud.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2))
    print(f"Saved to {out}\nFull event log: {_LOG_PATH}")


if __name__ == "__main__":
    main()
