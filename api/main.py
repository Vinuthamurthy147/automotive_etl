"""
FastAPI application — Automotive Sales Analytics API.

Start with:
    uvicorn api.main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import analytics, vehicles

app = FastAPI(
    title="Automotive Sales Analytics API",
    description=(
        "REST API exposing ETL-processed automotive sales data stored in MySQL. "
        "Provides vehicle listings, sales transactions, and aggregated analytics."
    ),
    version="1.0.0",
    contact={"name": "GitHub", "url": "https://github.com"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(vehicles.router)
app.include_router(analytics.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "Automotive Sales Analytics API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
