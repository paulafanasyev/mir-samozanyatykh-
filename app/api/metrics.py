from fastapi import APIRouter
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time

router = APIRouter(prefix="/api/metrics", tags=["Metrics"])

# Метрики
REQUEST_COUNT = Counter(
    "app_request_count", 
    "Total requests", 
    ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "app_request_latency_seconds", 
    "Request latency", 
    ["method", "endpoint"]
)
ACTIVE_USERS = Gauge(
    "app_active_users", 
    "Number of active users"
)
DB_CONNECTIONS = Gauge(
    "app_db_connections", 
    "Database connections"
)

@router.get("/prometheus", summary="Prometheus metrics")
async def prometheus_metrics():
    """Метрики в формате Prometheus"""
    from fastapi.responses import Response
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@router.get("/business", summary="Business metrics")
async def business_metrics():
    """Бизнес-метрики"""
    return {
        "users": {
            "total": 1234,
            "active_today": 892,
            "new_today": 15,
        },
        "revenue": {
            "today": 45000,
            "month": 1250000,
            "year": 15200000,
        },
        "invoices": {
            "total": 5678,
            "pending": 234,
            "paid": 5123,
            "overdue": 321,
        },
        "deals": {
            "total": 890,
            "won": 456,
            "lost": 234,
            "in_progress": 200,
        },
    }
