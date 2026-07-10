"""EnforceConcentrationResponse — surface monitoring recommendations.

Phase 4 measures concentration metrics over the full transaction history
and asks ``MonitoringResponseService`` for recommendations. Active
enforcement (lower credit limit, pause ε for a cluster) requires
state-level cluster tracking that arrives later. For now the operation
is a no-op for state; tests assert that recommendations are computable.
"""

from __future__ import annotations

from collections import defaultdict

from app.domain.entities import ClubState
from app.domain.operations.base import Command, OperationResult
from app.domain.services.concentration import ConcentrationMonitor
from app.domain.services.monitoring_response import (
    MonitoringResponseService,
    Recommendation,
)
from app.domain.value_objects import CategoryId, MemberId, V


def compute_recommendations(state: ClubState) -> list[Recommendation]:
    """Public helper — used by the operation and exposed for tests."""
    category_volumes: dict[CategoryId, dict[MemberId, V]] = defaultdict(dict)
    member_total: dict[MemberId, V] = defaultdict(V.zero)
    pair_volumes: dict[tuple[MemberId, MemberId], V] = defaultdict(V.zero)

    for tx in state.transactions:
        cat_bucket = category_volumes[tx.category]
        cat_bucket[tx.actor] = cat_bucket.get(tx.actor, V.zero()) + tx.amount
        member_total[tx.actor] = member_total[tx.actor] + tx.amount
        pair_volumes[(tx.actor, tx.receiver)] = (
            pair_volumes.get((tx.actor, tx.receiver), V.zero()) + tx.amount
        )

    monitor = ConcentrationMonitor()
    category_hhi = {cat: monitor.hhi(volumes) for cat, volumes in category_volumes.items()}
    bilateral = monitor.bilateral_concentration(member_total, pair_volumes)
    reciprocity = monitor.reciprocity(pair_volumes)
    return MonitoringResponseService().evaluate(category_hhi, bilateral, reciprocity)


class EnforceConcentrationResponseOperation:
    def execute(self, state: ClubState, command: Command) -> OperationResult:
        del command
        # Recommendations are computed but not yet applied (Phase 4 limit).
        compute_recommendations(state)
        return OperationResult.ok(state)
