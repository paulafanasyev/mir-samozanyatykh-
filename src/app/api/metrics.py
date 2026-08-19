"""Internal Prometheus metrics endpoint."""
from collections import Counter
from time import monotonic
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from app.core.config import settings

REQUESTS = Counter()
ERRORS = Counter()
LATENCY_SUM = 0.0

def record_request(status: int, duration: float):
    global LATENCY_SUM
    REQUESTS[(str(status // 100) + "xx")] += 1
    if status >= 500:
        ERRORS["5xx"] += 1
    LATENCY_SUM += duration

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

@router.get("/prometheus", response_class=PlainTextResponse, include_in_schema=False)
async def prometheus_metrics():
    total = sum(REQUESTS.values())
    body = [
        "# HELP mir_http_requests_total Total HTTP requests by status class",
        "# TYPE mir_http_requests_total counter",
        *[f'mir_http_requests_total{{status_class="{k}"}} {v}' for k,v in sorted(REQUESTS.items())],
        "# HELP mir_http_errors_total Total HTTP 5xx responses",
        "# TYPE mir_http_errors_total counter",
        f'mir_http_errors_total{{status_class="5xx"}} {ERRORS["5xx"]}',
        "# HELP mir_http_request_latency_seconds_total Sum of HTTP request durations",
        "# TYPE mir_http_request_latency_seconds_total counter",
        f"mir_http_request_latency_seconds_total {LATENCY_SUM:.6f}",
        "# HELP mir_process_requests_total Total observed HTTP requests",
        "# TYPE mir_process_requests_total gauge",
        f"mir_process_requests_total {total}",
    ]
    return "\n".join(body) + "\n"
