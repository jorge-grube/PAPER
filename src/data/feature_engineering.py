from __future__ import annotations

from typing import Iterable
import logging

import numpy as np
import pandas as pd

from .config import PipelineConfig
from .transformations import write_parquet


def _find_first(columns: Iterable[str], include: list[str], exclude: list[str] | None = None) -> str | None:
    exclude = exclude or []
    cols = list(columns)
    for col in cols:
        txt = col.lower()
        if all(tok in txt for tok in include) and not any(tok in txt for tok in exclude):
            return col
    return None


def _find_all(columns: Iterable[str], include_any: list[str]) -> list[str]:
    cols = []
    for col in columns:
        txt = col.lower()
        if any(tok in txt for tok in include_any):
            cols.append(col)
    return cols


def _find_country_yield(columns: Iterable[str], country_token: str) -> str | None:
    """Find a country yield-like column, avoiding unrelated macro series."""
    for col in columns:
        txt = col.lower()
        if country_token in txt and any(tok in txt for tok in ["yield", "bond", "longterm", "10y", "2y"]):
            return col
    return None


def _rolling_zscore(series: pd.Series, window: int = 52, min_periods: int = 26) -> pd.Series:
    m = series.rolling(window=window, min_periods=min_periods).mean()
    s = series.rolling(window=window, min_periods=min_periods).std()
    return (series - m) / s


def engineer_regime_features(
    regime_panel: pd.DataFrame,
    config: PipelineConfig,
    logger: logging.Logger,
) -> pd.DataFrame:
    """Engineer derived regime features for regime-aware portfolio allocation."""

    if regime_panel.empty:
        raise RuntimeError("Critical failure: regime panel is empty, cannot engineer features.")

    df = regime_panel.copy()
    f = pd.DataFrame(index=df.index)
    cols = list(df.columns)

    germany_10y = _find_first(cols, ["germany", "10y"]) or _find_first(cols, ["de", "10y"])
    germany_2y = _find_first(cols, ["germany", "2y"]) or _find_first(cols, ["de", "2y"])

    # Validate the 2Y column has actual market benchmark data.
    if germany_2y is not None:
        s2y_num = pd.to_numeric(df[germany_2y], errors="coerce")

        # Check 1: enough data at all?
        if s2y_num.notna().sum() < 10:
            logger.warning(
                "Germany 2Y yield column '%s' has fewer than 10 valid values -- "
                "treating as missing and falling back to ECB Deposit Facility Rate.",
                germany_2y,
            )
            germany_2y = None
        else:
            # Check 2: ECB hiking-cycle range test.
            # The ECB started hiking Jul 2022; by Q4 2022 the deposit rate was 1.5-2.5%.
            # A market benchmark 2Y Bund yield should be clearly positive (>0%) by then.
            # If the series is still negative or near-zero throughout Q4 2022 it is
            # almost certainly a Bundesbank "outstanding bonds at historical issue rates"
            # weighted average, which lags market repricing by 12-18 months and is
            # methodologically wrong for yield-curve slope construction.
            try:
                q4_2022 = s2y_num.loc["2022-10-01":"2022-12-31"]
            except (KeyError, TypeError):
                q4_2022 = pd.Series(dtype=float)

            if q4_2022.notna().sum() >= 4 and q4_2022.dropna().max() < 0.0:
                logger.warning(
                    "Germany 2Y column '%s' peaks at %.3f%% in Q4-2022 "
                    "(ECB deposit rate was 1.5-2.5%% over this period; actual 2Y Bund ~2.3%%). "
                    "This is a weighted-average-of-outstanding-bonds series (Bundesbank aDEWU). "
                    "Falling back to ECB Deposit Facility Rate for yield-curve slope construction.",
                    germany_2y,
                    q4_2022.dropna().max(),
                )
                germany_2y = None

    if germany_2y is None:
        # Fallback: ECB Deposit Facility Rate is the best available short-rate proxy.
        # It tracks the on-the-run 2Y Bund benchmark closely (spread typically < 20 bp)
        # and correctly captures monetary policy regime changes.
        germany_2y = _find_first(cols, ["ecb", "deposit"]) or _find_first(cols, ["deposit", "facility"])
        if germany_2y is not None:
            logger.warning(
                "Germany 2Y Bund yield unavailable; using %r as proxy for slope calculation. "
                "Replace Germany_2Y_Yield.xlsx with a market-benchmark export to remove this fallback.",
                germany_2y,
            )

    if germany_10y and germany_2y:
        f["germany_10y_2y_slope"] = pd.to_numeric(df[germany_10y], errors="coerce") - pd.to_numeric(
            df[germany_2y], errors="coerce"
        )
    else:
        logger.warning("Could not compute Germany 10Y-2Y slope (missing one or both legs).")

    ref_col = germany_10y
    if ref_col is None:
        logger.warning("No Germany 10Y reference found for sovereign spread construction.")

    spread_map = {
        "spread_spain_germany": "spain",
        "spread_france_germany": "france",
        "spread_portugal_germany": "portugal",
        "spread_belgium_germany": "belgium",
        "spread_netherlands_germany": "netherlands",
        "spread_italy_germany": "italy",
    }

    spread_cols: list[str] = []
    for feat_name, token in spread_map.items():
        ctry_col = _find_country_yield(cols, token)
        if ctry_col and ref_col:
            f[feat_name] = (
                pd.to_numeric(df[ctry_col], errors="coerce")
                - pd.to_numeric(df[ref_col], errors="coerce")
            )
            spread_cols.append(feat_name)

    peripheral_candidates = [
        c for c in ["spread_spain_germany", "spread_portugal_germany", "spread_italy_germany"]
        if c in f.columns
    ]
    if peripheral_candidates:
        f["peripheral_spread_avg"] = f[peripheral_candidates].mean(axis=1)
        f["peripheral_spread_dispersion"] = f[peripheral_candidates].std(axis=1)

    hicp_headline = _find_first(cols, ["eurozone", "hicp"], exclude=["core"])
    hicp_core = _find_first(cols, ["eurozone", "hicp", "core"])
    if hicp_headline and hicp_core:
        s_headline = pd.to_numeric(df[hicp_headline], errors="coerce")
        s_core_raw = pd.to_numeric(df[hicp_core], errors="coerce")

        # Unit-mismatch guard: if core looks like an index (median > 10) but
        # headline looks like a YoY rate (median < 10), convert core to YoY.
        # Weekly data: 52-period pct_change approximates year-on-year.
        median_headline = s_headline.dropna().median()
        median_core = s_core_raw.dropna().median()
        if abs(median_core) > 10 and abs(median_headline) <= 10:
            logger.info(
                "HICP core column '%s' appears to be an index (median=%.1f); "
                "converting to 52-week YoY rate before computing gap.",
                hicp_core, median_core,
            )
            s_core = s_core_raw.pct_change(periods=52) * 100.0
        else:
            s_core = s_core_raw

        f["hicp_headline_core_gap"] = s_headline - s_core
    else:
        logger.warning("Could not compute HICP headline-core gap.")

    # Changes in yields and spreads
    yield_cols = _find_all(cols, ["yield", "bond", "longterm", "10y", "2y"])
    for col in sorted(set(yield_cols)):
        s = pd.to_numeric(df[col], errors="coerce")
        f[f"delta_{col}_1w"] = s.diff()

    for col in spread_cols + ["germany_10y_2y_slope", "peripheral_spread_avg", "peripheral_spread_dispersion"]:
        if col in f.columns:
            f[f"delta_{col}_1w"] = pd.to_numeric(f[col], errors="coerce").diff()

    # Rolling realized volatility proxies from volatility indices
    vol_cols = _find_all(cols, ["vix", "vstoxx", "move", "realizedvol", "volatility"])
    for col in sorted(set(vol_cols)):
        s = pd.to_numeric(df[col], errors="coerce")
        log_ret = np.log(s.where(s > 0)).diff()
        f[f"rv_{col}_4w"] = log_ret.rolling(4, min_periods=3).std() * np.sqrt(52)
        f[f"rv_{col}_12w"] = log_ret.rolling(12, min_periods=8).std() * np.sqrt(52)

    # Rolling z-scores on selected macro-financial variables
    z_candidates = [
        _find_first(cols, ["dxy"]),
        _find_first(cols, ["pmi", "manufact"]),
        _find_first(cols, ["pmi", "services"]),
        _find_first(cols, ["economic", "sentiment"]),
        _find_first(cols, ["consumer", "confidence"]),
        _find_first(cols, ["vix"]),
        _find_first(cols, ["vstoxx"]),
        _find_first(cols, ["move"]),
    ]
    for col in [c for c in z_candidates if c is not None]:
        f[f"z52_{col}"] = _rolling_zscore(pd.to_numeric(df[col], errors="coerce"), window=52, min_periods=26)

    for col in ["germany_10y_2y_slope", "peripheral_spread_avg", "hicp_headline_core_gap"]:
        if col in f.columns:
            f[f"z52_{col}"] = _rolling_zscore(f[col], window=52, min_periods=26)

    output = f.sort_index().dropna(how="all")
    feature_path = config.processed_dir / "regime_features_weekly.parquet"
    write_parquet(output, feature_path, logger)
    logger.info("Engineered regime features: rows=%d cols=%d", len(output), output.shape[1])
    return output
