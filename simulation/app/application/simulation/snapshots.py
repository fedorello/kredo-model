"""Snapshot store — periodic + key-event state captures."""

from __future__ import annotations

from app.domain.entities import ClubState


class SnapshotStore:
    """In-memory list of (tick, ClubState) snapshots.

    Phase 7 will stream snapshots to Postgres jsonb; the in-memory
    interface stays the same.
    """

    def __init__(self, every: int = 30) -> None:
        if every <= 0:
            raise ValueError("snapshot interval must be positive")
        self._every = every
        self._snapshots: list[tuple[int, ClubState]] = []

    def maybe_store(self, state: ClubState, *, force: bool = False) -> None:
        if force or state.tick % self._every == 0:
            self._snapshots.append((state.tick, state))

    @property
    def snapshots(self) -> list[tuple[int, ClubState]]:
        return self._snapshots
