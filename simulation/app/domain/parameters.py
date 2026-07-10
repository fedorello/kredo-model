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

    # ---- v2: fraud deterrence — dynamic lock-up & audit escalation ------
    lockup_per_v: Decimal = Decimal("0")
    """w — extra conversion lock-up days per 1 V of a fresh conversion:
    ``τ_lock(W) = τ0 + w·W`` (improvements/04). ``0`` (default) keeps the
    constant lock-up, so legacy runs are unchanged. With ``w > 0``, large
    conversions of freshly acquired balance vest in tranches, so a fraud
    cluster must hold an unbacked position longer — the survival probability
    decays as ``e^{−β'W}`` with ``β' = β + w·ln(1/(1−p))``, pushing even the
    optimal adaptive fraud below zero at the default stake."""
    audit_rate_flagged: Decimal = Decimal("0.30")
    """Audit rate applied to a cluster flagged by concentration monitoring.
    At 0.30, ``1/β_flag = N̄/ln(1/(1−0.30)) ≈ 140 V < Λ`` — the deterrence
    threshold is met outright once a cluster is flagged (improvements/04)."""

    # ---- v2: revenue-backed emission (currency board) -------------------
    emission_budget_share: Decimal = Decimal("0")
    """η — share of external revenue that funds new credit emission.

    Kredo v2, improvements/01. When 0 (default) the feature is OFF and
    emission is unconstrained — every legacy scenario behaves exactly as
    before. When η > 0, each unit of external revenue adds
    ``η · amount / P_target`` V to a rolling emission budget; a credit
    emission that would exceed the remaining budget is refused. This makes
    the money supply endogenous to realised earnings: no sales → no fresh
    budget → the falling regime degrades into a *slowdown* (price holds
    near ``λ_inv / e``) instead of a collapse. The survival analysis
    requires ``η ≤ s`` where ``s = quarterly_to_fund`` is the retention
    share (see improvements/01-retention-channel.md)."""
    emission_price_target: V = Field(default_factory=lambda: V(1))
    """P_target — reference price converting revenue (USDC) into V budget."""

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

    # ---- v2: reputation decay & Sybil defense (improvements/03) ----------
    reputation_half_life_days: int | None = None
    """T½ for inactivity decay: r(t) = r₀·2^(−Δt_inactive/T½).

    ``None`` (default) disables decay — every legacy run is bit-identical.
    Set to 180 for v2. Forces a Sybil fleet to sustain genuine activity on
    every account or watch its reputation (and votes) melt away."""
    reputation_decay_grace_days: int = 30
    """Inactivity tolerated before decay starts (illness, holiday)."""
    vote_diversity_floor: Decimal = Decimal("0.2")
    """d_min in the diversity-weighted vote √R·D, D = max(d_min, 1 − HHI).

    A member whose trade is concentrated on few counterparties (a wash
    cluster) has HHI → 1, so D → d_min: its votes are scaled down to 20 %.
    Honest members trading broadly keep D ≈ 1."""

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

    @field_validator("lockup_per_v")
    @classmethod
    def _non_negative_decimal(cls, value: Decimal) -> Decimal:
        if value < 0:
            raise ValueError(f"lockup_per_v must be >= 0, got {value}")
        return value

    @field_validator(
        "delta_target", "audit_rate", "rho_min", "epsilon_max", "emission_budget_share",
        "audit_rate_flagged",
    )
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

    @field_validator("reputation_half_life_days")
    @classmethod
    def _positive_or_none(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError(f"reputation_half_life_days must be > 0 or None, got {value}")
        return value

    @field_validator("reputation_decay_grace_days")
    @classmethod
    def _non_negative_int(cls, value: int) -> int:
        if value < 0:
            raise ValueError(f"grace days must be >= 0, got {value}")
        return value

    @field_validator("vote_diversity_floor")
    @classmethod
    def _floor_in_unit(cls, value: Decimal) -> Decimal:
        if value < 0 or value > 1:
            raise ValueError(f"vote_diversity_floor must lie in [0, 1], got {value}")
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
        # v2 currency board: emission cannot outrun retention (η ≤ s).
        if self.emission_budget_share > 0:
            if self.emission_budget_share > self.quarterly_to_fund:
                raise ValueError(
                    f"emission_budget_share (η={self.emission_budget_share}) must not exceed "
                    f"the retention share s=quarterly_to_fund ({self.quarterly_to_fund})"
                )
            if not self.emission_price_target.is_positive():
                raise ValueError("emission_price_target must be positive when η > 0")
        return self
