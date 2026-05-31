"""
Extract module — reads raw data from CSV sources.
"""
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def extract_vehicles(filepath: str | Path) -> pd.DataFrame:
    """
    Extract vehicle specification data from a CSV file.

    Args:
        filepath: Path to the vehicles CSV.

    Returns:
        Raw DataFrame with all columns as-is.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Vehicles data file not found: {filepath}")

    logger.info("Extracting vehicles from '%s'", filepath)
    df = pd.read_csv(filepath, dtype=str)          # read everything as str first
    logger.info("Extracted %d vehicle records", len(df))
    return df


def extract_sales(filepath: str | Path) -> pd.DataFrame:
    """
    Extract sales transaction data from a CSV file.

    Args:
        filepath: Path to the sales CSV.

    Returns:
        Raw DataFrame with sale_date parsed as datetime.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Sales data file not found: {filepath}")

    logger.info("Extracting sales from '%s'", filepath)
    df = pd.read_csv(filepath, dtype=str)
    logger.info("Extracted %d sales records", len(df))
    return df
