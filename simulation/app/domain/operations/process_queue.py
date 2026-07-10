"""ProcessWithdrawalQueue — settle Convert requests whose execute_at has come.

Each entry in the queue is settled at the *current* discounted price
(a queued conversion done late benefits from any recovery; punished
by the discount if coverage is still low).
"""

from __future__ import annotations

from app.domain.entities import ClubState, LiquidityFund
from app.domain.events import DomainEvent, FundConverted
from app.domain.operations.base import Command, OperationResult
from app.domain.services.pricing import PricingService
from app.domain.value_objects import USDC


class ProcessWithdrawalQueueOperation:
    def execute(self, state: ClubState, command: Command) -> OperationResult:
        del command
        if not state.withdrawal_queue:
            return OperationResult.ok(state)

        pricing = PricingService(state.parameters)
        events: list[DomainEvent] = []
        new_queue = []
        new_fund = state.fund.balance

        for entry in state.withdrawal_queue:
            if entry.execute_at > state.tick:
                new_queue.append(entry)
                continue
            # Re-evaluate price and discount at execution time.
            supply = state.supply()
            price = pricing.price(
                fund=new_fund, ext_rev_annualized=state.ext_rev_annualized, supply=supply
            )
            coverage = pricing.coverage_ratio(new_fund, supply, price)
            discount = pricing.discount_factor(coverage)
            settle_price = price.root * discount
            usdc_out = USDC(entry.amount.root * settle_price)
            if new_fund < usdc_out:
                # Insufficient fund — keep in queue.
                new_queue.append(entry)
                continue
            new_fund = new_fund - usdc_out
            events.append(
                FundConverted(
                    member=entry.member,
                    v_amount=entry.amount,
                    usdc_paid=usdc_out,
                    discount_applied=discount < 1,
                )
            )

        new_state = state.model_copy(
            update={
                "withdrawal_queue": tuple(new_queue),
                "fund": LiquidityFund(balance=new_fund),
            }
        )
        return OperationResult.ok(new_state, *events)
