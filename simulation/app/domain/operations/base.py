"""Base types for operations.

An operation is a pure function ``(state, command) → result``. Each
concrete operation lives in its own module and exposes one ``execute``
method. The engine looks up the right operation by ``CommandKind`` and
invokes it.

The result type carries either a new state plus events, or an error
plus the original state (operations never partially apply).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from app.domain.entities import ClubState
from app.domain.events import DomainEvent


class CommandKind(StrEnum):
    """All operation kinds the engine knows about."""

    JOIN = "join"
    LEAVE = "leave"
    TRANSACT = "transact"
    CONVERT = "convert"
    INVEST = "invest"
    DEFAULT_LOAN = "default_loan"
    PROCESS_OVERDUE_LOANS = "process_overdue_loans"
    ACCRUE_TENURE_REPUTATION = "accrue_tenure_reputation"
    RECALCULATE_TURNOVER = "recalculate_turnover"
    QUARTERLY_DISTRIBUTION = "quarterly_distribution"
    PROCESS_WITHDRAWAL_QUEUE = "process_withdrawal_queue"
    RUN_STOCHASTIC_AUDIT = "run_stochastic_audit"
    ENFORCE_CONCENTRATION_RESPONSE = "enforce_concentration_response"
    RECORD_EXTERNAL_REVENUE = "record_external_revenue"


class ErrorCode(StrEnum):
    """Stable identifiers for predictable failure modes."""

    MEMBER_NOT_FOUND = "member_not_found"
    MEMBER_ALREADY_EXISTS = "member_already_exists"
    MEMBER_FROZEN = "member_frozen"
    LOCK_UP_ACTIVE = "lock_up_active"
    INSUFFICIENT_BALANCE = "insufficient_balance"
    INSUFFICIENT_FUND = "insufficient_fund"
    CREDIT_LIMIT_EXCEEDED = "credit_limit_exceeded"
    OPEN_LOANS_PRESENT = "open_loans_present"
    CONFIDENCE_TOO_LOW = "confidence_too_low"
    INVALID_AMOUNT = "invalid_amount"
    SAME_PARTIES = "same_parties"


@dataclass(frozen=True, slots=True)
class OperationError:
    code: ErrorCode
    message: str


class Command(Protocol):
    """Marker for operation commands."""

    @property
    def kind(self) -> CommandKind: ...


@dataclass(frozen=True, slots=True)
class OperationResult:
    """Outcome of one operation invocation.

    ``new_state`` is always populated:
    * on success — the post-state with all changes applied;
    * on failure — the unchanged input state.
    """

    new_state: ClubState
    events: tuple[DomainEvent, ...]
    error: OperationError | None = None

    @classmethod
    def ok(cls, state: ClubState, *events: DomainEvent) -> OperationResult:
        return cls(new_state=state, events=tuple(events))

    @classmethod
    def fail(cls, state: ClubState, error: OperationError) -> OperationResult:
        return cls(new_state=state, events=(), error=error)

    @property
    def succeeded(self) -> bool:
        return self.error is None


@runtime_checkable
class Operation(Protocol):
    """Every operation implements this interface."""

    def execute(self, state: ClubState, command: Command) -> OperationResult: ...
