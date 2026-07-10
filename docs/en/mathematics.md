# The mathematics of the Kredo economy

This document builds the Kredo model formally: from philosophy to axioms, from axioms
to invariants, from invariants to transition functions, and from there to the stability
results. Every claim is either an axiom or a consequence of one.

> Notation: **V** is the contribution token (working money + a share of the club),
> **R** is the reputation token (soulbound). USDC denotes an external stable asset held
> by the club's Liquidity Fund.

---

## 1. Five axioms

1. **Value is created, not extracted.** Reward must correspond to creation, not to a position of ownership.
2. **Value is subjective but consensual.** The only honest measure of value is the voluntary agreement of two parties in an honest market (alternatives exist, transparency holds, no coercion).
3. **Symmetry of winning and losing.** All participants are structurally bound to the fate of the system. No class is shielded from the risks of the others.
4. **No privileged knowledge.** All rules, metrics, balances and decisions are transparent. Information asymmetry is the main source of dishonest markets.
5. **Power is proportional to contribution, not capital.** The ability to change the rules follows from proven useful participation, not from accumulated resources.

---

## 2. State and the seven invariants

The system state at time $t$:

$$S_t = (M_t,\ b_t,\ r_t,\ d_t,\ F_t,\ E_t,\ G_t,\ H_t)$$

where $M_t$ is the set of members; $b_t:M_t\to\mathbb{R}$ the V balance (may be negative up to a credit limit); $r_t:M_t\to\mathbb{R}_{\ge 0}$ the reputation; $d_t$ accumulated debt; $F_t\in\mathbb{R}_{\ge 0}$ the Liquidity Fund in USDC; $E_t$ the Distribution Escrow; $G_t$ the Genesis Pool in V; $H_t$ the append-only transaction history.

The seven invariants are the formal expression of the five axioms:

- **I1 — Conservation on transfers.** For any pure transfer, $\sum_m b_t(m)=\sum_m b_{t+1}(m)$.
- **I2 — Emission is gated.** New V is minted only inside the confirmation protocol, and only when $\text{confidence}(\tau)\ge\theta_{\min}$.
- **I3 — Supply tracks verified value.** $\bigl|\text{Supply}(t)-\text{VerifiedValue}(t)\bigr|\le\epsilon_{\text{tol}}\cdot\text{Supply}(t)$, with $\epsilon_{\text{tol}}=0.05$ to absorb detection lag.
- **I4 — Credit limit.** For every member, $b_t(m)\ge -L\bigl(r_t(m)\bigr)$.
- **I5 — Price reflects fundamentals.** $P_t=\dfrac{F_t+\mu\cdot\text{ExtRev}_t}{\text{Supply}(t)}$ is always computed, never set by hand.
- **I6 — R is soulbound.** No transfer function for R exists; R only mints (for merit) and burns (for violations).
- **I7 — Universal rules.** Every function depends only on the observable state $b,r,d$, never on the identity of a member.

The transition functions are exactly seven — **Join, Leave, Transact, Repay, Default, Convert, Invest** — plus derived periodic operations (Distribute, Audit, Vote, …). Each must preserve all seven invariants.

---

## 3. Credit limit

$$L(r) = L_0\bigl(1+\alpha\ln(1+r)\bigr),\qquad L_0=100\ \text{V},\ \alpha=0.5$$

Logarithmic growth is deliberate: even a maximally reputable member cannot cause a catastrophic default.

| $r$ | 0 | 1 | 10 | 100 | 1000 | 10000 |
|---|---|---|---|---|---|---|
| $L(r)$ | 100 | 135 | 220 | 330 | 445 | 560 |

---

## 4. Confidence

For a transaction $\tau=(A,B,N,c,\text{evidence})$:

$$\text{confidence}(\tau)=w_a\,s_a+w_r\,s_r+w_x\,s_x,\qquad w_a+w_r+w_x=1$$

**Auto-score.** With $\mu_c,\sigma_c$ the mean and standard deviation of prices in category $c$ over 90 days and $z=(N-\mu_c)/\sigma_c$:

$$s_a=\begin{cases}1 & |z|\le 1\\[2pt]\exp\!\left(-\dfrac{(|z|-1)^2}{2}\right) & |z|>1\end{cases}$$

**Review-score.** With $k$ reviewers each voting $v_i\in\{0,0.5,1\}$: $s_r=\operatorname{median}(v_1,\dots,v_k)$ (median resists manipulation).

**Audit-score.** $s_x=1$ if the transaction passed (or was not selected for) the stochastic audit, else $0$.

Review is mandatory when $|z|>1$, or $N>N_{\text{auto}}(r_A,r_B)=50\sqrt{r_Ar_B+1}$, or a party is under monitoring, or the 3% audit selects it.

---

## 5. Emission and the compensation coefficient

A confirmed credit transaction mints $N_{\text{credit}}=\max(0,\,N-\max(0,b_B))$ for the provider and opens a debt for the receiver. Simultaneously a compensatory amount is minted into escrow:

$$\Delta E=\varepsilon(t)\cdot N_{\text{credit}}$$

The escrow is released, pro-rata to repayment, only when the debt is repaid, and is **burned** on default. The compensation coefficient is dynamic:

$$\varepsilon(t)=\max\!\Bigl(0,\ \min\bigl(0.95,\ K^\*-1-\kappa\,(\delta_t-\delta^\*)\bigr)\Bigr)$$

with target ratio $K^\*=1.5$, target default rate $\delta^\*=0.05$, sensitivity $\kappa=2$, and $\delta_t$ the observed default rate over a 90-day window.

| $\delta_t$ | 0 | 0.05 | 0.10 | 0.20 | 0.30 |
|---|---|---|---|---|---|
| $\varepsilon(t)$ | 0.60 | 0.50 | 0.40 | 0.20 | 0.00 |

### Theorem (stability under defaults)

*In a stationary regime with default rate $\delta_t\le 0.5$ and $\varepsilon$ as above, $\dfrac{\text{Supply}}{P_{\text{net}}}\le K^\*$, where $P_{\text{net}}=\text{VerifiedValue}\cdot(1-\delta_t)$.*

**Proof.** In stationarity, $\text{Supply}=N_{\text{total}}(1+\varepsilon)(1-\delta)$ and $P_{\text{net}}=N_{\text{total}}(1-\delta)$, so $\text{Supply}/P_{\text{net}}=1+\varepsilon\le 1+(K^\*-1)=K^\*$. For $\delta_t>\delta^\*$, $\varepsilon$ is smaller still, giving a tighter bound. $\blacksquare$

This is the automatic brake: when defaults rise, compensation falls, protecting the system from inflation.

---

## 6. Escrow distribution ("gift to all")

When a debt is repaid, released escrow is distributed across all members in proportion to their **active turnover** over 90 days, not their balance (this rewards useful activity, not hoarding):

$$\text{Turnover}(m,t)=\!\!\sum_{\tau\in H_t:\,t-\tau<90d,\ m\in\tau}\!\!N(\tau)\,\text{confidence}(\tau),\qquad \text{Share}(m,t)=\frac{\text{Turnover}(m,t)+\xi}{\sum_{m'}\text{Turnover}(m',t)+n_t\xi}$$

with a small smoothing constant $\xi=1$.

**Welcome grant.** Each new member receives $g_0=\min\!\bigl(100,\ G_t/\mathbb{E}[\text{NewMembers}]\bigr)$ from the Genesis Pool, which is fed by 15% of quarterly external revenue and half of collected fines. It shrinks automatically if growth outpaces earnings — a subsidy from nowhere is impossible.

---

## 7. Reputation and governance

Reputation accrues through logarithmic (activity) and linear (quality) terms and burns for failures:

$$\Delta R=\beta_1\ln(1+N_{\text{tx}})+\beta_2\,\text{audits}+\beta_3\ln(1+\text{tenure}/30)+\beta_4\,\text{disputes},\qquad \Delta R^-=\gamma_1\,\text{fails}+\dots+\gamma_4\,\text{fraud}$$

with $\gamma_4=100$ (proven fraud wipes years of reputation).

**Voting power** is $\sqrt{R}$. Strategic decisions require a **dual quorum**: a reputation quorum ($\sum\sqrt{r}$ over voters vs. total) *and* a stake quorum ($\sum b$ over voters vs. total), each above $\theta=0.5$ (or $0.66$ for constitutional changes). This blocks both capture by activists and capture by whales.

**Sybil resistance.** $k$ fake accounts with base reputation $r_0$ yield $k\sqrt{r_0}$ votes; obtaining $V$ votes needs $V^2/r_0$ accounts (e.g. 20,000 accounts for 100 votes at $r_0=0.5$), each requiring KYC-light and real activity. R cannot be bought (I6), so buying capital $C$ yields zero reputation votes.

---

## 8. Price and the Liquidity Fund

$$P_t=\frac{F_t+\mu\cdot\text{ExtRev}_t}{S_t},\qquad \mu=12\ \text{(a P/E-style multiplier)}$$

### Theorem (fund operations are price-neutral)

*Convert (sell V to the fund) and Invest (deposit USDC for V) do not change $P_t$.*

**Proof (Invest).** An investor deposits $\Delta U$, receives $\Delta V=\Delta U/P_t$. Using $F_t=P_tS_t-\mu\text{ExtRev}$:

$$P_{t+1}=\frac{F_t+\Delta U+\mu\text{ExtRev}}{S_t+\Delta U/P_t}=\frac{P_tS_t+\Delta U}{S_t+\Delta U/P_t}=P_t.$$

The Convert case is symmetric. $\blacksquare$

So price moves **only** from fundamentals: external profit $\text{ExtRev}$ and supply $S$. A credit emission dilutes price in the moment,

$$P_{t+1}=P_t\cdot\frac{S_t}{S_t+N_{\text{credit}}(1+\varepsilon)}<P_t,$$

and is recovered only if that value is later monetized externally. **Internal turnover alone creates no real wealth** — this is the model's central honest conclusion.

### Bank-run protection

Define fund coverage $\rho_t=\dfrac{F_t}{P_tS_t}$. When $\rho_t<\rho^\*=0.3$, conversions are queued and discounted:

$$P_{\text{actual}}=P_t\cdot\min\!\left(1,\ \frac{\rho_t}{\rho^\*}\right).$$

The discount both protects the fund and creates an incentive for investors to buy cheaply at the bottom, restoring $\rho$. The structural consequence is an emission ceiling: the system cannot mint more V than it can later buy back, $\Delta S_{\max}=(F-F_{\min})/P_{\text{target}}$.

---

## 9. Stationarity and the survival condition

Price is constant when supply growth matches asset growth:

$$\frac{1}{S}\frac{dS}{dt}=\frac{1}{F+\mu\text{ExtRev}}\frac{d(F+\mu\text{ExtRev})}{dt}.$$

This yields three regimes — **A (growth)**, **B (stable)**, **C (falling)** — and a minimum **survival condition**: to avoid a permanently falling price the club must earn externally at rate

$$\lambda_{\text{rev}}\ \ge\ \frac{1}{\mu}\bigl(\text{EmissionRate}\cdot P-\lambda_{\text{inv}}\bigr).$$

For example at $S=100{,}000$, $P=1$, $\mu=12$, emission $5{,}000$ V/mo, investment $2{,}000$ USDC/mo, the club must earn at least $250$ USDC/mo externally.

---

## 10. Parameter reference

| Symbol | Default | Meaning |
|---|---|---|
| $L_0,\ \alpha$ | 100, 0.5 | Base credit limit and reputation sensitivity |
| $g_0$ | 100 V | Welcome grant cap |
| $\varepsilon$ | 0 – 0.95 | Dynamic compensation coefficient |
| $K^\*$ | 1.5 | Target Supply/VerifiedValue |
| $\theta_{\min}$ | 0.6 | Minimum confidence for emission |
| $\delta^\*,\ \kappa$ | 0.05, 2 | Target default rate, sensitivity |
| $\mu$ | 12 | Price multiplier on external revenue |
| $\rho^\*$ | 0.3 | Minimum fund coverage before the withdrawal queue |
| audit rate | 0.03 | Fraction of transactions audited |

The invariants themselves, the soulbound nature of R, the ban on premine and founder allocations, and the symmetry of rules are **constitutional** — changeable only by a super-majority referendum, never by ordinary governance.

---

*The full original derivation (in Russian, with every step) is in [`../ru/mathematics.md`](../ru/mathematics.md). A language-neutral formula reference is in [`../../formulas.md`](../../formulas.md). The empirical validation of these results is in [`./validation.md`](./validation.md).*
