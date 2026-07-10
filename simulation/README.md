# Simulation code

The pure, framework-free core of the Kredo model and its simulation engine, extracted from the
full application. No database, no web framework — only the domain, the engine, and the experiment
protocols. The only dependency is `pydantic`.

## Layout

```
app/
  domain/
    value_objects/     V, USDC, R, Money, Category, ids — the vocabulary
    entities/          Member, Loan, Escrow, Fund, Queue, Transaction, ClubState (immutable)
    services/          the FORMULAS: credit_limit, epsilon, confidence, auto_score, pricing,
                       voting, distribution, welcome_grant, withdrawal_queue, reputation_delta, …
    invariants/        I1–I7 + a checker run after every operation
    operations/        the transition functions: join, leave, transact, convert, invest,
                       process_overdue, quarterly_distribution, run_audit, …
  application/
    simulation/        engine, behavior models, market models, metrics, snapshots
    scenarios/         normal_growth, mature_steady, fraud_attack, bank_run
    ports/             RandomProvider / Clock protocols (dependency inversion)
  infrastructure/
    random/            seeded PRNG (determinism)
experiments/           the validation protocols (see docs/en/validation.md)
```

The code maps directly onto [`../docs/en/mathematics.md`](../docs/en/mathematics.md): every service
is a formula from that document, every invariant is one of I1–I7, every operation is a transition
function that must preserve all seven.

## Run it

```bash
cd simulation
python -m venv .venv && source .venv/bin/activate   # Python 3.12+
pip install -r requirements.txt
python -m experiments.regime_analysis     # ~seconds: the three price regimes
python -m experiments.monte_carlo         # 4 scenarios × 30 seeds
python -m experiments.parameter_sweep     # 192 parameter combinations
python -m experiments.stress_tests        # combined attacks
```

### Kredo v2 — design-extension experiments ([`../improvements/`](../improvements))

```bash
python -m experiments.retention_analysis  # 01: survival at constant revenue + currency board
python -m experiments.sybil_attack        # 03: diversity-weighted votes, R-decay, vouching cost
python -m experiments.fraud_deterrence    # 04: dynamic lock-up & audit escalation (Thm 4–5)
python -m experiments.collusive_drift     # 05: two-window + CUSUM price-drift detector
python -m experiments.phase6_fraud        # end-to-end adversary: real ops, E[π] vs closed form
```

`phase6_fraud` runs an actual wash-trading cluster through the real
`Transact` / `Convert` / fraud-remediation operations with stochastic
detection, and writes a full per-event trace to
`experiments/logs/phase6_fraud.log`.

These exercise the v2 mechanisms; the five improvements are opt-in parameters
(`emission_budget_share`, `reputation_half_life_days`, `lockup_per_v`,
`audit_rate_flagged`, plus the diversity/vouching/drift services), so every
legacy run above is byte-for-byte unchanged.

Results are written to [`../results/`](../results). Runs are deterministic — the same seed gives a
byte-for-byte identical result.

## Design principles

- **Functional core, imperative shell.** Domain operations are pure functions
  `(State, Command) → (State, [Event])` over an immutable `ClubState`.
- **Dependency inversion.** Randomness and time enter through `Protocol` ports, injected explicitly —
  which is what makes runs reproducible.
- **Invariants as executable law.** After every command the checker verifies all seven invariants.
