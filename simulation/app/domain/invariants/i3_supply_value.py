"""I3 — Supply tracks verified value plus initial grants (within 5%).

The relaxed form (ARCHITECTURE §16.5):

    |Supply(t) − VerifiedValue(t) − InitialGenesisGrants(t)| ≤ 5% · Supply(t)

VerifiedValue(t) is the cumulative emission justified by confirmed
transactions and ongoing Genesis Pool funding:

    VerifiedValue(t) = Σ_τ N_credit(τ) · (1 + ε(τ)) · confidence(τ)
                     + (cumulative_funded − initial_genesis_grants)

The ``cumulative_funded − initial_genesis_grants`` term captures
"V deposited into the Pool but not yet granted" — those V are visible
in Supply (the Pool is part of Supply) but not yet in VerifiedValue
unless we count their original source. We treat them as verified
because the Genesis Pool is fed from external revenue or fines (both
verified flows).

The 5 % tolerance accommodates fraud detection latency: between a
fraudulent transaction and its detection, supply temporarily exceeds
verified value. As long as detection runs within the tolerance window,
the system stays inside the bound.

Edge case: at bootstrap (Supply ≈ 0), the absolute test would be brittle.
We always allow at least an absolute tolerance of 1 V to handle this.
"""

from __future__ import annotations

from decimal import Decimal

from app.domain.entities import ClubState
from app.domain.entities.transaction import TransactionRecord
from app.domain.invariants.checker import InvariantId, InvariantReport, OpKind

_RELATIVE_TOLERANCE = Decimal("0.05")
_ABSOLUTE_FLOOR = Decimal("1.0")


def _verified_value(state: ClubState) -> Decimal:
    """Cumulative emission justified by transactions, Genesis funding, and Invest.

    Per-loan accounting depends on loan state:

    * **OPEN**:     full emission ``N·(1+ε)·conf`` — N V is still in the
      actor's balance and ε·N is in escrow.
    * **REPAID**:   only ``ε·N·conf`` — the N V left the actor's balance
      back to the receiver (or its descendants), settling the IOU; the
      escrow portion remains in distributed balances.
    * **DEFAULTED**: 0 — both the actor's V and the escrow are burned.

    This matches the real-V conservation law: emissions stay accounted
    while the V is in circulation; both the credit principal and escrow
    are subtracted as they settle or burn.
    """
    tx_value = sum(
        (_credit_contribution(tx, state) for tx in state.transactions),
        Decimal(0),
    )
    pool_inflow_excluding_grants = (
        state.genesis.cumulative_funded.root - state.initial_genesis_grants.root
    )
    return tx_value + pool_inflow_excluding_grants + state.cumulative_invested_v.root


def _credit_contribution(tx: TransactionRecord, state: ClubState) -> Decimal:
    """Verified V contribution from this transaction, by loan state."""
    if tx.loan_id is None or tx.n_credit.is_zero():
        return Decimal(0)
    loan = state.loans.get(tx.loan_id)
    if loan is None:
        return Decimal(0)
    n_credit = tx.n_credit.root
    confidence = tx.confidence.root
    epsilon = loan.epsilon_at_creation
    if loan.is_open():
        return n_credit * (Decimal(1) + epsilon) * confidence
    if loan.is_repaid():
        # Principal returned to circulation via repayment; escrow distributed.
        return epsilon * n_credit * confidence
    # DEFAULTED — both N (cancelled with actor's burnt balance) and ε·N
    # (escrow burned) are gone.
    return Decimal(0)


def check(state_before: ClubState, state_after: ClubState, op_kind: OpKind) -> InvariantReport:
    supply = state_after.supply().root
    expected = _verified_value(state_after) + state_after.initial_genesis_grants.root
    drift = abs(supply - expected)
    tolerance = max(_ABSOLUTE_FLOOR, supply * _RELATIVE_TOLERANCE)
    holds = drift <= tolerance
    return InvariantReport(
        id=InvariantId.I3_SUPPLY_VALUE,
        holds=holds,
        measured=supply,
        expected=expected,
        tolerance=tolerance,
        detail=(f"supply={supply} verified={expected} drift={drift} (≤{tolerance})"),
    )
