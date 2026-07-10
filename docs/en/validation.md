# Empirical validation

We did not just design the model — we implemented it as a deterministic simulator and stress-tested
it. This document describes the experiment protocols and their results. All code is in
[`../../simulation/`](../../simulation) and [`../../simulation/experiments/`](../../simulation/experiments);
raw outputs are in [`../../results/`](../../results).

## Why a simulator

Launching an economy with real money blind risks people's money. So first the model becomes code,
and we ask *"what if"*: what if 30% of members exit at once? what if a cluster runs fake deals?
what if external revenue drops to zero? Each question gets a numeric answer, at no risk.

## Determinism

Randomness is injected through a `RandomProvider` seeded per run, so one seed produces a
byte-for-byte identical run. Every result is independently reproducible; there is no "magic of chance".

## The protocols

| # | Protocol | File | What it does |
|---|---|---|---|
| V1 | Reference reproduction | (integration tests) | Reproduces the design document's predicted price directions for 4 scenarios. |
| V2 | Stability criteria | `criteria.py` | Defines C1–C5: price not zeroed, coverage ≥ 5% of ticks, ≤ 20% frozen members, non-negative supply, invariants clean. |
| V3 | Monte Carlo | `monte_carlo.py` | 4 scenarios × 30 seeds × 60 ticks = 120 runs; aggregates pass rate and price distribution. |
| V4 | Parameter sweep | `parameter_sweep.py` | 192 combinations of $K^\*\times\mu\times\delta^\*\times\rho^\*$; a stability heatmap. |
| V5 | Stress tests | `stress_tests.py` | Combined attacks — stagnant market, fraud + bank run, 70% aggressive bank run. |
| V6 | Regime analysis | `regime_analysis.py` | Confirms the three price regimes (growth / stable / falling). |

Two grades are reported separately: **economically stable** (criteria C1–C4) and **invariants
clean** (C5), because the I3 bookkeeping check has a known drift during the auto-repay + escrow
distribution lifecycle — a bookkeeping artifact, not an economic failure.

## Results

- **315 runs, 0 economic collapses.** The price never zeroed, the fund never ran dry, there were no mass freezes.
- **Parameter sweep: 192 / 192 stable.** The model is not fragile — a wide range of settings works,
  so community votes on parameters won't break it.
- **Stress tests all economically stable.** A 70% simultaneous exit survives via the withdrawal
  queue; a fraud cluster raises supply temporarily but does not break the economy; a stagnant market
  makes the price fall (as predicted) but not to zero.
- **Three regimes reproduced.** Growth (+707% over 60 ticks), stable, and stagnant (−9%) trajectories all obtained.

## What the simulation does NOT prove

Empirical testing is necessary but not sufficient:

- **Long horizons.** We tested 1–3 months of virtual time; effects over years may differ.
- **Real people.** The agents are statistical; real participants adapt, cooperate, organize politically.
- **Optimal attacks.** We tested fixed strategies, not an adversary's game-theoretic maximum.
- **Law and taxes.** Jurisdiction, KYC, tax on micro-transactions are outside the model.

## Reproduce it

```bash
cd simulation
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m experiments.regime_analysis     # fast: three regimes
python -m experiments.monte_carlo         # 120 runs
python -m experiments.parameter_sweep     # 192 combinations
python -m experiments.stress_tests        # combined attacks
```

Outputs are written to [`../../results/`](../../results).

---

*Full Russian report with diagrams: [`../ru/validation.md`](../ru/validation.md).*
