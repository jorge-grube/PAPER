"""
Gaussian HMM regime detection for European multi-asset CVaR portfolio.

The module provides:
  - Feature selection and preprocessing for HMM
  - GaussianHMM fitting with BIC/AIC model selection (n_states ∈ {2, 3, 4})
  - Full-sample Viterbi decode (in-sample regime labels)
  - Walk-forward expanding-window regime sequence (no look-ahead bias)
  - Regime characterisation and economic interpretation helpers
  - Persistence: saves regime labels and diagnostics to data/processed/

Usage:
    python scripts/02_fit_hmm.py
"""
from __future__ import annotations

import json
import logging
import warnings
from pathlib import Path
from typing import NamedTuple

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from sklearn.preprocessing import StandardScaler


# ---------------------------------------------------------------------------
# Feature configuration
# ---------------------------------------------------------------------------

# Feature selection rationale
# ─────────────────────────────────────────────────────────────────────────────
# We restrict to features with ≥ 75 % coverage in the 1999-2026 analysis
# window AND that do not share the Germany_10Y truncation (ends Oct 2019).
# Features that use Germany_10Y as a reference (spreads, 10Y-2Y slope) are
# EXCLUDED here; they cover only 2004-2019 and would eliminate 45 % of the
# sample including the COVID crisis and the 2022 inflation shock.
#
# Coverage in 1999+ window (1427 weeks):
#   z52_VIX                                  100 %
#   z52_VSTOXX                                94 %
#   z52_MOVE                                  84 %
#   delta_US_10Y_Yield_1w                    100 %
#   z52_DXY_USD_Index                         94 %
#   z52_Eurozone_Economic_Sentiment_Indicator  78 %
#   z52_hicp_headline_core_gap                78 %
#   z52_germany_10y_2y_slope                  98 %   (ECB deposit rate as short-rate proxy)
#   z52_peripheral_spread_avg                 99 %
#
# NOTE: delta_Germany_2Y_Yield_1w removed -- the Bundesbank aDEWU outstanding-bond
# series is methodologically wrong for capturing weekly rate-shock signals during the
# 2022-2023 ECB hiking cycle (series lags market repricing by 12-18 months).
# yield-curve regime is now captured via z52_germany_10y_2y_slope instead.
REGIME_FEATURES: list[str] = [
    # All features are either 52-week rolling z-scores or weekly first differences.
    # This keeps the feature space on comparable scales and avoids the right-skewed
    # realized-vol distributions that destabilise full-covariance HMMs.

    # -- Volatility regime (global + European) --
    "z52_VIX",                                    # VIX 52-week z-score           (100 %)
    "z52_VSTOXX",                                 # VSTOXX z-score                (~94 %)
    # -- Bond market stress --
    "z52_MOVE",                                   # MOVE index z-score            (~84 %)
    # -- Yield curve shape (monetary regime) --
    # NOTE: delta_US_10Y_Yield_1w removed -- weekly first-differences of yields are
    # essentially noise at this frequency, causing the HMM to produce 1-week episodes
    # by alternating between near-identical states.  Monetary regime is captured more
    # stably via the slope z-score (which already embeds the direction of policy rates).
    "z52_germany_10y_2y_slope",                   # 10Y vs ECB-deposit z-score    (~98 %)
    # -- Credit / peripheral stress --
    "z52_peripheral_spread_avg",                  # avg ES/PT/IT spread to DE     (~99 %)
    # -- Currency / global risk appetite --
    "z52_DXY_USD_Index",                          # DXY z-score                   (~94 %)
    # -- Eurozone macro sentiment --
    "z52_Eurozone_Economic_Sentiment_Indicator",  # ESI z-score                   (~78 %)
    # -- Inflation regime --
    "z52_hicp_headline_core_gap",                 # HICP headline-core gap z-score (~78 %)
]

# Maximum forward-fill gap (weeks) before a row is considered unobservable
MAX_FFILL_WEEKS: int = 8

# Minimum training observations for walk-forward initialisation (5 years)
MIN_TRAIN_OBS: int = 260

# Walk-forward step size (refit every N weeks)
WALK_FORWARD_STEP: int = 4

# HMM hyperparameters
COVARIANCE_TYPE: str = "diag"   # diagonal cov: stable with ~1100 obs x 8 features
N_ITER: int = 500
N_INIT: int = 15          # restarts to escape local optima
RANDOM_STATE: int = 42


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def select_and_impute(
    features: pd.DataFrame,
    feature_names: list[str],
    max_ffill: int = MAX_FFILL_WEEKS,
    logger: logging.Logger | None = None,
) -> pd.DataFrame:
    """
    Select HMM features, forward-fill short gaps, drop rows still missing.

    Returns a DataFrame with the same index as `features` but only the
    selected columns and no NaN values (rows with residual NaN are dropped).
    """
    log = logger or logging.getLogger(__name__)

    available = [c for c in feature_names if c in features.columns]
    missing_cols = [c for c in feature_names if c not in features.columns]
    if missing_cols:
        log.warning("HMM feature(s) not found in panel, skipping: %s", missing_cols)

    df = features[available].copy()
    before = len(df)

    # Forward-fill up to max_ffill consecutive NaN weeks
    df = df.ffill(limit=max_ffill)

    # Drop rows where any feature is still NaN
    df = df.dropna()
    after = len(df)
    if before != after:
        log.info(
            "select_and_impute: dropped %d/%d rows with residual NaN after %d-week ffill",
            before - after,
            before,
            max_ffill,
        )

    log.info(
        "HMM feature matrix: %d obs x %d features  (%s .. %s)",
        len(df),
        df.shape[1],
        df.index.min().date() if len(df) else "—",
        df.index.max().date() if len(df) else "—",
    )
    return df


# ---------------------------------------------------------------------------
# Model fitting
# ---------------------------------------------------------------------------

class HMMFitResult(NamedTuple):
    model: GaussianHMM
    scaler: StandardScaler
    n_states: int
    log_likelihood: float
    bic: float
    aic: float
    n_obs: int
    n_features: int


def _fit_one(
    X_scaled: np.ndarray,
    n_states: int,
    n_init: int = N_INIT,
    n_iter: int = N_ITER,
    random_state: int = RANDOM_STATE,
) -> tuple[GaussianHMM, float]:
    """Fit one GaussianHMM with multiple random restarts; return best model and log-likelihood."""
    best_model: GaussianHMM | None = None
    best_ll = -np.inf

    for seed in range(random_state, random_state + n_init):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                m = GaussianHMM(
                    n_components=n_states,
                    covariance_type=COVARIANCE_TYPE,
                    n_iter=n_iter,
                    random_state=seed,
                    verbose=False,
                )
                m.fit(X_scaled)
                ll = m.score(X_scaled)
                if ll > best_ll:
                    best_ll = ll
                    best_model = m
            except Exception:
                continue

    if best_model is None:
        raise RuntimeError(f"All {n_init} HMM initialisations failed for n_states={n_states}")
    return best_model, best_ll


def fit_hmm(
    X: pd.DataFrame,
    n_states: int,
    logger: logging.Logger | None = None,
) -> HMMFitResult:
    """Fit a GaussianHMM with `n_states` states on feature matrix X."""
    log = logger or logging.getLogger(__name__)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X.values)

    log.info("Fitting GaussianHMM  n_states=%d  n_obs=%d  n_features=%d", n_states, len(X), X.shape[1])
    model, ll = _fit_one(X_scaled, n_states)

    # Parameter count for diagonal covariance GaussianHMM:
    #   means          : n_states * n_features
    #   diag variances : n_states * n_features  (NOT n_features^2 — that is full cov)
    #   transition A   : n_states * (n_states - 1)
    #   initial pi     : n_states - 1
    # hmmlearn.score() returns total log-likelihood (sum over T, not per-sample average).
    n_features = X.shape[1]
    n_params = (
        n_states * n_features                        # means
        + n_states * n_features                      # diagonal variances (diag cov)
        + n_states * (n_states - 1)                  # transition matrix rows
        + (n_states - 1)                             # initial state probabilities
    )
    ll_total = ll                                    # score() returns total LL
    bic = -2 * ll_total + n_params * np.log(len(X))
    aic = -2 * ll_total + 2 * n_params

    log.info(
        "  n_states=%d  ll_total=%.2f  ll_per_obs=%.4f  BIC=%.1f  AIC=%.1f",
        n_states, ll_total, ll_total / len(X), bic, aic,
    )
    return HMMFitResult(model, scaler, n_states, ll_total, bic, aic, len(X), X.shape[1])


def select_n_states(
    X: pd.DataFrame,
    candidates: list[int] | None = None,
    logger: logging.Logger | None = None,
) -> tuple[int, dict]:
    """
    Fit HMMs for each candidate number of states; return BIC-optimal n_states
    and a diagnostics dict.
    """
    log = logger or logging.getLogger(__name__)
    if candidates is None:
        candidates = [2, 3, 4]

    results: list[HMMFitResult] = []
    for n in candidates:
        try:
            r = fit_hmm(X, n_states=n, logger=log)
            results.append(r)
        except Exception as e:
            log.warning("HMM fitting failed for n_states=%d: %s", n, e)

    if not results:
        raise RuntimeError("No HMM models converged.")

    best = min(results, key=lambda r: r.bic)
    log.info("BIC-optimal n_states = %d", best.n_states)

    diagnostics = {
        "bic_comparison": {r.n_states: {"bic": r.bic, "aic": r.aic, "log_likelihood": r.log_likelihood} for r in results},
        "selected_n_states": best.n_states,
        "selected_bic": best.bic,
        "n_obs": best.n_obs,
        "n_features": best.n_features,
    }
    return best.n_states, diagnostics


# ---------------------------------------------------------------------------
# Regime decoding
# ---------------------------------------------------------------------------

def decode_regimes(
    result: HMMFitResult,
    X: pd.DataFrame,
) -> pd.Series:
    """
    Viterbi decode regime labels for all observations in X.
    Labels are aligned to X.index and returned as integer codes starting at 0.
    """
    X_scaled = result.scaler.transform(X.values)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        states = result.model.predict(X_scaled)
    return pd.Series(states, index=X.index, name="regime", dtype=int)


def walk_forward_regimes(
    X: pd.DataFrame,
    n_states: int,
    min_train: int = MIN_TRAIN_OBS,
    step: int = WALK_FORWARD_STEP,
    logger: logging.Logger | None = None,
) -> pd.Series:
    """
    Walk-forward expanding-window regime labelling.

    At each step the HMM is re-fitted on all observations up to and including
    the current window; the regime label for the *last* observation in the
    window is recorded.  This avoids look-ahead bias: the label for week t
    uses only information available at week t.

    Parameters
    ----------
    X        : feature matrix (already imputed, no NaN)
    n_states : number of HMM states (BIC-selected)
    min_train: minimum observations before the first fit
    step     : refit frequency in observations

    Returns
    -------
    pd.Series  regime label at each date in X.index
    """
    log = logger or logging.getLogger(__name__)
    n = len(X)
    labels = np.full(n, np.nan)
    posteriors = np.full((n, n_states), np.nan)   # posterior state probabilities

    log.info(
        "Walk-forward HMM  n_states=%d  n_obs=%d  min_train=%d  step=%d",
        n_states, n, min_train, step,
    )

    # Checkpoints at which we refit
    checkpoints = list(range(min_train, n + 1, step))
    if checkpoints[-1] < n:
        checkpoints.append(n)   # always include the final observation

    last_result: HMMFitResult | None = None

    for end in checkpoints:
        X_train = X.iloc[:end]
        try:
            result = fit_hmm(X_train, n_states=n_states, logger=log)
            last_result = result
        except Exception as e:
            log.warning("Walk-forward refit failed at obs %d: %s; using last good model", end, e)
            if last_result is None:
                continue
            result = last_result

        # Decode full training window; record label and posterior probs for last obs
        states = decode_regimes(result, X_train)
        labels[end - 1] = states.iloc[-1]

        # Posterior probabilities for the last observation
        X_scaled_train = result.scaler.transform(X_train.values)
        posteriors[end - 1, :] = result.model.predict_proba(X_scaled_train)[-1, :]

        log.debug("  end=%d  label=%d", end, labels[end - 1])

    # Forward-fill within the labelled region only.
    # The first min_train observations have no label (NaN) — this is intentional.
    # bfill() is deliberately omitted: look-ahead-free design requires that labels
    # are only assigned once sufficient training data exists.  The backtest burn-in
    # must start after the first non-NaN label, not before.
    labels_series = pd.Series(labels, index=X.index, name="regime_wf")
    labels_series = labels_series.ffill()
    # Return float series so NaN is representable; callers cast to int after dropna.
    probs_df = pd.DataFrame(
        posteriors,
        index=X.index,
        columns=[f"prob_regime_{k}" for k in range(n_states)],
    )
    probs_df = probs_df.ffill()   # forward-fill in sync with labels
    return labels_series, probs_df


# ---------------------------------------------------------------------------
# Regime interpretation
# ---------------------------------------------------------------------------

def characterise_regimes(
    result: HMMFitResult,
    feature_names: list[str],
    regime_labels: pd.Series,
    features: pd.DataFrame,
) -> dict:
    """
    Summarise each regime by:
      - Mean feature values (in original units, not scaled)
      - Frequency and average duration
      - Economic interpretation heuristic
    """
    summaries = {}
    for state in range(result.n_states):
        mask = regime_labels == state
        n_obs = mask.sum()
        freq = n_obs / len(regime_labels)

        # Duration: consecutive runs
        durations = []
        in_run = False
        run_len = 0
        for v in mask:
            if v:
                in_run = True
                run_len += 1
            else:
                if in_run:
                    durations.append(run_len)
                in_run = False
                run_len = 0
        if in_run:
            durations.append(run_len)

        avg_duration = np.mean(durations) if durations else 0
        mean_vals = features.loc[mask, feature_names].mean().to_dict() if n_obs > 0 else {}

        # Simple heuristic label
        vix_z = mean_vals.get("z52_VIX", 0)
        spread_z = mean_vals.get("z52_peripheral_spread_avg", 0)
        slope = mean_vals.get("germany_10y_2y_slope", np.nan)
        hicp_gap = mean_vals.get("hicp_headline_core_gap", 0)

        # Use features present in the lean z-score feature set
        move_z = mean_vals.get("z52_MOVE", 0) or 0
        dxy_z  = mean_vals.get("z52_DXY_USD_Index", 0) or 0
        esi_z  = mean_vals.get("z52_Eurozone_Economic_Sentiment_Indicator", 0) or 0
        us10y_d = mean_vals.get("delta_US_10Y_Yield_1w", 0) or 0
        avg_vol_z = (vix_z + (mean_vals.get("z52_VSTOXX", vix_z) or vix_z) + move_z) / 3

        if avg_vol_z > 0.8 and us10y_d < -0.01:
            # High vol + falling yields = flight-to-quality; acute risk-off
            label = "ACUTE_STRESS / FLIGHT_TO_QUALITY"
        elif avg_vol_z > 0.8:
            # High vol without clear yield direction = general stress
            # (covers inflation shocks, credit stress, political turmoil)
            label = "ELEVATED_RISK / GENERAL_STRESS"
        elif avg_vol_z < -0.4 and esi_z > 0 and us10y_d > 0.01:
            # Low vol + positive sentiment + yields clearly rising = late-cycle expansion
            label = "EXPANSION / RATE_RISING"
        elif avg_vol_z < -0.4 and esi_z >= -0.2:
            # Low vol + neutral-to-positive sentiment = calm bull market
            label = "RISK_ON / EXPANSION"
        elif avg_vol_z < -0.4:
            label = "LOW_VOL / SUBDUED"
        else:
            label = "NEUTRAL / MODERATE"

        summaries[state] = {
            "n_obs": int(n_obs),
            "frequency": float(freq),
            "avg_duration_weeks": float(avg_duration),
            "n_episodes": len(durations),
            "heuristic_label": label,
            "feature_means": {k: (float(v) if not np.isnan(v) else None) for k, v in mean_vals.items()},
        }

    return summaries


# ---------------------------------------------------------------------------
# Pipeline entry point
# ---------------------------------------------------------------------------

def run_hmm_pipeline(
    features_path: Path,
    output_dir: Path,
    config: dict | None = None,
    logger: logging.Logger | None = None,
) -> dict:
    """
    Full HMM regime detection pipeline.

    Parameters
    ----------
    features_path : path to regime_features_weekly.parquet
    output_dir    : directory for output parquets and JSON
    config        : optional overrides {n_states, start_date, feature_names}

    Returns
    -------
    dict with keys: n_states, diagnostics, regime_summary, output_paths
    """
    log = logger or logging.getLogger(__name__)
    cfg = config or {}

    output_dir.mkdir(parents=True, exist_ok=True)

    # -- Load features -------------------------------------------------------
    log.info("Loading features from %s", features_path)
    features = pd.read_parquet(features_path)
    features.index = pd.to_datetime(features.index)
    features = features.sort_index()

    # Restrict to analysis window (euro introduction onwards)
    start_date = pd.Timestamp(cfg.get("start_date", "1999-01-01"))
    features = features.loc[start_date:]
    log.info("Analysis window: %s .. %s (%d weeks)", features.index.min().date(), features.index.max().date(), len(features))

    # -- Prepare feature matrix ----------------------------------------------
    feature_names = cfg.get("feature_names", REGIME_FEATURES)
    X = select_and_impute(features, feature_names, logger=log)

    # -- Model selection (BIC) -----------------------------------------------
    n_states_forced = cfg.get("n_states")
    if n_states_forced:
        n_states = int(n_states_forced)
        log.info("Using forced n_states=%d (skipping BIC search)", n_states)
        result = fit_hmm(X, n_states=n_states, logger=log)
        diagnostics = {
            "bic_comparison": {n_states: {"bic": result.bic, "aic": result.aic, "log_likelihood": result.log_likelihood}},
            "selected_n_states": n_states,
            "selected_bic": result.bic,
            "n_obs": result.n_obs,
            "n_features": result.n_features,
        }
    else:
        n_states, diagnostics = select_n_states(X, candidates=[2, 3, 4], logger=log)
        result = fit_hmm(X, n_states=n_states, logger=log)

    # -- Full-sample Viterbi decode ------------------------------------------
    log.info("Decoding full-sample regimes (Viterbi)")
    regime_labels_full = decode_regimes(result, X)

    # -- Walk-forward (no look-ahead) ----------------------------------------
    log.info("Running walk-forward regime labelling")
    regime_labels_wf, regime_probs_wf = walk_forward_regimes(
        X,
        n_states=n_states,
        min_train=cfg.get("min_train", MIN_TRAIN_OBS),
        step=cfg.get("wf_step", WALK_FORWARD_STEP),
        logger=log,
    )

    # -- Regime characterisation ---------------------------------------------
    log.info("Characterising regimes")
    # Use only non-NaN walk-forward labels for characterisation
    wf_valid = regime_labels_wf.dropna().astype(int)
    regime_summary = characterise_regimes(result, list(X.columns), regime_labels_full, X)

    for state, info in regime_summary.items():
        log.info(
            "  Regime %d [%s]: %.1f%% of weeks, avg duration %.1f wk, %d episodes",
            state,
            info["heuristic_label"],
            info["frequency"] * 100,
            info["avg_duration_weeks"],
            info["n_episodes"],
        )

    # -- Persist outputs -----------------------------------------------------
    # 1. Full-sample labels aligned to X.index
    regime_labels_full.to_frame("regime_full").to_parquet(output_dir / "regime_labels_full.parquet")
    log.info("Wrote regime_labels_full.parquet (%d rows)", len(regime_labels_full))

    # 2. Walk-forward labels (NaN in burn-in, no bfill)
    regime_labels_wf.to_frame("regime_wf").to_parquet(output_dir / "regime_labels_wf.parquet")
    log.info("Wrote regime_labels_wf.parquet (%d rows, %d non-NaN)",
             len(regime_labels_wf), regime_labels_wf.notna().sum())

    # 2b. Walk-forward posterior probabilities
    regime_probs_wf.to_parquet(output_dir / "regime_probs_wf.parquet")
    log.info("Wrote regime_probs_wf.parquet (%d rows x %d cols)", *regime_probs_wf.shape)

    # 3. Combined: features + both label sequences
    combined = X.copy()
    combined["regime_full"] = regime_labels_full
    combined["regime_wf"] = regime_labels_wf
    combined.to_parquet(output_dir / "regime_dataset.parquet")
    log.info("Wrote regime_dataset.parquet (%d rows x %d cols)", *combined.shape)

    # 4. HMM model parameters (means, covars, transmat) as JSON
    model_params = {
        "n_states": n_states,
        "n_features": result.n_features,
        "feature_names": list(X.columns),
        "means": result.model.means_.tolist(),
        "covars": result.model.covars_.tolist(),
        "transmat": result.model.transmat_.tolist(),
        "startprob": result.model.startprob_.tolist(),
        "scaler_mean": result.scaler.mean_.tolist(),
        "scaler_scale": result.scaler.scale_.tolist(),
    }

    # 5. Full diagnostics JSON
    output = {
        "model_selection": diagnostics,
        "model_params": model_params,
        "regime_summary": {str(k): v for k, v in regime_summary.items()},
        "analysis_window": {
            "start": str(features.index.min().date()),
            "end": str(features.index.max().date()),
            "n_weeks_total": len(features),
            "n_weeks_hmm": len(X),
        },
    }
    diag_path = output_dir / "hmm_diagnostics.json"
    with open(diag_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    log.info("Wrote hmm_diagnostics.json")

    output_paths = {
        "regime_labels_full": str(output_dir / "regime_labels_full.parquet"),
        "regime_labels_wf": str(output_dir / "regime_labels_wf.parquet"),
        "regime_dataset": str(output_dir / "regime_dataset.parquet"),
        "hmm_diagnostics": str(diag_path),
    }
    return {
        "n_states": n_states,
        "diagnostics": diagnostics,
        "regime_summary": regime_summary,
        "output_paths": output_paths,
    }
