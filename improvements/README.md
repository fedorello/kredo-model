# Kredo model improvements (Kredo v2 — implemented)

> 🇷🇺 **Русская версия:** [README_ru.md](./README_ru.md)

Five worked-out solutions closing the weaknesses found while auditing the paper
(`paper/main.tex`). **All are implemented** as Kredo v2: opt-in
parameters/services in the simulator (with defaults off, all 315 legacy runs are
byte-for-byte identical), reflected in the paper §14 (EN+RU) and on the website.
Plus an end-to-end adversary in the engine (Phase 6,
`experiments/phase6_fraud.py`). Each document's status is at its end. Every
document is self-contained: problem → solution → formulas → calculations →
mechanism changes → how to check with the simulator → trade-offs → **status**.

| # | Document | Weakness it closes | Effort | Priority |
|---|---|---|---|---|
| 1 | [01-retention-channel.md](./01-retention-channel.md) | "Revenue treadmill": the survival condition demands perpetual growth | Model + parameters | **First** |
| 2 | [02-cooperative-closed-loop.md](./02-cooperative-closed-loop.md) | Regulatory risk (V as a security) + arbitrage against the formula price | Strategic decision | Before the pilot |
| 3 | [03-sybil-defense.md](./03-sybil-defense.md) | Sybil: the √-rule rewards splitting, the whole defense is the per-identity cost | Mechanism + code | Before 100 members |
| 4 | [04-dynamic-lockup.md](./04-dynamic-lockup.md) | Fraud deterrence threshold Λ≥N̄/a unmet by defaults (300 vs 1642) | Cheap mechanism | **First** (with #1) |
| 5 | [05-price-drift-detector.md](./05-price-drift-detector.md) | Collusive drift of μ_c within \|z\|≤1 (the open channel from Limitations) | Cheap mechanism | With #4 |

## Dependencies and order

- #1 and #4–5 are purely technical, verified by the existing simulator
  (`simulation/`), and need no external decisions. Do these first.
- #2 is a legal-and-architectural decision; it affects #1 (a closed loop
  simplifies pricing) — settle it before a pilot with real people.
- #3 is a social mechanism; needed before the community grows large enough to
  become a target.

## Link to the paper

Each solution references specific theorems/sections of the preprint:
Theorem 1 (stability), Theorem 2 (neutrality), the survival proposition,
Theorems 4–5 (fraud and deterrence), the Sybil proposition, the Limitations
section. Once implemented and run, this material became the basis for the
"Design extensions (Kredo v2)" section (§14) of the paper.
