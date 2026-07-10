"""V/USDC price formula and bank-run discount.

Math §5.1, §7.1, §7.3:

    P(t)   = (F + μ · ExtRev) / S            (Invariant I5)
    ρ(t)   = F / (P · S)
    P_disc = P · min(1, ρ / ρ*)              (when ρ < ρ*)

Two key theorems are checked numerically by the tests:
1. Convert and Invest are price-neutral (P_{t+1} = P_t).
2. Emission lowers price proportionally to ΔS.
"""

from __future__ import annotations

from decimal import Decimal

from app.domain.parameters import ClubParameters
from app.domain.value_objects import USDC, Price, V


class PricingService:
    """V/USDC price plus bank-run protection logic."""

    def __init__(self, params: ClubParameters) -> None:
        self._params = params

    def price(self, fund: USDC, ext_rev_annualized: USDC, supply: V) -> Price:
        """Fundamental price ``P = (F + μ·ExtRev) / S``.

        Returns ``Price.zero()`` when supply is zero (degenerate state at
        bootstrap, before any V exists).
        """
        if supply.is_zero():
            return Price.zero()
        if supply.is_negative():
            raise ValueError(f"supply must be non-negative, got {supply}")
        numerator = fund.root + self._params.pe_multiplier * ext_rev_annualized.root
        return Price(numerator / supply.root)

    def coverage_ratio(self, fund: USDC, supply: V, price: Price) -> Decimal:
        """ρ = F / (P · S). Falls in [0, 1] for healthy markets.

        Returns 0 when the denominator is zero (no V or zero price).
        """
        if supply.is_zero() or price.root == 0:
            return Decimal(0)
        return fund.root / (price.root * supply.root)

    def discount_factor(self, coverage: Decimal) -> Decimal:
        """Multiplier applied to the price during a bank-run protection event.

        At ρ ≥ ρ*, factor is 1 (no discount). At ρ → 0, factor → 0.
        """
        if coverage < 0:
            raise ValueError(f"coverage must be non-negative, got {coverage}")
        rho_star = self._params.rho_min
        if rho_star == 0:
            return Decimal(1)
        return min(Decimal(1), coverage / rho_star)

    def discounted_price(self, fund: USDC, ext_rev_annualized: USDC, supply: V) -> Price:
        """Effective conversion price after applying any bank-run discount."""
        base = self.price(fund, ext_rev_annualized, supply)
        coverage = self.coverage_ratio(fund, supply, base)
        return Price(base.root * self.discount_factor(coverage))
