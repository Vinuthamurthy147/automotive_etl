"""
SQLAlchemy ORM models and Pydantic response schemas.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    Column, Date, DateTime, Float, ForeignKey,
    Integer, String, Text, func,
)
from sqlalchemy.orm import relationship

from .database import Base


# ============================================================
# ORM Models
# ============================================================

class BrandORM(Base):
    __tablename__ = "brands"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), unique=True, nullable=False)
    country    = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())

    vehicles = relationship("VehicleORM", back_populates="brand")


class VehicleORM(Base):
    __tablename__ = "vehicles"

    id           = Column(Integer, primary_key=True, index=True)
    vehicle_id   = Column(Integer, unique=True, index=True, nullable=False)
    brand_id     = Column(Integer, ForeignKey("brands.id"), nullable=False)
    model        = Column(String(100), nullable=False)
    year         = Column(Integer, nullable=False)
    category     = Column(String(50))
    fuel_type    = Column(String(50))
    transmission = Column(String(50))
    engine_size  = Column(Float)
    horsepower   = Column(Integer)
    mpg_city     = Column(Float)
    mpg_highway  = Column(Float)
    mpg_combined = Column(Float)
    base_price   = Column(Float, nullable=False)
    created_at   = Column(DateTime, server_default=func.now())

    brand = relationship("BrandORM", back_populates="vehicles")
    sales = relationship("SaleORM", back_populates="vehicle")


class SaleORM(Base):
    __tablename__ = "sales"

    id              = Column(Integer, primary_key=True, index=True)
    sale_id         = Column(Integer, unique=True, index=True, nullable=False)
    vehicle_id      = Column(Integer, ForeignKey("vehicles.vehicle_id"), nullable=False)
    sale_date       = Column(Date, nullable=False)
    sale_price      = Column(Float, nullable=False)
    dealer_city     = Column(String(100))
    dealer_state    = Column(String(50))
    customer_type   = Column(String(50))
    color           = Column(String(50))
    mileage         = Column(Integer, default=0)
    discount_amount = Column(Float)
    discount_pct    = Column(Float)
    sale_year       = Column(Integer)
    sale_month      = Column(Integer)
    sale_quarter    = Column(Integer)
    created_at      = Column(DateTime, server_default=func.now())

    vehicle = relationship("VehicleORM", back_populates="sales")


class ETLLogORM(Base):
    __tablename__ = "etl_logs"

    id                  = Column(Integer, primary_key=True, index=True)
    run_date            = Column(DateTime, server_default=func.now())
    records_extracted   = Column(Integer, default=0)
    records_transformed = Column(Integer, default=0)
    records_loaded      = Column(Integer, default=0)
    status              = Column(String(20), nullable=False)
    message             = Column(Text)


# ============================================================
# Pydantic Schemas
# ============================================================

class BrandSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:      int
    name:    str
    country: Optional[str]


class VehicleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vehicle_id:   int
    model:        str
    year:         int
    category:     Optional[str]
    fuel_type:    Optional[str]
    transmission: Optional[str]
    engine_size:  Optional[float]
    horsepower:   Optional[int]
    mpg_city:     Optional[float]
    mpg_highway:  Optional[float]
    mpg_combined: Optional[float]
    base_price:   float
    brand:        BrandSchema


class SaleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sale_id:       int
    vehicle_id:    int
    sale_date:     date
    sale_price:    float
    dealer_city:   Optional[str]
    dealer_state:  Optional[str]
    customer_type: Optional[str]
    color:         Optional[str]
    mileage:       Optional[int]
    discount_pct:  Optional[float]


class ETLLogSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:                  int
    run_date:            datetime
    records_extracted:   int
    records_transformed: int
    records_loaded:      int
    status:              str
    message:             Optional[str]


# ── Analytics response schemas ────────────────────────────────────────────

class BrandSummarySchema(BaseModel):
    brand:           str
    country:         Optional[str]
    total_sales:     int
    total_revenue:   float
    avg_sale_price:  float
    avg_discount_pct: Optional[float]


class MonthlySalesSchema(BaseModel):
    year:         int
    month:        int
    total_sales:  int
    total_revenue: float
    avg_sale_price: float


class TopModelSchema(BaseModel):
    brand:        str
    model:        str
    year:         int
    total_sales:  int
    total_revenue: float


class FuelTypeBreakdownSchema(BaseModel):
    fuel_type:     str
    total_sales:   int
    total_revenue: float
    avg_sale_price: float


class StateRevenueSchema(BaseModel):
    dealer_state:  str
    total_sales:   int
    total_revenue: float
