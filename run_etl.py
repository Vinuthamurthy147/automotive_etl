#!/usr/bin/env python3
"""
Automotive Sales ETL Pipeline — entrypoint.

Usage:
    python run_etl.py

Reads DATABASE_URL and DATA_DIR from the .env file (or environment).
"""
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from etl.extract import extract_vehicles, extract_sales
from etl.transform import transform_vehicles, transform_sales
from etl.load import get_engine, load_brands, load_vehicles, load_sales, log_etl_run

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("etl_pipeline")


def run_pipeline() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL is not set. Check your .env file.")
        sys.exit(1)

    data_dir = Path(os.getenv("DATA_DIR", "data"))
    engine = get_engine(database_url)

    total_extracted = total_transformed = total_loaded = 0

    try:
        # ── EXTRACT ───────────────────────────────────────────────────────
        logger.info("=" * 55)
        logger.info("PHASE 1 — EXTRACT")
        logger.info("=" * 55)
        vehicles_raw = extract_vehicles(data_dir / "vehicles.csv")
        sales_raw    = extract_sales(data_dir / "sales.csv")
        total_extracted = len(vehicles_raw) + len(sales_raw)

        # ── TRANSFORM ─────────────────────────────────────────────────────
        logger.info("=" * 55)
        logger.info("PHASE 2 — TRANSFORM")
        logger.info("=" * 55)
        vehicles_clean = transform_vehicles(vehicles_raw)
        sales_clean    = transform_sales(sales_raw, vehicles_clean)
        total_transformed = len(vehicles_clean) + len(sales_clean)

        # ── LOAD ──────────────────────────────────────────────────────────
        logger.info("=" * 55)
        logger.info("PHASE 3 — LOAD")
        logger.info("=" * 55)
        brands_loaded   = load_brands(vehicles_clean, engine)
        vehicles_loaded = load_vehicles(vehicles_clean, engine)
        sales_loaded    = load_sales(sales_clean, engine)
        total_loaded    = brands_loaded + vehicles_loaded + sales_loaded

        log_etl_run(engine, total_extracted, total_transformed, total_loaded, "SUCCESS")
        logger.info("=" * 55)
        logger.info("ETL PIPELINE COMPLETED SUCCESSFULLY")
        logger.info(
            "Extracted=%d | Transformed=%d | Loaded=%d",
            total_extracted, total_transformed, total_loaded,
        )
        logger.info("=" * 55)

    except Exception as exc:
        logger.exception("ETL pipeline failed: %s", exc)
        log_etl_run(engine, total_extracted, total_transformed, 0, "FAILED", str(exc))
        sys.exit(1)


if __name__ == "__main__":
    run_pipeline()
