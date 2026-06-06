"""
Regime-aware CVaR portfolio optimisation.

Implements the Rockafellar-Uryasev (2000) linear-programme formulation of
Conditional Value-at-Risk minimisation:

    min_{w, zeta, z}   zeta + 1/((1-alpha)*T) * sum(z_t)

    s.t.   z_t  >= -w' r_t  -  zeta    for all t  (loss exceedance)
           z_t  >= 0                    for all t
           sum(w_i) = 1                            (fully invested)
           w_i  >= 0                    for all i  (long-only)
           w_i  <= max_weight           for all i  (concentration cap)

Variables: w  (n_assets), zeta (scalar), z (T auxiliaries)
Total: n + 1 + T — tractable via scipy.optimize.linprog (HiGHS backend).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Sequence

import numpy as np
import pandas as pd
from scipy.optimize import linprog

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class CVaRConfig:
    alpha: float = 0.95          # CVaR confidence level
    max_weight: float = 0.25     # max allocation per asset (canonical: 25% per asset)
    min_weight: float = 0.0      # min allocation per asset (0 = long-only)
    min_scenarios: int = 30      # minimum historical scenarios per solve
    min_mu: float | None = None  # optional: minimum expected return constraint (weekly)
    linprog_method: str = "highs"


# ---------------------------------------------------------------------------
# Core solver
# ---------------------------------------------------------------------------

def solve_cvar(
    scenarios: np.ndarray,          # shape (T, n) — weekly returns, losses = negative
    config: CVaRConfig | None = None,
) -> dict:
    """
    Solve min-CVaR(alpha) LP for a single scenario matrix.

    Parameters
    ----------
    scenarios : ndarray (T, n)
        Matrix of weekly asset returns.  Each row is one historical week.
    config : CVaRConfig
        Solver settings.

    Returns
    -------
    dict with keys:
        weights      ndarray (n,) — optimal weights
        cvar         float        — optimal CVaR value (as a loss, positive = bad)
        var          float        — Value-at-Risk (= zeta)
        success      bool
        message      str
    """
    if config is None:
        config = CVaRConfig()

    T, n = scenarios.shape
    alpha = config.alpha

    if T < config.min_scenarios:
        return {"weights": None, "cvar": np.nan, "var": np.nan,
                "success": False, "message": f"Too few scenarios: {T} < {config.min_scenarios}"}

    # -----------------------------------------------------------------------
    # Decision variables layout: [w_0,...,w_{n-1}, zeta, z_0,...,z_{T-1}]
    # Total: n + 1 + T
    # -----------------------------------------------------------------------
    n_vars = n + 1 + T

    # Objective: min  0·w  +  1·zeta  +  1/((1-α)T) · z
    c = np.zeros(n_vars)
    c[n] = 1.0                                # zeta coefficient
    c[n + 1:] = 1.0 / ((1.0 - alpha) * T)   # z coefficients

    # Inequality constraints:  A_ub @ x <= b_ub
    # (1)  -w' r_t  - zeta  - z_t  <=  0   for t = 0..T-1
    #      => loss_t - zeta - z_t <= 0  where loss_t = -r_t' w
    #      => -r_t' w  - zeta  - z_t  <=  0
    # (2)  -z_t  <=  0                       for t = 0..T-1  (z_t >= 0)
    n_ineq = 2 * T
    A_ub = np.zeros((n_ineq, n_vars))
    b_ub = np.zeros(n_ineq)

    for t in range(T):
        # Constraint (1): loss exceedance
        A_ub[t, :n] = -scenarios[t, :]   # -r_t' w
        A_ub[t, n] = -1.0                # -zeta
        A_ub[t, n + 1 + t] = -1.0       # -z_t
        # b_ub[t] = 0  (already)

        # Constraint (2): z_t >= 0  =>  -z_t <= 0
        A_ub[T + t, n + 1 + t] = -1.0

    # Equality constraints: sum(w) = 1
    A_eq = np.zeros((1, n_vars))
    A_eq[0, :n] = 1.0
    b_eq = np.array([1.0])

    # Optional: minimum expected return  w' mu >= min_mu  =>  -w' mu <= -min_mu
    if config.min_mu is not None:
        mu = scenarios.mean(axis=0)
        row = np.zeros((1, n_vars))
        row[0, :n] = -mu
        A_ub = np.vstack([A_ub, row])
        b_ub = np.append(b_ub, -config.min_mu)

    # Bounds
    bounds = (
        [(config.min_weight, config.max_weight)] * n +  # w_i
        [(None, None)] +                                  # zeta (unbounded)
        [(0.0, None)] * T                                 # z_t >= 0
    )

    result = linprog(
        c,
        A_ub=A_ub, b_ub=b_ub,
        A_eq=A_eq, b_eq=b_eq,
        bounds=bounds,
        method=config.linprog_method,
        options={"disp": False},
    )

    if not result.success:
        return {"weights": None, "cvar": np.nan, "var": np.nan,
                "success": False, "message": result.message}

    w = result.x[:n]
    zeta = result.x[n]
    z = result.x[n + 1:]
    cvar = zeta + np.mean(z) / (1.0 - alpha)

    return {
        "weights": w,
        "cvar": cvar,
        "var": zeta,
        "success": True,
        "message": "OK",
    }


# ---------------------------------------------------------------------------
# Regime-conditional solver
# ---------------------------------------------------------------------------

def regime_cvar_weights(
    returns: pd.DataFrame,
    regime_series: pd.Series,
    current_regime: int,
    config: CVaRConfig | None = None,
) -> dict:
    """
    Given all historical returns and the current regime, return CVaR-optimal
    weights using only the returns observed in the current regime.

    Parameters
    ----------
    returns : DataFrame (T_hist, n) — full historical weekly returns to date
    regime_series : Series (T_hist,) — integer regime label per week
    current_regime : int — the regime we are currently in
    config : CVaRConfig

    Returns
    -------
    dict from solve_cvar() plus 'n_scenarios' key.
    """
    if config is None:
        config = CVaRConfig()

    mask = regime_series == current_regime
    scenarios = returns.loc[mask].dropna().values

    result = solve_cvar(scenarios, config)
    result["n_scenarios"] = len(scenarios)
    result["regime"] = current_regime
    return result


# ---------------------------------------------------------------------------
# Unconditional CVaR (regime-blind benchmark)
# ---------------------------------------------------------------------------

def unconditional_cvar_weights(
    returns: pd.DataFrame,
    config: CVaRConfig | None = None,
) -> dict:
    """CVaR-optimal weights using all available historical returns (no regime)."""
    if config is None:
        config = CVaRConfig()
    scenarios = returns.dropna().values
    result = solve_cvar(scenarios, config)
    result["n_scenarios"] = len(scenarios)
    result["regime"] = -1
    return result


# ---------------------------------------------------------------------------
# Full backtest
# ---------------------------------------------------------------------------

def run_cvar_backtest(
    returns: pd.DataFrame,
    regime_labels: pd.Series,
    config: CVaRConfig | None = None,
    cash_col: str = "EURIBOR_3M",
    min_history_weeks: int = 156,   # ~3 years burn-in before first allocation
    rebalance_freq: int = 4,        # rebalance every N weeks
    logger: logging.Logger | None = None,
) -> dict:
    """
    DEPRECATED: Not used in active paper pipeline.
    Use scripts/06_panel_a_long_horizon.py and scripts/07_panel_b_regime_oos.py instead.
    This function is retained for reference only and will be removed in a future cleanup pass.

    Walk-forward CVaR backtest.

    For each rebalance date t (using only data up to t-1):
      1. Identify current regime from walk-forward labels
      2. Collect historical regime scenarios (expanding window)
      3. Solve regime-conditional CVaR LP
      4. Apply weights to next week's returns

    Also runs:
      - Unconditional CVaR (all-history, no regime)
      - Equal-weight (1/n across risky assets)
      - Market-cap proxy: 100% StoxxEurope600

    Returns
    -------
    dict with DataFrames:
        weights_regime     : weekly weights for regime-CVaR portfolio
        weights_uncond     : weekly weights for unconditional CVaR portfolio
        returns_all        : weekly returns for all strategies
        regime_sequence    : regime per week
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    if config is None:
        config = CVaRConfig()

    risky = [c for c in returns.columns if c != cash_col]
    n = len(risky)
    all_cols = returns.columns.tolist()

    # Align returns and regimes on a common weekly index
    common = returns.index.intersection(regime_labels.index)
    ret = returns.loc[common, risky].copy()
    reg = regime_labels.loc[common].copy()

    dates = ret.index
    T = len(dates)

    # Output containers
    w_regime = pd.DataFrame(index=dates, columns=risky, dtype=float)
    w_uncond  = pd.DataFrame(index=dates, columns=risky, dtype=float)

    current_w_reg  = np.ones(n) / n   # start equal-weight
    current_w_unc  = np.ones(n) / n

    rebalance_count = 0

    for i, date in enumerate(dates):
        if i < min_history_weeks:
            # Still in burn-in: hold equal weight
            w_regime.iloc[i] = current_w_reg
            w_uncond.iloc[i]  = current_w_unc
            continue

        # Rebalance every `rebalance_freq` weeks
        if (i - min_history_weeks) % rebalance_freq == 0:
            hist_ret  = ret.iloc[:i]          # strictly historical (no look-ahead)
            hist_reg  = reg.iloc[:i]
            cur_regime = int(reg.iloc[i])      # current regime (walk-forward, so no leak)

            # --- Regime-conditional CVaR ---
            res_reg = regime_cvar_weights(hist_ret, hist_reg, cur_regime, config)
            if res_reg["success"] and res_reg["weights"] is not None:
                current_w_reg = res_reg["weights"]
            else:
                logger.debug("Regime CVaR failed at %s (regime=%d, n_scen=%d): %s",
                             date.date(), cur_regime,
                             res_reg.get("n_scenarios", 0), res_reg["message"])

            # --- Unconditional CVaR ---
            res_unc = unconditional_cvar_weights(hist_ret, config)
            if res_unc["success"] and res_unc["weights"] is not None:
                current_w_unc = res_unc["weights"]

            rebalance_count += 1

        w_regime.iloc[i] = current_w_reg
        w_uncond.iloc[i]  = current_w_unc

    logger.info("Backtest complete: %d rebalances over %d weeks", rebalance_count, T)

    # Compute strategy returns (weights at t applied to return at t+1)
    # Shift weights by 1 week to simulate implementation lag
    w_reg_lag  = w_regime.shift(1).dropna()
    w_unc_lag  = w_uncond.shift(1).dropna()
    ret_lag    = ret.loc[w_reg_lag.index]

    strat_ret = pd.DataFrame(index=w_reg_lag.index)
    strat_ret["regime_cvar"]   = (w_reg_lag.values * ret_lag.values).sum(axis=1)
    strat_ret["uncond_cvar"]   = (w_unc_lag.values * ret_lag.values).sum(axis=1)
    strat_ret["equal_weight"]  = ret_lag.mean(axis=1)

    # Market proxy: StoxxEurope600 if available
    stoxx_col = next((c for c in risky if "stoxx" in c.lower() and "euro" in c.lower()
                      and "600" in c.lower()), None)
    if stoxx_col:
        strat_ret["stoxx600"] = ret_lag[stoxx_col]

    return {
        "weights_regime": w_regime,
        "weights_uncond": w_uncond,
        "returns": strat_ret,
        "regime_sequence": reg.loc[w_reg_lag.index],
    }


# ---------------------------------------------------------------------------
# Performance metrics
# ---------------------------------------------------------------------------

def compute_metrics(
    returns_series: pd.Series,
    alpha: float = 0.95,
    rf_series: "pd.Series | None" = None,
    rf_weekly: float = 0.0,
    weeks_per_year: int = 52,
) -> dict:
    """Compute annualised performance metrics for a weekly return series.

    Parameters
    ----------
    returns_series : pd.Series   weekly gross returns
    alpha          : float       CVaR confidence level
    rf_series      : pd.Series   EURIBOR (or other) weekly simple return, indexed
                                 by date.  If provided, Sharpe = mean(r-rf)/std(r-rf)*√52.
                                 Missing dates are filled with rf_weekly (default 0.0).
                                 No look-ahead: rf at t uses only data observable at t.
    rf_weekly      : float       Fallback scalar risk-free (backward-compat default = 0.0).
    weeks_per_year : int         52
    """
    r = returns_series.dropna()
    T = len(r)
    ann = weeks_per_year

    # ── Risk-free alignment ───────────────────────────────────────────────
    if rf_series is not None:
        rf_aligned = rf_series.reindex(r.index).fillna(rf_weekly)
    else:
        rf_aligned = pd.Series(rf_weekly, index=r.index)

    excess_r = r - rf_aligned

    # ── CAGR (gross) ──────────────────────────────────────────────────────
    total_ret = (1 + r).prod() - 1
    years     = T / ann
    cagr      = (1 + total_ret) ** (1 / years) - 1 if years > 0 else np.nan

    # ── Volatility (gross returns) ────────────────────────────────────────
    vol = r.std() * np.sqrt(ann)

    # ── Excess Sharpe ─────────────────────────────────────────────────────
    ex_std = excess_r.std()
    sharpe = excess_r.mean() / ex_std * np.sqrt(ann) if ex_std > 0 else np.nan

    # ── Max drawdown ──────────────────────────────────────────────────────
    cum         = (1 + r).cumprod()
    rolling_max = cum.cummax()
    drawdown    = (cum - rolling_max) / rolling_max
    max_dd      = drawdown.min()

    # ── Tail risk ─────────────────────────────────────────────────────────
    var_95  = r.quantile(1 - alpha)
    cvar_95 = r[r <= var_95].mean()

    # ── Calmar ────────────────────────────────────────────────────────────
    calmar = cagr / abs(max_dd) if max_dd != 0 else np.nan

    # ── Higher moments ────────────────────────────────────────────────────
    skew = r.skew()
    kurt = r.kurtosis()

    return {
        "CAGR":       round(cagr * 100, 2),
        "Vol":        round(vol * 100, 2),
        "Sharpe":     round(sharpe, 3),        # excess Sharpe if rf_series provided
        "MaxDD":      round(max_dd * 100, 2),
        "CVaR_95":    round(cvar_95 * 100, 2),
        "Calmar":     round(calmar, 3),
        "Skewness":   round(skew, 3),
        "Kurtosis":   round(kurt, 3),
        "N_weeks":    T,
        "RF_ann_pct": round(rf_aligned.mean() * ann * 100, 3),
    }


# ---------------------------------------------------------------------------
# Regime-dependent constraints (Version B)
# ---------------------------------------------------------------------------

@dataclass
class RegimeConstraints:
    """
    Per-regime portfolio constraints applied on top of the base CVaR LP.

    equity_cap  : maximum total weight in equity assets (0–1)
    cash_floor  : minimum weight in the cash/money-market asset (0–1)
    """
    equity_cap: float = 1.0     # default: unconstrained
    cash_floor: float = 0.0     # default: no floor


# Economically motivated regime-constraint map.
# Keys are ECONOMIC regime labels (set by characterise_regimes).
# For the numeric-label mapping, see REGIME_CONSTRAINT_BY_INT below.
REGIME_CONSTRAINTS_BY_LABEL: dict[str, RegimeConstraints] = {
    "ELEVATED_RISK":  RegimeConstraints(equity_cap=0.35, cash_floor=0.15),
    "NEUTRAL":        RegimeConstraints(equity_cap=0.55, cash_floor=0.05),
    "LOW_VOL":        RegimeConstraints(equity_cap=0.60, cash_floor=0.05),
    "RISK_ON":        RegimeConstraints(equity_cap=0.75, cash_floor=0.00),
}

# Fallback numeric-index map (used when economic labels aren't resolved yet).
# Regime with the most elevated vol/spread features → tightest constraints.
# Will be remapped to economic labels in run_constrained_cvar_backtest().
REGIME_CONSTRAINTS_DEFAULT: RegimeConstraints = RegimeConstraints(equity_cap=0.55, cash_floor=0.05)



def classify_assets(asset_names, cash_col="EURIBOR_3M"):
    """Heuristic equity vs. cash classification. Returns (equity_names_set, cash_name)."""
    equity_tokens = [
        "stoxx", "dax", "ftse", "cac", "s&p", "sp500", "msci",
        "equity", "stock", "share", "midcap", "smallcap",
    ]
    equity_names = set()
    cash_name = None
    for nm in asset_names:
        lnm = nm.lower()
        if nm == cash_col or "euribor" in lnm or "cash" in lnm:
            cash_name = nm
        elif any(tok in lnm for tok in equity_tokens):
            equity_names.add(nm)
    return equity_names, cash_name


def solve_cvar_constrained(scenarios, asset_names, equity_names, cash_name,
                           regime_constraints, config=None):
    """Min-CVaR LP with equity cap and cash floor constraints."""
    if config is None:
        config = CVaRConfig()
    T, n = scenarios.shape
    alpha = config.alpha
    if T < config.min_scenarios:
        return {"weights": None, "cvar": float("nan"), "var": float("nan"),
                "success": False, "message": f"Too few scenarios: {T} < {config.min_scenarios}"}
    n_vars = n + 1 + T
    c = np.zeros(n_vars)
    c[n] = 1.0
    c[n + 1:] = 1.0 / ((1.0 - alpha) * T)
    A_ub = np.zeros((2 * T, n_vars))
    b_ub = np.zeros(2 * T)
    for t in range(T):
        A_ub[t, :n] = -scenarios[t, :]
        A_ub[t, n] = -1.0
        A_ub[t, n + 1 + t] = -1.0
        A_ub[T + t, n + 1 + t] = -1.0
    extra_rows, extra_b = [], []
    equity_idx = [i for i, nm in enumerate(asset_names) if nm in equity_names]
    if equity_idx and regime_constraints.equity_cap < 1.0:
        row = np.zeros(n_vars)
        for i in equity_idx:
            row[i] = 1.0
        extra_rows.append(row)
        extra_b.append(regime_constraints.equity_cap)
    cash_idx = next((i for i, nm in enumerate(asset_names) if nm == cash_name), None)
    if cash_idx is not None and regime_constraints.cash_floor > 0.0:
        row = np.zeros(n_vars)
        row[cash_idx] = -1.0
        extra_rows.append(row)
        extra_b.append(-regime_constraints.cash_floor)
    if extra_rows:
        A_ub = np.vstack([A_ub] + extra_rows)
        b_ub = np.append(b_ub, extra_b)
    A_eq = np.zeros((1, n_vars))
    A_eq[0, :n] = 1.0
    b_eq = np.array([1.0])
    bounds = [(config.min_weight, config.max_weight)] * n + [(None, None)] + [(0.0, None)] * T
    result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                     bounds=bounds, method=config.linprog_method, options={"disp": False})
    if not result.success:
        return {"weights": None, "cvar": float("nan"), "var": float("nan"),
                "success": False, "message": result.message}
    w = result.x[:n]
    zeta = result.x[n]
    z = result.x[n + 1:]
    cvar = zeta + np.mean(z) / (1.0 - alpha)
    return {"weights": w, "cvar": cvar, "var": zeta, "success": True, "message": "OK"}


def weighted_cvar_weights(
    returns,
    weights_series,
    config=None,
):
    """
    Weighted CVaR: importance-weighted by regime posterior probability.

    Instead of hard-selecting only current-regime scenarios, this uses
    ALL historical observations weighted by P(current_regime | obs_t).
    This provides a smooth, statistically more efficient alternative to
    hard regime-conditional CVaR.

    The LP is a weighted generalisation of Rockafellar-Uryasev:
        min  zeta + 1/((1-alpha)*sum_w) * sum_t  w_t * z_t
        s.t. z_t >= -r_t'w - zeta,  z_t >= 0
    where w_t = P(current_regime | obs_t).

    Parameters
    ----------
    returns : DataFrame (T_hist, n)
    weights_series : Series (T_hist,) — non-negative importance weights
    config : CVaRConfig
    """
    if config is None:
        config = CVaRConfig()

    common = returns.index.intersection(weights_series.index)
    scen = returns.loc[common].dropna().values
    w_t = weights_series.loc[common].reindex(returns.loc[common].dropna().index).fillna(0).values
    w_t = w_t / w_t.sum() if w_t.sum() > 0 else np.ones(len(w_t)) / len(w_t)

    T, n = scen.shape
    alpha = config.alpha
    if T < config.min_scenarios:
        return {"weights": None, "cvar": float("nan"), "var": float("nan"),
                "success": False, "message": f"Too few scenarios: {T}"}

    n_vars = n + 1 + T
    c = np.zeros(n_vars)
    c[n] = 1.0
    c[n + 1:] = w_t / (1.0 - alpha)   # importance-weighted z coefficients

    A_ub = np.zeros((2 * T, n_vars))
    b_ub = np.zeros(2 * T)
    for t in range(T):
        A_ub[t, :n] = -scen[t, :]
        A_ub[t, n] = -1.0
        A_ub[t, n + 1 + t] = -1.0
        A_ub[T + t, n + 1 + t] = -1.0

    A_eq = np.zeros((1, n_vars))
    A_eq[0, :n] = 1.0
    b_eq = np.array([1.0])
    bounds = [(config.min_weight, config.max_weight)] * n + [(None, None)] + [(0.0, None)] * T

    result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                     bounds=bounds, method=config.linprog_method, options={"disp": False})

    if not result.success:
        return {"weights": None, "cvar": float("nan"), "var": float("nan"),
                "success": False, "message": result.message}

    w = result.x[:n]
    zeta = result.x[n]
    z = result.x[n + 1:]
    cvar = zeta + np.dot(w_t, z) / (1.0 - alpha)
    return {"weights": w, "cvar": cvar, "var": zeta, "success": True, "message": "OK",
            "n_scenarios": T}
