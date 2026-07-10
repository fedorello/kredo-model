"""Member — a participant in the Club."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.domain.value_objects import MemberId, MemberKind, R, V


class Member(BaseModel):
    """A Club participant.

    Frozen by design — every operation produces a new instance with the
    relevant fields replaced via :meth:`model_copy`.
    """

    model_config = ConfigDict(frozen=True)

    id: MemberId
    kind: MemberKind
    balance: V
    reputation: R
    joined_at: int
    """Tick at which this member joined the club."""
    is_frozen: bool = False
    """Account frozen following a Default. See ARCHITECTURE §5.2."""
    frozen_until: int | None = None
    """If set, the tick at which freeze / lock-up ends."""
    turnover_90d: V = Field(default_factory=V.zero)
    """Active turnover over the trailing 90 days. Drives escrow distribution."""
    cumulative_contribution: V = Field(default_factory=V.zero)
    """Total verified contribution over member lifetime — used for activity multiplier."""
