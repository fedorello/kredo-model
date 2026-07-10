# 01 — Revenue retention channel: removing the "treadmill"

## Problem

The survival condition in the paper (Proposition "Survival condition" + Proposition
"Long-run price") is derived from $\mathcal{A} = F + \mu\cdot\mathrm{ExtRev}$ with
$\dot{\mathcal{A}} = \lambda_{\mathrm{inv}} + \mu\lambda_{\mathrm{rev}}$, where
$\lambda_{\mathrm{rev}} = \dot{\mathrm{ExtRev}}$ — the **growth** of the trailing annual
revenue level. Consequence: for the price not to fall, annual revenue must grow
by $(eP-\lambda_{\mathrm{inv}})/\mu$ **every month forever** (in the paper's example —
+250 USDC/mo indefinitely). A constant revenue level ($\lambda_{\mathrm{rev}}=0$)
does not hold the price: the audit counter-simulation showed a decline of $1.00\to0.51$ over 24 mo
at a stable 250 USDC/mo.

This makes the economy "grow or die" — the model's main practical risk.

## Key observation

The Kredo design **already contains** the solution, it is simply not accounted for in the paper's
continuous model: revenue flows into the Liquidity Fund, and under quarterly
distribution **50% stays in the fund** (the 50/30/15/5 split). This means that
$\dot F$ has a term proportional to the **level** of the revenue flow, not its growth.
The simulator partially implements this (`record_external_revenue` puts revenue into the
fund; `quarterly_distribution` pays out the shares) — this is probably why in the
stagnant-regime experiment the price fell by only −9% instead of collapsing.

## Solution

### 1. Corrected continuous model

Let $R(t)$ be the current revenue flow (USDC/mo), $s\in[0,1]$ the fund
retention share. Then:

$$\dot F = \lambda_{\mathrm{inv}} + s\,R(t), \qquad
\dot{\mathcal{A}} = \lambda_{\mathrm{inv}} + s\,R(t) + \mu\,\lambda_{\mathrm{rev}}.$$

Condition for a non-decreasing price ($\dot{\mathcal A} \ge P\dot S$, as in the paper):

$$\boxed{\ \lambda_{\mathrm{inv}} + s\,R + \mu\,\lambda_{\mathrm{rev}} \ \ge\ e\cdot P\ }$$

where $e$ is net emission (V/mo). **In steady state** ($\lambda_{\mathrm{rev}}=0$):

$$R \ \ge\ \frac{e\,P - \lambda_{\mathrm{inv}}}{s}.$$

A constant revenue level suffices — perpetual growth is no longer needed.

### 2. Numbers (parameters of the paper's example)

$e=5000$ V/mo, $P=1$ USDC/V, $\lambda_{\mathrm{inv}}=2000$ USDC/mo, $s=0.5$:

| Quantity | Before (paper's model) | After (with retention) |
|---|---|---|
| Requirement | revenue level growth +250 USDC/mo **forever** | constant level $R \ge 6000$ USDC/mo |
| Long-run price | $(\lambda_{\mathrm{inv}}+\mu\lambda_{\mathrm{rev}})/e$ | $(\lambda_{\mathrm{inv}}+sR)/e$ |
| At $R=6000$ | — | $P_\infty = (2000+3000)/5000 = 1.00$ (stable) |
| At $R=12000$ | — | $P_\infty = (2000+6000)/5000 = 1.60$ (growth) |
| At $R=0$ | decline | $P_\infty = 2000/5000 = 0.40$ (decline, as it should) |

The lever $s$: at $s=0.7$ it is enough that $R\ge 4286$; at $s=0.3$ you need $R\ge 10000$.

### 3. Emission tied to revenue (a second lever, "currency board")

Make the credit emission budget endogenous:

$$e(t) \ \le\ \eta\cdot\frac{R(t)}{P_{\mathrm{target}}},$$

where $\eta$ is the revenue share that "backs" new money. Substituting into the
survival condition at $P\approx P_{\mathrm{target}}$ and $\lambda_{\mathrm{inv}}=0$
(worst case):

$$s\,R \ \ge\ \eta\,R \iff \boxed{\ \eta \le s\ }$$

— a clean design rule: **the emission share is no higher than the retention share**. Then
regime C ("decline") turns into a "slowdown": no sales → less new
money → the price is stable at low activity, instead of a death spiral.

## Changes

**In the paper:** rewrite $\dot{\mathcal A}$ with the $sR$ term; new survival
condition and price limit; the 6000 USDC/mo example; add the rule $\eta\le s$.
The long-run price proposition generalizes trivially (linear growth of
$\mathcal A$ is preserved).

**In the simulator** (`simulation/`):
- verify that `record_external_revenue` + `quarterly_distribution` implement
  an effective $s=0.5$ (revenue into the fund → 30/15/5 paid out);
- add the parameter `emission_budget_share` ($\eta$) to
  `app/domain/parameters.py` and the emission cap in `operations/transact.py`;
- a new scenario `constant_revenue` in `app/application/scenarios/`:
  $R=\mathrm{const}$, $\lambda_{\mathrm{rev}}=0$, 180 ticks.

## How to verify

1. Run `constant_revenue` at $R$ = 0.5×, 1.0×, 2.0× the threshold
   $(eP-\lambda_{\mathrm{inv}})/s$: expectation — decline / plateau / price growth.
2. Run with the cap $\eta\le s$ and $R\to 0$: expectation — emission contracts,
   the price does not collapse (plateau at $\lambda_{\mathrm{inv}}/e$).
3. Criteria — the same C1–C4 from `experiments/criteria.py`; compare with
   `results/regime_analysis.json`.

## Trade-offs

- Higher $s$ → a more stable price, but smaller dividends to participants "now" —
  a conflict between short-term motivation and sustainability; a parameter for voting.
- The emission cap $\eta R/P$ at launch (when $R=0$) blocks credit —
  a bootstrap mode is needed: a fixed minimum emission budget for the first
  $T_0$ months, financed from $\lambda_{\mathrm{inv}}$ (investor
  underwriting), with an automatic transition to the rule $\eta\le s$.

## Status

**Implemented (Kredo v2).** The parameters `emission_budget_share` (η) and
`emission_price_target` in `parameters.py` (validator `η ≤ s`), the field
`emission_budget` in `ClubState`, top-up in `record_external_revenue`, the
emission gate in `transact` (`EMISSION_BUDGET_EXCEEDED`). The experiment
`experiments/retention_analysis.py`.

Results (`results/retention_analysis.json`):
- **The revenue level sets the regime**: a sweep over constant revenue of 0/25/50/100/200
  per day — at 0 the price falls (0.165 → 0.049), at any positive value it grows
  (e.g. 200 → 4.80). It is precisely the **level**, not the growth, that determines the outcome.
- **Currency board**: after revenue stops at tick 90 with η = s = 0.5 the emission
  starves: without a cap the supply keeps growing (**+11.8k** post-stop), with a cap it
  declines slightly (**−1.6k**); over the whole run supply growth is halved (36.2k → 17.4k),
  the price is **24 % higher** (2.41 → 2.99). Regime C degrades into a slowdown, not a collapse.

η = 0 by default — all 315 legacy runs are bit-for-bit identical.
