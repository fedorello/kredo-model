"""``RunResult`` — outcome of a simulation run."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from app.domain.entities import ClubState
from app.domain.events import DomainEvent


@dataclass(frozen=True, slots=True)
class TickMetrics:
    """Time-series row for one tick."""

    tick: int
    supply: Decimal
    fund_usdc: Decimal
    ext_rev: Decimal
    price_usdc_per_v: Decimal
    coverage_ratio: Decimal
    epsilon: Decimal
    observed_default_rate: Decimal
    member_count: int
    frozen_count: int
    open_loans: int
    defaulted_loans: int
    queue_length: int
    escrow_total: Decimal
    invariant_violations: int


@dataclass(frozen=True, slots=True)
class RunResult:
    """Final result of a simulation run."""

    seed: int
    total_ticks: int
    completed_ticks: int
    stopped_early: bool
    final_state: ClubState
    metrics: list[TickMetrics] = field(default_factory=list)
    events: list[tuple[int, DomainEvent]] = field(default_factory=list)
    snapshots: list[tuple[int, ClubState]] = field(default_factory=list)
    invariant_violations: int = 0
