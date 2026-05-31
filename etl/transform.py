"""
Transform module — cleans and enriches raw DataFrames using Pandas & NumPy.
"""
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace and lowercase all column names."""
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    return df


def _to_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Coerce listed columns to numeric, turning errors into NaN."""
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.strip(), errors="coerce")
    return df


# ---------------------------------------------------------------------------
# Vehicle transformations
# ---------------------------------------------------------------------------

def transform_vehicles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and enrich raw vehicle data.

    Steps:
    1. Normalise column names
    2. Drop duplicates on vehicle_id
    3. Coerce numeric columns
    4. Fill missing fuel-efficiency values with column median
    5. Set engine_size to 0.0 for Electric vehicles
    6. Compute combined MPG: 55 % city + 45 % highway (EPA formula)
    7. Standardise string categories
    8. Drop rows with missing base_price
    """
    logger.info("Transforming vehicle data …")
    df = _normalise_columns(df.copy())

    df = df.drop_duplicates(subset=["vehicle_id"])

    numeric_cols = [
        "vehicle_id", "year", "engine_size", "horsepower",
        "mpg_city", "mpg_highway", "base_price",
    ]
    df = _to_numeric(df, numeric_cols)

    # Electric vehicles have no MPG — leave as NaN (excluded from avg calculations)
    is_electric = df["fuel_type"].str.strip().str.title() == "Electric"
    df.loc[is_electric, "engine_size"] = 0.0

    # Fill missing MPG with column median (non-electric only)
    for col in ["mpg_city", "mpg_highway"]:
        median_val = df.loc[~is_electric, col].median()
        df[col] = df[col].fillna(median_val)

    # Combined MPG (EPA weighting)
    df["mpg_combined"] = np.where(
        is_electric,
        np.nan,
        np.round(0.55 * df["mpg_city"] + 0.45 * df["mpg_highway"], 2),
    )

    # Standardise free-text fields
    for col in ["category", "fuel_type", "transmission", "brand", "country"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()

    df = df.dropna(subset=["base_price"])
    df["vehicle_id"] = df["vehicle_id"].astype(int)
    df["year"] = df["year"].astype(int)

    logger.info("Transformed %d vehicle records", len(df))
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Sales transformations
# ---------------------------------------------------------------------------

def transform_sales(
    df: pd.DataFrame, vehicles_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Clean and enrich raw sales data.

    Steps:
    1. Normalise columns & drop duplicates
    2. Parse sale_date; drop rows with invalid dates
    3. Coerce numeric columns
    4. Remove rows with non-positive sale_price
    5. Join base_price from vehicles to compute discount metrics
    6. Extract date parts: year, month, quarter
    """
    logger.info("Transforming sales data …")
    df = _normalise_columns(df.copy())
    df = df.drop_duplicates(subset=["sale_id"])

    df["sale_date"] = pd.to_datetime(
        df["sale_date"].astype(str).str.strip(), errors="coerce"
    )
    df = df.dropna(subset=["sale_date"])

    numeric_cols = ["sale_id", "vehicle_id", "sale_price", "mileage"]
    df = _to_numeric(df, numeric_cols)

    df = df.dropna(subset=["sale_price"])
    df = df[df["sale_price"] > 0]

    # Join base_price from the transformed vehicles DataFrame
    price_ref = vehicles_df[["vehicle_id", "base_price"]].drop_duplicates("vehicle_id")
    df = df.merge(price_ref, on="vehicle_id", how="left")

    df["discount_amount"] = np.round(df["base_price"] - df["sale_price"], 2)
    df["discount_pct"] = np.round(
        (df["discount_amount"] / df["base_price"]) * 100, 2
    )
    df = df.drop(columns=["base_price"])

    # Date parts
    df["sale_year"] = df["sale_date"].dt.year
    df["sale_month"] = df["sale_date"].dt.month
    df["sale_quarter"] = df["sale_date"].dt.quarter

    # Standardise string fields
    for col in ["dealer_city", "dealer_state", "customer_type", "color"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()

    df["sale_id"] = df["sale_id"].astype(int)
    df["vehicle_id"] = df["vehicle_id"].astype(int)
    df["mileage"] = df["mileage"].fillna(0).astype(int)

    logger.info("Transformed %d sales records", len(df))
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Aggregation — brand-level summary
# ---------------------------------------------------------------------------

def compute_brand_summary(
    vehicles_df: pd.DataFrame, sales_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Return a brand-level revenue summary DataFrame.

    Columns: brand, country, total_sales, total_revenue,
             avg_sale_price, avg_discount_pct
    """
    merged = sales_df.merge(
        vehicles_df[["vehicle_id", "brand", "country"]],
        on="vehicle_id",
        how="left",
    )
    summary = (
        merged.groupby(["brand", "country"])
        .agg(
            total_sales=("sale_id", "count"),
            total_revenue=("sale_price", "sum"),
            avg_sale_price=("sale_price", "mean"),
            avg_discount_pct=("discount_pct", "mean"),
        )
        .reset_index()
    )
    summary["total_revenue"] = np.round(summary["total_revenue"], 2)
    summary["avg_sale_price"] = np.round(summary["avg_sale_price"], 2)
    summary["avg_discount_pct"] = np.round(summary["avg_discount_pct"], 2)
    return summary.sort_values("total_revenue", ascending=False)
