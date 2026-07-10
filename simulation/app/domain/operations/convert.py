"""Convert — member sells V to the fund for USDC.

Two paths:
* Healthy fund (ρ ≥ ρ*): immediate execution at the fundamental price.
* Bank-run zone (ρ < ρ*): the request lands in the withdrawal queue
  with a delay and a discount, both computed from coverage.

Lock-up: members within ``frozen_until`` cannot Convert (math §6.4).
"""

from __future__ import annotations

from decimal import Decimal

from app.domain.entities import (
    ClubState,
    LiquidityFund,
    Member,
    WithdrawalQueueEntry,
)
from app.domain.events import FundConverted, FundQueued
from app.domain.operations.base import (
    Command,
    ErrorCode,
    OperationError,
    OperationResult,
)
from app.domain.operations.commands import ConvertCommand
from app.domain.services.pricing import PricingService
from app.domain.services.withdrawal_queue import WithdrawalQueueService
from app.domain.value_objects import USDC, Price


class ConvertOperation:
    """Convert V → USDC, immediately or via the withdrawal queue."""

    def execute(self, state: ClubState, command: Command) -> OperationResult:
        assert isinstance(command, ConvertCommand)

        member = state.members.get(command.member)
        if member is None:
            return OperationResult.fail(
                state,
                OperationError(
                    code=ErrorCode.MEMBER_NOT_FOUND,
                    message=f"member {command.member!r} not found",
                ),
            )
        if member.is_frozen:
            return OperationResult.fail(
                state,
                OperationError(
                    code=ErrorCode.MEMBER_FROZEN,
                    message=f"member {command.member!r} is frozen",
                ),
            )
        if member.frozen_until is not None and state.tick < member.frozen_until:
            return OperationResult.fail(
                state,
                OperationError(
                    code=ErrorCode.LOCK_UP_ACTIVE,
                    message=(
                        f"lock-up active until tick {member.frozen_until}; "
                        f"current tick {state.tick}"
                    ),
                ),
            )
        # v2 dynamic vesting (improvements/04): a large conversion of freshly
        # acquired balance must vest τ0 + w·W days since last activity, so a
        # fraud cluster holds its unbacked position through the audit hazard.
        vesting = WithdrawalQueueService(state.parameters).vesting_days(command.amount)
        if vesting > 0 and member.last_active_tick is not None:
            vested_at = member.last_active_tick + vesting
            if state.tick < vested_at:
                return OperationResult.fail(
                    state,
                    OperationError(
                        code=ErrorCode.LOCK_UP_ACTIVE,
                        message=(
                            f"conversion vesting active until tick {vested_at} "
                            f"(w·W={vesting}d); current tick {state.tick}"
                        ),
                    ),
                )
        if not command.amount.is_positive():
            return OperationResult.fail(
                state,
                OperationError(
                    code=ErrorCode.INVALID_AMOUNT,
                    message="convert amount must be positive",
                ),
            )
        if member.balance < command.amount:
            return OperationResult.fail(
                state,
                OperationError(
                    code=ErrorCode.INSUFFICIENT_BALANCE,
                    message=(f"member balance {member.balance} < requested {command.amount}"),
                ),
            )

        pricing = PricingService(state.parameters)
        supply = state.supply()
        price = pricing.price(
            fund=state.fund.balance,
            ext_rev_annualized=state.ext_rev_annualized,
            supply=supply,
        )
        coverage = pricing.coverage_ratio(state.fund.balance, supply, price)

        if coverage >= state.parameters.rho_min:
            return self._execute_immediately(state, command, member, price)
        return self._enqueue(state, command, member, coverage)

    def _execute_immediately(
        self,
        state: ClubState,
        command: ConvertCommand,
        member: Member,
        price: Price,
    ) -> OperationResult:
        usdc_out = USDC(command.amount.root * price.root)
        if state.fund.balance < usdc_out:
            return OperationResult.fail(
                state,
                OperationError(
                    code=ErrorCode.INSUFFICIENT_FUND,
                    message="fund cannot cover this conversion",
                ),
            )
        new_member = member.model_copy(update={"balance": member.balance - command.amount})
        new_fund = LiquidityFund(balance=state.fund.balance - usdc_out)
        new_state = state.model_copy(
            update={
                "members": {**state.members, command.member: new_member},
                "fund": new_fund,
            }
        )
        return OperationResult.ok(
            new_state,
            FundConverted(
                member=command.member,
                v_amount=command.amount,
                usdc_paid=usdc_out,
                discount_applied=False,
            ),
        )

    def _enqueue(
        self,
        state: ClubState,
        command: ConvertCommand,
        member: Member,
        coverage: Decimal,
    ) -> OperationResult:
        queue_service = WithdrawalQueueService(state.parameters)
        execute_at = queue_service.execute_at(coverage, state.tick)
        # Reserve the V on the member's balance until execution by removing
        # it now and remembering the request in the queue. This prevents
        # double-spending the same V before settlement.
        new_member = member.model_copy(update={"balance": member.balance - command.amount})
        entry = WithdrawalQueueEntry(
            member=command.member,
            amount=command.amount,
            requested_at=state.tick,
            execute_at=execute_at,
        )
        new_state = state.model_copy(
            update={
                "members": {**state.members, command.member: new_member},
                "withdrawal_queue": (*state.withdrawal_queue, entry),
            }
        )
        return OperationResult.ok(
            new_state,
            FundQueued(
                member=command.member,
                v_amount=command.amount,
                execute_at=execute_at,
            ),
        )
