"""
Backups API v7.3
Экспорт и резервное копирование данных
"""

import json
import io
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import log_audit
from app.core.auth import get_current_user, get_current_user_optional
from app.models import User, Client, Deal, Invoice, Task, Call, Product, PipelineStage

router = APIRouter(prefix="/api/backups", tags=["backups"])


@router.get("/export/json")
async def export_all_json(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Полный экспорт данных пользователя в JSON"""

    # Клиенты
    clients_result = await db.execute(
        select(Client).where(Client.user_id == current_user.id)
    )
    clients = clients_result.scalars().all()

    # Сделки
    deals_result = await db.execute(
        select(Deal).where(Deal.user_id == current_user.id)
    )
    deals = deals_result.scalars().all()

    # Счета
    invoices_result = await db.execute(
        select(Invoice).where(Invoice.user_id == current_user.id)
    )
    invoices = invoices_result.scalars().all()

    # Задачи
    tasks_result = await db.execute(
        select(Task).where(Task.user_id == current_user.id)
    )
    tasks = tasks_result.scalars().all()

    # Звонки
    calls_result = await db.execute(
        select(Call).where(Call.user_id == current_user.id)
    )
    calls = calls_result.scalars().all()

    # Продукты
    products_result = await db.execute(
        select(Product).where(Product.user_id == current_user.id)
    )
    products = products_result.scalars().all()

    # Этапы воронки
    stages_result = await db.execute(
        select(PipelineStage).where(PipelineStage.user_id == current_user.id)
    )
    stages = stages_result.scalars().all()

    backup_data = {
        "export_metadata": {
            "app_version": "7.3.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "user_id": current_user.id,
            "user_email": current_user.email,
        },
        "clients": [
            {
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "phone": c.phone,
                "inn": c.inn,
                "type": c.type,
                "address": c.address,
                "company": c.company,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in clients
        ],
        "deals": [
            {
                "id": d.id,
                "title": d.title,
                "amount": float(d.amount) if d.amount else None,
                "status": d.status,
                "priority": d.priority,
                "probability": d.probability,
                "client_id": d.client_id,
                "stage_id": d.stage_id,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in deals
        ],
        "invoices": [
            {
                "id": i.id,
                "invoice_number": i.invoice_number,
                "amount": float(i.amount) if i.amount else None,
                "status": i.status,
                "client_id": i.client_id,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in invoices
        ],
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "priority": t.priority,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "client_id": t.client_id,
                "deal_id": t.deal_id,
            }
            for t in tasks
        ],
        "calls": [
            {
                "id": c.id,
                "direction": c.direction,
                "duration": c.duration,
                "notes": c.notes,
                "outcome": c.outcome,
                "client_id": c.client_id,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in calls
        ],
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "price": float(p.price) if p.price else None,
                "unit": p.unit,
            }
            for p in products
        ],
        "pipeline_stages": [
            {
                "id": s.id,
                "name": s.name,
                "order": s.order,
                "color": s.color,
            }
            for s in stages
        ],
    }

    json_bytes = json.dumps(backup_data, ensure_ascii=False, indent=2).encode("utf-8")

    await log_audit(
        action="backup_exported",
        user_id=current_user.id,
        details=f"Full export, size: {len(json_bytes)} bytes",
    )

    return StreamingResponse(
        io.BytesIO(json_bytes),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=backup_{current_user.id}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"
        },
    )


@router.get("/export/csv")
async def export_all_csv(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Экспорт данных в CSV (ZIP архив)"""
    import csv
    import zipfile

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Клиенты
        clients_result = await db.execute(
            select(Client).where(Client.user_id == current_user.id)
        )
        clients = clients_result.scalars().all()

        clients_csv = io.StringIO()
        writer = csv.writer(clients_csv)
        writer.writerow(["id", "name", "email", "phone", "inn", "type", "address"])
        for c in clients:
            writer.writerow([c.id, c.name, c.email, c.phone, c.inn, c.type, c.address])
        zf.writestr("clients.csv", clients_csv.getvalue())

        # Сделки
        deals_result = await db.execute(
            select(Deal).where(Deal.user_id == current_user.id)
        )
        deals = deals_result.scalars().all()

        deals_csv = io.StringIO()
        writer = csv.writer(deals_csv)
        writer.writerow(["id", "title", "amount", "status", "priority", "client_id"])
        for d in deals:
            writer.writerow([d.id, d.title, d.amount, d.status, d.priority, d.client_id])
        zf.writestr("deals.csv", deals_csv.getvalue())

    zip_buffer.seek(0)

    await log_audit(
        action="backup_csv_exported",
        user_id=current_user.id,
    )

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=backup_{current_user.id}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.zip"
        },
    )


@router.post("/schedule")
async def schedule_backup(
    frequency: str = "weekly",  # daily, weekly, monthly
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Настройка автоматического бэкапа"""

    allowed = {"daily", "weekly", "monthly"}
    if frequency not in allowed:
        raise HTTPException(status_code=400, detail="Invalid backup frequency")
    current_user.backup_frequency = frequency
    current_user.backup_enabled = True
    await db.commit()

    return {
        "message": f"Автоматический бэкап настроен: {frequency}",
        "frequency": frequency,
        "next_backup": None,
        "scheduler": "docker-backup-service",
    }
