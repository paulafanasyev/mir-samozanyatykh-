"""
Metrics API - Security Hardened v8.4.1
ANO TsPS INN 9724016805
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import get_current_user, require_admin
from app.models import User

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/prometheus")
async def prometheus_metrics(
    current_user: User = Depends(require_admin)
):
    """
    Prometheus metrics - ADMIN ONLY

    Requires admin authentication.
    Not available to regular users or anonymous access.
    """
    # Return metrics only for admin users
    return {
        "status": "ok",
        "note": "Metrics require admin access",
        "user": current_user.email
    }
