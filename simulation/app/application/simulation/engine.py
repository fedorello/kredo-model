"""SimulationEngine — orchestrates one full run.

Architecture §8.1: every tick the engine executes the canonical pipeline:

    1. RecordExternalRevenue
    2. user-driven commands (Invest, Join, Transact, Convert/Leave)
    3. ProcessWithdrawalQueue
    4. RunStochasticAudit
    5. ProcessOverdueLoans
    6. AccrueTenureReputation
    7. RecalculateTurnover
    8. EnforceConcentrationResponse
    9. QuarterlyDistribution (every 90 ticks)
   10. Snapshot + metrics

After each operation the seven invariants are checked; violations
become ``InvariantViolated`` events but do not abort the run — we want
to *observe* misbehaviour, not paper over it.

Determinism: every random draw goes through the injected
``RandomProvider``. The PRNG state is snapshotted into ``ClubState``
once per tick so the run can be paused and resumed without drift.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.application.ports.cancellation import CancellationToken
from app.application.ports.random_provider import RandomProvider
from app.application.simulation.behavior import BehaviorModel
from app.application.simulation.market import MarketModel
from app.application.simulation.metrics import MetricsCollector
from app.application.simulation.periodic import PeriodicOperationRunner
from app.application.simulation.run_result import RunResult
from app.application.simulation.snapshots import SnapshotStore
from app.domain.entities import ClubState
from app.domain.events import InvariantViolated
from app.domain.invariants import check_all
from app.domain.operations import (
    Command,
    CommandKind,
    OperationRegistry,
    default_registry,
)
from app.domain.operations.transact import TransactOperation


@dataclass(frozen=True, slots=True)
class _NeverCancelled:
    def is_cancelled(self) -> bool:
        return False

    def cancel(self) -> None:
        pass


class SimulationEngine:
    """Run one simulation start-to-finish."""

    def __init__(
        self,
        rng: RandomProvider,
        *,
        registry: OperationRegistry | None = None,
        periodic: PeriodicOperationRunner | None = None,
    ) -> None:
        self._rng = rng
        self._registry = registry or default_registry()
        self._periodic = periodic or PeriodicOperationRunner()

    def run(
        self,
        initial_state: ClubState,
        *,
        total_ticks: int,
        seed: int,
        behavior: BehaviorModel,
        market: MarketModel,
        cancellation: CancellationToken | None = None,
        snapshot_every: int = 30,
    ) -> RunResult:
        cancel: CancellationToken = cancellation or _NeverCancelled()
        metrics = MetricsCollector()
        snapshots = SnapshotStore(every=snapshot_every)
        state = initial_state
        completed = 0
        stopped_early = False

        for tick in range(total_ticks):
            if cancel.is_cancelled():
                stopped_early = True
                break
            state = state.model_copy(update={"tick": tick})
            state = self._tick(state, behavior, market, metrics)
            metrics.record_tick(state, self._observed_default_rate(state))
            snapshots.maybe_store(state)
            completed = tick + 1

        return RunResult(
            seed=seed,
            total_ticks=total_ticks,
            completed_ticks=completed,
            stopped_early=stopped_early,
            final_state=state,
            metrics=list(metrics.metrics),
            events=list(metrics.events),
            snapshots=list(snapshots.snapshots),
            invariant_violations=metrics.total_violations,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _tick(
        self,
        state: ClubState,
        behavior: BehaviorModel,
        market: MarketModel,
        metrics: MetricsCollector,
    ) -> ClubState:
        market_tick = market.commands(state, state.tick, self._rng)
        commands: list[Command] = []
        if market_tick.external_revenue is not None:
            commands.append(market_tick.external_revenue)
        commands.extend(market_tick.invest)
        commands.extend(behavior.join_commands(state, state.tick, self._rng))
        commands.extend(behavior.transact_commands(state, state.tick, self._rng))
        commands.extend(behavior.convert_or_leave_commands(state, state.tick, self._rng))
        commands.extend(self._periodic.commands_for(state, state.tick))
        for cmd in commands:
            state = self._apply(state, cmd, metrics)
        return state

    def _apply(
        self,
        state: ClubState,
        command: Command,
        metrics: MetricsCollector,
    ) -> ClubState:
        prev = state
        operation = self._registry.get(command.kind)
        result = operation.execute(state, command)
        for event in result.events:
            metrics.record_event(state.tick, event)
        if not result.succeeded:
            return state
        # Run all seven invariants over the transition.
        for report in check_all(prev, result.new_state, command.kind.value):
            if report.is_violation():
                metrics.record_event(state.tick, InvariantViolated(report=report))
        return result.new_state

    def _observed_default_rate(self, state: ClubState) -> Decimal:
        if not state.loans:
            return Decimal(0)
        defaulted = sum(1 for loan in state.loans.values() if loan.is_defaulted())
        resolved = sum(
            1 for loan in state.loans.values() if loan.is_defaulted() or loan.is_repaid()
        )
        if resolved == 0:
            return Decimal(0)
        return Decimal(defaulted) / Decimal(resolved)


# Re-export for convenience.
__all__ = ["CommandKind", "SimulationEngine", "TransactOperation"]
