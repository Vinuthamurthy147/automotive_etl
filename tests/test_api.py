"""
Tests for the FastAPI analytics endpoints.
Uses httpx.AsyncClient with the ASGI transport — no running server needed.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from api.main import app

client = TestClient(app)


# ── Health ────────────────────────────────────────────────────────────────

def test_root_returns_200():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "version" in data


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ── Vehicles (mocked DB) ──────────────────────────────────────────────────

def _mock_brand():
    b = MagicMock()
    b.id = 1
    b.name = "Toyota"
    b.country = "Japan"
    return b


def _mock_vehicle():
    v = MagicMock()
    v.vehicle_id   = 1
    v.model        = "Camry"
    v.year         = 2022
    v.category     = "Sedan"
    v.fuel_type    = "Gasoline"
    v.transmission = "Automatic"
    v.engine_size  = 2.5
    v.horsepower   = 203
    v.mpg_city     = 28.0
    v.mpg_highway  = 39.0
    v.mpg_combined = 33.0
    v.base_price   = 25945.0
    v.brand        = _mock_brand()
    return v


@patch("api.routers.vehicles.get_db")
def test_list_brands(mock_get_db):
    mock_session = MagicMock()
    mock_session.query.return_value.order_by.return_value.all.return_value = [_mock_brand()]
    mock_get_db.return_value = iter([mock_session])

    response = client.get("/vehicles/brands")
    assert response.status_code == 200


@patch("api.routers.vehicles.get_db")
def test_get_vehicle_not_found(mock_get_db):
    mock_session = MagicMock()
    mock_session.query.return_value.join.return_value.filter.return_value.first.return_value = None
    mock_get_db.return_value = iter([mock_session])

    response = client.get("/vehicles/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Vehicle not found"


# ── Analytics (mocked DB) ─────────────────────────────────────────────────

@patch("api.routers.analytics.get_db")
def test_brand_summary_empty(mock_get_db):
    mock_session = MagicMock()
    mock_session.query.return_value.join.return_value.join.return_value \
        .group_by.return_value.order_by.return_value.all.return_value = []
    mock_get_db.return_value = iter([mock_session])

    response = client.get("/analytics/brand-summary")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@patch("api.routers.analytics.get_db")
def test_fuel_type_breakdown_empty(mock_get_db):
    mock_session = MagicMock()
    mock_session.query.return_value.join.return_value \
        .group_by.return_value.order_by.return_value.all.return_value = []
    mock_get_db.return_value = iter([mock_session])

    response = client.get("/analytics/fuel-type-breakdown")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ── ETL Transform unit tests ──────────────────────────────────────────────

def test_transform_vehicles_computes_mpg_combined():
    import pandas as pd
    from etl.transform import transform_vehicles

    raw = pd.DataFrame([{
        "vehicle_id": "1",
        "brand":       "Toyota",
        "model":       "Camry",
        "year":        "2022",
        "category":    "Sedan",
        "fuel_type":   "Gasoline",
        "transmission":"Automatic",
        "engine_size": "2.5",
        "horsepower":  "203",
        "mpg_city":    "28",
        "mpg_highway": "39",
        "base_price":  "25945",
        "country":     "Japan",
    }])

    result = transform_vehicles(raw)
    assert len(result) == 1
    expected_combined = round(0.55 * 28 + 0.45 * 39, 2)
    assert result.iloc[0]["mpg_combined"] == expected_combined


def test_transform_vehicles_drops_missing_base_price():
    import pandas as pd
    from etl.transform import transform_vehicles

    raw = pd.DataFrame([
        {"vehicle_id": "1", "brand": "X", "model": "A", "year": "2022",
         "category": "Sedan", "fuel_type": "Gasoline", "transmission": "Auto",
         "engine_size": "2.0", "horsepower": "150", "mpg_city": "30",
         "mpg_highway": "40", "base_price": "20000", "country": "USA"},
        {"vehicle_id": "2", "brand": "Y", "model": "B", "year": "2022",
         "category": "SUV", "fuel_type": "Diesel", "transmission": "Manual",
         "engine_size": "3.0", "horsepower": "200", "mpg_city": "25",
         "mpg_highway": "35", "base_price": "", "country": "Germany"},  # missing
    ])

    result = transform_vehicles(raw)
    assert len(result) == 1
    assert result.iloc[0]["vehicle_id"] == 1


def test_transform_sales_discount_calculation():
    import pandas as pd
    from etl.transform import transform_sales

    vehicles = pd.DataFrame([{
        "vehicle_id": 1, "brand": "Toyota", "model": "Camry",
        "year": 2022, "base_price": 25000.0,
        "fuel_type": "Gasoline", "country": "Japan",
    }])

    raw_sales = pd.DataFrame([{
        "sale_id":       "1",
        "vehicle_id":    "1",
        "sale_date":     "2023-06-15",
        "sale_price":    "24000",
        "dealer_city":   "LA",
        "dealer_state":  "CA",
        "customer_type": "Individual",
        "color":         "White",
        "mileage":       "0",
    }])

    result = transform_sales(raw_sales, vehicles)
    assert len(result) == 1
    assert result.iloc[0]["discount_amount"] == 1000.0
    assert result.iloc[0]["discount_pct"] == 4.0
