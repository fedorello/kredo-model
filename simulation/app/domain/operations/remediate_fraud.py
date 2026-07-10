"""RemediateFraud — freeze a detected cluster and forfeit its stake (v2).

The fraud-remediation operation of Theorems 4–5 and the remediation
hypothesis of Theorem 1: once monitoring/audit identifies a wash-trading
cluster, every member is frozen with balance and reputation burned to zero,
and their open loans default (burning the reserved escrow). The total burned
positive balance is the forfeited stake Λ. Unbacked issuance is removed from
circulation, so Supply falls back toward verified value.

Invoked only on detection (never by the default periodic pipeline), so it
does not affect any legacy run.
"""

from __future__ import annotations

from app.domain.entities import ClubState, DistributionEscrow, Member
from app.domain.events import DomainEvent, FraudRemediated, LoanDefaulted, MemberFrozen
from app.domain.operations.base import Command, OperationResult
from app.domain.operations.commands import RemediateFraudCommand
from app.domain.value_objects import LoanState, R, V


class RemediateFraudOperation:
    """Freeze a set of members, burn their balances/reputation, default loans."""

    def execute(self, state: ClubState, command: Command) -> OperationResult:
        assert isinstance(command, RemediateFraudCommand)
        targets = {m for m in command.members if m in state.members}
        if not targets:
            return OperationResult.ok(state)

        new_members = dict(state.members)
        burned_v = V.zero()
        events: list[DomainEvent] = []

        # 1. Default the cluster's open loans, burning their escrow.
        new_loans = dict(state.loans)
        burned_escrow = V.zero()
        for loan in state.loans.values():
            if loan.borrower in targets and loan.is_open():
                burned_escrow = burned_escrow + loan.escrow_reserved
                new_loans[loan.id] = loan.model_copy(
                    update={"state": LoanState.DEFAULTED, "escrow_reserved": V.zero()}
                )
                events.append(
                    LoanDefaulted(
                        loan_id=loan.id, borrower=loan.borrower, burned_escrow=loan.escrow_reserved
                    )
                )

        # 2. Freeze each member: burn positive balance + reputation (forfeit stake).
        for member_id in targets:
            member = new_members[member_id]
            if member.balance.is_positive():
                burned_v = burned_v + member.balance
            new_members[member_id] = _frozen(member, state.tick)
            events.append(MemberFrozen(member=member_id, reason="fraud remediation"))

        new_state = state.model_copy(
            update={
                "members": new_members,
                "loans": new_loans,
                "escrow": DistributionEscrow(total=state.escrow.total - burned_escrow),
            }
        )
        events.append(
            FraudRemediated(members=len(targets), burned_v=burned_v, burned_escrow=burned_escrow)
        )
        return OperationResult.ok(new_state, *events)


def _frozen(member: Member, tick: int) -> Member:
    return member.model_copy(
        update={
            "balance": V.zero(),
            "reputation": R.zero(),
            "is_frozen": True,
            "frozen_until": tick,
        }
    )
