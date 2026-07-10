"""MetricsCollector — captures one TickMetrics row per tick.

The engine calls ``record_tick(state, observed_default_rate, ...)`` after
finishing every tick. The result is a list[TickMetrics] of length
``total_ticks``. Phase 7 will stream this to Postgres in batches; for
now everything stays in memory.
"""

from __future__ import annotations

from decimal import Decimal

from app.application.simulation.run_result import TickMetrics
from app.domain.entities import ClubState
from app.domain.events import DomainEvent, InvariantViolated
from app.domain.services.epsilon import EpsilonCalculator
from app.domain.services.pricing import PricingService
from app.domain.value_objects import LoanState


class MetricsCollector:
    """In-memory recorder of tick metrics and events."""

    def __init__(self) -> None:
        self._metrics: list[TickMetrics] = []
        self._events: list[tuple[int, DomainEvent]] = []
        self._violation_count = 0

    def record_event(self, tick: int, event: DomainEvent) -> None:
        self._events.append((tick, event))
        if isinstance(event, InvariantViolated):
            self._violation_count += 1

    def record_tick(
        self,
        state: ClubState,
        observed_default_rate: Decimal,
    ) -> None:
        pricing = PricingService(state.parameters)
        supply = state.supply()
        price = pricing.price(state.fund.balance, state.ext_rev_annualized, supply)
        coverage = pricing.coverage_ratio(state.fund.balance, supply, price)
        epsilon = EpsilonCalculator(state.parameters).compute(observed_default_rate)
        members = state.members.values()
        loan_states = state.loans.values()
        violation_in_tick = sum(
            1
            for tick, event in self._events
            if tick == state.tick and isinstance(event, InvariantViolated)
        )
        self._metrics.append(
            TickMetrics(
                tick=state.tick,
                supply=supply.root,
                fund_usdc=state.fund.balance.root,
                ext_rev=state.ext_rev_annualized.root,
                price_usdc_per_v=price.root,
                coverage_ratio=coverage,
                epsilon=epsilon,
                observed_default_rate=observed_default_rate,
                member_count=len(state.members),
                frozen_count=sum(1 for m in members if m.is_frozen),
                open_loans=sum(1 for loan in loan_states if loan.is_open()),
                defaulted_loans=sum(1 for loan in loan_states if loan.state == LoanState.DEFAULTED),
                queue_length=len(state.withdrawal_queue),
                escrow_total=state.escrow.total.root,
                invariant_violations=violation_in_tick,
            )
        )

    @property
    def metrics(self) -> list[TickMetrics]:
        return self._metrics

    @property
    def events(self) -> list[tuple[int, DomainEvent]]:
        return self._events

    @property
    def total_violations(self) -> int:
        return self._violation_count
