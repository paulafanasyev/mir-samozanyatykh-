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
from app.models import User, Client, Deal
from app.core.auth import get_current_user, get_current_user_optional
from app.core.file_security import read_limited, validate_upload

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
    validate_upload(file.filename, file.content_type, {".csv"})
    content = await read_limited(file, 10 * 1024 * 1024)
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
            errors.append(f"Строка {imported + len(errors) + 1}: ошибка обработки")

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
    validate_upload(file.filename, file.content_type, {".csv"})
    content = await read_limited(file, 10 * 1024 * 1024)
    decoded = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))

    imported = 0
    errors = []

    for row in reader:
        try:
            from decimal import Decimal, InvalidOperation
            try:
                amount = Decimal(str(row.get("Сумма") or row.get("amount") or "0").replace(",", "."))
            except (InvalidOperation, ValueError):
                raise ValueError("Некорректная сумма")
            raw_client_id = row.get("Клиент ID") or row.get("client_id")
            client_id = int(raw_client_id) if raw_client_id else None
            if client_id is not None:
                client = await db.scalar(
                    select(Client).where(
                        Client.id == client_id,
                        Client.user_id == current_user.id,
                    )
                )
                if client is None:
                    raise ValueError("Клиент не найден")
            deal = Deal(
                user_id=current_user.id,
                title=(row.get("Название") or row.get("title") or "Без названия").strip()[:255],
                amount=amount,
                status=(row.get("Статус") or row.get("status") or "new").strip(),
                priority=(row.get("Приоритет") or row.get("priority") or "medium").strip(),
                client_id=client_id,
            )
            db.add(deal)
            imported += 1
        except Exception as e:
            errors.append(f"Строка {imported + len(errors) + 1}: ошибка обработки")

    await db.commit()

    return {
        "imported": imported,
        "errors": errors,
        "total": imported + len(errors),
    }
