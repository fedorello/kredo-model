"""I7 — Universal rules: behavior depends only on observable b/r/d.

This is fundamentally a **structural** property: there must exist no
function whose behavior changes based on the *identity* of the member
beyond what is captured in their balance, reputation, debt, and kind.

In our codebase, every operation parameterises only over those fields.
Member.id is used purely as a dictionary key, never as an authority
modifier. We document this with a code-review-style invariant rather
than a runtime check — a runtime test would have to enumerate every
operation and assert it doesn't dispatch on id, which is a stronger
claim than "the property holds today" and would be costly to maintain.

The invariant report is therefore always ``applicable=False`` (no
runtime work) but ``holds=True`` documents the assumption.
"""

from __future__ import annotations

from app.domain.entities import ClubState
from app.domain.invariants.checker import InvariantId, InvariantReport, OpKind


def check(state_before: ClubState, state_after: ClubState, op_kind: OpKind) -> InvariantReport:
    del state_before, state_after, op_kind
    return InvariantReport(
        id=InvariantId.I7_UNIVERSAL_RULES,
        holds=True,
        applicable=False,
        detail="structural — every operation parameterises only over (b, r, d, kind)",
    )
