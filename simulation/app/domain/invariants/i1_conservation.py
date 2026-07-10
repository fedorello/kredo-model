"""I1 — Conservation under pure transfers.

For any transaction that does **not** open a new credit position
(``n_credit == 0``) and does not involve the fund, the sum of member
balances is unchanged.

The check inspects the latest transaction in ``state_after``: if its
``n_credit`` is zero, this is a pure transfer and we expect Σb to be
identical to the previous tick's. If credit was emitted, I1 is not
applicable to this transition (Σb shifts by +N − N = 0 between actor
and receiver but Supply rises by N_credit · (1 + ε) — see I3).
"""

from __future__ import annotations

from decimal import Decimal

from app.domain.entities import ClubState
from app.domain.invariants.checker import InvariantId, InvariantReport, OpKind


def _balance_sum(state: ClubState) -> Decimal:
    """Σ b(m) — including negative balances."""
    return sum((m.balance.root for m in state.members.values()), Decimal(0))


def check(state_before: ClubState, state_after: ClubState, op_kind: OpKind) -> InvariantReport:
    if op_kind != "transact":
        return InvariantReport(
            id=InvariantId.I1_CONSERVATION,
            holds=True,
            applicable=False,
            detail=f"I1 only applies to 'transact'; got '{op_kind}'",
        )

    new_txs = state_after.transactions[len(state_before.transactions) :]
    if not new_txs:
        # No new transaction recorded — nothing to assert.
        return InvariantReport(
            id=InvariantId.I1_CONSERVATION,
            holds=True,
            applicable=False,
            detail="no transaction was added",
        )

    has_emission = any(tx.n_credit.is_positive() for tx in new_txs)
    if has_emission:
        return InvariantReport(
            id=InvariantId.I1_CONSERVATION,
            holds=True,
            applicable=False,
            detail="transaction included credit emission; I3 governs",
        )

    sum_before = _balance_sum(state_before)
    sum_after = _balance_sum(state_after)
    holds = sum_before == sum_after
    return InvariantReport(
        id=InvariantId.I1_CONSERVATION,
        holds=holds,
        measured=sum_after,
        expected=sum_before,
        tolerance=Decimal(0),
        detail=(
            "balance sum preserved on pure transfer"
            if holds
            else f"Σb changed from {sum_before} to {sum_after}"
        ),
    )
