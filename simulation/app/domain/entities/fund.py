"""Liquidity Fund — pool of USDC backing the V/USDC peg.

Bounded below by zero (USDC is non-negative by construction).
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict

from app.domain.value_objects import USDC


class LiquidityFund(BaseModel):
    """USDC reserves held by the Club for Convert / Invest / dividends."""

    model_config = ConfigDict(frozen=True)

    balance: USDC

    @classmethod
    def empty(cls) -> Self:
        return cls(balance=USDC.zero())
