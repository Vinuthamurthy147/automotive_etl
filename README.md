# Automotive Sales ETL Pipeline & Analytics API

A production-style data engineering project that demonstrates an end-to-end **ETL pipeline** with a **REST API** and **web dashboard** for automotive sales data.

## Architecture

```
CSV Files (Raw Data)
      │
      ▼
┌─────────────┐
│  ETL Pipeline│  pandas · numpy
│  extract →  │
│  transform →│
│  load       │
└──────┬──────┘
       │  SQLAlchemy
       ▼
┌─────────────┐
│    MySQL    │  automotive_db
│  Database   │
└──────┬──────┘
       │
  ┌────┴─────┐
  ▼          ▼
FastAPI    Flask
Analytics  Dashboard
  API      (calls API)
```

## Tech Stack

| Layer        | Technology                  |
|--------------|-----------------------------|
| Language     | Python 3.11+                |
| ETL          | Pandas, NumPy               |
| REST API     | FastAPI + Uvicorn           |
| Dashboard    | Flask + Chart.js            |
| Database     | MySQL 8.x + SQLAlchemy ORM  |
| Testing      | Pytest                      |

## Project Structure

```
automotive-etl-api/
├── data/
│   ├── vehicles.csv          # 25 vehicle specs
│   └── sales.csv             # 65 sales transactions
├── etl/
│   ├── extract.py            # CSV ingestion
│   ├── transform.py          # Pandas/NumPy cleaning & enrichment
│   └── load.py               # MySQL upserts via SQLAlchemy
├── api/
│   ├── main.py               # FastAPI app
│   ├── database.py           # DB session management
│   ├── models.py             # ORM + Pydantic schemas
│   └── routers/
│       ├── vehicles.py       # /vehicles endpoints
│       └── analytics.py      # /analytics endpoints
├── dashboard/
│   ├── app.py                # Flask app
│   └── templates/
│       └── index.html        # Chart.js dashboard
├── sql/
│   └── schema.sql            # MySQL DDL + views
├── tests/
│   └── test_api.py           # Pytest unit & integration tests
├── run_etl.py                # ETL entrypoint
├── requirements.txt
└── .env.example
```

##  Quick Start

### 1. Clone & install dependencies

```bash
git clone https://github.com/<your-username>/automotive-etl-api.git
cd automotive-etl-api

python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Set up MySQL

```bash
mysql -u root -p < sql/schema.sql
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env — set your MySQL credentials
```

### 4. Run the ETL pipeline

```bash
python run_etl.py
```

Output:
```
2024-01-01 | INFO     | etl_pipeline | PHASE 1 — EXTRACT
2024-01-01 | INFO     | etl.extract  | Extracted 25 vehicle records
2024-01-01 | INFO     | etl.extract  | Extracted 65 sales records
2024-01-01 | INFO     | etl_pipeline | PHASE 2 — TRANSFORM
2024-01-01 | INFO     | etl_pipeline | PHASE 3 — LOAD
2024-01-01 | INFO     | etl_pipeline | ETL PIPELINE COMPLETED SUCCESSFULLY
```

### 5. Start the FastAPI server

```bash
uvicorn api.main:app --reload --port 8000
```

Interactive API docs → http://localhost:8000/docs

### 6. Start the Flask dashboard

```bash
# In a second terminal
python -m dashboard.app
```

Dashboard → http://localhost:5000

## API Endpoints

### Vehicles

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/vehicles` | List vehicles (filter by brand, category, fuel_type, year, price) |
| GET | `/vehicles/{vehicle_id}` | Get vehicle details |
| GET | `/vehicles/brands` | List all brands |
| GET | `/vehicles/{vehicle_id}/sales` | Sales history for a vehicle |

### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/brand-summary` | Revenue & sales count by brand |
| GET | `/analytics/monthly-sales` | Monthly sales trend |
| GET | `/analytics/top-models` | Best-selling models |
| GET | `/analytics/fuel-type-breakdown` | Sales by fuel type |
| GET | `/analytics/state-revenue` | Revenue by dealer state |

### Example request

```bash
curl "http://localhost:8000/analytics/brand-summary"
```

```json
[
  {
    "brand": "Tesla",
    "country": "Usa",
    "total_sales": 8,
    "total_revenue": 334800.0,
    "avg_sale_price": 41850.0,
    "avg_discount_pct": 2.15
  },
  ...
]
```

## Data Model

```sql
brands      (id, name, country)
    │
    └── vehicles (vehicle_id, brand_id, model, year, category,
    │             fuel_type, transmission, engine_size,
    │             horsepower, mpg_city, mpg_highway, mpg_combined, base_price)
    │
    └── sales    (sale_id, vehicle_id, sale_date, sale_price,
                  dealer_city, dealer_state, customer_type, color,
                  mileage, discount_amount, discount_pct)

etl_logs    (id, run_date, records_extracted, records_transformed,
             records_loaded, status, message)
```

## Running Tests

```bash
pytest tests/ -v
```

## ETL Transform Steps

| Step | Operation |
|------|-----------|
| Extract | Read CSV into Pandas DataFrames |
| Clean | Normalise column names, drop duplicates |
| Type cast | Coerce numerics, parse dates |
| Enrich | Compute `mpg_combined` (EPA formula: 55% city + 45% hwy) |
| Enrich | Compute `discount_amount` and `discount_pct` per sale |
| Date parts | Extract `sale_year`, `sale_month`, `sale_quarter` |
| Load | Upsert to MySQL via SQLAlchemy (`ON DUPLICATE KEY UPDATE`) |
| Log | Write ETL run summary to `etl_logs` table |


