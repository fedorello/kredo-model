"""I4 — No member is below their credit limit.

For every member m::

    b(m) ≥ −L(r(m))

Always applicable, every tick. Computed by ``CreditLimitService``.
"""

from __future__ import annotations

from decimal import Decimal

from app.domain.entities import ClubState
from app.domain.invariants.checker import InvariantId, InvariantReport, OpKind
from app.domain.services.credit_limit import CreditLimitService


def check(state_before: ClubState, state_after: ClubState, op_kind: OpKind) -> InvariantReport:
    del state_before, op_kind  # unused — I4 is a property of the post-state alone

    service = CreditLimitService(state_after.parameters)
    deepest_below = Decimal(0)
    offender = ""
    for member in state_after.members.values():
        limit = service.compute(member.reputation)
        # b(m) ≥ -L(r(m))   ⇔   b(m) + L(r(m)) ≥ 0
        slack = member.balance.root + limit.root
        if slack < deepest_below or (deepest_below == 0 and slack < 0):
            deepest_below = slack
            offender = member.id

    holds = deepest_below >= 0
    return InvariantReport(
        id=InvariantId.I4_CREDIT_LIMIT,
        holds=holds,
        measured=deepest_below,
        expected=Decimal(0),
        detail=(
            "all members within credit limit"
            if holds
            else f"member {offender!r} is below limit by {-deepest_below}"
        ),
    )
