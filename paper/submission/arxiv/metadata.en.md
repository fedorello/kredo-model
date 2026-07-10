# arXiv — metadata (copy-paste)

## Title

```
Kredo: A Contribution-Based Mutual-Credit Economy with Soulbound Reputation and Compensatory Emission
```

## Authors

```
Fedor Chishchin
```

## Abstract

(1,860 characters — within arXiv's 1,920 limit. No URLs here; links go in Comments.)

```
We present Kredo, an economic mechanism designed to reward the creation of value rather than the position of ownership. The design is derived top-down: five philosophical axioms are formalized as seven state invariants, and every transition function is required to preserve them. The economy uses two assets: a transferable contribution token V (working money and a claim on the club's external profit) and a non-transferable "soulbound" reputation token R. Credit is issued at the moment of a confirmed transaction and accompanied by a compensatory emission -- a deferred, escrowed "dividend to all" whose magnitude is governed by a dynamic coefficient that shrinks as the observed default rate grows. We prove that this coefficient keeps the money supply bounded relative to verified value even under nonzero defaults, and that operations against the liquidity fund are price-neutral, so the price cannot be moved by fund operations. Governance uses quadratic (square-root-of-reputation) voting under a dual reputation-and-stake quorum, which, together with the soulbound property of R, forces any would-be captor to win a majority of verified, active reputation and a majority of circulating stake simultaneously. We derive a minimal external-revenue-growth survival condition for a non-declining price, show that the discounted-withdrawal rule leaves the fund positive at every partial level of exit, and prove a stake threshold (mean transaction size over audit rate) beyond which even the optimal adaptive wash-trading fraud is unprofitable. A deterministic agent-based simulator implementing the full mechanism is exercised across 315 stability runs -- Monte Carlo, a 192-point parameter sweep, and combined-attack stress tests -- none of which produced an economic collapse, while a separate regime analysis reproduces the predicted price trajectories.
```

## Comments

```
15 pages, 2 figures, 7 tables. Code, data, experiment protocols and a Russian translation of the paper: https://github.com/fedorello/kredo-model
```

Once the Zenodo DOI exists, use this version instead:

```
15 pages, 2 figures, 7 tables. Code, data, experiment protocols and a Russian translation: https://github.com/fedorello/kredo-model. Archived version: https://doi.org/10.5281/zenodo.XXXXXXX
```

## Categories

```
Primary:    econ.TH  (Theoretical Economics)
Cross-list: cs.GT    (Computer Science and Game Theory)
```

## License

```
arXiv.org perpetual, non-exclusive license (default)   — or CC-BY-4.0, your choice
```
