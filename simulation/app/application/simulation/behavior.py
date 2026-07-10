"""BehaviorModel — generates member-driven commands.

Three independent streams the engine asks for, in order:
1. join_commands  — new members entering the club this tick
2. transact_commands — service exchanges between existing members
3. convert_or_leave_commands — members withdrawing V or leaving

Architecture §8.3. Each strategy may use the injected RandomProvider
for stochastic decisions; pure deterministic strategies are useful for
tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Protocol

from app.application.ports.random_provider import RandomProvider
from app.domain.entities import ClubState
from app.domain.operations import (
    ConvertCommand,
    JoinCommand,
    LeaveCommand,
    TransactCommand,
)
from app.domain.value_objects import (
    CategoryId,
    MemberId,
    MemberKind,
    V,
    member_id,
)


def _deterministic_member_id(rng: RandomProvider, tick: int) -> MemberId:
    """Build a deterministic id from tick + rng draw — keeps runs reproducible."""
    suffix = rng.randint(0, 2**32 - 1)
    return member_id(f"m-{tick:06d}-{suffix:010d}")


class BehaviorModel(Protocol):
    """Internal-member action strategy."""

    def join_commands(
        self, state: ClubState, tick: int, rng: RandomProvider
    ) -> tuple[JoinCommand, ...]: ...

    def transact_commands(
        self, state: ClubState, tick: int, rng: RandomProvider
    ) -> tuple[TransactCommand, ...]: ...

    def convert_or_leave_commands(
        self, state: ClubState, tick: int, rng: RandomProvider
    ) -> tuple[ConvertCommand | LeaveCommand, ...]: ...


# ---------------------------------------------------------------------------
# Concrete strategies
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class NoBehavior:
    """Empty behavior — no commands. Useful as a baseline in tests."""

    def join_commands(
        self, state: ClubState, tick: int, rng: RandomProvider
    ) -> tuple[JoinCommand, ...]:
        del state, tick, rng
        return ()

    def transact_commands(
        self, state: ClubState, tick: int, rng: RandomProvider
    ) -> tuple[TransactCommand, ...]:
        del state, tick, rng
        return ()

    def convert_or_leave_commands(
        self, state: ClubState, tick: int, rng: RandomProvider
    ) -> tuple[ConvertCommand | LeaveCommand, ...]:
        del state, tick, rng
        return ()


@dataclass(frozen=True, slots=True)
class NormalActivityBehavior:
    """Steady joins and transactions parameterised by daily rates.

    Joins arrive Poisson-style (using rng.random against ``join_prob``);
    transactions are sampled by random pairs of active members.
    """

    daily_join_prob: Decimal = Decimal("0.1")
    daily_tx_per_member: Decimal = Decimal("0.13")  # 4/month
    avg_amount: V = field(default_factory=lambda: V(50))
    category: CategoryId = CategoryId.DEV

    def join_commands(
        self, state: ClubState, tick: int, rng: RandomProvider
    ) -> tuple[JoinCommand, ...]:
        del state
        if Decimal(str(rng.random())) < self.daily_join_prob:
            return (
                JoinCommand(
                    member=_deterministic_member_id(rng, tick),
                    member_kind=MemberKind.ACTIVE,
                ),
            )
        return ()

    def transact_commands(
        self, state: ClubState, tick: int, rng: RandomProvider
    ) -> tuple[TransactCommand, ...]:
        del tick
        eligible = [
            mid
            for mid, m in state.members.items()
            if not m.is_frozen
            and m.kind != MemberKind.INVESTOR
            and (m.frozen_until is None or m.frozen_until <= state.tick)
        ]
        if len(eligible) < 2:
            return ()
        # Expected transactions this tick.
        n = int(len(eligible) * float(self.daily_tx_per_member))
        if n == 0:
            return ()
        commands: list[TransactCommand] = []
        for _ in range(n):
            pair = rng.sample(eligible, 2)
            commands.append(
                TransactCommand(
                    actor=pair[0],
                    receiver=pair[1],
                    amount=self.avg_amount,
                    category=self.category,
                )
            )
        return tuple(commands)

    def convert_or_leave_commands(
        self, state: ClubState, tick: int, rng: RandomProvider
    ) -> tuple[ConvertCommand | LeaveCommand, ...]:
        del state, tick, rng
        return ()


@dataclass(frozen=True, slots=True)
class FraudClusterBehavior:
    """Fraud cluster: a fixed set of members trades only with each other.

    Each tick they generate one wash transaction between two cluster
    members. Used in fraud-attack scenarios (math §6.3).
    """

    members: tuple[MemberId, ...]
    amount: V = field(default_factory=lambda: V(50))
    category: CategoryId = CategoryId.OTHER

    def join_commands(
        self, state: ClubState, tick: int, rng: RandomProvider
    ) -> tuple[JoinCommand, ...]:
        del state, tick, rng
        return ()

    def transact_commands(
        self, state: ClubState, tick: int, rng: RandomProvider
    ) -> tuple[TransactCommand, ...]:
        del tick
        cluster_in_state = [m for m in self.members if m in state.members]
        if len(cluster_in_state) < 2:
            return ()
        pair = rng.sample(cluster_in_state, 2)
        return (
            TransactCommand(
                actor=pair[0],
                receiver=pair[1],
                amount=self.amount,
                category=self.category,
            ),
        )

    def convert_or_leave_commands(
        self, state: ClubState, tick: int, rng: RandomProvider
    ) -> tuple[ConvertCommand | LeaveCommand, ...]:
        del state, tick, rng
        return ()


@dataclass(frozen=True, slots=True)
class BankRunBehavior:
    """At ``trigger_tick`` a fraction of members all Convert at once."""

    trigger_tick: int
    fraction: Decimal = Decimal("0.3")

    def join_commands(
        self, state: ClubState, tick: int, rng: RandomProvider
    ) -> tuple[JoinCommand, ...]:
        del state, tick, rng
        return ()

    def transact_commands(
        self, state: ClubState, tick: int, rng: RandomProvider
    ) -> tuple[TransactCommand, ...]:
        del state, tick, rng
        return ()

    def convert_or_leave_commands(
        self, state: ClubState, tick: int, rng: RandomProvider
    ) -> tuple[ConvertCommand | LeaveCommand, ...]:
        if tick != self.trigger_tick:
            return ()
        eligible = sorted(
            mid
            for mid, m in state.members.items()
            if m.balance.is_positive()
            and not m.is_frozen
            and (m.frozen_until is None or m.frozen_until <= tick)
        )
        n = int(len(eligible) * float(self.fraction))
        if n == 0:
            return ()
        chosen = rng.sample(eligible, n)
        commands: list[ConvertCommand | LeaveCommand] = [
            ConvertCommand(member=mid, amount=state.members[mid].balance) for mid in chosen
        ]
        return tuple(commands)


@dataclass(frozen=True, slots=True)
class CompositeBehavior:
    """Sum of multiple behaviors. Commands from each are concatenated."""

    parts: tuple[BehaviorModel, ...]

    def join_commands(
        self, state: ClubState, tick: int, rng: RandomProvider
    ) -> tuple[JoinCommand, ...]:
        out: list[JoinCommand] = []
        for part in self.parts:
            out.extend(part.join_commands(state, tick, rng))
        return tuple(out)

    def transact_commands(
        self, state: ClubState, tick: int, rng: RandomProvider
    ) -> tuple[TransactCommand, ...]:
        out: list[TransactCommand] = []
        for part in self.parts:
            out.extend(part.transact_commands(state, tick, rng))
        return tuple(out)

    def convert_or_leave_commands(
        self, state: ClubState, tick: int, rng: RandomProvider
    ) -> tuple[ConvertCommand | LeaveCommand, ...]:
        out: list[ConvertCommand | LeaveCommand] = []
        for part in self.parts:
            out.extend(part.convert_or_leave_commands(state, tick, rng))
        return tuple(out)
