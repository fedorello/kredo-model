"""Invest — investor deposits USDC, receives V at the prevailing price.

By math §7.1 this operation is price-neutral. ``cumulative_invested_v``
is incremented so I3 can account for the emission.
"""

from __future__ import annotations

from app.domain.entities import ClubState, LiquidityFund
from app.domain.events import Invested
from app.domain.operations.base import (
    Command,
    ErrorCode,
    OperationError,
    OperationResult,
)
from app.domain.operations.commands import InvestCommand
from app.domain.services.pricing import PricingService
from app.domain.value_objects import V


class InvestOperation:
    """Receive USDC into the fund, mint V to the investor."""

    def execute(self, state: ClubState, command: Command) -> OperationResult:
        assert isinstance(command, InvestCommand)

        member = state.members.get(command.member)
        if member is None:
            return OperationResult.fail(
                state,
                OperationError(
                    code=ErrorCode.MEMBER_NOT_FOUND,
                    message=f"investor {command.member!r} must Join first",
                ),
            )
        if command.amount.is_zero():
            return OperationResult.fail(
                state,
                OperationError(
                    code=ErrorCode.INVALID_AMOUNT,
                    message="invest amount must be positive",
                ),
            )

        pricing = PricingService(state.parameters)
        price = pricing.price(
            fund=state.fund.balance,
            ext_rev_annualized=state.ext_rev_annualized,
            supply=state.supply(),
        )
        # At bootstrap (price == 0) we use 1:1 USDC → V. This is the
        # only path where price is zero, and the invariant theorem
        # (math §7.1) is then trivial because the post-state price will
        # also be re-computed from a non-zero supply.
        v_out_amount = command.amount.root if price.root == 0 else command.amount.root / price.root
        v_out = V(v_out_amount)

        new_member = member.model_copy(update={"balance": member.balance + v_out})
        new_members = {**state.members, command.member: new_member}
        new_fund = LiquidityFund(balance=state.fund.balance + command.amount)
        new_state = state.model_copy(
            update={
                "members": new_members,
                "fund": new_fund,
                "cumulative_invested_v": state.cumulative_invested_v + v_out,
            }
        )
        return OperationResult.ok(
            new_state,
            Invested(
                member=command.member,
                usdc_in=command.amount,
                v_out=v_out,
            ),
        )
