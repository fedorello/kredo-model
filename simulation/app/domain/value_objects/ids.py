"""Strongly-typed identifiers.

Each id is a `NewType` over `str` — at runtime it is a plain string, but
mypy keeps `MemberId` distinct from `LoanId` and from arbitrary `str`,
so accidental swaps are caught statically.

Construction goes through dedicated factories that return UUID-v4 strings.
Tests can pass deterministic values via the `from_str` helpers when a
`RandomProvider` cannot easily be threaded through.
"""

from __future__ import annotations

import uuid
from typing import NewType

MemberId = NewType("MemberId", str)
TransactionId = NewType("TransactionId", str)
LoanId = NewType("LoanId", str)


def new_member_id() -> MemberId:
    return MemberId(str(uuid.uuid4()))


def new_transaction_id() -> TransactionId:
    return TransactionId(str(uuid.uuid4()))


def new_loan_id() -> LoanId:
    return LoanId(str(uuid.uuid4()))


def member_id(value: str) -> MemberId:
    """Build a MemberId from an existing string (for tests and deserialization)."""
    return MemberId(value)


def transaction_id(value: str) -> TransactionId:
    return TransactionId(value)


def loan_id(value: str) -> LoanId:
    return LoanId(value)
