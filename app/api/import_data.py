"""
Import data API with CSV protection
"""

import csv
import io
import magic
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter(prefix="/import", tags=["import"])

MAX_CSV_SIZE = 5 * 1024 * 1024
MAX_CSV_ROWS = 10000
MAX_CELL_SIZE = 10000
MAX_ROW_SIZE = 100000


def sanitize_csv_cell(cell: str) -> str:
    """Prevent CSV formula injection"""
    if cell and cell[0] in ('=', '+', '-', '@', '\t', '\r'):
        return "'" + cell
    return cell


@router.post("/preview")
async def import_preview(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Preview CSV with security checks"""
    content = await file.read(MAX_CSV_SIZE + 1)
    if len(content) > MAX_CSV_SIZE:
        raise HTTPException(413, f"File too large (max {MAX_CSV_SIZE} bytes)")

    mime = magic.from_buffer(content, mime=True)
    if mime not in ('text/csv', 'text/plain', 'application/csv'):
        raise HTTPException(400, f"Invalid file type: {mime}")

    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(400, "File must have .csv extension")

    text = content.decode('utf-8', errors='replace')
    reader = csv.reader(io.StringIO(text))

    rows = []
    row_count = 0
    for row in reader:
        row_count += 1
        if row_count > MAX_CSV_ROWS:
            raise HTTPException(413, f"Too many rows (max {MAX_CSV_ROWS})")

        row_text = ','.join(row)
        if len(row_text) > MAX_ROW_SIZE:
            raise HTTPException(413, "Row too large")

        cleaned = []
        for cell in row:
            if len(cell) > MAX_CELL_SIZE:
                raise HTTPException(413, "Cell too large")
            cleaned.append(sanitize_csv_cell(cell))

        rows.append(cleaned)

    return {
        "rows": rows[:100],
        "total_rows": row_count,
        "columns": rows[0] if rows else []
    }
