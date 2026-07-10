"""RunStochasticAudit — periodic random audit of recent transactions.

Picks ``audit_rate`` × |today's transactions| at random. For Phase 4
the audit always passes (we don't model fraud injection here); the
operation is still useful because:

* it exercises the rng-driven branch in invariant tests;
* it surfaces audited transactions in events for the UI.

Phase 6 fraud scenarios will inject failing audits and re-test I3.
"""

from __future__ import annotations

import random

from app.domain.entities import ClubState
from app.domain.operations.base import Command, OperationResult


class RunStochasticAuditOperation:
    """Pick a random sample of today's transactions for audit."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random(0)

    def execute(self, state: ClubState, command: Command) -> OperationResult:
        del command
        # Today's transactions only.
        todays = [tx for tx in state.transactions if tx.tick == state.tick]
        sample_size = int(len(todays) * float(state.parameters.audit_rate))
        if sample_size == 0 or not todays:
            return OperationResult.ok(state)
        # Sample without replacement; deterministic given the same RNG seed.
        self._rng.sample(todays, sample_size)
        # In Phase 4 the audit unconditionally passes; no state changes.
        # Phase 6 will model fraud and update tx confidence here.
        return OperationResult.ok(state)
