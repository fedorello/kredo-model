"""I2 — Emission only follows confirmed transactions.

Supply may grow only via:
  • a new transaction with ``confidence ≥ θ_min``,
  • an Invest operation (V issued in exchange for USDC),
  • a Genesis Pool top-up (``cumulative_funded`` increases) — this is
    structurally identical to "verified value flowed in" because the
    Pool is fed only from external revenue, fines, or initial seeding.

If supply grew between two ticks but none of the above happened,
something is wrong.
"""

from __future__ import annotations

from decimal import Decimal

from app.domain.entities import ClubState
from app.domain.invariants.checker import InvariantId, InvariantReport, OpKind

_EMISSION_OPS = {"transact", "join", "invest", "quarterly_distribution"}


def check(state_before: ClubState, state_after: ClubState, op_kind: OpKind) -> InvariantReport:
    supply_before = state_before.supply().root
    supply_after = state_after.supply().root
    delta_supply = supply_after - supply_before

    if delta_supply <= 0:
        return InvariantReport(
            id=InvariantId.I2_EMISSION_GATED,
            holds=True,
            measured=delta_supply,
            detail="supply did not grow",
        )

    # Supply grew. Verify a legitimate cause exists.
    if op_kind not in _EMISSION_OPS:
        return InvariantReport(
            id=InvariantId.I2_EMISSION_GATED,
            holds=False,
            measured=delta_supply,
            detail=(
                f"supply increased by {delta_supply} but op '{op_kind}' "
                "is not an emission-permitted operation"
            ),
        )

    # For 'transact', additionally require a new tx with confidence ≥ θ_min.
    if op_kind == "transact":
        new_txs = state_after.transactions[len(state_before.transactions) :]
        theta = state_after.parameters.theta_min.root
        if not new_txs or any(tx.confidence.root < theta for tx in new_txs):
            return InvariantReport(
                id=InvariantId.I2_EMISSION_GATED,
                holds=False,
                measured=delta_supply,
                expected=Decimal(0),
                detail="emission without a confidence ≥ θ_min transaction",
            )

    return InvariantReport(
        id=InvariantId.I2_EMISSION_GATED,
        holds=True,
        measured=delta_supply,
        detail=f"emission justified by op '{op_kind}'",
    )
