"""Concrete command types for each operation.

Commands are immutable input bundles. Every command exposes ``kind``
so the registry can dispatch without an isinstance ladder.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.operations.base import CommandKind
from app.domain.value_objects import (
    USDC,
    CategoryId,
    Confidence,
    MemberId,
    MemberKind,
    V,
)


@dataclass(frozen=True, slots=True)
class JoinCommand:
    member: MemberId
    member_kind: MemberKind = MemberKind.ACTIVE
    expected_new_members: int = 1

    @property
    def kind(self) -> CommandKind:
        return CommandKind.JOIN


@dataclass(frozen=True, slots=True)
class LeaveCommand:
    member: MemberId

    @property
    def kind(self) -> CommandKind:
        return CommandKind.LEAVE


@dataclass(frozen=True, slots=True)
class TransactCommand:
    actor: MemberId
    receiver: MemberId
    amount: V
    category: CategoryId
    review_score: Confidence | None = None
    audit_score: Confidence | None = None

    @property
    def kind(self) -> CommandKind:
        return CommandKind.TRANSACT


@dataclass(frozen=True, slots=True)
class ConvertCommand:
    member: MemberId
    amount: V

    @property
    def kind(self) -> CommandKind:
        return CommandKind.CONVERT


@dataclass(frozen=True, slots=True)
class InvestCommand:
    member: MemberId
    """Investor's member id. The member must already exist (via Join)."""
    amount: USDC

    @property
    def kind(self) -> CommandKind:
        return CommandKind.INVEST


@dataclass(frozen=True, slots=True)
class RecordExternalRevenueCommand:
    amount: USDC

    @property
    def kind(self) -> CommandKind:
        return CommandKind.RECORD_EXTERNAL_REVENUE


@dataclass(frozen=True, slots=True)
class RemediateFraudCommand:
    """Freeze a detected fraud cluster and forfeit its stake (v2, Phase 6)."""

    members: tuple[MemberId, ...]

    @property
    def kind(self) -> CommandKind:
        return CommandKind.REMEDIATE_FRAUD


# Periodic, parameterless commands:


@dataclass(frozen=True, slots=True)
class _BarePeriodicCommand:
    """Periodic system commands carry no input besides their kind."""

    kind: CommandKind


def make_process_overdue() -> _BarePeriodicCommand:
    return _BarePeriodicCommand(kind=CommandKind.PROCESS_OVERDUE_LOANS)


def make_accrue_tenure() -> _BarePeriodicCommand:
    return _BarePeriodicCommand(kind=CommandKind.ACCRUE_TENURE_REPUTATION)


def make_recalculate_turnover() -> _BarePeriodicCommand:
    return _BarePeriodicCommand(kind=CommandKind.RECALCULATE_TURNOVER)


def make_quarterly_distribution() -> _BarePeriodicCommand:
    return _BarePeriodicCommand(kind=CommandKind.QUARTERLY_DISTRIBUTION)


def make_process_withdrawal_queue() -> _BarePeriodicCommand:
    return _BarePeriodicCommand(kind=CommandKind.PROCESS_WITHDRAWAL_QUEUE)


def make_run_stochastic_audit() -> _BarePeriodicCommand:
    return _BarePeriodicCommand(kind=CommandKind.RUN_STOCHASTIC_AUDIT)


def make_enforce_concentration_response() -> _BarePeriodicCommand:
    return _BarePeriodicCommand(kind=CommandKind.ENFORCE_CONCENTRATION_RESPONSE)


def make_decay_reputation() -> _BarePeriodicCommand:
    return _BarePeriodicCommand(kind=CommandKind.DECAY_REPUTATION)
