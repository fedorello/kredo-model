"""ClubState — the single immutable snapshot of the entire Club at one tick.

Every operation produces a new ClubState. The full state is JSON-
serialisable (round-trip is part of the Phase 1 DoD), which gives us
free history, free comparison, and free remote storage of long runs.

The state intentionally carries the PRNG state (`rng_state`) so a
simulation can be paused and resumed without losing determinism.
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.entities.escrow import DistributionEscrow
from app.domain.entities.fund import LiquidityFund
from app.domain.entities.genesis import GenesisPool
from app.domain.entities.loan import Loan
from app.domain.entities.member import Member
from app.domain.entities.queue import WithdrawalQueueEntry
from app.domain.entities.transaction import TransactionRecord
from app.domain.parameters import ClubParameters
from app.domain.value_objects import USDC, LoanId, MemberId, V


class ClubState(BaseModel):
    """Full Club state at one tick.

    ``model_copy(update={...})`` is the canonical way operations build
    a new state — pydantic enforces frozen=True so accidental in-place
    mutation is impossible.
    """

    model_config = ConfigDict(frozen=True)

    tick: int

    members: dict[MemberId, Member] = Field(default_factory=dict)
    loans: dict[LoanId, Loan] = Field(default_factory=dict)

    fund: LiquidityFund = Field(default_factory=LiquidityFund.empty)
    genesis: GenesisPool = Field(default_factory=GenesisPool.empty)
    escrow: DistributionEscrow = Field(default_factory=DistributionEscrow.empty)

    ext_rev_annualized: USDC = Field(default_factory=USDC.zero)
    """Sliding-window annualised external revenue used in price formula."""

    transactions: tuple[TransactionRecord, ...] = ()
    """Append-only log of every confirmed transaction."""

    withdrawal_queue: tuple[WithdrawalQueueEntry, ...] = ()

    parameters: ClubParameters = Field(default_factory=ClubParameters)

    initial_genesis_grants: V = Field(default_factory=V.zero)
    """Cumulative V issued as welcome grants. Required for Invariant I3."""

    cumulative_invested_v: V = Field(default_factory=V.zero)
    """Cumulative V emitted in Invest operations (V given to investors in
    exchange for USDC deposited into the fund). Required for I3."""

    last_quarterly_distribution_tick: int = 0

    rng_state: bytes = b""
    """Serialised RandomProvider state — empty before first use."""

    @field_validator("tick", "last_quarterly_distribution_tick")
    @classmethod
    def _non_negative_int(cls, value: int) -> int:
        if value < 0:
            raise ValueError(f"tick must be >= 0, got {value}")
        return value

    @field_validator("initial_genesis_grants", "cumulative_invested_v")
    @classmethod
    def _v_field_non_negative(cls, value: V) -> V:
        if value.is_negative():
            raise ValueError(f"value must be >= 0, got {value}")
        return value

    @classmethod
    def initial(cls, parameters: ClubParameters | None = None) -> Self:
        """Build an empty state at tick 0 with default or supplied parameters."""
        return cls(tick=0, parameters=parameters or ClubParameters())

    # ---- derived getters used across the codebase -----------------------

    def positive_balance_total(self) -> V:
        """Sum of all positive member balances. Used in Supply formula."""
        total = V.zero()
        for member in self.members.values():
            if member.balance.is_positive():
                total = total + member.balance
        return total

    def supply(self) -> V:
        """Supply(t) = Σ max(0, b(m)) + Escrow + GenesisPool.

        Note: this is the *strict* supply per ARCHITECTURE §16.5 (final I3
        formulation). InitialGenesisGrants is tracked separately on the
        state and reconciled by the I3 invariant checker.
        """
        return self.positive_balance_total() + self.escrow.total + self.genesis.balance
