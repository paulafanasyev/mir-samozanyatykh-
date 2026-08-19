"""
API импорта данных v7.9
CSV, Excel загрузка с валидацией и отчётом об ошибках
АНО ЦПС ИНН 9724016805
"""

import csv
import io
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import log_audit
from app.core.auth import get_current_user, get_current_user_optional
from app.models import User, Product, Client
from app.core.file_security import read_limited, validate_upload

router = APIRouter(prefix="/api/import", tags=["import"])


# ============ SCHEMAS ============

class ImportResult(BaseModel):
    total_rows: int
    imported: int
    errors: List[dict]
    warnings: List[str]


class ImportPreview(BaseModel):
    headers: List[str]
    rows: List[dict]
    total_rows: int


# ============ HELPERS ============

def parse_csv_file(content: bytes) -> tuple[List[str], List[dict]]:
    """Парсинг CSV файла"""
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    headers = reader.fieldnames or []
    rows = list(reader)
    return headers, rows


# ============ PRODUCTS IMPORT ============

@router.post("/products", response_model=ImportResult)
async def import_products(
    file: UploadFile = File(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Импорт продуктов из CSV"""
    validate_upload(file.filename, file.content_type, {".csv"})
    content = await read_limited(file, 10 * 1024 * 1024)
    headers, rows = parse_csv_file(content)

    errors = []
    imported = 0
    warnings = []

    # Ожидаемые колонки
    expected = ["name", "description", "price", "unit", "sku"]
    missing = [h for h in expected if h not in headers]
    if missing:
        warnings.append(f"Отсутствуют колонки (будут пропущены): {', '.join(missing)}")

    for i, row in enumerate(rows, 1):
        try:
            name = row.get("name", "").strip()
            if not name:
                errors.append({"row": i, "error": "Пустое название"})
                continue

            price_str = row.get("price", "0").strip().replace(",", ".")
            try:
                price = Decimal(price_str) if price_str else Decimal("0")
                if price < 0:
                    raise InvalidOperation
            except (InvalidOperation, ValueError):
                price = 0
                warnings.append(f"Строка {i}: неверная цена, установлено 0")

            # Проверка дубликата по SKU
            sku = row.get("sku", "").strip()
            if sku:
                existing = await db.scalar(
                    select(Product).where(
                        Product.user_id == current_user.id,
                        Product.sku == sku,
                    )
                )
                if existing:
                    errors.append({"row": i, "error": f"SKU {sku} уже существует"})
                    continue

            product = Product(
                user_id=current_user.id,
                name=name,
                description=row.get("description", "").strip() or None,
                price=price,
                unit=row.get("unit", "").strip() or None,
                sku=sku or None,
                is_active=True,
            )
            db.add(product)
            imported += 1

        except Exception as e:
            errors.append({"row": i, "error": "row_import_failed"})

    await db.commit()

    await log_audit(
        action="import_products",
        user_id=current_user.id,
        ip_address=request.client.host if request else None,
        details=f"Imported {imported}/{len(rows)} products, errors={len(errors)}",
    )

    return ImportResult(
        total_rows=len(rows),
        imported=imported,
        errors=errors,
        warnings=warnings,
    )


# ============ CLIENTS IMPORT ============

@router.post("/clients", response_model=ImportResult)
async def import_clients(
    file: UploadFile = File(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Импорт клиентов из CSV"""
    validate_upload(file.filename, file.content_type, {".csv"})
    content = await read_limited(file, 10 * 1024 * 1024)
    headers, rows = parse_csv_file(content)

    errors = []
    imported = 0
    warnings = []

    expected = ["name", "email", "phone", "company", "inn"]
    missing = [h for h in expected if h not in headers]
    if missing:
        warnings.append(f"Отсутствуют колонки: {', '.join(missing)}")

    for i, row in enumerate(rows, 1):
        try:
            name = row.get("name", "").strip()
            if not name:
                errors.append({"row": i, "error": "Пустое имя"})
                continue

            email = row.get("email", "").strip()
            if email:
                existing = await db.scalar(
                    select(Client).where(
                        Client.user_id == current_user.id,
                        Client.email == email,
                    )
                )
                if existing:
                    errors.append({"row": i, "error": f"Email {email} уже существует"})
                    continue

            client = Client(
                user_id=current_user.id,
                name=name,
                email=email or None,
                phone=row.get("phone", "").strip() or None,
                company=row.get("company", "").strip() or None,
                inn=row.get("inn", "").strip() or None,
                total_revenue=0,
                invoices_count=0,
            )
            db.add(client)
            imported += 1

        except Exception as e:
            errors.append({"row": i, "error": "row_import_failed"})

    await db.commit()

    await log_audit(
        action="import_clients",
        user_id=current_user.id,
        ip_address=request.client.host if request else None,
        details=f"Imported {imported}/{len(rows)} clients, errors={len(errors)}",
    )

    return ImportResult(
        total_rows=len(rows),
        imported=imported,
        errors=errors,
        warnings=warnings,
    )


# ============ PREVIEW ============

@router.post("/preview")
async def preview_import(
    file: UploadFile = File(...),
    max_rows: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """Предпросмотр CSV перед импортом"""
    validate_upload(file.filename, file.content_type, {".csv"})
    content = await read_limited(file, 10 * 1024 * 1024)
    headers, rows = parse_csv_file(content)

    return ImportPreview(
        headers=headers,
        rows=rows[:max_rows],
        total_rows=len(rows),
    )
