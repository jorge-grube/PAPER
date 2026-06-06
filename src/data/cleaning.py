from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
import logging
import re
import warnings as _warnings

import numpy as np
import pandas as pd


DATE_NAME_PATTERN = re.compile(r"date|period|time", re.IGNORECASE)
VALUE_NAME_PATTERN = re.compile(
    r"close|price|value|yield|rate|index|fixing|actual|trade|last|level", re.IGNORECASE
)


def parse_datetime_value(value: Any) -> pd.Timestamp | pd.NaT:
    """Parse mixed date representations into pandas Timestamp."""

    if value is None or (isinstance(value, float) and np.isnan(value)):
        return pd.NaT

    if isinstance(value, pd.Timestamp):
        return value

    if isinstance(value, datetime):
        return pd.Timestamp(value)

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        as_float = float(value)
        if 1000 < as_float < 80000 and abs(as_float - round(as_float)) < 1e-9:
            dt = pd.to_datetime(as_float, unit="D", origin="1899-12-30", errors="coerce")
            if pd.notna(dt) and 1900 <= dt.year <= 2100:
                return dt

    txt = str(value).strip()
    if txt == "" or txt.lower() in {"nan", "none", "null"}:
        return pd.NaT

    dt = pd.to_datetime(txt, errors="coerce", dayfirst=True)
    if pd.notna(dt) and 1900 <= dt.year <= 2100:
        return dt

    dt2 = pd.to_datetime(txt, errors="coerce", dayfirst=False)
    if pd.notna(dt2) and 1900 <= dt2.year <= 2100:
        return dt2
    return pd.NaT


_SLASH_DATE_RE = re.compile(r"^(\d{1,2})/(\d{1,2})/\d{2,4}$")
_QUARTER_DATE_RE = re.compile(r"^Q([1-4])\s+(\d{4})$")
_QUARTER_MONTH_END = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}


def _infer_dayfirst(series: pd.Series) -> bool:
    """Infer whether dates in a string series use DD/MM (dayfirst=True) or
    MM/DD (dayfirst=False) ordering by sampling up to 300 values.

    Logic:
    - If ≥1 value has a *first* component > 12, it must be DD/MM → True.
    - If ≥1 value has a *second* component > 12, it must be MM/DD → False.
    - Majority vote when both signals are present.
    - Default: True (European convention used by LSEG for most series).

    Rationale: pandas ≥2.0 does NOT fall back for ambiguous slash dates when
    dayfirst=True — "01/15/1990" with dayfirst=True gives NaT (month 15
    is invalid and no retry occurs).  Auto-detecting the format prevents
    ~60% loss of VIX data and any other US-format series.
    """
    first_gt12 = 0   # first component >12  →  day is first  (DD/MM/YYYY)
    second_gt12 = 0  # second component >12 →  month is first (MM/DD/YYYY)
    for val in series.dropna().head(300):
        m = _SLASH_DATE_RE.match(str(val).strip())
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if a > 12:
                first_gt12 += 1
            if b > 12:
                second_gt12 += 1
    # Unambiguous signals
    if second_gt12 > 0 and first_gt12 == 0:
        return False  # MM/DD/YYYY confirmed
    if first_gt12 > 0 and second_gt12 == 0:
        return True   # DD/MM/YYYY confirmed
    # Both signals present — majority vote; tie → dayfirst=True (European)
    return first_gt12 >= second_gt12


def _fast_parse_dates(series: pd.Series) -> pd.Series:
    """Vectorized date parsing for column-detection scoring.

    ~50x faster than element-wise parse_datetime_value.  Handles:
    - datetime64 columns (passthrough)
    - Excel serial integers in range 1 000–80 000 (detected BEFORE generic
      pd.to_datetime so that e.g. 36526 → 2000-01-03, not 1970-01-01)
    - String / object dates with automatic DD/MM vs MM/DD detection
      (pandas ≥2.0 does not fall back on ambiguous dayfirst= strings)
    Results are clipped to 1900-2100; out-of-range values become NaT.
    """
    if pd.api.types.is_datetime64_any_dtype(series):
        result = series.copy()
        valid_year = result.notna() & (result.dt.year >= 1900) & (result.dt.year <= 2100)
        return result.where(valid_year, other=pd.NaT)

    # ── Excel serial integer detection ───────────────────────────────────────
    # Must happen BEFORE generic pd.to_datetime: pd.to_datetime(36526) returns
    # 1970-01-01 (ns from epoch) which is wrong; we want days from 1899-12-30.
    numeric_check = pd.to_numeric(series, errors="coerce")
    non_null = int(series.notna().sum())
    excel_candidates = (
        numeric_check.notna()
        & (numeric_check > 1000)
        & (numeric_check < 80000)
        & ((numeric_check - numeric_check.round()).abs() < 1e-9)
    )
    excel_ratio = float(excel_candidates.sum()) / non_null if non_null > 0 else 0.0

    if excel_ratio >= 0.50:
        # Majority of non-null values look like Excel serial dates
        result = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
        excel_dates = pd.to_datetime(
            numeric_check.where(excel_candidates),
            unit="D", origin="1899-12-30", errors="coerce",
        )
        result.update(excel_dates)
        valid_year = result.notna() & (result.dt.year >= 1900) & (result.dt.year <= 2100)
        return result.where(valid_year, other=pd.NaT)

    # ── String / mixed path ──────────────────────────────────────────────────
    # Suppress integers that are clearly NOT Excel serial dates (range 1–80 000).
    # pd.to_datetime(79_609_782) would produce 1970-01-01 00:00:00.079... which
    # passes all plausibility checks and contaminates column selection.
    non_excel_num = numeric_check.notna() & (
        (numeric_check <= 1000) | (numeric_check >= 80000)
    )
    if non_excel_num.any():
        series_clean = series.copy().astype(object)
        series_clean[non_excel_num] = None
    else:
        series_clean = series

    # Auto-detect MM/DD vs DD/MM ordering to avoid pandas ≥2.0 NaT on mismatch
    dayfirst = _infer_dayfirst(series_clean)

    with _warnings.catch_warnings():
        _warnings.simplefilter("ignore")
        result = pd.to_datetime(series_clean, errors="coerce", dayfirst=dayfirst)

    # If first attempt produces high NaT rate, retry with opposite dayfirst.
    # Handles edge cases where all sampled values were ambiguous (both components ≤12).
    non_null_mask = series.notna()
    if non_null_mask.any():
        nat_rate = float(result[non_null_mask].isna().sum()) / float(non_null_mask.sum())
        if nat_rate > 0.40:
            with _warnings.catch_warnings():
                _warnings.simplefilter("ignore")
                result2 = pd.to_datetime(series_clean, errors="coerce", dayfirst=not dayfirst)
            nat_rate2 = float(result2[non_null_mask].isna().sum()) / float(non_null_mask.sum())
            if nat_rate2 < nat_rate:
                result = result2

    # Fallback: quarter-year strings  "Q4 2025" → 2025-12-31
    # pd.to_datetime cannot parse this format natively; handle before Excel fallback.
    failed_mask = result.isna() & series.notna()
    if failed_mask.any():
        quarter_dates = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
        for idx in series[failed_mask].index:
            raw = str(series.at[idx]).strip()
            m = _QUARTER_DATE_RE.match(raw)
            if m:
                q, yr = int(m.group(1)), int(m.group(2))
                mo, dy = _QUARTER_MONTH_END[q]
                try:
                    quarter_dates.at[idx] = pd.Timestamp(yr, mo, dy)
                except Exception:
                    pass
        filled = quarter_dates.notna()
        if filled.any():
            result = result.copy()
            result.update(quarter_dates[filled])
        failed_mask = result.isna() & series.notna()

    # Fallback: remaining NaT values that look like Excel serial integers
    if failed_mask.any() and excel_candidates.any():
        overlap = failed_mask & excel_candidates
        if overlap.any():
            excel_dates = pd.to_datetime(
                numeric_check[overlap], unit="D", origin="1899-12-30", errors="coerce"
            )
            result = result.copy()
            result.update(excel_dates)

    valid_year = result.notna() & (result.dt.year >= 1900) & (result.dt.year <= 2100)
    return result.where(valid_year, other=pd.NaT)


def parse_euro_number(value: Any) -> float:
    """Parse numeric values handling European and mixed locale conventions."""

    if value is None:
        return np.nan

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if pd.isna(value):
            return np.nan
        return float(value)

    txt = str(value).strip()
    if txt == "" or txt.lower() in {"nan", "none", "null", "n/a", "na", "expected soon"}:
        return np.nan

    negative = txt.startswith("(") and txt.endswith(")")
    if negative:
        txt = txt[1:-1]

    is_percent = "%" in txt
    txt = txt.replace("%", "")

    txt = txt.replace(" ", " ").replace(" ", "")
    txt = txt.replace("EUR", "").replace("USD", "").replace("GBP", "")

    txt = re.sub(r"[^0-9,\.\-eE+]", "", txt)
    if txt in {"", ".", ",", "-"}:
        return np.nan

    if "," in txt and "." in txt:
        if txt.rfind(",") > txt.rfind("."):
            txt = txt.replace(".", "")
            txt = txt.replace(",", ".")
        else:
            txt = txt.replace(",", "")
    elif "," in txt:
        chunks = txt.split(",")
        if len(chunks) > 1 and all(len(c) == 3 for c in chunks[1:]):
            txt = "".join(chunks)
        else:
            txt = txt.replace(",", ".")

    try:
        val = float(txt)
    except ValueError:
        return np.nan

    if negative:
        val = -val
    if is_percent:
        val = val / 100.0
    return val


def _fast_numeric_series(series: pd.Series) -> pd.Series:
    """Fast numeric coercion for column-detection scoring.

    Uses pd.to_numeric (vectorized) first; falls back to the full
    parse_euro_number only for columns where the fast path yields < 10%
    valid values (covers European-format and percentage-heavy series).
    """
    numeric = pd.to_numeric(series, errors="coerce")
    non_null = int(series.notna().sum())
    if non_null == 0:
        return numeric
    fast_ratio = float(numeric.notna().sum()) / non_null
    if fast_ratio >= 0.10:
        return numeric
    # Slow fallback for European-format columns
    return series.map(parse_euro_number)


def _make_unique(names: list[str]) -> list[str]:
    """Ensure column names are unique after normalization."""

    seen: dict[str, int] = {}
    out: list[str] = []
    for name in names:
        base = str(name).strip() or "col"
        count = seen.get(base, 0)
        if count == 0:
            out.append(base)
        else:
            out.append(f"{base}_{count}")
        seen[base] = count + 1
    return out


def prepare_working_frame(
    raw_df: pd.DataFrame,
    source_ext: str,
    header_row: Any,
    data_start_row: Any,
) -> tuple[pd.DataFrame, list[str]]:
    """Prepare a working dataframe from raw file content."""

    df = raw_df.copy()
    transformations: list[str] = []

    if source_ext in {".xlsx", ".xls"}:
        header_idx = None
        if pd.notna(header_row):
            try:
                header_idx = int(float(header_row)) - 1
            except Exception:
                header_idx = None

        if header_idx is not None and 0 <= header_idx < len(df):
            header_vals = ["" if pd.isna(v) else str(v).strip() for v in df.iloc[header_idx].tolist()]
            header_vals = [v if v else f"col_{i}" for i, v in enumerate(header_vals)]
            df.columns = _make_unique(header_vals)
            transformations.append(f"applied_header_row={header_idx + 1}")
        else:
            df.columns = [f"col_{i}" for i in range(df.shape[1])]
            transformations.append("applied_generic_headers")

        start_idx = 0
        if pd.notna(data_start_row):
            try:
                start_idx = max(0, int(float(data_start_row)) - 1)
            except Exception:
                start_idx = 0
        elif header_idx is not None:
            start_idx = header_idx + 1

        if start_idx > 0:
            df = df.iloc[start_idx:]
            transformations.append(f"trimmed_from_row={start_idx + 1}")

    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
    df = df.reset_index(drop=True)
    df.columns = [str(c).strip() for c in df.columns]
    return df, transformations


def detect_date_column(df: pd.DataFrame) -> tuple[str | None, pd.Series, dict[str, Any]]:
    """Detect the most likely date column in a dataframe."""

    best_col: str | None = None
    best_parsed = pd.Series(dtype="datetime64[ns]")
    best_score = -1.0
    best_stats: dict[str, Any] = {"valid_dates": 0, "ratio": 0.0}

    for col in df.columns:
        series = df[col]
        # Vectorized fast path — ~50x faster than element-wise map
        parsed = _fast_parse_dates(series)
        valid = int(parsed.notna().sum())
        non_null = int(series.notna().sum())
        ratio = valid / non_null if non_null > 0 else 0.0

        if valid == 0:
            continue

        parsed_clean = parsed.dropna()
        parsed_unique = parsed_clean.drop_duplicates()
        unique_ratio = float(len(parsed_unique) / valid) if valid > 0 else 0.0
        in_plausible_range = parsed_clean[
            (parsed_clean >= pd.Timestamp("1950-01-01"))
            & (parsed_clean <= pd.Timestamp.today() + pd.Timedelta(days=370))
        ]
        plausible_ratio = float(len(in_plausible_range) / valid) if valid > 0 else 0.0

        # Require the date series to span at least 30 calendar days.
        # A column of integers mis-parsed as nanosecond timestamps all land on
        # 1970-01-01 (span = 0 days) and would otherwise score perfectly.
        date_span_days = int((parsed_clean.max() - parsed_clean.min()).days)
        if date_span_days < 30:
            continue

        chrono_score = 0.0
        if len(parsed_clean) >= 5:
            ordered = parsed_clean.reset_index(drop=True)
            diffs = ordered.diff().dropna().dt.days
            if len(diffs) > 0:
                asc_ratio = float((diffs >= 0).mean())
                desc_ratio = float((diffs <= 0).mean())
                chrono_score = max(asc_ratio, desc_ratio)

        bonus = 0.25 if DATE_NAME_PATTERN.search(str(col)) else 0.0
        score = ratio + bonus + min(valid / 10000.0, 0.25)
        score += 0.20 * plausible_ratio
        score += 0.20 * unique_ratio
        score += 0.20 * chrono_score

        if score > best_score:
            best_score = score
            best_col = str(col)
            best_parsed = parsed
            best_stats = {
                "valid_dates": valid,
                "non_null": non_null,
                "ratio": ratio,
                "unique_ratio": unique_ratio,
                "plausible_ratio": plausible_ratio,
                "chronology_ratio": chrono_score,
            }

    if best_col is None:
        return None, pd.Series(dtype="datetime64[ns]"), {"valid_dates": 0, "ratio": 0.0}

    if (
        best_stats["valid_dates"] < 3
        or best_stats["ratio"] < 0.10
        or float(best_stats.get("plausible_ratio", 0.0)) < 0.60
        or float(best_stats.get("chronology_ratio", 0.0)) < 0.60
    ):
        return None, pd.Series(dtype="datetime64[ns]"), best_stats

    return best_col, best_parsed, best_stats


def detect_value_column(
    df: pd.DataFrame,
    date_col: str | None,
    data_rows_df: pd.DataFrame | None = None,
) -> tuple[str | None, pd.Series, dict[str, Any]]:
    """Detect the most likely value column in a dataframe.

    Parameters
    ----------
    df:
        Full working dataframe (used for column enumeration and final value extraction).
    date_col:
        Name of the already-detected date column (excluded from scoring).
    data_rows_df:
        Optional subset of ``df`` restricted to rows that contain valid dates.
        When provided, scoring is done only on these rows so that header/stats
        sections (e.g. LSEG VAP histograms) do not contaminate the detection.
        The returned value Series is still aligned to ``df``'s index.
    """

    scoring_df = data_rows_df if data_rows_df is not None and not data_rows_df.empty else df

    col_names = list(df.columns)
    best_col: str | None = None
    best_score = -1.0
    best_stats: dict[str, Any] = {"valid_numeric": 0, "ratio": 0.0}

    for col in col_names:
        if date_col is not None and str(col) == str(date_col):
            continue

        series = scoring_df[col]
        # Fast vectorized numeric coercion for scoring
        numeric = _fast_numeric_series(series)
        valid = int(numeric.notna().sum())
        non_null = int(series.notna().sum())
        ratio = valid / non_null if non_null > 0 else 0.0

        if valid < 3:
            continue

        std = float(numeric.dropna().std()) if valid > 1 else 0.0
        name_bonus = 0.30 if VALUE_NAME_PATTERN.search(str(col)) else 0.0
        col_order_penalty = col_names.index(str(col)) * 0.001
        # Use completeness (valid / total rows) as the primary signal so that
        # sparse columns with high quality do not beat dense columns via name bonus.
        # e.g. MOVE: Close has 5796/5796=1.0 vs PriceChange 1621/5796=0.28 + 0.3 bonus
        n_total = max(len(scoring_df), 1)
        completeness = valid / n_total
        score = completeness + name_bonus + min(valid / 2000.0, 0.5) - col_order_penalty
        if std > 0:
            score += 0.05

        if score > best_score:
            best_score = score
            best_col = str(col)
            best_stats = {
                "valid_numeric": valid,
                "non_null": non_null,
                "ratio": ratio,
                "std": std,
            }

    if best_col is None:
        return None, pd.Series(dtype="float64"), {"valid_numeric": 0, "ratio": 0.0}

    if best_stats["valid_numeric"] < 3 or best_stats["ratio"] < 0.10:
        return None, pd.Series(dtype="float64"), best_stats

    # Extract values from the *full* df using the precise parser for correctness
    best_values = df[best_col].map(parse_euro_number)
    return best_col, best_values, best_stats


def profile_non_numeric_columns(df: pd.DataFrame, date_col: str | None) -> list[str]:
    """List non-date columns with very low numeric parse ratio."""

    bad_cols: list[str] = []
    for col in df.columns:
        if date_col is not None and str(col) == str(date_col):
            continue
        series = df[col]
        non_null = int(series.notna().sum())
        if non_null == 0:
            continue
        ratio = float(series.map(parse_euro_number).notna().sum() / non_null)
        if ratio < 0.10:
            bad_cols.append(str(col))
    return bad_cols


def clean_single_payload(payload: dict[str, Any], logger: logging.Logger) -> dict[str, Any]:
    """Clean one raw payload into a date-value tidy series plus diagnostics."""

    meta = dict(payload.get("meta", {}))
    source_ext = str(meta.get("file_ext", "")).lower()

    result: dict[str, Any] = {
        "meta": meta,
        "sheet_used": payload.get("sheet_used"),
        "available_sheets": payload.get("available_sheets"),
        "data": pd.DataFrame(columns=["date", "value"]),
        "selected_date_column": None,
        "selected_value_column": None,
        "date_column_stats": {},
        "value_column_stats": {},
        "non_numeric_columns": [],
        "duplicate_dates_removed": 0,
        "transformations": [],
        "warnings": [],
        "errors": [],
    }

    if payload.get("error"):
        result["errors"].append(f"load_error: {payload['error']}")
        return result

    raw_df = payload.get("raw_df")
    if raw_df is None or not isinstance(raw_df, pd.DataFrame) or raw_df.empty:
        result["errors"].append("empty_raw_frame")
        return result

    df, transformations = prepare_working_frame(
        raw_df=raw_df,
        source_ext=source_ext,
        header_row=meta.get("header_row"),
        data_start_row=meta.get("data_start_row"),
    )
    result["transformations"].extend(transformations)

    if df.empty:
        result["errors"].append("empty_after_trim")
        return result

    date_col, date_parsed, date_stats = detect_date_column(df)
    result["selected_date_column"] = date_col
    result["date_column_stats"] = date_stats

    if date_col is None:
        result["errors"].append("date_column_not_found")
        return result

    # Restrict value-column scoring to rows that actually contain valid dates.
    # This prevents LSEG VAP histograms, summary statistics, and other header
    # sections that appear before or after the time-series from biasing detection
    # toward volume or non-price columns.
    data_mask = date_parsed.notna()
    df_data_only = df[data_mask] if data_mask.any() else df

    # Support an explicit override from inventory metadata (0-indexed column position).

    # Inventory override: if metadata specifies a 0-indexed column position,
    # use it directly instead of running column detection.
    inventory_value_col: int | None = None
    raw_vc = meta.get("value_col")
    if raw_vc is not None:
        try:
            inventory_value_col = int(float(raw_vc))
        except (TypeError, ValueError):
            inventory_value_col = None

    if inventory_value_col is not None and 0 <= inventory_value_col < len(df.columns):
        value_col = str(df.columns[inventory_value_col])
        values = df[value_col].map(parse_euro_number)
        value_stats: dict[str, Any] = {
            "valid_numeric": int(values.notna().sum()),
            "ratio": float(values.notna().sum() / max(df[value_col].notna().sum(), 1)),
            "source": "inventory_override",
        }
        result["transformations"].append(f"value_col_override_col_idx={inventory_value_col}")
    else:
        value_col, values, value_stats = detect_value_column(
            df, date_col, data_rows_df=df_data_only,
        )

    result["selected_value_column"] = value_col
    result["value_column_stats"] = value_stats

    if value_col is None:
        result["errors"].append("value_column_not_found")
        return result

    result["non_numeric_columns"] = profile_non_numeric_columns(df, date_col)

    # Build tidy date/value pairs restricted to rows with valid dates
    tidy = pd.DataFrame({
        "date": date_parsed[data_mask].values,
        "value": values[data_mask].values,
    })
    tidy = tidy.dropna(subset=["date"])
    tidy["date"] = pd.to_datetime(tidy["date"])
    tidy = tidy.sort_values("date").reset_index(drop=True)

    # Remove duplicate dates — keep last (LSEG convention for revised data)
    n_before = len(tidy)
    tidy = tidy.drop_duplicates(subset=["date"], keep="last")
    result["duplicate_dates_removed"] = n_before - len(tidy)

    result["data"] = tidy
    return result


def clean_all_sources(
    raw_payloads: list[dict[str, Any]],
    logger: logging.Logger,
) -> list[dict[str, Any]]:
    """Run clean_single_payload over every raw payload; log summary on completion."""
    results: list[dict[str, Any]] = []
    n_ok = n_warn = n_err = 0

    for payload in raw_payloads:
        meta = payload.get("meta", {})
        series_id = meta.get("id", "unknown")
        try:
            rec = clean_single_payload(payload, logger)
        except Exception as exc:
            logger.error(
                "Unhandled exception cleaning %s: %s", series_id, exc, exc_info=True
            )
            rec = {
                "meta": meta,
                "data": pd.DataFrame(columns=["date", "value"]),
                "errors": [f"unhandled_exception: {exc}"],
                "warnings": [],
                "transformations": [],
            }

        errors = rec.get("errors", [])
        warnings = rec.get("warnings", [])
        n_rows = len(rec.get("data", pd.DataFrame()))

        if errors:
            n_err += 1
            logger.warning("%-40s  ERRORS=%s", series_id, errors)
        elif warnings:
            n_warn += 1
            logger.debug("%-40s  rows=%-6d  WARN=%s", series_id, n_rows, warnings)
        else:
            n_ok += 1
            logger.debug("%-40s  rows=%-6d  OK", series_id, n_rows)

        results.append(rec)

    logger.info(
        "Cleaning complete: %d OK  /  %d warn  /  %d error  (total %d)",
        n_ok, n_warn, n_err, len(results),
    )
    return results
