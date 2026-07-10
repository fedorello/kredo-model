"""Types and dispatch for the seven Club invariants.

Each invariant is a pure function:

    check(state_before, state_after, op_kind) -> InvariantReport

Some invariants are unconditional (I4 — credit limits always hold for
every member), some are conditional on the operation kind (I1 only
applies to operations that don't emit), some are structural and don't
need a runtime check at all (I6 — checked once via class introspection).

This module provides the report type, the registry, and the public
``check_all`` entry point used by the simulation engine.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from app.domain.entities import ClubState

# Op-kind strings the runtime check functions understand. Phase 4 will
# wire these to a proper CommandKind enum; for now the surface is
# intentionally string-based to keep invariants independent of the
# operations layer.
OpKind = str


class InvariantId(StrEnum):
    """Stable identifiers for each invariant — used in events and storage."""

    I1_CONSERVATION = "I1"
    I2_EMISSION_GATED = "I2"
    I3_SUPPLY_VALUE = "I3"
    I4_CREDIT_LIMIT = "I4"
    I5_PRICE_FORMULA = "I5"
    I6_R_SOULBOUND = "I6"
    I7_UNIVERSAL_RULES = "I7"


@dataclass(frozen=True, slots=True)
class InvariantReport:
    """Outcome of a single invariant check.

    ``applicable`` distinguishes "this invariant doesn't apply to the
    operation that just ran" from "the invariant holds". A non-
    applicable check is treated as ``holds=True`` for engine purposes
    but logged differently in the UI.
    """

    id: InvariantId
    holds: bool
    applicable: bool = True
    measured: Decimal | None = None
    expected: Decimal | None = None
    tolerance: Decimal | None = None
    detail: str = ""

    def is_violation(self) -> bool:
        return self.applicable and not self.holds


CheckFn = Callable[[ClubState, ClubState, OpKind], InvariantReport]


@dataclass(frozen=True, slots=True)
class _Registry:
    checks: tuple[CheckFn, ...]

    def run(
        self, state_before: ClubState, state_after: ClubState, op_kind: OpKind
    ) -> list[InvariantReport]:
        return [check(state_before, state_after, op_kind) for check in self.checks]


def build_registry() -> _Registry:
    """Construct the default registry containing all runtime invariants.

    Imported lazily inside the function to break the otherwise-circular
    import: each individual invariant module imports types from this one.
    """
    from app.domain.invariants.i1_conservation import check as i1  # noqa: PLC0415
    from app.domain.invariants.i2_emission_gated import check as i2  # noqa: PLC0415
    from app.domain.invariants.i3_supply_value import check as i3  # noqa: PLC0415
    from app.domain.invariants.i4_credit_limit import check as i4  # noqa: PLC0415
    from app.domain.invariants.i5_price_formula import check as i5  # noqa: PLC0415
    from app.domain.invariants.i6_r_soulbound import check as i6  # noqa: PLC0415
    from app.domain.invariants.i7_universal_rules import check as i7  # noqa: PLC0415

    return _Registry(checks=(i1, i2, i3, i4, i5, i6, i7))


def check_all(
    state_before: ClubState,
    state_after: ClubState,
    op_kind: OpKind,
) -> list[InvariantReport]:
    """Run every invariant for one state transition.

    Use this once after each operation. The reports are sorted by
    invariant id so consumers (UI, tests, persistence) get a stable
    ordering.
    """
    return build_registry().run(state_before, state_after, op_kind)
