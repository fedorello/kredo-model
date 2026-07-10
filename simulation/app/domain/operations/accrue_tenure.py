"""AccrueTenureReputation — daily logarithmic tenure-based R bump."""

from __future__ import annotations

from app.domain.entities import ClubState
from app.domain.operations.base import Command, OperationResult
from app.domain.services.reputation_delta import ReputationDeltaService


class AccrueTenureReputationOperation:
    """Add β₃·log(...) to every active member's reputation."""

    def execute(self, state: ClubState, command: Command) -> OperationResult:
        del command
        rep_service = ReputationDeltaService(state.parameters)
        new_members = {}
        for member_id, member in state.members.items():
            if member.is_frozen:
                new_members[member_id] = member
                continue
            tenure = state.tick - member.joined_at
            delta = rep_service.for_tenure_day(tenure)
            new_members[member_id] = member.model_copy(
                update={"reputation": member.reputation.add(delta)}
            )
        return OperationResult.ok(state.model_copy(update={"members": new_members}))
