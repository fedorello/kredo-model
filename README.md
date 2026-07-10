# Kredo — the open economic model

**An economy where value is created, not extracted.** Kredo is a club economy built on two tokens
(V — contribution, R — reputation), mutual credit, and compensatory emission. This repository shares
the model openly: the mathematics, the formulas, the simulation code, the experiment protocols, and
the raw results.

> Read the overview in your language:
> **[English](docs/en/whitepaper.md)** · **[Русский](docs/ru/whitepaper.md)** ·
> **[Español](docs/es/overview.md)** · **[中文](docs/zh/overview.md)**

The idea powers the website at **[kredoclub.com](https://kredoclub.com)**. This repo is the science
behind it — open for anyone to read, check, run, and build on.

---

## What's inside

| Path | What it is |
|---|---|
| [`docs/en/whitepaper.md`](docs/en/whitepaper.md) | Accessible explanation of the whole model (English) |
| [`docs/en/mathematics.md`](docs/en/mathematics.md) | The full formal model: axioms, invariants, formulas, theorems |
| [`docs/en/validation.md`](docs/en/validation.md) | Experiment protocols and results |
| [`docs/ru/`](docs/ru) | Original Russian documents: whitepaper, full derivation, validation report |
| [`docs/es/overview.md`](docs/es/overview.md) · [`docs/zh/overview.md`](docs/zh/overview.md) | Overviews in Spanish and Chinese |
| [`formulas.md`](formulas.md) | Language-neutral formula reference, labelled in EN/RU/ES/ZH |
| [`simulation/`](simulation) | The pure simulation code (domain = formulas, engine, protocols) — runnable |
| [`results/`](results) | Raw JSON outputs of the validation runs |

## The idea in one minute

Two familiar models are unfair by construction: rent capitalism (capital earns without working) and
the commune (no reward for the active). Kredo is a **third way** — reward proportional to *created*
value. Two tokens make it work: **V** (money, transferable) and **R** (reputation, soulbound, cannot
be bought). Money is minted at the moment of a confirmed deal, with a compensatory "gift to all" held
in escrow and burned on default, so there is no inflation. V's real price rests on the club selling
value to the outside world. Under attack — inflation, panic, fraud — the system defends itself.

The philosophy is formalized as **5 axioms** and **7 invariants**, implemented as a deterministic
simulator, and stress-tested: across **315 runs, the economy never collapsed**.

## Reproduce the experiments

```bash
cd simulation
python -m venv .venv && source .venv/bin/activate   # Python 3.12+
pip install -r requirements.txt
python -m experiments.regime_analysis
python -m experiments.monte_carlo
```

See [`simulation/README.md`](simulation/README.md) for the full guide.

## Status & honesty

The simulator answers *"will the structure hold?"* — and it does. It does **not** prove long-horizon
behavior, the response of real (adaptive) people, game-theoretically optimal attacks, or anything
legal/tax-related. Those are named openly in the validation document. This is a foundation, shared for
scrutiny — not a finished product.

## License

[MIT](LICENSE). Use it, check it, fork it, build on it.
