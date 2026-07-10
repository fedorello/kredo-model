# Kredo — an economy where value is created, not extracted

## The problem

Two familiar economic models each carry a built-in unfairness:

- **Rent capitalism.** Whoever holds capital earns more, even without working. Value is
  *extracted from a position of ownership* rather than created. The person who makes
  something useful and the person who takes the profit are often different people.
- **Communes and cooperatives.** Everyone is equal, but there is no mechanism for growth or
  for rewarding the active. The free-rider problem appears; the active burn out; the system stagnates.

Kredo is a **third way**: reward proportional to the *creation* of value; the active earn more
than the passive, but no one is left with nothing; and under attack the system defends itself.

## Two tokens

Money can be transferred; trust cannot. That single asymmetry is why the club needs two tokens.

- **V (Contribution)** — working money *and* a share in the club. It pays for services, grants a
  share of the club's external profit, and can be exchanged for real money (USDC) through the
  fund. Its balance can go negative — that is a loan from the system. V is **transferable**.
- **R (Reputation)** — soulbound. It cannot be transferred, sold or gifted, only earned through
  work and burned for violations. It raises your credit limit and gives voting weight (by $\sqrt{R}$).

If reputation could be bought, a wealthy actor would buy the maximum credit limit and voting
power and capture the system without creating value. Non-transferable R makes influence follow
proven contribution, not the size of a wallet.

## How money is born

A newcomer with zero V can still receive a service. The money is created at the moment of the deal,
in a way that devalues no one:

1. **A deal on credit.** B orders a service from A but lacks funds. The system mints V for the
   provider A; B takes on a debt (a negative balance).
2. **A gift to everyone.** Simultaneously a little V is minted for all active members — so the
   emission does not dilute their savings. Whoever created more value receives more.
3. **The gift waits in escrow.** It is frozen until the debt is repaid: repaid → released to all;
   not repaid within 90 days → burned. No one ends up in the red; there is no inflation.
4. **An automatic brake.** The gift's size is dynamic ($\varepsilon$): the more defaults, the less
   is minted, keeping money tied to real value.

## Self-defense

Every economy faces inflation, a run for the exit, and fraud. Each has a built-in response:

- **Dynamic $\varepsilon$** — more bad loans, less emission. The money supply stays tied to value created.
- **Withdrawal queue** — if everyone cashes out at once, a discounted queue kicks in; the fund does
  not empty, and investors profitably restore it at the bottom.
- **Burn on default** — fake deals detected → balances and their escrow burn; the price returns to its level. Fraud does not pay.

## Where V's real value comes from

$$\text{Price of V}=\frac{\text{Fund}+12\times\text{External revenue}}{\text{Total V}}$$

When the club earns externally, the numerator grows and every holder gets richer. Fund operations
(invest / cash out) are **price-neutral** by construction — proven algebraically. Price moves only
from fundamentals. **Without external revenue, V's price is doomed to fall** — not a flaw but a
mathematical necessity, so the club must have a plan for what it sells to the world.

## Governance

Everyday decisions are made by the algorithm and by elected roles. Parameters are changed by
$\sqrt{R}$ voting; strategic decisions require a **dual quorum** (a reputation quorum *and* a stake
quorum), which blocks capture by either activists or whales. The invariants, the soulbound nature of
R, and the ban on premine and founder allocations are constitutional.

## Why trust the model

The philosophy is formalized as **five axioms** and **seven invariants**, then implemented as a
deterministic simulator and stress-tested. Across **315 runs** — Monte Carlo, a 192-point parameter
sweep, combined-attack stress tests, and regime analysis — **the economy never collapsed**. See
[the mathematics](./mathematics.md) for the formal model and [the validation](./validation.md) for
the protocols and results.

The simulator answers *"will the structure hold?"* — and it does. It does not answer *"will real
people use it?"* — that is social, legal and product work. But that work cannot begin without a
resilient structure. The foundation is here.

---

*Original Russian whitepaper: [`../ru/whitepaper.md`](../ru/whitepaper.md).*
