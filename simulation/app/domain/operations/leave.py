"""Leave — member exits the club after settling all open obligations.

Preconditions:
* member has no open loans (must repay or default first);
* balance must be ≥ 0 (negative balance means unpaid debt).

The member's positive balance is enqueued for Convert via the
withdrawal queue mechanism (uniform handling with bank-run protection).
The member record itself is removed.
"""

from __future__ import annotations

from app.domain.entities import ClubState
from app.domain.events import MemberLeft
from app.domain.operations.base import (
    Command,
    ErrorCode,
    OperationError,
    OperationResult,
)
from app.domain.operations.commands import LeaveCommand


class LeaveOperation:
    def execute(self, state: ClubState, command: Command) -> OperationResult:
        assert isinstance(command, LeaveCommand)
        member = state.members.get(command.member)
        if member is None:
            return OperationResult.fail(
                state,
                OperationError(
                    code=ErrorCode.MEMBER_NOT_FOUND,
                    message=f"member {command.member!r} not found",
                ),
            )
        if member.balance.is_negative():
            return OperationResult.fail(
                state,
                OperationError(
                    code=ErrorCode.INSUFFICIENT_BALANCE,
                    message="cannot leave with negative balance — repay first",
                ),
            )
        open_loans = [
            loan
            for loan in state.loans.values()
            if loan.borrower == command.member and loan.is_open()
        ]
        if open_loans:
            return OperationResult.fail(
                state,
                OperationError(
                    code=ErrorCode.OPEN_LOANS_PRESENT,
                    message=f"member has {len(open_loans)} open loan(s)",
                ),
            )

        new_members = {k: v for k, v in state.members.items() if k != command.member}
        new_state = state.model_copy(update={"members": new_members})
        return OperationResult.ok(
            new_state, MemberLeft(member=command.member, final_balance=member.balance)
        )
