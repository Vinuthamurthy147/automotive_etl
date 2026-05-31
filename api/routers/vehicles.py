"""
Vehicles router — CRUD-style endpoints for vehicle and sales data.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import (
    BrandSchema, ETLLogSchema, SaleSchema, VehicleSchema,
    BrandORM, VehicleORM, SaleORM, ETLLogORM,
)

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


# ── Brands ────────────────────────────────────────────────────────────────

@router.get("/brands", response_model=list[BrandSchema], summary="List all brands")
def list_brands(db: Session = Depends(get_db)):
    return db.query(BrandORM).order_by(BrandORM.name).all()


@router.get("/brands/{brand_id}", response_model=BrandSchema, summary="Get brand by ID")
def get_brand(brand_id: int, db: Session = Depends(get_db)):
    brand = db.query(BrandORM).filter(BrandORM.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


# ── Vehicles ──────────────────────────────────────────────────────────────

@router.get("", response_model=list[VehicleSchema], summary="List vehicles with optional filters")
def list_vehicles(
    brand:     Optional[str] = Query(None, description="Filter by brand name"),
    category:  Optional[str] = Query(None, description="Filter by category (Sedan, SUV …)"),
    fuel_type: Optional[str] = Query(None, description="Filter by fuel type"),
    year:      Optional[int] = Query(None, description="Filter by model year"),
    min_price: Optional[float] = Query(None, description="Minimum base price"),
    max_price: Optional[float] = Query(None, description="Maximum base price"),
    limit:     int = Query(50, le=200),
    offset:    int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(VehicleORM).join(BrandORM)

    if brand:
        query = query.filter(BrandORM.name.ilike(f"%{brand}%"))
    if category:
        query = query.filter(VehicleORM.category.ilike(f"%{category}%"))
    if fuel_type:
        query = query.filter(VehicleORM.fuel_type.ilike(f"%{fuel_type}%"))
    if year:
        query = query.filter(VehicleORM.year == year)
    if min_price is not None:
        query = query.filter(VehicleORM.base_price >= min_price)
    if max_price is not None:
        query = query.filter(VehicleORM.base_price <= max_price)

    return query.order_by(BrandORM.name, VehicleORM.model).offset(offset).limit(limit).all()


@router.get("/{vehicle_id}", response_model=VehicleSchema, summary="Get vehicle by vehicle_id")
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = (
        db.query(VehicleORM)
        .join(BrandORM)
        .filter(VehicleORM.vehicle_id == vehicle_id)
        .first()
    )
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


# ── Sales ─────────────────────────────────────────────────────────────────

@router.get("/{vehicle_id}/sales", response_model=list[SaleSchema], summary="Sales for a vehicle")
def get_vehicle_sales(
    vehicle_id: int,
    limit:  int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    vehicle = db.query(VehicleORM).filter(VehicleORM.vehicle_id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    return (
        db.query(SaleORM)
        .filter(SaleORM.vehicle_id == vehicle_id)
        .order_by(SaleORM.sale_date.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


# ── ETL Logs ──────────────────────────────────────────────────────────────

@router.get(
    "/etl/logs",
    response_model=list[ETLLogSchema],
    tags=["ETL"],
    summary="Recent ETL run logs",
)
def list_etl_logs(limit: int = Query(10, le=50), db: Session = Depends(get_db)):
    return (
        db.query(ETLLogORM)
        .order_by(ETLLogORM.run_date.desc())
        .limit(limit)
        .all()
    )
