"""
API импорта/экспорта v6.8
CSV, Excel для клиентов и сделок
"""

import csv
import io
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User, Client, Deal

router = APIRouter(prefix="/api/import-export", tags=["import-export"])


# ============ EXPORT ============

@router.get("/clients/csv")
async def export_clients_csv(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Экспорт клиентов в CSV"""
    result = await db.execute(
        select(Client).where(Client.user_id == current_user.id)
    )
    clients = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Имя", "Email", "Телефон", "ИНН", "Тип", "Адрес", "Создан"])

    for c in clients:
        writer.writerow([
            c.id, c.name, c.email, c.phone, c.inn,
            c.type, c.address, c.created_at.isoformat() if c.created_at else ""
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=clients.csv"}
    )


@router.get("/deals/csv")
async def export_deals_csv(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Экспорт сделок в CSV"""
    result = await db.execute(
        select(Deal).where(Deal.user_id == current_user.id)
    )
    deals = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Название", "Сумма", "Статус", "Приоритет", "Клиент ID", "Создан"])

    for d in deals:
        writer.writerow([
            d.id, d.title, float(d.amount) if d.amount else 0,
            d.status, d.priority, d.client_id,
            d.created_at.isoformat() if d.created_at else ""
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=deals.csv"}
    )


# ============ IMPORT ============

@router.post("/clients/csv")
async def import_clients_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Импорт клиентов из CSV"""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Требуется CSV файл")

    content = await file.read()
    decoded = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))

    imported = 0
    errors = []

    for row in reader:
        try:
            client = Client(
                user_id=current_user.id,
                name=row.get("Имя") or row.get("name") or "Без имени",
                email=row.get("Email") or row.get("email"),
                phone=row.get("Телефон") or row.get("phone"),
                inn=row.get("ИНН") or row.get("inn"),
                type=row.get("Тип") or row.get("type") or "individual",
                address=row.get("Адрес") or row.get("address"),
            )
            db.add(client)
            imported += 1
        except Exception as e:
            errors.append(f"Строка {imported + len(errors) + 1}: {str(e)}")

    await db.commit()

    return {
        "imported": imported,
        "errors": errors,
        "total": imported + len(errors),
    }


@router.post("/deals/csv")
async def import_deals_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Импорт сделок из CSV"""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Требуется CSV файл")

    content = await file.read()
    decoded = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))

    imported = 0
    errors = []

    for row in reader:
        try:
            amount = float(row.get("Сумма") or row.get("amount") or 0)
            deal = Deal(
                user_id=current_user.id,
                title=row.get("Название") or row.get("title") or "Без названия",
                amount=amount,
                status=row.get("Статус") or row.get("status") or "new",
                priority=row.get("Приоритет") or row.get("priority") or "medium",
                client_id=int(row.get("Клиент ID") or row.get("client_id")) if (row.get("Клиент ID") or row.get("client_id")) else None,
            )
            db.add(deal)
            imported += 1
        except Exception as e:
            errors.append(f"Строка {imported + len(errors) + 1}: {str(e)}")

    await db.commit()

    return {
        "imported": imported,
        "errors": errors,
        "total": imported + len(errors),
    }
