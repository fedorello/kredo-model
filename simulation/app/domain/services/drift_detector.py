"""Collusive price-drift detector (Kredo v2 — improvements/05).

The auto-score anchors trust to a category's *rolling* price distribution, so
a colluding ring can inch declared prices upward — each step within |z| ≤ 1 —
and drag the reference mean μ_c along without ever tripping review. That is
covert emission (inflated N → inflated credit → unbacked V).

This service adds a low-frequency guard:

* **Two-window rule.** Compare a short window (default 90 d) against a long
  one (default 365 d); flag when ``|μ_short − μ_long| > κ·σ_long``. A linear
  drift of ``v`` per day makes a window of length T lag the current level by
  ``vT/2``, so the two means separate by ``v·(T_long − T_short)/2``. The
  detector therefore bounds the *sustainable undetected* drift to

      v* = κ·σ_long / ((T_long − T_short)/2)          ( = κσ/137.5 at 365/90 )

  — doubling a price then takes years, which is economically pointless.
* **CUSUM.** A cumulative-sum chart catches slow drift *and* small step
  series that a windowed mean smooths over.
* **Robust anchors.** μ via median and σ via MAD, so an attacker's probe
  trades cannot lever the anchor.
"""

from __future__ import annotations

from decimal import Decimal
from collections.abc import Sequence

_MAD_TO_SIGMA = Decimal("1.4826")  # MAD → σ for a normal distribution


def median(values: Sequence[Decimal]) -> Decimal:
    """Median of a non-empty sequence."""
    if not values:
        raise ValueError("median of empty sequence")
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2 == 1:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / Decimal(2)


def mad_sigma(values: Sequence[Decimal]) -> Decimal:
    """Robust σ estimate: ``1.4826 · median(|x − median(x)|)``."""
    if not values:
        raise ValueError("mad of empty sequence")
    med = median(values)
    deviations = [abs(x - med) for x in values]
    return _MAD_TO_SIGMA * median(deviations)


def detrended_sigma(values: Sequence[Decimal]) -> Decimal:
    """Inherent noise σ, robust to a linear drift.

    A drifting window's raw MAD conflates drift with noise and would mask the
    very drift we hunt. First-differencing removes the linear trend: for
    ``x_t = μ + v·t + ε_t`` the differences are ``v + (ε_t − ε_{t−1})``, whose
    MAD reflects only the noise. Dividing by ``√2`` (the variance inflation of
    differencing) recovers σ_ε.
    """
    if len(values) < 2:
        raise ValueError("need at least two points to detrend")
    diffs = [values[i] - values[i - 1] for i in range(1, len(values))]
    two = Decimal(2)
    return mad_sigma(diffs) / two.sqrt()


class DriftDetectorService:
    """Two-window + CUSUM detector for collusive price drift."""

    def __init__(
        self,
        *,
        short_window_days: int = 90,
        long_window_days: int = 365,
        kappa: Decimal = Decimal("1.5"),
    ) -> None:
        if not 0 < short_window_days < long_window_days:
            raise ValueError("require 0 < short_window < long_window")
        if kappa <= 0:
            raise ValueError("kappa must be positive")
        self._short = short_window_days
        self._long = long_window_days
        self._kappa = kappa

    @property
    def _lag_gap(self) -> Decimal:
        """``(T_long − T_short)/2`` — the mean-lag separation per unit drift."""
        return Decimal(self._long - self._short) / Decimal(2)

    def two_window_flag(
        self,
        short_prices: Sequence[Decimal],
        long_prices: Sequence[Decimal],
    ) -> bool:
        """Flag when ``|median_short − median_long| > κ·σ`` with a detrended σ.

        σ is estimated by :func:`detrended_sigma` on the long window so a large
        drift cannot inflate the threshold and hide itself.
        """
        mu_short = median(short_prices)
        mu_long = median(long_prices)
        sigma = detrended_sigma(long_prices)
        return abs(mu_short - mu_long) > self._kappa * sigma

    def max_undetected_drift_per_day(self, sigma_long: Decimal) -> Decimal:
        """``v* = κ·σ_long / ((T_long − T_short)/2)`` — the covert speed limit.

        Once both windows are full, a linear drift ``v`` holds the two means a
        constant ``v·lag_gap`` apart, so any drift above ``v*`` is flagged and
        any drift at or below it never is. The guarantee is thus a hard cap on
        undetected drift speed, not a race against the clock.
        """
        return self._kappa * sigma_long / self._lag_gap

    def steady_state_separation(self, drift_per_day: Decimal) -> Decimal:
        """``v · (T_long − T_short)/2`` — the offset the two means settle to."""
        return drift_per_day * self._lag_gap

    @staticmethod
    def days_to_double(drift_per_day: Decimal, base_price: Decimal) -> Decimal:
        """Days for a covert drift ``v`` to double the category price.

        This is the economic-pointlessness metric for the undetected regime:
        at or below ``v*`` the drift is invisible, but doubling a price takes
        ``base_price / v`` days — years — while the ring stays exposed to
        concentration and reciprocity monitoring the whole time.
        """
        if drift_per_day <= 0:
            raise ValueError("drift_per_day must be positive")
        return base_price / drift_per_day

    def cusum_flag(
        self,
        prices: Sequence[Decimal],
        anchor: Decimal,
        slack: Decimal,
        threshold: Decimal,
    ) -> bool:
        """Upper-CUSUM: flag if ``S_t = max(0, S_{t−1} + (x−anchor−k))`` exceeds h."""
        s = Decimal(0)
        for x in prices:
            s = max(Decimal(0), s + (x - anchor - slack))
            if s > threshold:
                return True
        return False
