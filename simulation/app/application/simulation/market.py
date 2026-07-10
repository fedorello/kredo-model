"""MarketModel — generates investment and external-revenue commands.

The "market" is the world outside the Club: investors deposit USDC,
external clients buy services. Engine asks the market every tick what
USDC inflows happened, and routes them through ``Invest`` and
``RecordExternalRevenue`` operations.

Architecture §8.3 separates this from BehaviorModel — internal
member action vs external market signals are independent drivers.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from app.application.ports.random_provider import RandomProvider
from app.domain.entities import ClubState
from app.domain.operations import (
    InvestCommand,
    RecordExternalRevenueCommand,
)
from app.domain.value_objects import USDC, MemberId


@dataclass(frozen=True, slots=True)
class MarketTick:
    """Commands the market produces for one tick."""

    invest: tuple[InvestCommand, ...] = ()
    external_revenue: RecordExternalRevenueCommand | None = None


class MarketModel(Protocol):
    """Strategy for external-market activity."""

    def commands(self, state: ClubState, tick: int, rng: RandomProvider) -> MarketTick: ...


# ---------------------------------------------------------------------------
# Concrete strategies
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class StagnantMarket:
    """Zero external revenue, zero investment.

    Used to test the math §10.4 minimum-survival condition: without
    external income the system is mathematically condemned to falling
    price.
    """

    def commands(self, state: ClubState, tick: int, rng: RandomProvider) -> MarketTick:
        del state, tick, rng
        return MarketTick()


@dataclass(frozen=True, slots=True)
class ConstantInflowMarket:
    """Steady ``λ_inv`` and ``λ_rev`` per tick.

    investor_ids cycle through a fixed list — caller is responsible
    for joining those members beforehand.
    """

    daily_invest: USDC
    daily_revenue: USDC
    investor_ids: tuple[MemberId, ...]

    def commands(self, state: ClubState, tick: int, rng: RandomProvider) -> MarketTick:
        del rng
        invest_cmds: list[InvestCommand] = []
        if self.daily_invest.is_positive() and self.investor_ids:
            picked = self.investor_ids[tick % len(self.investor_ids)]
            if picked in state.members:
                invest_cmds.append(InvestCommand(member=picked, amount=self.daily_invest))
        rev_cmd = (
            RecordExternalRevenueCommand(amount=self.daily_revenue)
            if self.daily_revenue.is_positive()
            else None
        )
        return MarketTick(invest=tuple(invest_cmds), external_revenue=rev_cmd)


@dataclass(frozen=True, slots=True)
class GrowthMarket:
    """Initial ``daily_revenue`` growing geometrically each tick."""

    initial_revenue: USDC
    daily_growth_rate: Decimal
    """e.g. 0.001 ≈ 5 %/month."""
    investor_ids: tuple[MemberId, ...] = ()

    def commands(self, state: ClubState, tick: int, rng: RandomProvider) -> MarketTick:
        del rng
        factor = (Decimal(1) + self.daily_growth_rate) ** tick
        rev_amount = USDC(self.initial_revenue.root * factor)
        rev_cmd = (
            RecordExternalRevenueCommand(amount=rev_amount) if rev_amount.is_positive() else None
        )
        invest_cmds: list[InvestCommand] = []
        if self.investor_ids and tick % 7 == 0:
            picked = self.investor_ids[tick % len(self.investor_ids)]
            if picked in state.members:
                invest_cmds.append(InvestCommand(member=picked, amount=rev_amount))
        return MarketTick(invest=tuple(invest_cmds), external_revenue=rev_cmd)


@dataclass(frozen=True, slots=True)
class CompositeMarket:
    """Sum of multiple market strategies."""

    parts: tuple[MarketModel, ...]

    def commands(self, state: ClubState, tick: int, rng: RandomProvider) -> MarketTick:
        invest: list[InvestCommand] = []
        rev_total: USDC = USDC.zero()
        for part in self.parts:
            piece = part.commands(state, tick, rng)
            invest.extend(piece.invest)
            if piece.external_revenue is not None:
                rev_total = rev_total + piece.external_revenue.amount
        rev_cmd = (
            RecordExternalRevenueCommand(amount=rev_total) if rev_total.is_positive() else None
        )
        return MarketTick(invest=tuple(invest), external_revenue=rev_cmd)


def chain_invest_commands(
    parts: Iterable[InvestCommand],
) -> tuple[InvestCommand, ...]:
    """Helper to build an Invest tuple in tests."""
    return tuple(parts)
