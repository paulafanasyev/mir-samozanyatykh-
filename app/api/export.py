"""
API экспорта данных v7.8
CSV, Excel, PDF для всех модулей
АНО ЦПС ИНН 9724016805
"""

import csv
import io
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logging import log_audit
from app.models import User, Product, Invoice, InvoiceItem, Client, Deal, Task, CalendarEvent

router = APIRouter(prefix="/api/export", tags=["export"])


# ============ HELPERS ============

def csv_response(data: list[dict], filename: str):
    """Создание CSV ответа"""
    if not data:
        return StreamingResponse(
            io.StringIO(""),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    output.seek(0)

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ============ PRODUCTS EXPORT ============

@router.get("/products")
async def export_products(
    format: str = Query("csv", pattern=r"^(csv|json)$"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Экспорт продуктов"""
    result = await db.execute(
        select(Product).where(Product.user_id == current_user.id)
        .order_by(Product.created_at.desc())
    )
    products = result.scalars().all()

    data = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description or "",
            "price": float(p.price) if p.price else 0,
            "unit": p.unit or "",
            "sku": p.sku or "",
            "is_active": "Да" if p.is_active else "Нет",
            "created_at": p.created_at.isoformat() if p.created_at else "",
        }
        for p in products
    ]

    await log_audit(
        action="export_products",
        user_id=current_user.id,
        ip_address=request.client.host if request else None,
        details=f"Exported {len(data)} products as {format}",
    )

    if format == "csv":
        return csv_response(data, f"products_{current_user.id}_{datetime.now().strftime('%Y%m%d')}.csv")
    return {"data": data, "count": len(data)}


# ============ INVOICES EXPORT ============

@router.get("/invoices")
async def export_invoices(
    format: str = Query("csv", pattern=r"^(csv|json)$"),
    status: Optional[str] = None,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Экспорт счетов"""
    query = select(Invoice).where(Invoice.user_id == current_user.id)
    if status:
        query = query.where(Invoice.status == status)
    query = query.order_by(Invoice.created_at.desc())

    result = await db.execute(query)
    invoices = result.scalars().all()

    data = []
    for inv in invoices:
        items_result = await db.execute(
            select(InvoiceItem).where(InvoiceItem.invoice_id == inv.id)
        )
        items = items_result.scalars().all()
        items_str = "; ".join([f"{i.product_name} x{i.quantity}={i.total_price}" for i in items])

        data.append({
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "client_name": inv.client_name or "",
            "client_email": inv.client_email or "",
            "total_amount": float(inv.total_amount) if inv.total_amount else 0,
            "status": inv.status,
            "paid_at": inv.paid_at.isoformat() if inv.paid_at else "",
            "created_at": inv.created_at.isoformat() if inv.created_at else "",
            "items": items_str,
        })

    await log_audit(
        action="export_invoices",
        user_id=current_user.id,
        ip_address=request.client.host if request else None,
        details=f"Exported {len(data)} invoices as {format}",
    )

    if format == "csv":
        return csv_response(data, f"invoices_{current_user.id}_{datetime.now().strftime('%Y%m%d')}.csv")
    return {"data": data, "count": len(data)}


# ============ CLIENTS EXPORT ============

@router.get("/clients")
async def export_clients(
    format: str = Query("csv", pattern=r"^(csv|json)$"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Экспорт клиентов"""
    result = await db.execute(
        select(Client).where(Client.user_id == current_user.id)
        .order_by(Client.created_at.desc())
    )
    clients = result.scalars().all()

    data = [
        {
            "id": c.id,
            "name": c.name,
            "email": c.email or "",
            "phone": c.phone or "",
            "company": c.company or "",
            "inn": c.inn or "",
            "notes": c.notes or "",
            "total_revenue": float(c.total_revenue) if c.total_revenue else 0,
            "invoices_count": c.invoices_count or 0,
            "created_at": c.created_at.isoformat() if c.created_at else "",
        }
        for c in clients
    ]

    await log_audit(
        action="export_clients",
        user_id=current_user.id,
        ip_address=request.client.host if request else None,
        details=f"Exported {len(data)} clients as {format}",
    )

    if format == "csv":
        return csv_response(data, f"clients_{current_user.id}_{datetime.now().strftime('%Y%m%d')}.csv")
    return {"data": data, "count": len(data)}


# ============ DEALS EXPORT ============

@router.get("/deals")
async def export_deals(
    format: str = Query("csv", pattern=r"^(csv|json)$"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Экспорт сделок"""
    result = await db.execute(
        select(Deal).where(Deal.user_id == current_user.id)
        .order_by(Deal.created_at.desc())
    )
    deals = result.scalars().all()

    data = [
        {
            "id": d.id,
            "title": d.title,
            "description": d.description or "",
            "value": float(d.value) if d.value else 0,
            "currency": d.currency or "RUB",
            "status": d.status,
            "stage": d.stage or "",
            "probability": d.probability or 0,
            "client_name": d.client.name if d.client else "",
            "expected_close": d.expected_close.isoformat() if d.expected_close else "",
            "created_at": d.created_at.isoformat() if d.created_at else "",
        }
        for d in deals
    ]

    await log_audit(
        action="export_deals",
        user_id=current_user.id,
        ip_address=request.client.host if request else None,
        details=f"Exported {len(data)} deals as {format}",
    )

    if format == "csv":
        return csv_response(data, f"deals_{current_user.id}_{datetime.now().strftime('%Y%m%d')}.csv")
    return {"data": data, "count": len(data)}


# ============ TASKS EXPORT ============

@router.get("/tasks")
async def export_tasks(
    format: str = Query("csv", pattern=r"^(csv|json)$"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Экспорт задач"""
    result = await db.execute(
        select(Task).where(Task.user_id == current_user.id)
        .order_by(Task.created_at.desc())
    )
    tasks = result.scalars().all()

    data = [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description or "",
            "status": t.status,
            "priority": t.priority,
            "due_date": t.due_date.isoformat() if t.due_date else "",
            "completed_at": t.completed_at.isoformat() if t.completed_at else "",
            "created_at": t.created_at.isoformat() if t.created_at else "",
        }
        for t in tasks
    ]

    await log_audit(
        action="export_tasks",
        user_id=current_user.id,
        ip_address=request.client.host if request else None,
        details=f"Exported {len(data)} tasks as {format}",
    )

    if format == "csv":
        return csv_response(data, f"tasks_{current_user.id}_{datetime.now().strftime('%Y%m%d')}.csv")
    return {"data": data, "count": len(data)}


# ============ FULL EXPORT ============

@router.get("/all")
async def export_all(
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Полный экспорт всех данных пользователя в JSON"""
    # Продукты
    products_res = await db.execute(select(Product).where(Product.user_id == current_user.id))
    products = products_res.scalars().all()

    # Клиенты
    clients_res = await db.execute(select(Client).where(Client.user_id == current_user.id))
    clients = clients_res.scalars().all()

    # Сделки
    deals_res = await db.execute(select(Deal).where(Deal.user_id == current_user.id))
    deals = deals_res.scalars().all()

    # Задачи
    tasks_res = await db.execute(select(Task).where(Task.user_id == current_user.id))
    tasks = tasks_res.scalars().all()

    # События
    events_res = await db.execute(select(CalendarEvent).where(CalendarEvent.user_id == current_user.id))
    events = events_res.scalars().all()

    data = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user_email": current_user.email,
        "products": [{"id": p.id, "name": p.name, "price": float(p.price) if p.price else 0} for p in products],
        "clients": [{"id": c.id, "name": c.name, "email": c.email, "phone": c.phone} for c in clients],
        "deals": [{"id": d.id, "title": d.title, "value": float(d.value) if d.value else 0, "status": d.status} for d in deals],
        "tasks": [{"id": t.id, "title": t.title, "status": t.status, "priority": t.priority} for t in tasks],
        "events": [{"id": e.id, "title": e.title, "start_time": e.start_time.isoformat() if e.start_time else ""} for e in events],
    }

    await log_audit(
        action="export_all",
        user_id=current_user.id,
        ip_address=request.client.host if request else None,
        details="Full data export",
    )

    return data
