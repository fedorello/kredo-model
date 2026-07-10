# 04 — Dynamic lock-up and audit escalation: closing the fraud-deterrence threshold

## Problem

The deterrence theorem (thm:deter) gives a threshold: the optimal adaptive
fraud is unprofitable when the cluster's forfeited stake

$$\Lambda \ \ge\ \frac{1}{\beta} = \frac{\bar N}{\ln(1/(1-a))} \ \approx\ \frac{\bar N}{a}.$$

At the illustrative parameters ($a=0.03$, $\bar N=50$ V):
$1/\beta = 1641.5$ V, while the actual stake $\Lambda\approx300$ V →
**a profitable optimum $\approx+425$ V at $W^\dagger\approx1342$ V**. The paper
honestly flags: "defaults must be strengthened". Raising $\Lambda$ to a 1642 V
stake is prohibitive for honest newcomers. We need levers that hit $\beta$
(the detection rate), not the stake.

## Solution — two mechanisms

### 1. Lock-up growing with the amount (conversion vesting)

Currently $\tau_{\mathrm{lock}}$ is a constant (60 days). Make it a function of
fresh volume: the conversion of an amount $W$ unlocks gradually,

$$\tau_{\mathrm{lock}}(W) = \tau_0 + w\cdot W .$$

Then the probability of surviving until withdrawal:

$$q(W) = (1-a)^{W/\bar N}\,(1-p)^{\tau_0 + wW}
      = c_0\, e^{-\beta' W},\qquad
\boxed{\ \beta' = \beta + w\cdot p'\ },\quad p' = \ln\!\frac{1}{1-p},$$

— the decay rate of survival grows **linearly in $w$**, and the deterrence
condition $\Lambda \ge 1/\beta'$ is reached by tuning $w$ at the same
stake $\Lambda=300$:

$$\beta' \ \ge\ \frac{1}{300}=0.00333\quad\Rightarrow\quad
w \ \ge\ \frac{0.00333-0.000609}{p'} = \frac{0.00272}{p'}.$$

**Table: required vesting at different daily detection probabilities $p$**

| $p$ (per day) | $p'=\ln\frac{1}{1-p}$ | $w$ (days per 1 V) | Extra lock-up per 100 V | Verdict |
|---|---|---|---|---|
| 1% | 0.01005 | 0.271 | ≈27 days | harsh |
| 2% | 0.02020 | 0.135 | ≈13.5 days | acceptable |
| 5% | 0.05129 | 0.053 | **≈5.3 days** | easy |
| 10% | 0.10536 | 0.026 | ≈2.6 days | unnoticeable |

Interpretation: if the system detects an active fraud cluster with a probability
of at least 5% per day, it is enough to add ~5 days of unlocking per each
100 V of fresh balance — and even the optimal adaptive attack at a 300 V stake
goes negative. The UX cost for honest users: large fresh inflows are withdrawn
in tranches (a familiar vesting pattern).

### 2. Audit escalation on a monitoring flag (two-phase $a$)

The design already contains a 3% → 30% escalation for flagged categories — carry
it through to the theorem. For a flagged cluster:

$$a_{\mathrm{flag}} = 0.30\ \Rightarrow\
\frac{1}{\beta_{\mathrm{flag}}} = \frac{50}{\ln(1/0.7)} = \frac{50}{0.3567}
\approx 140\ \mathrm{V} \ <\ \Lambda = 300\ \mathrm{V}. \ \checkmark$$

That is, **after a flag the deterrence threshold is met with margin even at the
default stake**. All the weight shifts onto the quality of the flag: HHI by
category, two-sided concentration, reciprocity of short cycles (already in the
mechanism) + the guarantee graph (see 03) + the drift detector (see 05).

Two-phase model for the paper: before the flag $\beta_1$ (a=3%), after the flag
$\beta_2$ (a=30%); if monitoring flags the cluster after $n_{\mathrm{flag}}$
trades, the effective survival is
$q(W) = (1-a_1)^{\min(n, n_{\mathrm{flag}})}\,(1-a_2)^{\max(0,n-n_{\mathrm{flag}})}\cdot c$
— deterrence reduces to estimating $n_{\mathrm{flag}}$.

### 3. Audit randomization (a cheap bonus)

Keep the actual $a_t$ random in $[a_{\min}, a_{\max}]$ with a hidden schedule
(the seed is not published). For a risk-neutral attacker the mean $\bar a$
applies, but: (i) one cannot precisely optimize $W^\dagger$ against a known
constant; (ii) one cannot cheaply "probe" the current frequency with test
trades; (iii) a cautious (risk-averse) attacker plans against $a_{\max}$. The
implementation cost is ≈ zero.

## Changes

**In the paper:** after thm:deter add a Corollary with $\beta'=\beta+wp'$
and the two-phase $a$; update the "Fraud deterrence" point in Design guidance:
the levers are $w$, $a_{\mathrm{flag}}$, $\Lambda$; include the table above.

**In the simulator:**
- `app/domain/parameters.py`: `lockup_per_v` ($w$), `audit_rate_flagged`;
- `app/domain/services/withdrawal_queue.py` (or the convert path): vesting of
  the unlock by age and inflow volume;
- `app/domain/operations/run_audit.py`: frequency from two phases by the
  `enforce_concentration` flag;
- experiment `fraud_attack`: vary $w\in\{0,0.05,0.13,0.27\}$ and
  measure the attacking cluster's $\mathbb E[\pi]$ over 30 seeds — expectation:
  a transition to negative according to the table.

## Trade-offs

- Vesting delays withdrawals for honest participants with large one-off earnings
  — tranches and "whitelists" of long-standing members (low $w$ at high
  tenure×R — careful: do not open a loophole for aged accounts; a single $w$
  is better).
- The 30% escalation loads reviewers — but is applied only to flagged
  clusters (a small share of volume).
- Randomizing $a$ slightly complicates audit reproducibility — keep the seed
  private, disclose it retrospectively.

## Status

**Implemented (Kredo v2).** The parameters `lockup_per_v` (w) and `audit_rate_flagged`;
conversion vesting `WithdrawalQueueService.vesting_days` + a gate in `convert`
(by `last_active_tick`); the theorem formulas are moved out into
`FraudDeterrenceService` (Theorems 4–5). Experiment
`experiments/fraud_deterrence.py`.

Results (`results/fraud_deterrence.json`) — reproduce the paper exactly:
- **Base** (a = 0.03, Λ = 300, audit-only p=0): 1/β = 1642 V, W† = 1342 V,
  max = **+425 V** → NOT deterred.
- **Dynamic lock-up** (p = 5 %/day on growing vesting, the base lock-up
  non-detecting — to isolate the vesting contribution): needs w ≈ 0.053 d/V ≈
  **5.3 days per 100 V**. Sweep of max over w: **+425 → +67 → 0** at w = 0/0.02/0.053
  → fraud is non-positive (deterred) at an unchanged stake of 300. *(Audit
  correction: previously there was a −286 V here — this is a double-counting of
  detection, crediting the base 60-day lock-up as well with the value of p; an
  honest isolation of vesting gives a crossover to 0.)*
- **Audit escalation** (a = 0.30): 1/β = **140 V < 300** → deterred immediately.
  *(The parameter `audit_rate_flagged` is used in `FraudDeterrenceService` and
  the `phase6_fraud` experiment, not in the engine's `run_audit` — the base
  audit remains a no-op; vesting and remediation, by contrast, are wired into
  the engine.)*

**End-to-end (Phase 6, `experiments/phase6_fraud.py`).** A real wash-trading
cluster is run through the actual engine operations (`Transact` wash-trades V,
`Convert` through the vesting gate extracts USDC, `RemediateFraud` freezes and
burns), detection is stochastic (Bernoulli per trade and per lock-up day).
Over 30 seeds the empirical E[π] follows the closed-form formula:
- **Base** (a=0.03, w=0): profitable at any W (+233/+307/+260 V, W=500/1000/2500).
- **Vesting only** (a=0.03, w=0.053, p=0.05): deterred (−113/−257/−300) —
  the cluster survives the wash trading but is caught during the vesting hold
  (the log shows "LOCK-UP DETECTION day N").
- **Flagged audit only** (a=0.30): deterred (−300) on the wash trading.

The full trace of every event — `experiments/logs/phase6_fraud.log`.
The new operation `RemediateFraudOperation` is invoked only by command (not in
the periodic pipeline) → legacy runs are bit-for-bit identical; w = 0 by default.
