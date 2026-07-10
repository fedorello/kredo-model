"""RecalculateTurnover — refresh the trailing 90-day active-volume window.

For each member, sum the ``amount * confidence`` of confirmed
transactions in which they participated (as actor or receiver) over
the trailing 90 ticks. This drives:

* escrow distribution shares (DistributionService);
* activity multiplier for quarterly dividends.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from app.domain.entities import ClubState
from app.domain.operations.base import Command, OperationResult
from app.domain.value_objects import MemberId, V

_WINDOW_DAYS = 90


class RecalculateTurnoverOperation:
    def execute(self, state: ClubState, command: Command) -> OperationResult:
        del command
        cutoff = state.tick - _WINDOW_DAYS
        totals: defaultdict[MemberId, Decimal] = defaultdict(lambda: Decimal(0))
        for tx in state.transactions:
            if tx.tick < cutoff:
                continue
            weighted = tx.amount.root * tx.confidence.root
            totals[tx.actor] += weighted
            totals[tx.receiver] += weighted
        new_members = {}
        for member_id, member in state.members.items():
            new_members[member_id] = member.model_copy(
                update={"turnover_90d": V(totals.get(member_id, Decimal(0)))}
            )
        return OperationResult.ok(state.model_copy(update={"members": new_members}))
