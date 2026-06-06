from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.build_panels import build_investable_panels, build_regime_panel
from src.data.cleaning import clean_all_sources
from src.data.config import default_config, setup_logging
from src.data.feature_engineering import engineer_regime_features
from src.data.loaders import (
    build_source_catalog,
    discover_data_files,
    load_all_raw_sources,
    load_inventory_records,
)
from src.data.reporting import write_dataset_metadata, write_final_dataset_summary, write_validation_reports
from src.data.validation import validate_series_collection


def main() -> None:
    logger = setup_logging()
    config = default_config(project_root=PROJECT_ROOT)

    logger.info("Starting data validation and preprocessing pipeline")
    logger.info("Project root: %s", config.project_root)

    data_files = discover_data_files(config.data_dir)
    if not data_files:
        raise RuntimeError(f"No raw data files found under {config.data_dir}")

    logger.info("Discovered %s raw files.", len(data_files))

    inventory_records = load_inventory_records(config.inventory_path, logger)
    catalog = build_source_catalog(data_files, inventory_records, config.project_root)
    if catalog.empty:
        raise RuntimeError("Catalog build failed: no data sources available.")

    raw_payloads = load_all_raw_sources(catalog, logger)
    cleaned_records = clean_all_sources(raw_payloads, logger)

    validation_bundle = validate_series_collection(cleaned_records, config, logger)
    write_validation_reports(validation_bundle, config, logger)

    prices_weekly, returns_weekly = build_investable_panels(cleaned_records, config, logger)
    regime_weekly = build_regime_panel(
        cleaned_records,
        validation_bundle["series_report"],
        config,
        logger,
    )
    regime_features = engineer_regime_features(regime_weekly, config, logger)

    write_final_dataset_summary(
        investable_prices=prices_weekly,
        investable_returns=returns_weekly,
        regime_panel=regime_weekly,
        regime_features=regime_features,
        series_report=validation_bundle["series_report"],
        config=config,
        logger=logger,
    )

    write_dataset_metadata(
        catalog=catalog,
        series_report=validation_bundle["series_report"],
        investable_returns=returns_weekly,
        regime_panel=regime_weekly,
        config=config,
        logger=logger,
    )

    logger.info("Pipeline finished successfully.")


if __name__ == "__main__":
    main()
