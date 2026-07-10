"""PeriodicOperationRunner — schedules system periodic ops.

Order is fixed (Architecture §8.1). The runner exposes one method,
``commands_for(tick)``, that returns the system commands the engine
should apply *after* user-driven actions.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.entities import ClubState
from app.domain.operations import (
    Command,
    make_accrue_tenure,
    make_enforce_concentration_response,
    make_process_overdue,
    make_process_withdrawal_queue,
    make_quarterly_distribution,
    make_recalculate_turnover,
    make_run_stochastic_audit,
)


@dataclass(frozen=True, slots=True)
class PeriodicOperationRunner:
    """Yields the deterministic sequence of periodic commands per tick."""

    quarterly_period_days: int = 90

    def commands_for(self, state: ClubState, tick: int) -> tuple[Command, ...]:
        """Return periodic commands in the canonical order from §8.1."""
        commands: list[Command] = [
            make_process_withdrawal_queue(),
            make_run_stochastic_audit(),
            make_process_overdue(),
            make_accrue_tenure(),
            make_recalculate_turnover(),
            make_enforce_concentration_response(),
        ]
        if tick > 0 and tick % self.quarterly_period_days == 0:
            commands.append(make_quarterly_distribution())
        return tuple(commands)
