from __future__ import annotations

from typing import Any, cast
import logging

import numpy as np
import pandas as pd

from .config import PipelineConfig


def infer_frequency(date_series: pd.Series) -> tuple[str, float]:
    """Infer frequency label from median day step."""

    ds = pd.to_datetime(date_series, errors="coerce").dropna().sort_values().drop_duplicates()
    if len(ds) < 3:
        return "unknown", float("nan")

    steps = ds.diff().dropna().dt.days
    if steps.empty:
        return "unknown", float("nan")

    median_days = float(steps.median())
    if median_days <= 2:
        return "daily", median_days
    if median_days <= 10:
        return "weekly", median_days
    if median_days <= 35:
        return "monthly", median_days
    if median_days <= 110:
        return "quarterly", median_days
    return "yearly", median_days


def minimum_required_obs(freq_label: str, config: PipelineConfig) -> int:
    """Minimum sample size thresholds by inferred/expected frequency."""

    key = str(freq_label).lower()
    return int(config.min_obs_by_freq.get(key, config.min_obs_by_freq["unknown"]))


def detect_outliers(values: pd.Series, threshold: float = 6.0) -> tuple[pd.Series, str]:
    """Detect suspicious outliers using robust z-scores on changes."""

    s = pd.to_numeric(values, errors="coerce")
    valid = s.dropna()
    if len(valid) < 20:
        return pd.Series(False, index=s.index), "insufficient_data"

    base = valid.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
    method = "pct_change"
    if len(base) < 20 or float(base.abs().sum()) == 0.0:
        base = valid.diff().dropna()
        method = "diff"

    if len(base) < 20:
        return pd.Series(False, index=s.index), "insufficient_data"

    med = float(base.median())
    mad = float((base - med).abs().median())
    if mad == 0 or np.isnan(mad):
        return pd.Series(False, index=s.index), "zero_mad"

    robust_z = 0.6745 * (base - med) / mad
    flags_base = robust_z.abs() > threshold

    flags = pd.Series(False, index=s.index)
    flags.loc[flags_base.index] = flags_base
    return flags, method


def _frequency_inconsistent(expected: str | None, inferred: str) -> bool:
    if expected is None or expected == "" or expected == "unknown" or inferred == "unknown":
        return False
    expected = expected.lower()
    inferred = inferred.lower()

    if expected == inferred:
        return False

    # Allow daily expected series to infer weekly when sparse in source.
    if expected == "daily" and inferred == "weekly":
        return False

    return True


def validate_series_collection(
    cleaned_records: list[dict[str, Any]],
    config: PipelineConfig,
    logger: logging.Logger,
) -> dict[str, pd.DataFrame]:
    """Validate cleaned series and build core validation tables."""

    series_rows: list[dict[str, Any]] = []
    outlier_rows: list[dict[str, Any]] = []

    for rec in cleaned_records:
        meta = rec.get("meta", {})
        series_id = meta.get("id")
        tidy = rec.get("data", pd.DataFrame(columns=["date", "value"]))

        errors = list(rec.get("errors", []))
        warnings = list(rec.get("warnings", []))

        expected_freq = str(meta.get("freq", "unknown")).lower() if pd.notna(meta.get("freq")) else "unknown"
        inferred_freq = "unknown"
        median_step_days = float("nan")

        n_obs = int(len(tidy))

        value_series = cast(pd.Series, pd.to_numeric(tidy.get("value", pd.Series(dtype=float)), errors="coerce"))
        missing_count = int(cast(float, value_series.isna().sum())) if n_obs else 0
        missing_pct = float(missing_count / n_obs) if n_obs else 1.0

        date_series = cast(pd.Series, pd.to_datetime(tidy.get("date", pd.Series(dtype=object)), errors="coerce"))
        start_date = cast(pd.Timestamp, date_series.min()) if n_obs else pd.NaT
        end_date = cast(pd.Timestamp, date_series.max()) if n_obs else pd.NaT

        outlier_count = 0
        outlier_method = "none"

        if n_obs > 0:
            inferred_freq, median_step_days = infer_frequency(tidy["date"])
            flags, outlier_method = detect_outliers(tidy["value"], threshold=config.outlier_z_threshold)
            outlier_count = int(flags.sum())

            if outlier_count > 0:
                outlier_points = tidy.loc[flags, ["date", "value"]].copy()
                for _, row in outlier_points.iterrows():
                    outlier_rows.append(
                        {
                            "id": series_id,
                            "path": meta.get("relative_path"),
                            "date": row["date"],
                            "value": row["value"],
                            "method": outlier_method,
                        }
                    )

        freq_inconsistent = _frequency_inconsistent(expected_freq, inferred_freq)
        if freq_inconsistent:
            warnings.append("frequency_inconsistent")

        min_required = minimum_required_obs(expected_freq if expected_freq != "unknown" else inferred_freq, config)
        short_series = n_obs < min_required
        if short_series:
            warnings.append("short_series")

        if rec.get("non_numeric_columns"):
            warnings.append("non_numeric_columns_detected")

        if missing_pct > config.max_missing_ratio_warning:
            warnings.append("missing_ratio_above_threshold")

        row: dict[str, Any] = {
            "id": series_id,
            "path": meta.get("relative_path"),
            "category": meta.get("category"),
            "subcategory": meta.get("subcategory"),
            "ticker": meta.get("ticker"),
            "status": meta.get("status"),
            "sheet_expected": meta.get("sheet"),
            "sheet_used": rec.get("sheet_used") or meta.get("sheet"),
            "selected_date_column": rec.get("selected_date_column"),
            "selected_value_column": rec.get("selected_value_column"),
            "n_obs": n_obs,
            "start_date": start_date,
            "end_date": end_date,
            "missing_count": missing_count,
            "missing_pct": missing_pct,
            "duplicate_dates_removed": int(rec.get("duplicate_dates_removed", 0)),
            "outlier_count": outlier_count,
            "outlier_method": outlier_method,
            "expected_frequency": expected_freq,
            "inferred_frequency": inferred_freq,
            "median_step_days": median_step_days,
            "frequency_inconsistent": freq_inconsistent,
            "short_series": short_series,
            "non_numeric_columns": "; ".join(rec.get("non_numeric_columns", [])),
            "warnings": "; ".join(sorted(set(warnings))),
            "errors": "; ".join(errors),
            "transformations_applied": "; ".join(rec.get("transformations", [])),
            "critical_ok": len(errors) == 0,
        }
        series_rows.append(row)

    series_report = pd.DataFrame(series_rows)
    if series_report.empty:
        raise RuntimeError("Validation failed: no series were processed.")

    missing_values_report = series_report[
        [
            "id",
            "path",
            "selected_value_column",
            "n_obs",
            "missing_count",
            "missing_pct",
            "warnings",
            "errors",
        ]
    ].sort_values(["missing_pct", "id"], ascending=[False, True])

    series_coverage_report = series_report[
        [
            "id",
            "path",
            "category",
            "subcategory",
            "start_date",
            "end_date",
            "n_obs",
            "short_series",
            "critical_ok",
            "warnings",
        ]
    ].sort_values(["category", "subcategory", "id"])

    frequency_report = series_report[
        [
            "id",
            "path",
            "expected_frequency",
            "inferred_frequency",
            "median_step_days",
            "frequency_inconsistent",
            "warnings",
        ]
    ].sort_values(["frequency_inconsistent", "id"], ascending=[False, True])

    outlier_report = pd.DataFrame(outlier_rows)
    if outlier_report.empty:
        outlier_report = pd.DataFrame(columns=["id", "path", "date", "value", "method"])

    logger.info(
        "Validation complete: total=%s critical_ok=%s with_errors=%s",
        len(series_report),
        int(series_report["critical_ok"].sum()),
        int((~series_report["critical_ok"]).sum()),
    )

    return {
        "series_report": series_report,
        "missing_values_report": missing_values_report,
        "series_coverage_report": series_coverage_report,
        "frequency_report": frequency_report,
        "outlier_report": outlier_report,
    }
