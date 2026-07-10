# 03 — Sybil defense: vouching, R decay, weight × graph diversity

## Problem

The corrected Sybil Proposal (post-audit) honestly states: the
$\sqrt{\R}$ rule **on its own does not curb splitting, it encourages it**:

$$k\sqrt{r_0} \ \ge\ \sqrt{k\,r_0} \quad\text{(splitting is profitable)},\qquad
k = Q/\sqrt{r_0}\ \text{accounts for }Q\text{ votes.}$$

Against a community of $10^3$ members with average $r=100$
($\sum\sqrt r = 10^4$) you need $>1.4\times10^4$ fakes at $r_0=0.5$ — a lot, but
the whole defense rests on the **per-identity cost** ("KYC-lite"). External KYC is
buyable and evadable; if the per-identity cost drops to ~1 USD (farms), the attack
costs ~\$14k. Endogenous barriers are needed that do not depend on the quality of the KYC provider.

## Solution — three mechanisms (they stack)

### 1. Vouching with slashing (identity cost becomes endogenous)

Joining requires $m$ vouchers who are active members; each stakes
$\sigma_R$ of reputation (and/or $\sigma_V$ of V collateral) for a probationary period $T_v$.
Proven fraud by the vouched member within $T_v$ → the vouchers lose their stake.

- Per fake identity cost to the attacker:
  $$c_{\mathrm{id}} \ \ge\ m\cdot\underbrace{\Pr[\mathrm{detect}]\cdot(\sigma_R^{\$}+\sigma_V)}_{\text{minimum bribe price for a voucher}} + c_{\mathrm{KYC}},$$
  i.e. the attack = **corrupting real members**, not deceiving a provider.
- Cost of attacking a quorum: $k\cdot c_{\mathrm{id}} = (Q/\sqrt{r_0})\cdot c_{\mathrm{id}}$ —
  grows with the number of votes and with the reliability of detection.
- Side effect: the vouching graph is a ready-made input for concentration
  monitoring (a fake cluster = a dense vouching subgraph).
- Starting parameters: $m=2$, $\sigma_R = 5$ (≈ half a year of activity),
  $\sigma_V = 50$ V, $T_v = 90$ days.

### 2. Reputation decay on inactivity

$$r(t) = r_0\cdot 2^{-\Delta t_{\mathrm{inactive}}/T_{1/2}},\qquad
T_{1/2} = 180\ \text{days (after a 30-day grace).}$$

- Sybil effect: maintaining $k$ accounts requires **continuous** genuine
  activity on each one — ongoing operational costs of $k\cdot c_a$/period,
  and the fakes' activity with one another is caught by reciprocity monitoring.
- Governance bonus: "dead weight" (those who left but earned reputation) stops
  voting; quorums are counted against the living community.
- Invariants: I6 is preserved (decay is not a transfer); in the paper change the phrase
  "R only minted and burned" → "minted, burned, and decays with inactivity".

### 3. Vote weight × graph diversity (reusing anti-fraud metrics)

The mechanism already computes two-sided counterparty concentration. Use it
in governance too:

$$\mathrm{vote}(m) = \sqrt{r_m}\cdot D_m,\qquad
D_m = \max\bigl(d_{\min},\ 1 - \mathrm{HHI}_m\bigr),$$

where $\mathrm{HHI}_m=\sum_j s_{mj}^2$ is the Herfindahl of member $m$'s turnover shares by
counterparty $j$, and $d_{\min}=0.2$ is the floor (newcomers are not zeroed out).

Effect calculation:

| Profile | Counterparties | HHI | $D$ | Effective vote |
|---|---|---|---|---|
| Honest active | 10+ evenly | ≈0.10 | 0.90 | $0.90\sqrt r$ |
| Honest newcomer | 2–3 | ≈0.40 | 0.60 | $0.60\sqrt r$ |
| Fake in a cluster (pairs) | 1–2 inside the cluster | 0.50–1.0 | 0.20 (floor) | $0.20\sqrt{r_0}$ |

A cluster gets **×0.2** to votes → the attack threshold from the example grows from
$1.4\times10^4$ to $\approx 7\times10^4$ identities (5×), or the attacker
has to trade with real members (expensive, slow, leaves a trail).

- Invariants: I7 is preserved ($D$ is a function of observable state, not of
  identity). A change to the voting rule — check whether it is parametric
  or constitutional; recommendation: fix the formula constitutionally.

## Total attack cost (example)

A community of $10^3$ members, $\bar r=100$; attack on a reputation quorum:

$$k \ \approx\ \frac{10^4}{\sqrt{r_0}\cdot D_{\mathrm{fake}}}
= \frac{10^4}{0.707\cdot 0.2} \approx 7.1\times10^4\ \text{identities},$$

each: $m=2$ vouchers × slashing + continuous activity against decay +
KYC. And even on success — the second (share-based) quorum is bought separately.
The attack costs more than building a competing community.

## Simulator code changes

- `app/domain/services/voting.py`: the $D_m$ multiplier (HHI data already exists in
  `services/concentration.py`).
- `app/domain/services/reputation_delta.py` + a periodic operation
  `decay_reputation` (new, modeled on `accrue_tenure`).
- New operation `vouch` + slashing in `process_overdue`/fraud remediation;
  entity `Vouch(voucher, vouchee, stake, expires)`.
- Experiment: the `sybil_attack` scenario — a cluster of $k$ accounts tries to
  push through a vote; criterion: the cluster's vote share < θ for $k$ up to
  10× the honest community.

## Trade-offs

- Vouching slows growth (you need to find 2 members) — this is a feature for a club,
  but a constraint for "viral" growth; you can relax to $m=1$ at an early stage.
- R decay penalizes legitimate pauses (illness, vacation) — grace of 30 days +
  "freeze on request".
- The $D$-weight penalizes honest tight pairs (two partners who work only with each
  other) — the $d_{\min}$ floor and accounting for tenure soften this.

## Status

**Implemented (Kredo v2).** D-weighted vote (`VotingService.diversity_weighted_power`
+ `ConcentrationMonitor`, parameter `vote_diversity_floor`); reputation decay
(`ReputationDecayService` + operation `DecayReputationOperation`, parameters
`reputation_half_life_days`/`reputation_decay_grace_days`, field
`Member.last_active_tick`, engine-wired into the periodic pipeline); vouching
(`VouchingService` + `Vouch`/`VouchPolicy`). Experiment
`experiments/sybil_attack.py`.

Results (`results/sybil_attack.json`):
- **D-weight**: for the majority you need 14,142 fakes (pure √R) → **63,640** with
  D-weight (**×4.5**); honest D = 0.9, fake cluster D = 0.2.
- **R decay (T½ = 180 d)**: 56% is retained after 180 days of inactivity, 28% after
  a year, 7% after two — a fleet without activity melts away.
- **Vouching**: per-identity cost $55, full attack on the majority —
  **$777,817**.

Decay is opt-in (`reputation_half_life_days=None` by default) and engine-wired
(a periodic operation). D-weight and vouching are **analytical services**:
the engine does not model voting and the join flow (governance is out of the engine's scope,
see `voting.py`), so they are verified at the service level, not end-to-end.
Legacy runs are unaffected (the same violation statistics).
