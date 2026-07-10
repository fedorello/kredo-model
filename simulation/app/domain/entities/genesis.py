"""Genesis Pool — V reserve for welcome grants.

`cumulative_funded` tracks every V ever moved into this pool. It is
required for the strict form of Invariant I3:

    Supply = VerifiedValue + InitialGenesisGrants + drift

without it we could not separate "issued because someone joined" from
"issued because someone created value".
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.value_objects import V


class GenesisPool(BaseModel):
    """Welcome-grant reservoir."""

    model_config = ConfigDict(frozen=True)

    balance: V
    """Current V available for grants. Always ≥ 0."""
    cumulative_funded: V
    """Total V ever deposited into the pool over its lifetime."""

    @field_validator("balance", "cumulative_funded")
    @classmethod
    def _non_negative(cls, value: V) -> V:
        if value.is_negative():
            raise ValueError(f"genesis pool field must be non-negative, got {value}")
        return value

    @classmethod
    def empty(cls) -> Self:
        return cls(balance=V.zero(), cumulative_funded=V.zero())
