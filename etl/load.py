"""
Load module — writes transformed DataFrames into MySQL via SQLAlchemy.
"""
import logging
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Engine factory
# ---------------------------------------------------------------------------

def get_engine(database_url: str) -> Engine:
    """Create and return a SQLAlchemy engine."""
    return create_engine(database_url, pool_pre_ping=True, echo=False)


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_brands(vehicles_df: pd.DataFrame, engine: Engine) -> int:
    """
    Upsert unique brands from the vehicles DataFrame.

    Returns:
        Number of brand rows processed.
    """
    brands = (
        vehicles_df[["brand", "country"]]
        .drop_duplicates(subset=["brand"])
        .rename(columns={"brand": "name"})
    )

    loaded = 0
    with engine.begin() as conn:
        for _, row in brands.iterrows():
            conn.execute(
                text(
                    """
                    INSERT INTO brands (name, country)
                    VALUES (:name, :country)
                    ON DUPLICATE KEY UPDATE country = VALUES(country)
                    """
                ),
                {"name": row["name"], "country": row.get("country", "Unknown")},
            )
            loaded += 1

    logger.info("Loaded/updated %d brands", loaded)
    return loaded


def load_vehicles(vehicles_df: pd.DataFrame, engine: Engine) -> int:
    """
    Upsert vehicles, resolving brand_id from the brands table.

    Returns:
        Number of vehicle rows processed.
    """
    with engine.connect() as conn:
        brand_rows = conn.execute(text("SELECT id, name FROM brands")).fetchall()
    brand_map = {row.name: row.id for row in brand_rows}

    loaded = 0
    with engine.begin() as conn:
        for _, row in vehicles_df.iterrows():
            brand_id = brand_map.get(row["brand"])
            if brand_id is None:
                logger.warning("Brand '%s' not found — skipping vehicle_id %s", row["brand"], row["vehicle_id"])
                continue

            conn.execute(
                text(
                    """
                    INSERT INTO vehicles
                        (vehicle_id, brand_id, model, year, category, fuel_type,
                         transmission, engine_size, horsepower, mpg_city,
                         mpg_highway, mpg_combined, base_price)
                    VALUES
                        (:vehicle_id, :brand_id, :model, :year, :category,
                         :fuel_type, :transmission, :engine_size, :horsepower,
                         :mpg_city, :mpg_highway, :mpg_combined, :base_price)
                    ON DUPLICATE KEY UPDATE
                        model        = VALUES(model),
                        year         = VALUES(year),
                        category     = VALUES(category),
                        fuel_type    = VALUES(fuel_type),
                        transmission = VALUES(transmission),
                        engine_size  = VALUES(engine_size),
                        horsepower   = VALUES(horsepower),
                        mpg_city     = VALUES(mpg_city),
                        mpg_highway  = VALUES(mpg_highway),
                        mpg_combined = VALUES(mpg_combined),
                        base_price   = VALUES(base_price)
                    """
                ),
                {
                    "vehicle_id":   int(row["vehicle_id"]),
                    "brand_id":     brand_id,
                    "model":        row["model"],
                    "year":         int(row["year"]),
                    "category":     row.get("category"),
                    "fuel_type":    row.get("fuel_type"),
                    "transmission": row.get("transmission"),
                    "engine_size":  _safe_float(row.get("engine_size")),
                    "horsepower":   _safe_int(row.get("horsepower")),
                    "mpg_city":     _safe_float(row.get("mpg_city")),
                    "mpg_highway":  _safe_float(row.get("mpg_highway")),
                    "mpg_combined": _safe_float(row.get("mpg_combined")),
                    "base_price":   float(row["base_price"]),
                },
            )
            loaded += 1

    logger.info("Loaded/updated %d vehicles", loaded)
    return loaded


def load_sales(sales_df: pd.DataFrame, engine: Engine) -> int:
    """
    Upsert sales transactions.

    Returns:
        Number of sale rows processed.
    """
    loaded = 0
    with engine.begin() as conn:
        for _, row in sales_df.iterrows():
            conn.execute(
                text(
                    """
                    INSERT INTO sales
                        (sale_id, vehicle_id, sale_date, sale_price,
                         dealer_city, dealer_state, customer_type, color,
                         mileage, discount_amount, discount_pct,
                         sale_year, sale_month, sale_quarter)
                    VALUES
                        (:sale_id, :vehicle_id, :sale_date, :sale_price,
                         :dealer_city, :dealer_state, :customer_type, :color,
                         :mileage, :discount_amount, :discount_pct,
                         :sale_year, :sale_month, :sale_quarter)
                    ON DUPLICATE KEY UPDATE
                        sale_price      = VALUES(sale_price),
                        discount_amount = VALUES(discount_amount),
                        discount_pct    = VALUES(discount_pct)
                    """
                ),
                {
                    "sale_id":        int(row["sale_id"]),
                    "vehicle_id":     int(row["vehicle_id"]),
                    "sale_date":      row["sale_date"].date(),
                    "sale_price":     float(row["sale_price"]),
                    "dealer_city":    row.get("dealer_city"),
                    "dealer_state":   row.get("dealer_state"),
                    "customer_type":  row.get("customer_type"),
                    "color":          row.get("color"),
                    "mileage":        int(row.get("mileage", 0)),
                    "discount_amount": _safe_float(row.get("discount_amount")),
                    "discount_pct":   _safe_float(row.get("discount_pct")),
                    "sale_year":      int(row["sale_year"]),
                    "sale_month":     int(row["sale_month"]),
                    "sale_quarter":   int(row["sale_quarter"]),
                },
            )
            loaded += 1

    logger.info("Loaded/updated %d sales records", loaded)
    return loaded


def log_etl_run(
    engine: Engine,
    extracted: int,
    transformed: int,
    loaded: int,
    status: str,
    message: str = "",
) -> None:
    """Persist an ETL run summary row to etl_logs."""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO etl_logs
                    (records_extracted, records_transformed, records_loaded, status, message)
                VALUES
                    (:extracted, :transformed, :loaded, :status, :message)
                """
            ),
            {
                "extracted":   extracted,
                "transformed": transformed,
                "loaded":      loaded,
                "status":      status,
                "message":     message,
            },
        )
    logger.info("ETL log written — status=%s", status)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _safe_float(value) -> float | None:
    try:
        import math
        f = float(value)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def _safe_int(value) -> int | None:
    try:
        import math
        f = float(value)
        return None if math.isnan(f) else int(f)
    except (TypeError, ValueError):
        return None
