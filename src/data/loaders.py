from __future__ import annotations

from pathlib import Path
from typing import Any
import logging

import pandas as pd
import yaml


SUPPORTED_EXTENSIONS = {".xlsx", ".xls", ".csv"}


def normalize_rel_path(path: str | Path) -> str:
    """Normalize a relative path for stable dictionary key matching."""

    txt = str(path).replace("\\", "/").strip()
    if txt.startswith("./"):
        txt = txt[2:]
    return txt


def build_default_id(rel_path: Path) -> str:
    """Create a deterministic identifier from a file path."""

    stem = rel_path.with_suffix("")
    slug = "_".join(stem.parts)
    slug = slug.replace(" ", "_").replace("-", "_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.lower()


def discover_data_files(data_dir: Path) -> list[Path]:
    """Recursively discover supported raw data files under data/."""

    files: list[Path] = []
    for ext in SUPPORTED_EXTENSIONS:
        files.extend(data_dir.rglob(f"*{ext}"))
    files = [p for p in files if p.is_file() and "processed" not in p.parts]
    return sorted(set(files))


def load_inventory_records(inventory_path: Path, logger: logging.Logger) -> dict[str, dict[str, Any]]:
    """Load YAML inventory records keyed by normalized relative path."""

    if not inventory_path.exists():
        logger.warning("Inventory file not found at %s. Pipeline will infer metadata.", inventory_path)
        return {}

    with inventory_path.open("r", encoding="utf-8") as f:
        payload = yaml.safe_load(f) or {}

    datasets = payload.get("datasets", [])
    records: dict[str, dict[str, Any]] = {}
    for row in datasets:
        rel = normalize_rel_path(row.get("path", ""))
        if not rel:
            continue
        records[rel] = row
    logger.info("Loaded %s metadata records from inventory.", len(records))
    return records


def build_source_catalog(
    data_files: list[Path],
    inventory_records: dict[str, dict[str, Any]],
    project_root: Path,
) -> pd.DataFrame:
    """Build a source catalog that merges filesystem discovery with inventory metadata."""

    rows: list[dict[str, Any]] = []

    for path in data_files:
        rel_path = normalize_rel_path(path.relative_to(project_root))
        rel_obj = Path(rel_path)
        inv = inventory_records.get(rel_path, {})

        parts = rel_obj.parts
        category = inv.get("category")
        subcategory = inv.get("subcategory")
        ticker = inv.get("ticker")

        if not category and len(parts) >= 3 and parts[0] == "data":
            category = parts[1]
        if not subcategory and len(parts) >= 4 and parts[0] == "data":
            subcategory = parts[2]
        if not ticker:
            ticker = rel_obj.stem

        rows.append(
            {
                "id": inv.get("id") or build_default_id(rel_obj),
                "relative_path": rel_path,
                "absolute_path": path,
                "file_ext": path.suffix.lower(),
                "from_inventory": bool(inv),
                "category": category,
                "subcategory": subcategory,
                "ticker": ticker,
                "sheet": inv.get("sheet"),
                "header_row": inv.get("header_row"),
                "data_start_row": inv.get("data_start_row"),
                "freq": inv.get("freq"),
                "unit": inv.get("unit"),
                "status": inv.get("status", "UNKNOWN"),
                "notes": inv.get("notes", ""),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.sort_values(["category", "subcategory", "relative_path"]).reset_index(drop=True)
    return df


def read_raw_table(source_row: pd.Series, logger: logging.Logger) -> dict[str, Any]:
    """Read one source file into a raw dataframe with provenance info."""

    path = Path(source_row["absolute_path"])
    ext = str(source_row.get("file_ext", "")).lower()

    payload: dict[str, Any] = {
        "meta": source_row.to_dict(),
        "raw_df": None,
        "sheet_used": None,
        "available_sheets": None,
        "error": None,
    }

    try:
        if ext == ".csv":
            df = pd.read_csv(path, low_memory=False)
            payload["raw_df"] = df
            return payload

        if ext in {".xlsx", ".xls"}:
            xls = pd.ExcelFile(path)
            available_sheets = list(xls.sheet_names)
            expected_sheet = source_row.get("sheet")
            sheet_used = expected_sheet if isinstance(expected_sheet, str) and expected_sheet in available_sheets else available_sheets[0]

            df = pd.read_excel(path, sheet_name=sheet_used, header=None, dtype=object)
            payload["raw_df"] = df
            payload["sheet_used"] = sheet_used
            payload["available_sheets"] = available_sheets
            return payload

        payload["error"] = f"Unsupported extension: {ext}"
        return payload

    except Exception as exc:  # pragma: no cover
        logger.exception("Failed reading file %s", path)
        payload["error"] = str(exc)
        return payload


def load_all_raw_sources(catalog: pd.DataFrame, logger: logging.Logger) -> list[dict[str, Any]]:
    """Read all files listed in the catalog and return raw payload objects."""

    payloads: list[dict[str, Any]] = []
    for _, row in catalog.iterrows():
        payloads.append(read_raw_table(row, logger))

    ok = sum(1 for x in payloads if x.get("error") is None)
    fail = len(payloads) - ok
    logger.info("Loaded raw sources: ok=%s fail=%s total=%s", ok, fail, len(payloads))
    return payloads
