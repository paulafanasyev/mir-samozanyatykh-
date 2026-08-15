"""
Export API with CSV formula injection protection
"""

import csv
import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter(prefix="/export", tags=["export"])


def sanitize_csv_value(value: str) -> str:
    """Prevent CSV formula injection"""
    if value and value[0] in ('=', '+', '-', '@', '\t', '\r'):
        return "'" + value
    return value


@router.get("/csv")
async def export_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export data as CSV with formula injection protection"""
    data = []

    output = io.StringIO()
    writer = csv.writer(output)

    if data:
        headers = list(data[0].keys())
        writer.writerow([sanitize_csv_value(h) for h in headers])

        for row in data:
            writer.writerow([
                sanitize_csv_value(str(v)) for v in row.values()
            ])

    output.seek(0)

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=export.csv"}
    )
