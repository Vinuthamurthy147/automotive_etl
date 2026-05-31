"""
Analytics router — aggregated insights using SQL + SQLAlchemy.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import (
    BrandORM, VehicleORM, SaleORM,
    BrandSummarySchema, FuelTypeBreakdownSchema,
    MonthlySalesSchema, StateRevenueSchema, TopModelSchema,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/brand-summary",
    response_model=list[BrandSummarySchema],
    summary="Revenue and sales count grouped by brand",
)
def brand_summary(db: Session = Depends(get_db)):
    rows = (
        db.query(
            BrandORM.name.label("brand"),
            BrandORM.country,
            func.count(SaleORM.sale_id).label("total_sales"),
            func.round(func.sum(SaleORM.sale_price), 2).label("total_revenue"),
            func.round(func.avg(SaleORM.sale_price), 2).label("avg_sale_price"),
            func.round(func.avg(SaleORM.discount_pct), 2).label("avg_discount_pct"),
        )
        .join(VehicleORM, BrandORM.id == VehicleORM.brand_id)
        .join(SaleORM, VehicleORM.vehicle_id == SaleORM.vehicle_id)
        .group_by(BrandORM.id, BrandORM.name, BrandORM.country)
        .order_by(desc("total_revenue"))
        .all()
    )
    return [BrandSummarySchema(**r._asdict()) for r in rows]


@router.get(
    "/monthly-sales",
    response_model=list[MonthlySalesSchema],
    summary="Monthly sales volume and revenue",
)
def monthly_sales(
    year: Optional[int] = Query(None, description="Filter by year"),
    db: Session = Depends(get_db),
):
    query = db.query(
        SaleORM.sale_year.label("year"),
        SaleORM.sale_month.label("month"),
        func.count(SaleORM.sale_id).label("total_sales"),
        func.round(func.sum(SaleORM.sale_price), 2).label("total_revenue"),
        func.round(func.avg(SaleORM.sale_price), 2).label("avg_sale_price"),
    ).group_by(SaleORM.sale_year, SaleORM.sale_month)

    if year:
        query = query.filter(SaleORM.sale_year == year)

    rows = query.order_by(SaleORM.sale_year, SaleORM.sale_month).all()
    return [MonthlySalesSchema(**r._asdict()) for r in rows]


@router.get(
    "/top-models",
    response_model=list[TopModelSchema],
    summary="Best-selling vehicle models",
)
def top_models(
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(
            BrandORM.name.label("brand"),
            VehicleORM.model,
            VehicleORM.year,
            func.count(SaleORM.sale_id).label("total_sales"),
            func.round(func.sum(SaleORM.sale_price), 2).label("total_revenue"),
        )
        .join(VehicleORM, BrandORM.id == VehicleORM.brand_id)
        .join(SaleORM, VehicleORM.vehicle_id == SaleORM.vehicle_id)
        .group_by(BrandORM.name, VehicleORM.model, VehicleORM.year)
        .order_by(desc("total_sales"))
        .limit(limit)
        .all()
    )
    return [TopModelSchema(**r._asdict()) for r in rows]


@router.get(
    "/fuel-type-breakdown",
    response_model=list[FuelTypeBreakdownSchema],
    summary="Sales distribution by fuel type",
)
def fuel_type_breakdown(db: Session = Depends(get_db)):
    rows = (
        db.query(
            VehicleORM.fuel_type,
            func.count(SaleORM.sale_id).label("total_sales"),
            func.round(func.sum(SaleORM.sale_price), 2).label("total_revenue"),
            func.round(func.avg(SaleORM.sale_price), 2).label("avg_sale_price"),
        )
        .join(SaleORM, VehicleORM.vehicle_id == SaleORM.vehicle_id)
        .group_by(VehicleORM.fuel_type)
        .order_by(desc("total_sales"))
        .all()
    )
    return [FuelTypeBreakdownSchema(**r._asdict()) for r in rows]


@router.get(
    "/state-revenue",
    response_model=list[StateRevenueSchema],
    summary="Revenue by dealer state",
)
def state_revenue(db: Session = Depends(get_db)):
    rows = (
        db.query(
            SaleORM.dealer_state,
            func.count(SaleORM.sale_id).label("total_sales"),
            func.round(func.sum(SaleORM.sale_price), 2).label("total_revenue"),
        )
        .group_by(SaleORM.dealer_state)
        .order_by(desc("total_revenue"))
        .all()
    )
    return [StateRevenueSchema(**r._asdict()) for r in rows]
