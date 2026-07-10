"""Registry — maps CommandKind to its Operation instance."""

from __future__ import annotations

from app.domain.operations.accrue_tenure import AccrueTenureReputationOperation
from app.domain.operations.base import (
    Command,
    CommandKind,
    Operation,
    OperationResult,
)
from app.domain.operations.convert import ConvertOperation
from app.domain.operations.enforce_concentration import (
    EnforceConcentrationResponseOperation,
)
from app.domain.operations.invest import InvestOperation
from app.domain.operations.join import JoinOperation
from app.domain.operations.leave import LeaveOperation
from app.domain.operations.process_overdue import ProcessOverdueLoansOperation
from app.domain.operations.process_queue import ProcessWithdrawalQueueOperation
from app.domain.operations.quarterly_distribution import QuarterlyDistributionOperation
from app.domain.operations.recalculate_turnover import RecalculateTurnoverOperation
from app.domain.operations.record_external_revenue import (
    RecordExternalRevenueOperation,
)
from app.domain.operations.run_audit import RunStochasticAuditOperation
from app.domain.operations.transact import TransactOperation


class OperationRegistry:
    """Holds one operation instance per CommandKind."""

    def __init__(self, operations: dict[CommandKind, Operation]) -> None:
        self._operations = dict(operations)

    def get(self, kind: CommandKind) -> Operation:
        try:
            return self._operations[kind]
        except KeyError as exc:
            raise KeyError(f"no operation registered for kind {kind!r}") from exc

    def execute(self, state, command: Command) -> OperationResult:  # type: ignore[no-untyped-def]
        return self.get(command.kind).execute(state, command)

    @property
    def kinds(self) -> tuple[CommandKind, ...]:
        return tuple(self._operations.keys())


def default_registry() -> OperationRegistry:
    """Build the registry with default operation instances.

    For tests and the engine. Each operation is parameter-free or
    constructed with safe defaults; the engine in Phase 5 will rebuild
    the registry per tick when it needs to inject the running default
    rate into TransactOperation.
    """
    return OperationRegistry(
        {
            CommandKind.JOIN: JoinOperation(),
            CommandKind.LEAVE: LeaveOperation(),
            CommandKind.TRANSACT: TransactOperation(),
            CommandKind.CONVERT: ConvertOperation(),
            CommandKind.INVEST: InvestOperation(),
            CommandKind.RECORD_EXTERNAL_REVENUE: RecordExternalRevenueOperation(),
            CommandKind.PROCESS_OVERDUE_LOANS: ProcessOverdueLoansOperation(),
            CommandKind.ACCRUE_TENURE_REPUTATION: AccrueTenureReputationOperation(),
            CommandKind.RECALCULATE_TURNOVER: RecalculateTurnoverOperation(),
            CommandKind.QUARTERLY_DISTRIBUTION: QuarterlyDistributionOperation(),
            CommandKind.PROCESS_WITHDRAWAL_QUEUE: ProcessWithdrawalQueueOperation(),
            CommandKind.RUN_STOCHASTIC_AUDIT: RunStochasticAuditOperation(),
            CommandKind.ENFORCE_CONCENTRATION_RESPONSE: EnforceConcentrationResponseOperation(),
            # DEFAULT_LOAN handled internally by ProcessOverdueLoansOperation.
        }
    )
