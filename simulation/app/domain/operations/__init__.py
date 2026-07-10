"""Domain operations — pure ``(state, command) → result`` transitions."""

from __future__ import annotations

from app.domain.operations.base import (
    Command,
    CommandKind,
    ErrorCode,
    Operation,
    OperationError,
    OperationResult,
)
from app.domain.operations.commands import (
    ConvertCommand,
    InvestCommand,
    JoinCommand,
    LeaveCommand,
    RecordExternalRevenueCommand,
    RemediateFraudCommand,
    TransactCommand,
    make_accrue_tenure,
    make_decay_reputation,
    make_enforce_concentration_response,
    make_process_overdue,
    make_process_withdrawal_queue,
    make_quarterly_distribution,
    make_recalculate_turnover,
    make_run_stochastic_audit,
)
from app.domain.operations.registry import OperationRegistry, default_registry

__all__ = [
    "Command",
    "CommandKind",
    "ConvertCommand",
    "ErrorCode",
    "InvestCommand",
    "JoinCommand",
    "LeaveCommand",
    "Operation",
    "OperationError",
    "OperationRegistry",
    "OperationResult",
    "RecordExternalRevenueCommand",
    "RemediateFraudCommand",
    "TransactCommand",
    "default_registry",
    "make_accrue_tenure",
    "make_decay_reputation",
    "make_enforce_concentration_response",
    "make_process_overdue",
    "make_process_withdrawal_queue",
    "make_quarterly_distribution",
    "make_recalculate_turnover",
    "make_run_stochastic_audit",
]
