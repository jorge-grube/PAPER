from __future__ import annotations

from pathlib import Path
import logging
from typing import Any

import pandas as pd
import yaml

from .config import PipelineConfig


def _to_text_table(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df.empty:
        return "(no rows)"
    return df.head(max_rows).to_string(index=False)


def write_validation_reports(
    validation_bundle: dict[str, pd.DataFrame],
    config: PipelineConfig,
    logger: logging.Logger,
) -> None:
    """Write validation CSV reports and markdown summary."""

    series_report = validation_bundle["series_report"].copy()
    missing_report = validation_bundle["missing_values_report"].copy()
    coverage_report = validation_bundle["series_coverage_report"].copy()
    frequency_report = validation_bundle["frequency_report"].copy()
    outlier_report = validation_bundle["outlier_report"].copy()

    missing_path = config.reports_dir / "missing_values_report.csv"
    coverage_path = config.reports_dir / "series_coverage_report.csv"
    outlier_path = config.reports_dir / "outlier_report.csv"
    frequency_path = config.reports_dir / "frequency_report.csv"

    missing_report.to_csv(missing_path, index=False)
    coverage_report.to_csv(coverage_path, index=False)
    outlier_report.to_csv(outlier_path, index=False)
    frequency_report.to_csv(frequency_path, index=False)

    total_series = len(series_report)
    critical_ok = int(series_report["critical_ok"].sum())
    with_errors = int((~series_report["critical_ok"]).sum())

    mean_missing_pct = float(series_report["missing_pct"].mean()) if total_series else 0.0
    short_series_n = int(series_report["short_series"].sum()) if total_series else 0
    freq_inconsistent_n = int(series_report["frequency_inconsistent"].sum()) if total_series else 0

    snapshot = series_report.sort_values(["critical_ok", "missing_pct"], ascending=[True, False])[
        [
            "id",
            "start_date",
            "end_date",
            "missing_pct",
            "inferred_frequency",
            "selected_value_column",
            "warnings",
            "transformations_applied",
        ]
    ]

    summary_lines = [
        "# Data Validation Summary",
        "",
        "## Overview",
        f"- Total series analyzed: {total_series}",
        f"- Critical OK series: {critical_ok}",
        f"- Series with critical errors: {with_errors}",
        f"- Average missing percentage: {mean_missing_pct:.2%}",
        f"- Short series flagged: {short_series_n}",
        f"- Frequency inconsistencies flagged: {freq_inconsistent_n}",
        "",
        "## Output Files",
        f"- {missing_path.relative_to(config.project_root)}",
        f"- {coverage_path.relative_to(config.project_root)}",
        f"- {outlier_path.relative_to(config.project_root)}",
        f"- {frequency_path.relative_to(config.project_root)}",
        "",
        "## Series Snapshot",
        "",
        "```text",
        _to_text_table(snapshot, max_rows=25),
        "```",
    ]

    summary_path = config.reports_dir / "data_validation_summary.md"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
    logger.info("Wrote validation summary: %s", summary_path)


def write_final_dataset_summary(
    investable_prices: pd.DataFrame,
    investable_returns: pd.DataFrame,
    regime_panel: pd.DataFrame,
    regime_features: pd.DataFrame,
    series_report: pd.DataFrame,
    config: PipelineConfig,
    logger: logging.Logger,
) -> None:
    """Write final markdown summary for processed datasets."""

    def span(df: pd.DataFrame) -> tuple[str, str]:
        if df.empty:
            return "NA", "NA"
        idx = pd.to_datetime(df.index, errors="coerce")
        idx = idx[~idx.isna()]
        if len(idx) == 0:
            return "NA", "NA"
        return str(idx.min().date()), str(idx.max().date())

    p_start, p_end = span(investable_prices)
    r_start, r_end = span(investable_returns)
    g_start, g_end = span(regime_panel)
    f_start, f_end = span(regime_features)

    final_lines = [
        "# Final Dataset Summary",
        "",
        "## Processed Panels",
        f"- Investable weekly prices: rows={len(investable_prices)} cols={investable_prices.shape[1]} span={p_start} to {p_end}",
        f"- Investable weekly returns: rows={len(investable_returns)} cols={investable_returns.shape[1]} span={r_start} to {r_end}",
        f"- Regime variables weekly: rows={len(regime_panel)} cols={regime_panel.shape[1]} span={g_start} to {g_end}",
        f"- Regime features weekly: rows={len(regime_features)} cols={regime_features.shape[1]} span={f_start} to {f_end}",
        "",
        "## Data Quality Snapshot",
        f"- Total raw series: {len(series_report)}",
        f"- Critical errors: {int((~series_report['critical_ok']).sum())}",
        f"- Mean missing ratio: {float(series_report['missing_pct'].mean()):.2%}",
        f"- Mean outlier count: {float(series_report['outlier_count'].mean()):.2f}",
        "",
        "## Methodological Notes",
        "- Weekly alignment is anchored to Friday (W-FRI).",
        "- Weekly levels use last available observation inside each week.",
        "- Monthly/quarterly regime variables are aligned to weekly via forward fill only (no backfill).",
        "- Investable simple (arithmetic) returns are computed after weekly level resampling.",
        "- Cash (EURIBOR 3M) is converted from annualized rate to weekly simple return.",
        "- Sovereign spread features are engineered against Germany 10Y when available.",
    ]

    final_path = config.reports_dir / "final_dataset_summary.md"
    final_path.write_text("\n".join(final_lines), encoding="utf-8")
    logger.info("Wrote final dataset summary: %s", final_path)


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def _span_from_index(df: pd.DataFrame) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
    if df.empty:
        return None, None
    idx = pd.to_datetime(df.index, errors="coerce")
    idx = idx[~idx.isna()]
    if len(idx) == 0:
        return None, None
    return pd.Timestamp(idx.min()), pd.Timestamp(idx.max())


def _normalize_freq_label(freq: str) -> str:
    txt = str(freq or "").strip().lower()
    mapping = {
        "daily": "Daily",
        "weekly": "Weekly",
        "monthly": "Monthly",
        "quarterly": "Quarterly",
        "yearly": "Yearly",
        "annual": "Yearly",
        "unknown": "Unknown",
    }
    return mapping.get(txt, txt.title() if txt else "Unknown")


def _source_group_key(row: pd.Series) -> tuple[str, str]:
    return str(row.get("category", "unknown")), str(row.get("subcategory", "unknown"))


def write_dataset_metadata(
    catalog: pd.DataFrame,
    series_report: pd.DataFrame,
    investable_returns: pd.DataFrame,
    regime_panel: pd.DataFrame,
    config: PipelineConfig,
    logger: logging.Logger,
) -> Path:
    """Write publication-grade dataset metadata YAML using detected source-level diagnostics."""

    returns_cols = int(investable_returns.shape[1])
    regime_cols = int(regime_panel.shape[1])

    r_start, r_end = _span_from_index(investable_returns)
    g_start, g_end = _span_from_index(regime_panel)

    start_candidates = [d for d in [r_start, g_start] if d is not None]
    end_candidates = [d for d in [r_end, g_end] if d is not None]
    global_start = min(start_candidates) if start_candidates else None
    global_end = max(end_candidates) if end_candidates else None

    observations = int(min(len(investable_returns), len(regime_panel))) if not investable_returns.empty and not regime_panel.empty else int(max(len(investable_returns), len(regime_panel)))

    source_rows = catalog.copy()
    if not series_report.empty:
        source_rows = source_rows.merge(
            series_report[
                [
                    "id",
                    "path",
                    "selected_value_column",
                    "selected_date_column",
                    "start_date",
                    "end_date",
                    "n_obs",
                    "missing_count",
                    "missing_pct",
                    "inferred_frequency",
                    "warnings",
                    "errors",
                ]
            ],
            left_on="id",
            right_on="id",
            how="left",
        )

    data_sources: list[dict[str, Any]] = []
    if not source_rows.empty:
        for (cat, subcat), grp in source_rows.groupby(["category", "subcategory"], dropna=False):
            category_name = f"{cat}_{subcat}" if str(subcat) not in {"", "nan", "None"} else str(cat)
            variables: list[dict[str, Any]] = []
            for _, row in grp.sort_values("ticker").iterrows():
                freq_label = _normalize_freq_label(str(row.get("inferred_frequency") or row.get("freq") or "unknown"))
                var = {
                    "id": str(row.get("id", "unknown")),
                    "name": str(row.get("ticker") or row.get("id") or "unknown"),
                    "description": f"Detected value column: {str(row.get('selected_value_column') or 'unknown')}",
                    "path": str(row.get("relative_path") or row.get("path") or ""),
                    "frequency": freq_label,
                    "units": str(row.get("unit") or "level"),
                    "coverage": {
                        "start": str(pd.to_datetime(row.get("start_date"), errors="coerce").date()) if pd.notna(pd.to_datetime(row.get("start_date"), errors="coerce")) else "NA",
                        "end": str(pd.to_datetime(row.get("end_date"), errors="coerce").date()) if pd.notna(pd.to_datetime(row.get("end_date"), errors="coerce")) else "NA",
                        "observations": _safe_int(row.get("n_obs"), 0),
                    },
                    "quality": {
                        "missing_count": _safe_int(row.get("missing_count"), 0),
                        "missing_ratio": round(_safe_float(row.get("missing_pct"), 0.0), 6),
                        "warnings": str(row.get("warnings") or ""),
                        "errors": str(row.get("errors") or ""),
                    },
                }
                variables.append(var)

            data_sources.append(
                {
                    "category": category_name,
                    "provider": "Declared in source files; formal provider mapping pending curation",
                    "variables": variables,
                }
            )

    missing_original = int(series_report["missing_count"].sum()) if not series_report.empty else 0
    missing_final_returns = int(investable_returns.isna().sum().sum()) if not investable_returns.empty else 0
    missing_final_regime = int(regime_panel.isna().sum().sum()) if not regime_panel.empty else 0
    missing_final = missing_final_returns + missing_final_regime

    completeness = 1.0
    total_cells = int(investable_returns.size + regime_panel.size)
    if total_cells > 0:
        completeness = 1.0 - (missing_final / total_cells)

    metadata_payload: dict[str, Any] = {
        "dataset_info": {
            "name": "Multi-Asset Weekly Portfolio Dataset",
            "version": "3.0.0",
            "created": str(pd.Timestamp.today().date()),
            "period": {
                "start": str(global_start.date()) if global_start is not None else "NA",
                "end": str(global_end.date()) if global_end is not None else "NA",
                "frequency": "Weekly (W-FRI)",
                "observations": observations,
            },
            "dimensions": {
                "total_variables": int(returns_cols + regime_cols),
                "returns_variables": returns_cols,
                "regime_variables": regime_cols,
            },
        },
        "data_sources": data_sources,
        "transformations": {
            "1_numeric_cleaning": {
                "description": "Locale-robust numeric parsing for mixed European and US formats",
                "details": "Converts values such as 1.234,56 and 1,234.56 and strips currency/percent markers",
                "affected": "All source variables",
            },
            "2_simple_returns": {
                "description": "Weekly simple (arithmetic) return construction for investable non-cash assets",
                "formula": "P_t / P_t-1 - 1",
                "affected": "Investable assets except cash",
                "note": "compute_log_returns is retained in transformations.py for regime feature "
                        "engineering (log-differences of volatility indices) but is NOT used "
                        "for the investable portfolio return panels.",
            },
            "3_cash_rate_conversion": {
                "description": "Annualized short-rate converted to weekly simple return",
                "formula": "(1+r_annual)^(1/52)-1",
                "affected": "Cash assets",
            },
            "4_frequency_alignment": {
                "description": "Weekly alignment anchored to Friday close",
                "details": "Low-frequency macro series are forward-filled to weekly; no backward fill is used",
                "affected": "All variables",
            },
            "5_missing_values": {
                "description": "No statistical imputation at this stage",
                "details": "Missing values are kept explicit for exploratory analysis and later ETL policy selection",
                "affected": "All variables",
            },
        },
        "quality_metrics": {
            "completeness": round(completeness, 6),
            "frequency_consistency_issues": int(series_report["frequency_inconsistent"].sum()) if not series_report.empty else 0,
            "critical_errors": int((~series_report["critical_ok"]).sum()) if not series_report.empty else 0,
            "missing_values_original": missing_original,
            "missing_values_final": missing_final,
        },
        "usage_notes": [
            "Use investable weekly returns directly for portfolio optimization models.",
            "Keep macro and regime variables in levels for interpretability, then scale inside ML pipelines.",
            "No imputation is applied yet; missing values remain explicit by design.",
            "Weekly frequency reduces microstructure noise while preserving tactical regime information.",
        ],
        "citation": {
            "author": "Jorge Grube",
            "institution": "Universidad Francisco de Vitoria",
            "degree": "Business Analytics",
            "year": pd.Timestamp.today().year,
            "title": "Regime-Aware Multi-Asset Portfolio Construction",
        },
    }

    output_path = config.processed_dir / "metadata.yaml"
    output_path.write_text(yaml.safe_dump(metadata_payload, sort_keys=False, allow_unicode=False, width=140), encoding="utf-8")
    logger.info("Wrote dataset metadata: %s", output_path)
    return output_path
