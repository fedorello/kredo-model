"""Confidence aggregator.

Math §3.2:

    confidence(τ) = w_a·s_a + w_r·s_r + w_x·s_x

with the weight set selected by which checks were activated:

    | Checks                  | w_a | w_r | w_x |
    |-------------------------|-----|-----|-----|
    | auto only               | 1.0 | 0   | 0   |
    | auto + review           | 0.3 | 0.7 | 0   |
    | auto + review + audit   | 0.2 | 0.4 | 0.4 |

Using the median of reviewer votes (math §3.2) is the responsibility of
the caller — this calculator takes a single ``review_score`` already
aggregated.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.domain.value_objects import Confidence


@dataclass(frozen=True, slots=True)
class ConfidenceWeights:
    """Weights for the three confidence components."""

    auto: Decimal
    review: Decimal
    audit: Decimal

    @classmethod
    def auto_only(cls) -> ConfidenceWeights:
        return cls(Decimal(1), Decimal(0), Decimal(0))

    @classmethod
    def auto_plus_review(cls) -> ConfidenceWeights:
        return cls(Decimal("0.3"), Decimal("0.7"), Decimal(0))

    @classmethod
    def all_three(cls) -> ConfidenceWeights:
        return cls(Decimal("0.2"), Decimal("0.4"), Decimal("0.4"))


class ConfidenceCalculator:
    """Aggregate auto-score, review-score, and audit-score into a single confidence."""

    def compute(
        self,
        auto_score: Confidence,
        review_score: Confidence | None = None,
        audit_score: Confidence | None = None,
    ) -> Confidence:
        weights = self._select_weights(review_score, audit_score)
        total = (
            weights.auto * auto_score.root
            + weights.review * (review_score.root if review_score else Decimal(0))
            + weights.audit * (audit_score.root if audit_score else Decimal(0))
        )
        return Confidence(total)

    @staticmethod
    def _select_weights(review: Confidence | None, audit: Confidence | None) -> ConfidenceWeights:
        if audit is not None and review is not None:
            return ConfidenceWeights.all_three()
        if review is not None:
            return ConfidenceWeights.auto_plus_review()
        return ConfidenceWeights.auto_only()
