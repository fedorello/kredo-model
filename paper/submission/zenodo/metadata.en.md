# Zenodo — metadata (copy-paste)

## Resource type

Publication → Preprint

## Title

```
Kredo: A Contribution-Based Mutual-Credit Economy with Soulbound Reputation and Compensatory Emission
```

## Creators

```
Chishchin, Fedor — Independent Researcher
```

## Description (abstract)

```
We present Kredo, an economic mechanism designed to reward the creation of value rather than the position of ownership. The design is derived top-down: five philosophical axioms are formalized as seven state invariants, and every transition function is required to preserve them. The economy uses two assets: a transferable contribution token V (working money and a claim on the club's external profit) and a non-transferable "soulbound" reputation token R. Credit is issued at the moment of a confirmed transaction and accompanied by a compensatory emission — a deferred, escrowed "dividend to all" whose magnitude is governed by a dynamic coefficient that shrinks as the observed default rate grows. We prove that this coefficient keeps the money supply bounded relative to verified value under a nonzero default rate, and that operations against the liquidity fund are price-neutral, so the token's price responds only to fundamentals. Governance uses quadratic (square-root-of-reputation) voting under a dual reputation-and-stake quorum, which, together with the soulbound property of R, makes capture by capital or by Sybil accounts economically unprofitable. We derive a minimal external-revenue survival condition for a non-declining price, show that the discounted-withdrawal rule leaves the fund positive at every level of exit, and prove a stake threshold (mean transaction size over audit rate) beyond which even the optimal adaptive wash-trading fraud is loss-making. A deterministic agent-based simulator implementing the full mechanism is exercised across 315 stability runs — Monte Carlo, a 192-point parameter sweep, and combined-attack stress tests — none of which produced an economic collapse, while a separate regime analysis reproduces the predicted price trajectories.

Code, derivations, experiment protocols and raw results: https://github.com/fedorello/kredo-model

The record includes the English paper (main.pdf) and a Russian translation (main-ru.pdf).
```

## Keywords

```
mutual credit
complementary currency
mechanism design
token economics
quadratic voting
Sybil resistance
agent-based simulation
```

## License

```
Creative Commons Attribution 4.0 International (CC-BY-4.0)
```

## Related works

```
https://github.com/fedorello/kredo-model — relation: Is supplemented by
```

## Language

```
English
```
