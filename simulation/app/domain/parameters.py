"""Λ — system parameters configurable per simulation run.

Defaults reproduce the values from the Club design document. Every
parameter is meant to be sweepable in a simulation; changing one is
equivalent to defining a new scenario. Validation here is structural
(types, bounds, sums-to-1 constraints) — semantic relationships
between parameters (e.g., "given this ε, this δ regime is unstable")
are checked by the simulation itself.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.value_objects import CategoryId, Confidence, V

_TOLERANCE = Decimal("0.0001")


class CategoryParams(BaseModel):
    """Price distribution for one service category — drives auto-score."""

    model_config = ConfigDict(frozen=True)

    mu: Decimal
    """Expected price (V) within this category."""
    sigma: Decimal
    """Standard deviation of prices."""

    @field_validator("mu", "sigma")
    @classmethod
    def _positive(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError(f"category mu/sigma must be > 0, got {value}")
        return value


class GenesisFundingPolicy(BaseModel):
    """How Genesis Pool is replenished.

    Architecture §16.1 documents the discrepancy between v2 and the math
    spec; both strategies are exposed here.
    """

    model_config = ConfigDict(frozen=True)

    strategy: str = "math_spec"
    """One of ``"math_spec"`` (default) or ``"v2_doc"``."""
    from_ext_rev_share: Decimal = Decimal("0.15")
    """Math spec: ``0.15 × Quarterly_External_Revenue``."""
    from_fines_share: Decimal = Decimal("0.5")
    """Math spec: ``Φ × Stream_of_Fines`` with Φ ≈ 0.5."""
    from_investment_year1_share: Decimal = Decimal("0.5")
    """v2: 50 % of investment inflows during the first year."""

    @field_validator("strategy")
    @classmethod
    def _valid_strategy(cls, value: str) -> str:
        if value not in {"math_spec", "v2_doc"}:
            raise ValueError(f"strategy must be 'math_spec' or 'v2_doc', got {value!r}")
        return value

    @field_validator("from_ext_rev_share", "from_fines_share", "from_investment_year1_share")
    @classmethod
    def _share_in_range(cls, value: Decimal) -> Decimal:
        if value < 0 or value > 1:
            raise ValueError(f"share must lie in [0, 1], got {value}")
        return value


def _default_categories() -> dict[CategoryId, CategoryParams]:
    """Mu=50 V, sigma=15 V is a neutral starting distribution.

    For real scenarios these are tuned per category — copywriting has
    smaller mu than dev consulting, etc.
    """
    return {
        category: CategoryParams(mu=Decimal("50"), sigma=Decimal("15")) for category in CategoryId
    }


class ClubParameters(BaseModel):
    """Full set of tunable system parameters."""

    model_config = ConfigDict(frozen=True)

    # ---- credit limit ----------------------------------------------------
    L0: V = Field(default_factory=lambda: V(100))
    """Base credit limit for r = 0."""
    alpha: Decimal = Decimal("0.5")
    """Credit-limit growth coefficient: L(r) = L0·(1 + α·ln(1+r))."""

    # ---- welcome grant ---------------------------------------------------
    g0: V = Field(default_factory=lambda: V(100))
    """Target welcome grant; actual is clamped by Genesis Pool size."""

    # ---- dynamic compensation ε -----------------------------------------
    K_target: Decimal = Decimal("1.5")
    """Target Supply / NetVerifiedValue ratio (ARCHITECTURE §6.4)."""
    delta_target: Decimal = Decimal("0.05")
    """Expected default rate."""
    kappa: Decimal = Decimal("2.0")
    """Sensitivity of ε to deviations from delta_target."""
    epsilon_max: Decimal = Decimal("0.95")
    """Upper bound on ε regardless of formula output."""

    # ---- confidence ------------------------------------------------------
    theta_min: Confidence = Field(default_factory=lambda: Confidence("0.6"))
    """Minimum confidence for a transaction to be approved (Invariant I2)."""

    # ---- timing ----------------------------------------------------------
    tau_credit_days: int = 90
    """Days before an unrepaid loan defaults."""
    tau_lock_days: int = 60
    """Days new members cannot Convert."""
    snapshot_every: int = 30
    """Tick interval for full state snapshots (architecture §15.2)."""

    # ---- pricing ---------------------------------------------------------
    pe_multiplier: Decimal = Decimal("12")
    """μ in P = (F + μ·ExtRev)/S."""
    rho_min: Decimal = Decimal("0.3")
    """Bank-run threshold: below this F/(P·S), Convert applies a discount."""

    # ---- audit -----------------------------------------------------------
    audit_rate: Decimal = Decimal("0.03")
    """Fraction of transactions sampled for stochastic audit."""

    # ---- distribution smoothing -----------------------------------------
    xi: V = Field(default_factory=lambda: V(1))
    """Smoothing constant in escrow distribution shares."""

    # ---- reputation accumulation (β) ------------------------------------
    beta_tx: Decimal = Decimal("0.5")
    beta_audit: Decimal = Decimal("1.0")
    beta_tenure: Decimal = Decimal("0.3")
    beta_dispute: Decimal = Decimal("2.0")

    # ---- reputation burning (γ) -----------------------------------------
    gamma_failed_audit: Decimal = Decimal("2.0")
    gamma_dispute_lost: Decimal = Decimal("5.0")
    gamma_default_per_v: Decimal = Decimal("0.1")
    """R burned per 1 V of defaulted principal."""
    gamma_fraud: Decimal = Decimal("100.0")

    # ---- quarterly profit distribution (50 / 30 / 15 / 5) ---------------
    quarterly_to_fund: Decimal = Decimal("0.50")
    quarterly_to_dividend: Decimal = Decimal("0.30")
    quarterly_to_genesis: Decimal = Decimal("0.15")
    quarterly_to_ops: Decimal = Decimal("0.05")

    # ---- activity multiplier --------------------------------------------
    activity_min: Decimal = Decimal("0.3")
    activity_max: Decimal = Decimal("1.7")

    # ---- categories ------------------------------------------------------
    categories: dict[CategoryId, CategoryParams] = Field(default_factory=_default_categories)

    # ---- genesis funding -------------------------------------------------
    genesis_funding: GenesisFundingPolicy = Field(default_factory=GenesisFundingPolicy)

    # ---- validation ------------------------------------------------------

    @field_validator("alpha", "kappa", "pe_multiplier")
    @classmethod
    def _positive(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError(f"must be positive, got {value}")
        return value

    @field_validator("delta_target", "audit_rate", "rho_min", "epsilon_max")
    @classmethod
    def _share(cls, value: Decimal) -> Decimal:
        if value < 0 or value > 1:
            raise ValueError(f"share must lie in [0, 1], got {value}")
        return value

    @field_validator("K_target")
    @classmethod
    def _k_at_least_one(cls, value: Decimal) -> Decimal:
        if value < 1:
            raise ValueError(f"K_target must be >= 1, got {value}")
        return value

    @field_validator("tau_credit_days", "tau_lock_days", "snapshot_every")
    @classmethod
    def _positive_int(cls, value: int) -> int:
        if value <= 0:
            raise ValueError(f"days must be > 0, got {value}")
        return value

    @model_validator(mode="after")
    def _consistency(self) -> ClubParameters:
        total = (
            self.quarterly_to_fund
            + self.quarterly_to_dividend
            + self.quarterly_to_genesis
            + self.quarterly_to_ops
        )
        if abs(total - Decimal("1")) > _TOLERANCE:
            raise ValueError(f"quarterly distribution shares must sum to 1, got {total}")
        if self.activity_min < 0 or self.activity_max <= self.activity_min:
            raise ValueError(f"activity bounds invalid: [{self.activity_min}, {self.activity_max}]")
        if not self.categories:
            raise ValueError("at least one category must be configured")
        return self
