"""DecayReputation — daily inactivity decay of soulbound R (v2).

Applies :class:`ReputationDecayService` to every member each tick. A member
whose ``last_active_tick`` is within the grace window keeps full reputation;
past it, R melts with the configured half-life. Frozen members are left
untouched (their reputation is already reset on freeze). When decay is
disabled (``reputation_half_life_days is None``) the operation is a no-op,
so legacy runs are unchanged.
"""

from __future__ import annotations

from app.domain.entities import ClubState
from app.domain.operations.base import Command, OperationResult
from app.domain.services.reputation_decay import ReputationDecayService
from app.domain.value_objects import R


class DecayReputationOperation:
    """Multiply each active member's R by its inactivity-decay factor."""

    def execute(self, state: ClubState, command: Command) -> OperationResult:
        del command
        service = ReputationDecayService(state.parameters)
        if not service.enabled:
            return OperationResult.ok(state)
        new_members = {}
        for member_id, member in state.members.items():
            last_active = member.last_active_tick
            if last_active is None:
                last_active = member.joined_at
            inactive_days = state.tick - last_active
            factor = service.factor(inactive_days)
            if member.is_frozen or factor >= 1 or member.reputation.is_zero():
                new_members[member_id] = member
                continue
            decayed = R(member.reputation.root * factor)
            new_members[member_id] = member.model_copy(update={"reputation": decayed})
        return OperationResult.ok(state.model_copy(update={"members": new_members}))
