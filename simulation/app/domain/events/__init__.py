"""Domain events emitted by operations.

Every operation may produce zero or more events. Events are append-only
records that the engine collects, persists, and surfaces in the UI.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.domain.invariants import InvariantReport
from app.domain.value_objects import (
    USDC,
    LoanId,
    MemberId,
    TransactionId,
    V,
)


@dataclass(frozen=True, slots=True)
class MemberJoined:
    member: MemberId
    grant: V


@dataclass(frozen=True, slots=True)
class MemberLeft:
    member: MemberId
    final_balance: V


@dataclass(frozen=True, slots=True)
class MemberFrozen:
    member: MemberId
    reason: str


@dataclass(frozen=True, slots=True)
class TransactionConfirmed:
    tx_id: TransactionId
    actor: MemberId
    receiver: MemberId
    amount: V


@dataclass(frozen=True, slots=True)
class LoanOpened:
    loan_id: LoanId
    borrower: MemberId
    principal: V
    epsilon: Decimal


@dataclass(frozen=True, slots=True)
class LoanRepaid:
    loan_id: LoanId
    amount: V
    fully_repaid: bool


@dataclass(frozen=True, slots=True)
class LoanDefaulted:
    loan_id: LoanId
    borrower: MemberId
    burned_escrow: V


@dataclass(frozen=True, slots=True)
class EscrowReleased:
    """Escrow distributed across members in proportion to turnover."""

    total_released: V
    recipients: int


@dataclass(frozen=True, slots=True)
class FundConverted:
    """V was sold back to the fund for USDC."""

    member: MemberId
    v_amount: V
    usdc_paid: USDC
    discount_applied: bool


@dataclass(frozen=True, slots=True)
class FundQueued:
    """A Convert request landed in the withdrawal queue."""

    member: MemberId
    v_amount: V
    execute_at: int


@dataclass(frozen=True, slots=True)
class Invested:
    """USDC deposited into the fund in exchange for V."""

    member: MemberId
    usdc_in: USDC
    v_out: V


@dataclass(frozen=True, slots=True)
class ExternalRevenueRecorded:
    amount: USDC


@dataclass(frozen=True, slots=True)
class QuarterlyDistribution:
    to_fund: USDC
    to_dividends: USDC
    to_genesis: USDC
    to_ops: USDC


@dataclass(frozen=True, slots=True)
class FraudRemediated:
    """A detected fraud cluster was frozen and its stake forfeited (v2).

    ``burned_v`` is the total positive V balance burned across the cluster —
    the forfeited stake Λ of Theorems 4–5 (plus burned escrow, reported
    separately by the LoanDefaulted events this remediation triggers)."""

    members: int
    burned_v: V
    burned_escrow: V


@dataclass(frozen=True, slots=True)
class InvariantViolated:
    """Surfaced when an invariant check returns ``is_violation()`` is True."""

    report: InvariantReport


# Sum type so engine code can treat all events uniformly.
DomainEvent = (
    MemberJoined
    | MemberLeft
    | MemberFrozen
    | TransactionConfirmed
    | LoanOpened
    | LoanRepaid
    | LoanDefaulted
    | EscrowReleased
    | FundConverted
    | FundQueued
    | Invested
    | ExternalRevenueRecorded
    | QuarterlyDistribution
    | FraudRemediated
    | InvariantViolated
)


__all__ = [
    "DomainEvent",
    "EscrowReleased",
    "ExternalRevenueRecorded",
    "FraudRemediated",
    "FundConverted",
    "FundQueued",
    "InvariantViolated",
    "Invested",
    "LoanDefaulted",
    "LoanOpened",
    "LoanRepaid",
    "MemberFrozen",
    "MemberJoined",
    "MemberLeft",
    "QuarterlyDistribution",
    "TransactionConfirmed",
]
