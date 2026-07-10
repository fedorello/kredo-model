"""Fraud-deterrence economics — Theorems 4–5 as domain code (v2, improvements/04).

The paper proves that a wash-trading fraud extracting ``W`` succeeds only by
surviving both the per-transaction audit and the conversion lock-up, so its
survival probability decays exponentially in ``W`` while the prize grows only
linearly:

    β    = ln(1/(1−a)) / N̄                      (per-V audit hazard)
    q(W) = (1−a)^{W/N̄} · (1−p)^{τ_lock}          (reach conversion undetected)
    E[π] ≤ q(W)·W − (1−q(W))·Λ                   (Theorem 4)
    g(W) = c·e^{−βW}(W+Λ) − Λ,  c = (1−p)^{τ_lock} (Theorem 5, tight bound)

Deterrence (Theorem 5): every adaptive strategy is loss-making iff
``max_W g ≤ 0``. The stake condition ``Λ ≥ 1/β`` is sufficient. The v2
dynamic lock-up ``τ_lock(W) = τ0 + w·W`` steepens the decay to
``β' = β + w·ln(1/(1−p))``, meeting the threshold at the *default* stake
without raising Λ. This service is the single home for those formulas; the
``fraud_deterrence`` experiment reads its numbers.
"""

from __future__ import annotations

from decimal import Decimal


def _ln(x: Decimal) -> Decimal:
    return x.ln()


class FraudDeterrenceService:
    """Closed-form fraud-profit bounds and deterrence thresholds."""

    def __init__(
        self,
        *,
        mean_tx_size: Decimal,
        audit_rate: Decimal,
        lockup_days: int,
        detection_per_day: Decimal,
        lockup_per_v: Decimal = Decimal("0"),
    ) -> None:
        if not (0 < audit_rate < 1):
            raise ValueError("audit_rate must lie in (0, 1)")
        if not (0 <= detection_per_day < 1):
            raise ValueError("detection_per_day must lie in [0, 1)")
        if mean_tx_size <= 0:
            raise ValueError("mean_tx_size must be positive")
        self._n_bar = mean_tx_size
        self._a = audit_rate
        self._tau0 = lockup_days
        self._p = detection_per_day
        self._w = lockup_per_v

    @property
    def beta(self) -> Decimal:
        """Per-V audit hazard ``β = ln(1/(1−a)) / N̄``."""
        return _ln(Decimal(1) / (Decimal(1) - self._a)) / self._n_bar

    @property
    def _p_prime(self) -> Decimal:
        """``p' = ln(1/(1−p))`` — the per-day lock-up hazard."""
        if self._p == 0:
            return Decimal(0)
        return _ln(Decimal(1) / (Decimal(1) - self._p))

    @property
    def effective_beta(self) -> Decimal:
        """``β' = β + w·p'`` — the decay rate under the dynamic lock-up."""
        return self.beta + self._w * self._p_prime

    def _lockup_survival_constant(self) -> Decimal:
        """``c = (1−p)^{τ0}`` — survival through the base lock-up."""
        if self._p == 0:
            return Decimal(1)
        return (Decimal(self._tau0) * _ln(Decimal(1) - self._p)).exp()

    def survival_probability(self, theft: Decimal) -> Decimal:
        """``q(W) = (1−p)^{τ0} · e^{−β'W}`` — reach conversion undetected."""
        return self._lockup_survival_constant() * (-self.effective_beta * theft).exp()

    def expected_profit_bound(self, theft: Decimal, stake: Decimal) -> Decimal:
        """Theorem 4 bound ``q(W)·W − (1−q(W))·Λ``."""
        q = self.survival_probability(theft)
        return q * theft - (Decimal(1) - q) * stake

    def profit_bound(self, theft: Decimal, stake: Decimal) -> Decimal:
        """Theorem 5 tight per-cluster bound ``g(W) = c·e^{−β'W}(W+Λ) − Λ``."""
        c = self._lockup_survival_constant()
        return c * (-self.effective_beta * theft).exp() * (theft + stake) - stake

    def deterrence_threshold_stake(self) -> Decimal:
        """``1/β'`` — the stake making the optimal adaptive fraud loss-making."""
        return Decimal(1) / self.effective_beta

    def optimal_theft(self, stake: Decimal) -> Decimal:
        """``W† = 1/β' − Λ`` — the fraud's profit-maximising size (may be ≤ 0)."""
        return Decimal(1) / self.effective_beta - stake

    def max_profit(self, stake: Decimal) -> Decimal:
        """``max_W g(W)`` under stake ``Λ`` — ≤ 0 means fully deterred."""
        w_star = self.optimal_theft(stake)
        if w_star <= 0:
            # g is decreasing on [0, ∞); maximum is g(0) = (c−1)·Λ ≤ 0.
            return self._lockup_survival_constant() * stake - stake
        return self.profit_bound(w_star, stake)

    def is_deterred(self, stake: Decimal) -> bool:
        """True iff the optimal adaptive fraud is non-positive (Theorem 5)."""
        return self.max_profit(stake) <= 0
