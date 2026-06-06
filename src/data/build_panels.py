from __future__ import annotations

from typing import Any
import logging

import pandas as pd

from .config import PipelineConfig
from .transformations import (
    annualized_rate_to_weekly_return,
    compute_simple_returns,
    resample_weekly_last,
    weekly_ffill_from_low_frequency,
    write_parquet,
)


def _series_name(meta: dict[str, Any]) -> str:
    ticker = meta.get("ticker")
    if isinstance(ticker, str) and ticker.strip():
        return ticker.strip().replace(" ", "_")
    return str(meta.get("id", "unknown_series"))


def _record_to_level_series(record: dict[str, Any]) -> pd.Series:
    tidy = record.get("data", pd.DataFrame(columns=["date", "value"]))
    if tidy.empty:
        return pd.Series(dtype="float64")

    s = pd.Series(
        pd.to_numeric(tidy["value"], errors="coerce").values,
        index=pd.to_datetime(tidy["date"], errors="coerce"),
        name=_series_name(record.get("meta", {})),
    )
    s = s[~s.index.isna()].sort_index()
    s = s[~s.index.duplicated(keep="last")]
    return s


def build_investable_panels(
    cleaned_records: list[dict[str, Any]],
    config: PipelineConfig,
    logger: logging.Logger,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build weekly investable price and return panels.

    All return series are simple (arithmetic) returns so that portfolio
    return r_p = sum_i w_i * r_i is exact.  This ensures homogeneity with
    the EURIBOR cash return which is already a weekly simple return derived
    from the annualised rate.
    """

    prices: dict[str, pd.Series] = {}
    returns: dict[str, pd.Series] = {}

    for rec in cleaned_records:
        meta = rec.get("meta", {})
        if meta.get("category") != "investable_assets":
            continue
        if rec.get("errors"):
            logger.warning("Skipping investable series with errors: %s", meta.get("id"))
            continue

        s = _record_to_level_series(rec)
        if s.empty:
            logger.warning("Empty investable series after cleaning: %s", meta.get("id"))
            continue

        name = _series_name(meta)
        subcategory = str(meta.get("subcategory", "")).lower()

        weekly_level = resample_weekly_last(s, weekly_frequency=config.weekly_frequency)

        if subcategory == "cash":
            # EURIBOR: convert annualised rate → weekly simple return
            weekly_ret = annualized_rate_to_weekly_return(weekly_level)
            weekly_price = (1.0 + weekly_ret.fillna(0.0)).cumprod()
            prices[name] = weekly_price
            returns[name] = weekly_ret
            continue

        # All risky assets: simple (pct_change) returns — homogeneous with cash
        weekly_ret = compute_simple_returns(weekly_level)
        prices[name] = weekly_level
        returns[name] = weekly_ret

    if not prices:
        raise RuntimeError("Critical failure: no investable price series could be built.")

    prices_df = pd.DataFrame(prices).sort_index()
    returns_df = pd.DataFrame(returns).sort_index()

    prices_df = prices_df.dropna(how="all")
    returns_df = returns_df.dropna(how="all")

    prices_path = config.processed_dir / "investable_prices_weekly.parquet"
    returns_path = config.processed_dir / "investable_returns_weekly.parquet"

    write_parquet(prices_df, prices_path, logger)
    write_parquet(returns_df, returns_path, logger)

    return prices_df, returns_df


def build_regime_panel(
    cleaned_records: list[dict[str, Any]],
    series_report: pd.DataFrame,
    config: PipelineConfig,
    logger: logging.Logger,
) -> pd.DataFrame:
    """Build weekly regime variable panel with frequency-aware alignment."""

    if series_report.empty:
        raise RuntimeError("Critical failure: series report is empty, cannot build regime panel.")

    by_id = {
        str(row["id"]): row for _, row in series_report[["id", "inferred_frequency"]].iterrows()
    }

    panel: dict[str, pd.Series] = {}
    for rec in cleaned_records:
        meta = rec.get("meta", {})
        if meta.get("category") != "regime_variables":
            continue
        if rec.get("errors"):
            logger.warning("Skipping regime series with errors: %s", meta.get("id"))
            continue

        s = _record_to_level_series(rec)
        if s.empty:
            logger.warning("Empty regime series after cleaning: %s", meta.get("id"))
            continue

        name = _series_name(meta)
        expected_freq = str(meta.get("freq", "unknown")).lower()
        inferred_freq = str(by_id.get(str(meta.get("id")), {}).get("inferred_frequency", "unknown")).lower()

        low_freq = expected_freq in {"monthly", "quarterly", "yearly"} or inferred_freq in {
            "monthly",
            "quarterly",
            "yearly",
        }

        if low_freq:
            aligned = weekly_ffill_from_low_frequency(s, weekly_frequency=config.weekly_frequency)
        else:
            aligned = resample_weekly_last(s, weekly_frequency=config.weekly_frequency)

        panel[name] = aligned

    if not panel:
        raise RuntimeError("Critical failure: no regime variable series could be built.")

    regime_df = pd.DataFrame(panel).sort_index().dropna(how="all")
    regime_path = config.processed_dir / "regime_variables_weekly.parquet"
    write_parquet(regime_df, regime_path, logger)
    return regime_df
