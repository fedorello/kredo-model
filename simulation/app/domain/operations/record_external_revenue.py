"""RecordExternalRevenue — external income flows into the fund.

The market model emits this command each tick to inject ``λ_rev``.
``ext_rev_annualized`` is updated by the engine via the same interface
used for periodic ops; here we just bump the fund balance and the
sliding-window annualised rate.

This operation is intentionally simple: the engine maintains the
12-month sliding window outside the operation by re-aggregating
historical revenue events. For Phase 4 we set
``ext_rev_annualized = ext_rev_annualized + amount * 12``-style only
when the engine wraps this — the operation itself just records the
inflow into the fund.
"""

from __future__ import annotations

from app.domain.entities import ClubState, LiquidityFund
from app.domain.events import ExternalRevenueRecorded
from app.domain.operations.base import (
    Command,
    ErrorCode,
    OperationError,
    OperationResult,
)
from app.domain.operations.commands import RecordExternalRevenueCommand
from app.domain.value_objects import V


class RecordExternalRevenueOperation:
    def execute(self, state: ClubState, command: Command) -> OperationResult:
        assert isinstance(command, RecordExternalRevenueCommand)
        if command.amount.is_zero():
            return OperationResult.fail(
                state,
                OperationError(
                    code=ErrorCode.INVALID_AMOUNT,
                    message="external revenue must be positive",
                ),
            )
        update = {
            "fund": LiquidityFund(balance=state.fund.balance + command.amount),
            "ext_rev_annualized": state.ext_rev_annualized + command.amount,
        }
        # v2 currency board (improvements/01): a share η of realised revenue
        # replenishes the credit-emission budget, converted to V at P_target.
        eta = state.parameters.emission_budget_share
        if eta > 0:
            budget_added = V(eta * command.amount.root / state.parameters.emission_price_target.root)
            update["emission_budget"] = state.emission_budget + budget_added
        new_state = state.model_copy(update=update)
        return OperationResult.ok(new_state, ExternalRevenueRecorded(amount=command.amount))
