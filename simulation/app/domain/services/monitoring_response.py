"""Recommend enforcement actions when concentration metrics breach thresholds.

ARCHITECTURE §2.3 / §6 — the algorithm does *not* control prices.
When concentration is detected it can:

* lower the credit limit for the suspect cluster,
* boost the audit rate inside the affected category,
* pause compensatory emission (ε → 0) for transactions in the cluster,
* surface the issue to a community vote.

This service computes the *recommendations*. Whether and how the engine
applies them is the responsibility of the EnforceConcentrationResponse
periodic operation in Phase 4.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from app.domain.value_objects import CategoryId, MemberId

_HHI_MODERATE = Decimal(2500)
_HHI_HIGH = Decimal(4000)
_BILATERAL_THRESHOLD = Decimal("0.30")
_RECIPROCITY_SUSPICIOUS = Decimal("0.85")


class ResponseAction(StrEnum):
    INCREASE_AUDIT_RATE = "increase_audit_rate"
    LOWER_CREDIT_LIMIT = "lower_credit_limit"
    PAUSE_COMPENSATION = "pause_compensation"
    FLAG_PAIR_FOR_REVIEW = "flag_pair_for_review"
    RAISE_VOTE = "raise_vote"


@dataclass(frozen=True, slots=True)
class Recommendation:
    """One action targeted at a specific entity."""

    action: ResponseAction
    category: CategoryId | None = None
    member: MemberId | None = None
    pair: tuple[MemberId, MemberId] | None = None
    reason: str = ""


class MonitoringResponseService:
    """Translate concentration measurements into enforcement recommendations."""

    def evaluate(
        self,
        category_hhi: dict[CategoryId, Decimal],
        bilateral: dict[tuple[MemberId, MemberId], Decimal],
        reciprocity: dict[frozenset[MemberId], Decimal],
    ) -> list[Recommendation]:
        recommendations: list[Recommendation] = []
        recommendations.extend(self._from_hhi(category_hhi))
        recommendations.extend(self._from_bilateral(bilateral))
        recommendations.extend(self._from_reciprocity(reciprocity))
        return recommendations

    @staticmethod
    def _from_hhi(
        category_hhi: dict[CategoryId, Decimal],
    ) -> list[Recommendation]:
        out: list[Recommendation] = []
        for category, hhi in category_hhi.items():
            if hhi >= _HHI_HIGH:
                out.append(
                    Recommendation(
                        action=ResponseAction.RAISE_VOTE,
                        category=category,
                        reason=f"HHI={hhi:.0f} indicates monopolisation",
                    )
                )
                out.append(
                    Recommendation(
                        action=ResponseAction.PAUSE_COMPENSATION,
                        category=category,
                        reason="protect supply during single-provider dominance",
                    )
                )
            elif hhi >= _HHI_MODERATE:
                out.append(
                    Recommendation(
                        action=ResponseAction.INCREASE_AUDIT_RATE,
                        category=category,
                        reason=f"HHI={hhi:.0f} above moderate threshold",
                    )
                )
        return out

    @staticmethod
    def _from_bilateral(
        bilateral: dict[tuple[MemberId, MemberId], Decimal],
    ) -> list[Recommendation]:
        return [
            Recommendation(
                action=ResponseAction.LOWER_CREDIT_LIMIT,
                member=actor,
                reason=(
                    f"{share:.0%} of {actor}'s volume is with {counter} — "
                    "potential dependency or wash-trading"
                ),
            )
            for (actor, counter), share in bilateral.items()
            if share > _BILATERAL_THRESHOLD
        ]

    @staticmethod
    def _from_reciprocity(
        reciprocity: dict[frozenset[MemberId], Decimal],
    ) -> list[Recommendation]:
        out: list[Recommendation] = []
        for pair_set, score in reciprocity.items():
            if score < _RECIPROCITY_SUSPICIOUS:
                continue
            members = tuple(sorted(pair_set))
            if len(members) != 2:
                continue
            out.append(
                Recommendation(
                    action=ResponseAction.FLAG_PAIR_FOR_REVIEW,
                    pair=(members[0], members[1]),
                    reason=(f"reciprocity={score:.2f} suggests round-tripping"),
                )
            )
        return out
