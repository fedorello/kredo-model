"""Per-event reputation deltas (β for accumulation, γ for burning).

The source document gives R as a *cumulative* logarithmic function of
counts (math §4.1):

    ΔR_total = β₁·ln(1+N_tx) + β₂·N_audits + β₃·ln(1+tenure/30)
             + β₄·N_disputes_resolved

In the discrete simulator, operations are applied event-by-event, so we
need *per-event* deltas. We use the per-event simplification documented
in ARCHITECTURE §16 (and used in math §4.1 at the operation level):

    actor   gets β₁ · confidence(τ) per confirmed transaction
    receiver gets β₁ · confidence(τ) · 0.3 per confirmed transaction

This loses the diminishing-returns property of the logarithmic form (a
member with 1000 transactions gets the same per-tx bump as one with 10),
but it is what the operations layer actually applies. If we want to
restore the log form later, we add a `cumulative_completed_transactions`
field to Member and switch to incremental log-deltas — the change is
local to this service.
"""

from __future__ import annotations

from decimal import Decimal

from app.domain.parameters import ClubParameters
from app.domain.value_objects import Confidence, R, V

_RECEIVER_FACTOR = Decimal("0.3")


class ReputationDeltaService:
    """Reputation increments and decrements for each event type."""

    def __init__(self, params: ClubParameters) -> None:
        self._params = params

    # ----- accumulation (β) ----------------------------------------------

    def for_actor_transaction(self, confidence: Confidence) -> R:
        """β₁ · confidence — earned by the executor of a confirmed transaction."""
        return R(self._params.beta_tx * confidence.root)

    def for_receiver_transaction(self, confidence: Confidence) -> R:
        """β₁ · confidence · 0.3 — earned by the receiver."""
        return R(self._params.beta_tx * confidence.root * _RECEIVER_FACTOR)

    def for_successful_audit(self) -> R:
        """β₂ — earned by an auditor who made a correct call."""
        return R(self._params.beta_audit)

    def for_tenure_day(self, tenure_days: int) -> R:
        """β₃ · (ln(1+T/30) − ln(T/30))   discrete daily increment.

        Equivalent to the doc's ``β₃·log(1+tenure/30)`` formula evaluated
        at consecutive days and differenced. Returns the delta for the
        single day going from ``tenure_days-1`` → ``tenure_days``.
        """
        if tenure_days <= 0:
            return R.zero()
        prev = (Decimal(1) + Decimal(tenure_days - 1) / 30).ln()
        curr = (Decimal(1) + Decimal(tenure_days) / 30).ln()
        return R(self._params.beta_tenure * (curr - prev))

    def for_dispute_resolved(self) -> R:
        """β₄ — earned by a member whose dispute resolution was correct."""
        return R(self._params.beta_dispute)

    # ----- burning (γ) ---------------------------------------------------

    def for_failed_audit(self) -> R:
        return R(self._params.gamma_failed_audit)

    def for_dispute_lost(self) -> R:
        return R(self._params.gamma_dispute_lost)

    def for_default(self, defaulted_principal: V) -> R:
        """γ₃ · principal — scaled by the size of the default."""
        if defaulted_principal.is_negative():
            raise ValueError("defaulted principal must be non-negative")
        return R(self._params.gamma_default_per_v * defaulted_principal.root)

    def for_proven_fraud(self) -> R:
        """γ₄ — wipes years of accumulated reputation."""
        return R(self._params.gamma_fraud)
