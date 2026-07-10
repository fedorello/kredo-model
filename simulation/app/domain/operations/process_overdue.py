"""ProcessOverdueLoans — apply progressive sanctions to ageing loans.

ARCHITECTURE §9.1:

    | day | event                                      |
    |-----|--------------------------------------------|
    | 30  | reputation × 0.95                          |
    | 60  | reputation × 0.7, no new credit            |
    | 90  | full default — burn escrow, freeze member  |

The engine calls this once per tick; the operation iterates all open
loans and applies the appropriate sanction based on age. Loans that
hit 90 days transition to the DEFAULTED state and burn their reserved
escrow.
"""

from __future__ import annotations

from decimal import Decimal

from app.domain.entities import (
    ClubState,
    DistributionEscrow,
    Loan,
    Member,
)
from app.domain.events import DomainEvent, LoanDefaulted, MemberFrozen
from app.domain.operations.base import Command, OperationResult
from app.domain.value_objects import LoanId, LoanState, MemberId, R, V

_DAY_30_DECAY = Decimal("0.95")
_DAY_60_DECAY = Decimal("0.7")
_THRESHOLD_30 = 30
_THRESHOLD_60 = 60
_THRESHOLD_DEFAULT = 90


class ProcessOverdueLoansOperation:
    """Apply ageing sanctions to all open loans."""

    def execute(self, state: ClubState, command: Command) -> OperationResult:
        del command  # parameterless periodic
        new_loans = dict(state.loans)
        new_members = dict(state.members)
        new_escrow_total = state.escrow.total
        events: list[DomainEvent] = []

        for loan in state.loans.values():
            if not loan.is_open():
                continue
            age = state.tick - loan.opened_at
            if age >= _THRESHOLD_DEFAULT:
                new_loans, new_members, new_escrow_total, default_events = _default_loan(
                    loan, new_loans, new_members, new_escrow_total
                )
                events.extend(default_events)
                continue
            if age == _THRESHOLD_60:
                borrower = new_members.get(loan.borrower)
                if borrower is None:
                    continue
                new_members[loan.borrower] = borrower.model_copy(
                    update={
                        "reputation": _decay_reputation(borrower.reputation, _DAY_60_DECAY),
                        "frozen_until": max(
                            borrower.frozen_until or 0,
                            state.tick + (_THRESHOLD_DEFAULT - _THRESHOLD_60),
                        ),
                    }
                )
            elif age == _THRESHOLD_30:
                borrower = new_members.get(loan.borrower)
                if borrower is None:
                    continue
                new_members[loan.borrower] = borrower.model_copy(
                    update={
                        "reputation": _decay_reputation(borrower.reputation, _DAY_30_DECAY),
                    }
                )

        new_state = state.model_copy(
            update={
                "loans": new_loans,
                "members": new_members,
                "escrow": DistributionEscrow(total=new_escrow_total),
            }
        )
        return OperationResult.ok(new_state, *events)


def _decay_reputation(reputation: R, factor: Decimal) -> R:
    return R(reputation.root * factor)


def _default_loan(
    loan: Loan,
    loans: dict[LoanId, Loan],
    members: dict[MemberId, Member],
    escrow_total: V,
) -> tuple[dict[LoanId, Loan], dict[MemberId, Member], V, list[DomainEvent]]:
    burned = loan.escrow_reserved
    new_loans = {
        **loans,
        loan.id: loan.model_copy(
            update={
                "state": LoanState.DEFAULTED,
                "escrow_reserved": V.zero(),
            }
        ),
    }
    new_escrow_total = escrow_total - burned
    events: list[DomainEvent] = [
        LoanDefaulted(loan_id=loan.id, borrower=loan.borrower, burned_escrow=burned)
    ]
    new_members = dict(members)
    borrower = members.get(loan.borrower)
    if borrower is not None:
        new_members[loan.borrower] = borrower.model_copy(
            update={
                "balance": V.zero(),
                "reputation": R.zero(),
                "is_frozen": True,
            }
        )
        events.append(
            MemberFrozen(
                member=loan.borrower,
                reason=f"loan {loan.id} defaulted",
            )
        )
    return new_loans, new_members, new_escrow_total, events
