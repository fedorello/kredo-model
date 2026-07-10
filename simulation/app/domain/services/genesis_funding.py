"""Compute Genesis Pool inflows according to the configured policy.

ARCHITECTURE §16.1 documents the discrepancy between the v2 design and
the math spec:

    math_spec:  inflow_V = 0.15 · ExtRev_quarter   (in V terms)
                + 0.5 · fines_quarter              (already in V)

    v2_doc:     inflow_V = 0.5 · investment_year1 (in V terms)
                + fines + share of dividends

Both the math spec and v2 mix V-denominated and USDC-denominated
inflows. The simulator threads price through this conversion: an
``ExtRev_quarter_in_v`` argument is the operations layer's
responsibility to compute (USDC amount × current Price).

This service does pure arithmetic — it accepts already-converted
V-amounts and applies the configured shares.
"""

from __future__ import annotations

from app.domain.parameters import ClubParameters
from app.domain.value_objects import V


class GenesisFundingService:
    """Compute Genesis Pool inflows for the current period."""

    def __init__(self, params: ClubParameters) -> None:
        self._params = params

    def inflow(
        self,
        ext_rev_quarter_in_v: V,
        fines_quarter: V,
        investment_year1_in_v: V | None = None,
    ) -> V:
        """Return the total V to deposit into the Genesis Pool this period.

        Args:
            ext_rev_quarter_in_v: external revenue this quarter, converted
                to V at the prevailing price.
            fines_quarter: total fines collected this quarter, in V.
            investment_year1_in_v: only used by the ``v2_doc`` strategy;
                investment inflows during the club's first year, in V.
        """
        if ext_rev_quarter_in_v.is_negative() or fines_quarter.is_negative():
            raise ValueError("inflow components must be non-negative")
        if investment_year1_in_v is not None and investment_year1_in_v.is_negative():
            raise ValueError("inflow components must be non-negative")

        policy = self._params.genesis_funding
        if policy.strategy == "math_spec":
            return (
                ext_rev_quarter_in_v * policy.from_ext_rev_share
                + fines_quarter * policy.from_fines_share
            )
        # v2_doc
        invest = investment_year1_in_v or V.zero()
        return invest * policy.from_investment_year1_share + fines_quarter * policy.from_fines_share
