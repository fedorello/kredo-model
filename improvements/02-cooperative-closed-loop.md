# 02 — Cooperative form and closed loop V

## Problem (twofold)

**(a) Regulatory.** V today = working money **plus** a right to a share of
profit (dividend + price appreciation via the fund). The combination "investing
money + common enterprise + expectation of profit from the efforts of others"
is almost word-for-word the Howey test: in most jurisdictions V risks being
classified as a security. The article honestly flags this in Limitations, but
for launch this is likely a **binding constraint** — harder than any
mathematical one.

**(b) Arbitrage.** The price $P=(F+\mu\,\mathrm{ExtRev})/S$ is an administrative
formula (I5), not a market price. As soon as a secondary market for V appears
(an OTC chat is enough), a second price arises, and arbitrage hits the fund:
- secondary price < formula price → everyone sells to the fund, buying cheap
  elsewhere;
- secondary > formula → the fund "hands out" cheap V to investors (Invest).
The history of formula-priced tokens is almost entirely about this.

## Solution

### 1. Legal form: a platform cooperative

Key observation: Kredo's mechanics are almost isomorphic to a classic
cooperative with mutual credit. The activity-weighted dividend is legally a
**patronage dividend** (a return proportional to participation, not capital) — a
legal construction that cooperative law has road-tested for decades.

Correspondence table:

| Kredo | Cooperative analog |
|---|---|
| V (internal settlements) | internal clearing credit (like the WIR franc) |
| Activity dividend (30%) | patronage refund |
| R (reputation) | membership status / seniority |
| Genesis grant | joining membership credit |
| Investors via Invest | cooperative investor shares (limited rights) |
| Dual quorum √R + V | **⚠ check**: many co-op statutes require "one member — one vote" |

Open legal question (flag for a lawyer): compatibility of the dual quorum with
the "one member — one vote" imperative in a specific jurisdiction; options — an
advisory V-quorum + a decisive membership one, or a jurisdiction with flexible
cooperative law.

### 2. Closed loop: V is not transferable outward

Rule: V is transferred **only between verified members**; no listing, no
transfers to external addresses; exit into USDC only through the fund (Convert).
The precedent is WIR (90+ years): WIR francs are not exchanged outward.

What this gives:
- **No secondary market → no second price → no arbitrage against (I5).** The
  formula remains the only price by construction.
- Regulatory: a closed settlement system among cooperative members is an
  order of magnitude more defensible position than a freely circulating token.
- The fund's mechanics do not change: the Theorems on neutrality and
  inexhaustibility (norun) hold as-is.

The cost: lower liquidity and "investment attractiveness" of V. For a club this
aligns with the philosophy (Axiom 1: not speculation, but contribution).

### 3. If an external market is nonetheless needed: the fund as a limited market-maker

A compromise option instead of the rigid formula is a **band** around the
fundamental price $P_f=(F+\mu\,\mathrm{ExtRev})/S$:

$$\mathrm{bid} = P_f\,(1-\sigma), \qquad \mathrm{ask} = P_f\,(1+\sigma),
\qquad \sigma(\rho) = \sigma_0\cdot\max\!\Bigl(1,\ \frac{\rho^*}{\rho}\Bigr).$$

- The spread widens as coverage $\rho=F/(P_fS)$ falls — the same logic as the
  discount queue; at $\rho\ge\rho^*$ the spread is minimal $\sigma_0$ (1–2%).
- The fund itself arbitrages deviations of the secondary price from the band:
  above ask — it sells (backed Invest), below bid — it buys back (Convert+burn).
- **Honest boundary**: the ability to defend the bid is limited by the fund; the
  same curve $F=F_0(S/S_0)^{1/\rho^*}$ (Theorem norun) applies — publish the
  "firepower" openly, do not promise a peg beyond it.

## Impact on axioms and invariants

- I1–I7 are preserved; I5 in the closed loop becomes stricter (the only price).
- Axiom 3 (symmetry): investor shares must not receive priority — the
  requirement holds in the cooperative form too (shares without seniority).
- Constitutional list: add "closedness of the loop" as a constitutional
  provision (changed only by referendum), otherwise governance could "open" the
  loop by a simple vote and bring back the arbitrage risk.

## How to apply

1. **Decision on the form** (before the pilot): cooperative + closed loop = the
   base variant; the band market-maker is a deferred v2 option.
2. Lawyer: choice of jurisdiction (flexible cooperative law, treatment of
   internal clearing units), verification of the dual quorum, status of the
   USDC fund.
3. In the whitepaper/article: a "Legal form" section with the correspondence
   table above.
4. Nothing to change in the simulator (the mechanics are the same); for the
   band — add the parameter $\sigma_0$ and a scenario with an external market
   shock.

## Trade-offs

| Variant | Regulatory risk | Arbitrage | Liquidity | Attractiveness for an investor |
|---|---|---|---|---|
| Open token (current) | high | high | high | high |
| **Co-op + closed loop** | **low** | **zero** | medium (via the fund) | medium (shares + patronage) |
| Co-op + band | medium | limited | high | high |

## Status

Undecided — a strategic choice for the founder. Recommendation: cooperative +
closed loop for the pilot; consider the band only after sustained external
revenue (see 01).
