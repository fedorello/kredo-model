"""QuarterlyProfitDistribution — split accumulated quarterly profit.

ARCHITECTURE §2.6 v2:
    50 % stays in Liquidity Fund (raises price)
    30 % paid as dividends to V holders
    15 % to Genesis Pool
     5 % to operational/development (modelled as a fund debit only)

The "quarterly profit" available for split is the *delta* in the fund
since the last distribution event. We approximate this by computing
``λ_rev × 90 days`` in the engine and recording it via this op. The
operation receives no command parameters; it consults ``state.fund``
and ``state.last_quarterly_distribution_tick``.

For Phase 4 we use a simplified profit model: every tick during the
quarter, ``ext_rev`` accumulates into the fund. At the distribution
tick we take 30 % / 15 % / 5 % of the fund balance as the quarterly
profit (50 % stays). This is a deliberate simplification: real profit
accounting would track explicit incoming and outgoing flows.
"""

from __future__ import annotations

from decimal import Decimal

from app.domain.entities import (
    ClubState,
    GenesisPool,
    LiquidityFund,
)
from app.domain.events import QuarterlyDistribution
from app.domain.operations.base import Command, OperationResult
from app.domain.services.activity_multiplier import ActivityMultiplierService
from app.domain.services.pricing import PricingService
from app.domain.value_objects import USDC, V


class QuarterlyDistributionOperation:
    def execute(self, state: ClubState, command: Command) -> OperationResult:
        del command
        params = state.parameters
        # The full fund is partitioned by the configured shares.
        # 50% stays => those USDC remain in the fund, no debit.
        # 30% leaves the fund as dividends paid in V (converted at price).
        # 15% leaves the fund and converts to V into the genesis pool.
        # 5% leaves the fund (operations expense).
        fund_balance = state.fund.balance
        if fund_balance.is_zero():
            return OperationResult.ok(state)

        to_dividends = USDC(fund_balance.root * params.quarterly_to_dividend)
        to_genesis = USDC(fund_balance.root * params.quarterly_to_genesis)
        to_ops = USDC(fund_balance.root * params.quarterly_to_ops)
        # Sanity: leftover fund stays.
        new_fund_balance = fund_balance - to_dividends - to_genesis - to_ops

        # Convert USDC dividend / genesis amounts to V using current price.
        pricing = PricingService(params)
        supply = state.supply()
        price = pricing.price(state.fund.balance, state.ext_rev_annualized, supply)

        def to_v(usdc: USDC) -> V:
            if price.root > 0:
                return V(usdc.root / price.root)
            return V(usdc.root)

        dividend_in_v = to_v(to_dividends)
        genesis_in_v = to_v(to_genesis)

        new_state = state.model_copy(
            update={
                "fund": LiquidityFund(balance=new_fund_balance),
                "genesis": GenesisPool(
                    balance=state.genesis.balance + genesis_in_v,
                    cumulative_funded=state.genesis.cumulative_funded + genesis_in_v,
                ),
                "members": _distribute_dividends(state, dividend_in_v),
                "last_quarterly_distribution_tick": state.tick,
            }
        )
        return OperationResult.ok(
            new_state,
            QuarterlyDistribution(
                to_fund=USDC(fund_balance.root * params.quarterly_to_fund),
                to_dividends=to_dividends,
                to_genesis=to_genesis,
                to_ops=to_ops,
            ),
        )


def _distribute_dividends(state: ClubState, total: V) -> dict:  # type: ignore[type-arg]
    """Split ``total`` V across V holders weighted by balance × activity multiplier."""
    if total.is_zero() or not state.members:
        return state.members
    activity = ActivityMultiplierService(state.parameters)
    mean_contribution = _mean_active_contribution(state)
    weights: dict = {}  # type: ignore[type-arg]
    total_weight = Decimal(0)
    for member_id, member in state.members.items():
        if not member.balance.is_positive():
            continue
        multiplier = activity.multiplier(member.cumulative_contribution, mean_contribution)
        weight = member.balance.root * multiplier
        weights[member_id] = weight
        total_weight += weight
    if total_weight == 0:
        return state.members
    new_members = {**state.members}
    for member_id, weight in weights.items():
        share = weight / total_weight
        addition = V(total.root * share)
        recipient = new_members[member_id]
        new_members[member_id] = recipient.model_copy(
            update={"balance": recipient.balance + addition}
        )
    return new_members


def _mean_active_contribution(state: ClubState) -> V:
    active = [m for m in state.members.values() if m.cumulative_contribution.is_positive()]
    if not active:
        return V.zero()
    total = sum((m.cumulative_contribution.root for m in active), Decimal(0))
    return V(total / len(active))
