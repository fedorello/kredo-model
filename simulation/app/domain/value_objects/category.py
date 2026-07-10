"""Enumerations used across the domain.

These are intentionally fixed in v1. The real club would have a dynamic
taxonomy of service categories voted on by members, but for proving the
economic model out, six categories with parameterised price distributions
are sufficient (see ARCHITECTURE §4.4 and §16.5).
"""

from __future__ import annotations

from enum import StrEnum


class CategoryId(StrEnum):
    """Service category. Used by HHI / concentration monitoring."""

    CONSULTING = "consulting"
    DESIGN = "design"
    COPYWRITING = "copywriting"
    DEV = "dev"
    EDUCATION = "education"
    OTHER = "other"


class MemberKind(StrEnum):
    """Behavioural archetype for simulation purposes.

    ACTIVE   — issues and accepts transactions, can take credit.
    INVESTOR — only Invest and (after lock-up) Convert; no transactions.
    MIXED    — both modes.
    """

    ACTIVE = "active"
    INVESTOR = "investor"
    MIXED = "mixed"


class LoanState(StrEnum):
    """Lifecycle of a credit position opened during Transact."""

    OPEN = "open"
    REPAID = "repaid"
    DEFAULTED = "defaulted"
