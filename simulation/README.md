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

Results are written to [`../results/`](../results). Runs are deterministic — the same seed gives a
byte-for-byte identical result.

## Design principles

- **Functional core, imperative shell.** Domain operations are pure functions
  `(State, Command) → (State, [Event])` over an immutable `ClubState`.
- **Dependency inversion.** Randomness and time enter through `Protocol` ports, injected explicitly —
  which is what makes runs reproducible.
- **Invariants as executable law.** After every command the checker verifies all seven invariants.
