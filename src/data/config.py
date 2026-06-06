from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import logging


@dataclass(slots=True)
class PipelineConfig:
    """Global configuration for the data preparation pipeline."""

    project_root: Path
    data_dir: Path
    processed_dir: Path
    reports_dir: Path
    inventory_path: Path
    weekly_frequency: str = "W-FRI"
    max_missing_ratio_warning: float = 0.25
    outlier_z_threshold: float = 6.0
    min_obs_by_freq: dict[str, int] = field(
        default_factory=lambda: {
            "daily": 252,
            "weekly": 104,
            "monthly": 36,
            "quarterly": 20,
            "yearly": 10,
            "unknown": 30,
        }
    )


def default_config(project_root: Path | None = None) -> PipelineConfig:
    """Create default config from project root and ensure output folders exist."""

    root = project_root or Path(__file__).resolve().parents[2]
    data_dir = root / "data"
    processed_dir = data_dir / "processed"
    reports_dir = root / "reports"
    inventory_path = reports_dir / "data_inventory.yml"

    config = PipelineConfig(
        project_root=root,
        data_dir=data_dir,
        processed_dir=processed_dir,
        reports_dir=reports_dir,
        inventory_path=inventory_path,
    )
    ensure_directories(config)
    return config


def ensure_directories(config: PipelineConfig) -> None:
    """Create required output directories if they do not exist."""

    config.processed_dir.mkdir(parents=True, exist_ok=True)
    config.reports_dir.mkdir(parents=True, exist_ok=True)


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure and return a pipeline logger."""

    logger = logging.getLogger("data_pipeline")
    if logger.handlers:
        logger.setLevel(level)
        return logger

    logger.setLevel(level)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger
