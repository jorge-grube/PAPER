from __future__ import annotations

from pathlib import Path
import importlib.util
import logging

import numpy as np
import pandas as pd


def ensure_datetime_index(series: pd.Series) -> pd.Series:
    """Return a series with a clean datetime index and deduplicated timestamps."""

    s = series.copy()
    s.index = pd.to_datetime(s.index, errors="coerce")
    s = s[~s.index.isna()]
    s = s.sort_index()
    s = s[~s.index.duplicated(keep="last")]
    return s


def resample_weekly_last(series: pd.Series, weekly_frequency: str = "W-FRI") -> pd.Series:
    """Weekly last-observation resampling for market series."""

    s = ensure_datetime_index(series)
    return s.resample(weekly_frequency).last()


def weekly_ffill_from_low_frequency(series: pd.Series, weekly_frequency: str = "W-FRI") -> pd.Series:
    """Weekly alignment for low-frequency macro variables using forward fill only."""

    s = ensure_datetime_index(series)
    return s.resample(weekly_frequency).last().ffill()


def compute_log_returns(level_series: pd.Series) -> pd.Series:
    """Compute log-returns from positive level series.

    DEPRECATED for investable returns panel — use compute_simple_returns instead
    to ensure homogeneous arithmetic with cash (EURIBOR) simple returns.
    Retained for regime feature engineering where log-differences are appropriate.
    """

    s = pd.to_numeric(level_series, errors="coerce")
    s = s.where(s > 0)
    return np.log(s).diff()


def compute_simple_returns(level_series: pd.Series) -> pd.Series:
    """Compute simple (arithmetic) returns from positive level series.

    Use this for the investable returns panel to ensure portfolio arithmetic
    r_p = sum_i w_i * r_i is exact (no Jensen's-inequality approximation).
    Matches the return type of annualized_rate_to_weekly_return (EURIBOR cash).
    """

    s = pd.to_numeric(level_series, errors="coerce")
    s = s.where(s > 0)
    return s.pct_change()


def annualized_rate_to_weekly_return(rate_series: pd.Series) -> pd.Series:
    """Convert annualized short rate into weekly simple return."""

    r = pd.to_numeric(rate_series, errors="coerce")
    median = r.dropna().median() if r.notna().any() else np.nan
    if pd.notna(median) and median > 1.0:
        r = r / 100.0
    return (1.0 + r).pow(1.0 / 52.0) - 1.0


def assert_parquet_engine_available() -> None:
    """Fail loudly when parquet dependencies are not available."""

    has_pyarrow = importlib.util.find_spec("pyarrow") is not None
    has_fastparquet = importlib.util.find_spec("fastparquet") is not None
    if not has_pyarrow and not has_fastparquet:
        raise RuntimeError(
            "No parquet engine found. Install pyarrow or fastparquet to write parquet outputs."
        )


def write_parquet(df: pd.DataFrame, output_path: Path, logger: logging.Logger) -> None:
    """Write dataframe to parquet with explicit safety checks."""

    assert_parquet_engine_available()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path)
    logger.info("Wrote parquet: %s (rows=%s cols=%s)", output_path, len(df), df.shape[1])
