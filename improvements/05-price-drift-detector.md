# 05 — Collusive price drift detector (two windows + CUSUM)

## Problem

An open channel from the paper's Limitations: the auto-score is tied to the
**rolling** 90-day price distribution of a category. Colluding participants
can move their declared prices in small steps — each step within $|z|\le1$ —
and the anchor mean $\mu_c$ will drift along with them, **never once triggering
a review**. A slow coordinated pump of a category's price = hidden emission
(inflated $N$ → inflated credits → unbacked V).

## Solution

### 1. Two-window detector

Compute a category's statistics in two windows — a short one (90 days, as now)
and a long one (365 days) — and flag the divergence:

$$\boxed{\ \bigl|\mu_c^{90}(t) - \mu_c^{365}(t)\bigr| \ >\ \kappa_d\cdot\sigma_c^{365}\ \Rightarrow\ \text{category under review}\ }$$

**Why it works (calculation).** Suppose the attackers run a linear drift at
speed $v$ (USDC/day). The mean of a window of length $T$ lags the current level
by $vT/2$:

$$\mu^{90} \approx \mu(t) - 45\,v,\qquad \mu^{365} \approx \mu(t) - 182.5\,v
\quad\Rightarrow\quad \mu^{90}-\mu^{365} \approx 137.5\,v .$$

The trigger threshold sets the **maximum undetectable drift speed**:

$$v^* = \frac{\kappa_d\,\sigma_c}{137.5}\ \text{per day}.$$

**Numeric example.** A category with $\mu_c=100$ V, $\sigma_c=10$ V,
$\kappa_d=1$: $v^* = 10/137.5 \approx 0.073$ V/day. To double the price
(+100 V), the collusion would need $100/0.073 \approx 1375$ days ≈ **3.8 years**
of continuous coordination — while any faster step is flagged immediately, and
the whole time the cluster shows up in concentration/reciprocity monitoring. The
channel is not closed absolutely, but it becomes economically pointless.

### 2. CUSUM as a reinforcement (also catches "steps")

The two-window detector is a low-pass filter; the classic CUSUM catches both
slow drift and series of small steps:

$$S_t = \max\bigl(0,\ S_{t-1} + (x_t - \mu_c^{365} - k_s)\bigr),\qquad
S_t > h_s \Rightarrow \text{flag},$$

where $x_t$ is the price of the next trade, $k_s\approx\sigma_c/2$ (tolerance),
$h_s\approx 5\sigma_c$ (threshold). Standard properties: the mean time to a
false alarm and to detection are tuned by the pair $(k_s,h_s)$.

### 3. Robustness of the anchor statistics (hygiene)

- Compute $\mu_c$ as the **median**, $\sigma_c$ via MAD (or winsorize 5%):
  outliers and the attackers' "probe" trades do not drag the anchor. (Review
  already uses the median — unify.)
- For commodity-like categories — an optional external reference (oracle) as a
  third anchor with a large tolerance weight.
- A degenerate window $\sigma_c=0$ → mandatory review (already added in the
  paper).

### 4. Response to a flag (link with 04)

A category flagged for drift →
1) **anchor freeze**: the auto-score temporarily computes $z$ from
   $\mu_c^{365}$ (the long window) rather than the short one — the drift stops
   "self-confirming";
2) audit escalation $a\to a_{\mathrm{flag}}=0.30$ (see 04 — the deterrence
   threshold after a flag is met with margin);
3) suspension of compensatory emission on the category's trades (the mechanism
   already exists);
4) on repetition — escalation to a vote.

## Changes

**In the paper:** supplement the Limitations paragraph on collusive drift with a
reference to the mechanism: "a two-window drift detector bounds the sustainable
undetected drift to $\kappa_d\sigma_c/137.5$ per day"; it can be framed as a
short Proposition with the derivation above (the mean lag $vT/2$ — one line).

**In the simulator:**
- `app/domain/services/auto_score.py`: a second window 365d, median/MAD;
- a new service `drift_detector.py` (two windows + CUSUM) + a periodic
  operation modeled on `enforce_concentration`;
- link with `run_audit` (two-phase $a$) and emission suspension;
- experiment `collusive_drift`: a cluster moves prices at $v\in\{0.5v^*, 2v^*\}$
  — expectation: slow drift does not pay off over the horizon, fast drift is
  flagged within $\approx 137.5\,\kappa_d\sigma/v$ days; measure the unbacked
  emission before the flag.

## Trade-offs

- False positives on an **honest** rise in a category's prices (skill
  inflation, seasonality): a flag ≠ a penalty — it is a review+audit; an honest
  category passes review and the anchor is updated. Tuning $\kappa_d$: start
  with 1.5–2.0.
- The yearly window requires year+ of history — for new categories use a global
  anchor (the median over related categories) until enough data accumulates.
- CUSUM is sensitive to the choice of $k_s,h_s$ — calibrate on the simulator.

## Status

**Implemented (Kredo v2).** `DriftDetectorService` (two windows + CUSUM +
robust median/MAD anchors; detrended σ via first differences, so the drift does
not inflate the threshold and mask itself). Experiment
`experiments/collusive_drift.py`.

Results (`results/collusive_drift.json`, κ = 1.5, σ = 10):
- **v\* = 0.109 V/day** — the ceiling of undetectable drift.
- **Slow drift** (0.5·v\*): not flagged, but to double the price — **1835 days
  ≈ 5 years** (economically pointless).
- **Fast drift** (2·v\*): flagged (gap 30 > κσ = 15).
- **CUSUM** catches the slow drift that the two-window mean smooths out.

Audit subtlety: the naive MAD-σ of the long window is inflated by the drift
itself — so σ is estimated from first differences (detrending).

`DriftDetectorService` is a **standalone analytical service**, not wired into
`auto_score`/the engine: categories in the simulator have static μ/σ (there is
no rolling price window), so the drift channel is not reproduced in the run
itself, and the detector is validated on synthetic series rather than
end-to-end.
