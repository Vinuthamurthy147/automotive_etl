"""
Flask dashboard — fetches data from the FastAPI backend and renders a web UI.

Start with:
    python -m dashboard.app
or:
    flask --app dashboard.app run --port 5000
"""
import os

import requests
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify

load_dotenv()

app = Flask(__name__)

API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")


def _fetch(endpoint: str) -> list | dict:
    """Call the FastAPI backend and return parsed JSON."""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        app.logger.error("Failed to reach API at %s: %s", endpoint, exc)
        return []


# ── Routes ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    brand_summary      = _fetch("/analytics/brand-summary")
    fuel_breakdown     = _fetch("/analytics/fuel-type-breakdown")
    top_models         = _fetch("/analytics/top-models?limit=5")
    monthly_sales      = _fetch("/analytics/monthly-sales")
    state_revenue      = _fetch("/analytics/state-revenue")

    # Aggregate KPIs
    total_revenue = sum(b.get("total_revenue", 0) for b in brand_summary)
    total_sales   = sum(b.get("total_sales", 0)   for b in brand_summary)
    avg_price     = round(total_revenue / total_sales, 2) if total_sales else 0
    brand_count   = len(brand_summary)

    return render_template(
        "index.html",
        brand_summary=brand_summary,
        fuel_breakdown=fuel_breakdown,
        top_models=top_models,
        monthly_sales=monthly_sales,
        state_revenue=state_revenue[:10],
        total_revenue=total_revenue,
        total_sales=total_sales,
        avg_price=avg_price,
        brand_count=brand_count,
    )


@app.route("/api/brand-summary")
def api_brand_summary():
    return jsonify(_fetch("/analytics/brand-summary"))


@app.route("/api/monthly-sales")
def api_monthly_sales():
    return jsonify(_fetch("/analytics/monthly-sales"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
