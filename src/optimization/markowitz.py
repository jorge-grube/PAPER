"""
Markowitz minimum-variance portfolio with Ledoit-Wolf covariance shrinkage.

Design choices:
- Objective: minimum-variance (no expected-return estimation to avoid corner solutions).
- Covariance: sklearn LedoitWolf shrinkage (analytical, no cross-validation needed).
- Constraints: long-only, weights sum to 1, per-asset cap = max_weight.
- Solver: scipy.optimize.minimize with SLSQP (fast, handles linear constraints).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.covariance import LedoitWolf


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class MarkowitzConfig:
    max_weight: float = 0.25          # per-asset upper bound
    min_weight: float = 0.0           # long-only
    min_scenarios: int = 52           # minimum weekly obs to attempt optimization
    fallback_to_equal: bool = True    # if solver fails, return equal-weight


# ---------------------------------------------------------------------------
# Core solver
# ---------------------------------------------------------------------------

def solve_min_variance(
    returns: pd.DataFrame,
    config: MarkowitzConfig,
) -> tuple[np.ndarray, float]:
    """
    Solve min w' Σ w subject to:
      Σ w = 1,  0 ≤ w_i ≤ max_weight.

    Returns
    -------
    weights : np.ndarray of shape (n_assets,)
    portfolio_variance : float
    """
    n = returns.shape[1]

    # Ledoit-Wolf shrinkage covariance (annualised → weekly: no need, optimizer
    # cares about relative scale only, weekly cov is fine).
    clean = returns.dropna()
    if len(clean) < config.min_scenarios:
        raise ValueError(f"Too few clean obs: {len(clean)}")
    n = clean.shape[1]
    lw = LedoitWolf().fit(clean.values)
    cov = lw.covariance_           # (n x n)

    # Starting point: equal weight
    w0 = np.full(n, 1.0 / n)

    def portfolio_variance(w: np.ndarray) -> float:
        return float(w @ cov @ w)

    def portfolio_variance_grad(w: np.ndarray) -> np.ndarray:
        return 2.0 * cov @ w

    constraints = {"type": "eq", "fun": lambda w: w.sum() - 1.0}
    bounds = [(config.min_weight, config.max_weight)] * n

    result = minimize(
        portfolio_variance,
        w0,
        jac=portfolio_variance_grad,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"ftol": 1e-12, "maxiter": 1000},
    )

    if not result.success:
        if config.fallback_to_equal:
            w = w0.copy()
        else:
            raise RuntimeError(f"Markowitz solver failed: {result.message}")
    else:
        w = result.x
        # Clip numerical noise
        w = np.clip(w, 0.0, config.max_weight)
        w /= w.sum()

    return w, float(w @ cov @ w)


# ---------------------------------------------------------------------------
# Walk-forward backtest helper
# ---------------------------------------------------------------------------

def run_markowitz_backtest(
    returns: pd.DataFrame,
    config: MarkowitzConfig | None = None,
    rebalance_weeks: int = 4,
    min_history_weeks: int = 156,
) -> tuple[pd.Series, pd.DataFrame]:
    """
    Walk-forward minimum-variance Markowitz backtest.

    Parameters
    ----------
    returns : weekly simple-return DataFrame, assets as columns.
    config : MarkowitzConfig.
    rebalance_weeks : refit frequency (weeks).
    min_history_weeks : expanding-window burn-in (weeks).

    Returns
    -------
    portfolio_returns : pd.Series of weekly portfolio returns.
    weights_history   : pd.DataFrame, one row per rebalance date.
    """
    if config is None:
        config = MarkowitzConfig()

    n_obs, n_assets = returns.shape
    dates = returns.index
    weights = np.full(n_assets, 1.0 / n_assets)   # initial equal-weight

    port_rets: list[float] = []
    port_dates: list[pd.Timestamp] = []
    weights_rows: list[dict] = []

    rebalance_counter = 0

    for t in range(n_obs):
        # Rebalance if we have enough history and it's a rebalance week
        if t >= min_history_weeks and rebalance_counter == 0:
            hist = returns.iloc[:t]
            if hist.shape[0] >= config.min_scenarios:
                try:
                    weights, _ = solve_min_variance(hist, config)
                except Exception:
                    pass  # keep previous weights
            weights_rows.append({"date": dates[t], **dict(zip(returns.columns, weights))})

        if t >= min_history_weeks:
            rebalance_counter = (rebalance_counter + 1) % rebalance_weeks
            # Compute portfolio return for this period
            port_rets.append(float(returns.iloc[t].values @ weights))
            port_dates.append(dates[t])

    port_series = pd.Series(port_rets, index=pd.DatetimeIndex(port_dates), name="markowitz")
    weights_df = pd.DataFrame(weights_rows).set_index("date") if weights_rows else pd.DataFrame()
    return port_series, weights_df
