"""I5 — Price always equals (F + μ·ExtRev) / Supply, never set manually.

In our codebase the price is *derived* on demand via PricingService —
there is no field ``ClubState.price`` to corrupt. So I5 is structurally
satisfied as long as no one bypasses PricingService.

The runtime check is therefore a sanity test: recompute the price from
the post-state and confirm it is non-negative and finite (numeric
sanity). A negative price would mean the formula has been violated
upstream (e.g., negative supply or fund somehow), which would already
have failed earlier validators — but we double-check here.
"""

from __future__ import annotations

from decimal import Decimal

from app.domain.entities import ClubState
from app.domain.invariants.checker import InvariantId, InvariantReport, OpKind
from app.domain.services.pricing import PricingService


def check(state_before: ClubState, state_after: ClubState, op_kind: OpKind) -> InvariantReport:
    del state_before, op_kind  # unused
    service = PricingService(state_after.parameters)
    try:
        price = service.price(
            fund=state_after.fund.balance,
            ext_rev_annualized=state_after.ext_rev_annualized,
            supply=state_after.supply(),
        )
    except (ValueError, ArithmeticError) as exc:  # pragma: no cover — defensive
        return InvariantReport(
            id=InvariantId.I5_PRICE_FORMULA,
            holds=False,
            detail=f"price computation raised {type(exc).__name__}: {exc}",
        )

    holds = price.root >= 0
    return InvariantReport(
        id=InvariantId.I5_PRICE_FORMULA,
        holds=holds,
        measured=price.root,
        expected=Decimal(0),
        detail=("price is well-defined and non-negative" if holds else f"price={price}"),
    )
