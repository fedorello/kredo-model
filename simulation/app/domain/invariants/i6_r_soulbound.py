"""I6 — R is soulbound: no transfer between members.

Two-part check:

1. **Structural** (one-time): the ``R`` class must not expose any
   transfer-like method. This is checked once at module import via
   :func:`assert_r_is_soulbound`.

2. **Runtime**: when an operation finishes, the **only** way total Σ R
   should have changed is by mint or burn — never by reshuffling.
   We can't detect a perfect-zero-sum reshuffle (e.g., +5 to A, −5 to B
   in the same step) without explicit mint/burn events, so this runtime
   check looks for the most common breach: total R changed in a way
   that doesn't match what mint/burn callers would have logged.

   For Phase 3 we lack the event log of individual mint/burn calls.
   We therefore implement only the structural part as the strict check
   and the runtime side returns ``applicable=False`` — Phase 4 will add
   event-level mint/burn logging that lets us tighten this.
"""

from __future__ import annotations

from app.domain.entities import ClubState
from app.domain.invariants.checker import InvariantId, InvariantReport, OpKind
from app.domain.value_objects import R

_FORBIDDEN_NAMES = ("transfer", "send", "move", "delegate", "give")


def assert_r_is_soulbound() -> None:
    """Static check: R has no transfer-like method.

    Called from a top-level test on import to fail loud if anyone adds
    such a method by accident or design.
    """
    for name in _FORBIDDEN_NAMES:
        if hasattr(R, name):
            raise AssertionError(
                f"Invariant I6 violated: R class exposes forbidden method '{name}'"
            )


def check(state_before: ClubState, state_after: ClubState, op_kind: OpKind) -> InvariantReport:
    del state_before, state_after, op_kind  # not yet used at runtime
    # Structural check is run once at import time; the runtime hook is a
    # no-op until Phase 4 introduces a mint/burn event log.
    return InvariantReport(
        id=InvariantId.I6_R_SOULBOUND,
        holds=True,
        applicable=False,
        detail="structural — verified by assert_r_is_soulbound at import",
    )


# Run the structural check at import. If anyone adds R.transfer, every
# test that imports this module will fail immediately.
assert_r_is_soulbound()
