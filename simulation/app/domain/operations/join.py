"""Join — a new member enters the club and receives a welcome grant."""

from __future__ import annotations

from app.domain.entities import ClubState, GenesisPool, Member
from app.domain.events import MemberJoined
from app.domain.operations.base import (
    Command,
    ErrorCode,
    OperationError,
    OperationResult,
)
from app.domain.operations.commands import JoinCommand
from app.domain.services.welcome_grant import WelcomeGrantService
from app.domain.value_objects import R


class JoinOperation:
    """Add a member, debit the Genesis Pool by the welcome grant.

    Invariants touched:
    * supply does not change overall (V moves from Pool to Member balance);
    * ``initial_genesis_grants`` increases by the grant amount, used by I3.
    """

    def execute(self, state: ClubState, command: Command) -> OperationResult:
        assert isinstance(command, JoinCommand)

        if command.member in state.members:
            return OperationResult.fail(
                state,
                OperationError(
                    code=ErrorCode.MEMBER_ALREADY_EXISTS,
                    message=f"member {command.member!r} already exists",
                ),
            )

        grant_service = WelcomeGrantService(state.parameters)
        grant = grant_service.grant(
            genesis_pool_balance=state.genesis.balance,
            expected_new_members=max(1, command.expected_new_members),
        )

        new_member = Member(
            id=command.member,
            kind=command.member_kind,
            balance=grant,
            reputation=R.zero(),
            joined_at=state.tick,
            frozen_until=state.tick + state.parameters.tau_lock_days,
        )
        new_pool = GenesisPool(
            balance=state.genesis.balance - grant,
            cumulative_funded=state.genesis.cumulative_funded,
        )
        new_members = {**state.members, command.member: new_member}
        new_state = state.model_copy(
            update={
                "members": new_members,
                "genesis": new_pool,
                "initial_genesis_grants": state.initial_genesis_grants + grant,
            }
        )
        return OperationResult.ok(new_state, MemberJoined(member=command.member, grant=grant))
