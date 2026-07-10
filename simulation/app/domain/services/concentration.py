"""Market concentration metrics — HHI, bilateral, reciprocity.

ARCHITECTURE §2.3 / §6:

    HHI(category)         = 10000 · Σ_i (volume_i / total_volume)²
    bilateral(A, B)       = volume(A→B) / total_volume(A)
    reciprocity(A, B)     = min(volume(A→B), volume(B→A)) / max(...)

These are *measurements*. Decisions about what to do when a metric
breaches a threshold live in MonitoringResponseService — separation
of concerns lets us reuse measurement in dashboards without coupling
to enforcement.
"""

from __future__ import annotations

from decimal import Decimal

from app.domain.value_objects import MemberId, V


class ConcentrationMonitor:
    """Compute concentration metrics over transaction volume aggregates."""

    @staticmethod
    def hhi(volumes_by_provider: dict[MemberId, V]) -> Decimal:
        """Herfindahl-Hirschman Index, scaled to [0, 10000].

        HHI ≤ 1500 — competitive. 1500–2500 — moderate concentration.
        ≥ 2500 — high concentration. ≥ 4000 — single-provider dominance.
        """
        total = sum((v.root for v in volumes_by_provider.values()), Decimal(0))
        if total <= 0:
            return Decimal(0)
        return Decimal(10_000) * sum(
            ((v.root / total) ** 2 for v in volumes_by_provider.values()),
            Decimal(0),
        )

    @staticmethod
    def bilateral_concentration(
        member_total_volumes: dict[MemberId, V],
        pair_volumes: dict[tuple[MemberId, MemberId], V],
    ) -> dict[tuple[MemberId, MemberId], Decimal]:
        """For each ordered pair (A, B), the share of A's volume going to B."""
        result: dict[tuple[MemberId, MemberId], Decimal] = {}
        for (actor, counterparty), pair_vol in pair_volumes.items():
            actor_total = member_total_volumes.get(actor)
            if actor_total is None or actor_total.is_zero():
                continue
            result[(actor, counterparty)] = pair_vol.root / actor_total.root
        return result

    @staticmethod
    def reciprocity(
        pair_volumes: dict[tuple[MemberId, MemberId], V],
    ) -> dict[frozenset[MemberId], Decimal]:
        """Mutual-trade ratio for each member pair.

        1.0 — perfectly symmetric exchange (each party paid the other equally).
        0.0 — one-directional only (potential round-tripping pattern).
        Computed as ``min(A→B, B→A) / max(A→B, B→A)``.
        """
        seen: dict[frozenset[MemberId], Decimal] = {}
        for (actor, counter), volume in pair_volumes.items():
            if actor == counter:
                continue
            key = frozenset({actor, counter})
            if key in seen:
                continue
            reverse = pair_volumes.get((counter, actor), V.zero())
            forward = volume
            if forward.is_zero() and reverse.is_zero():
                seen[key] = Decimal(0)
                continue
            f, r = forward.root, reverse.root
            seen[key] = min(f, r) / max(f, r)
        return seen
