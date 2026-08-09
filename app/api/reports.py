"""
PDF Reports API v7.3
Генерация отчётов и документов в PDF
"""

import io
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logging import log_audit
from app.models import User, Client, Deal, Invoice, Task

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/revenue/pdf")
async def revenue_report_pdf(
    period: str = "month",  # week, month, quarter, year
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """PDF отчёт по выручке"""

    now = datetime.now(timezone.utc)
    if period == "week":
        start = now - timedelta(days=7)
    elif period == "month":
        start = now - timedelta(days=30)
    elif period == "quarter":
        start = now - timedelta(days=90)
    elif period == "year":
        start = now - timedelta(days=365)
    else:
        start = now - timedelta(days=30)

    # Статистика
    revenue = await db.scalar(
        select(func.sum(Deal.amount)).where(
            Deal.user_id == current_user.id,
            Deal.status == "won",
            Deal.actual_close_date >= start,
        )
    ) or 0

    deals_count = await db.scalar(
        select(func.count(Deal.id)).where(
            Deal.user_id == current_user.id,
            Deal.status == "won",
            Deal.actual_close_date >= start,
        )
    )

    # Генерация HTML для PDF
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Отчёт по выручке</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; color: #333; }}
        h1 {{ color: #1976D2; border-bottom: 2px solid #1976D2; padding-bottom: 10px; }}
        .header {{ margin-bottom: 30px; }}
        .stat {{ background: #f5f5f5; padding: 20px; margin: 10px 0; border-radius: 8px; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #1976D2; }}
        .stat-label {{ font-size: 14px; color: #666; }}
        .footer {{ margin-top: 40px; font-size: 12px; color: #999; border-top: 1px solid #ddd; padding-top: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Отчёт по выручке</h1>
        <p>Пользователь: {current_user.full_name or current_user.email}</p>
        <p>Период: {period} ({start.strftime('%d.%m.%Y')} — {now.strftime('%d.%m.%Y')})</p>
    </div>

    <div class="stat">
        <div class="stat-label">Общая выручка</div>
        <div class="stat-value">{float(revenue):,.2f} ₽</div>
    </div>

    <div class="stat">
        <div class="stat-label">Закрытых сделок</div>
        <div class="stat-value">{deals_count}</div>
    </div>

    <div class="stat">
        <div class="stat-label">Средний чек</div>
        <div class="stat-value">{float(revenue)/deals_count if deals_count else 0:,.2f} ₽</div>
    </div>

    <div class="footer">
        <p>Сгенерировано: {now.strftime('%d.%m.%Y %H:%M')}</p>
        <p>Мир Самозанятых — АНО ЦПС, ИНН 9724016805</p>
    </div>
</body>
</html>
"""

    # В реальном приложении — конвертация HTML в PDF через WeasyPrint или pdfkit
    # Здесь возвращаем HTML для демонстрации

    await log_audit(
        action="report_generated",
        user_id=current_user.id,
        details=f"Revenue report, period: {period}",
    )

    return StreamingResponse(
        io.BytesIO(html_content.encode("utf-8")),
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename=revenue_{period}.html"},
    )


@router.get("/clients/pdf")
async def clients_report_pdf(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """PDF отчёт по клиентам"""

    result = await db.execute(
        select(Client).where(Client.user_id == current_user.id)
    )
    clients = result.scalars().all()

    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Отчёт по клиентам</title>
<style>
    body {{ font-family: Arial, sans-serif; margin: 40px; }}
    h1 {{ color: #1976D2; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
    th {{ background: #1976D2; color: white; padding: 10px; text-align: left; }}
    td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
    tr:nth-child(even) {{ background: #f5f5f5; }}
</style>
</head>
<body>
    <h1>Отчёт по клиентам</h1>
    <p>Всего клиентов: {len(clients)}</p>
    <table>
        <tr><th>№</th><th>Имя</th><th>Email</th><th>Телефон</th><th>Тип</th><th>Создан</th></tr>
"""

    for i, c in enumerate(clients, 1):
        html += f"""
        <tr>
            <td>{i}</td>
            <td>{c.name}</td>
            <td>{c.email or '-'}</td>
            <td>{c.phone or '-'}</td>
            <td>{c.type}</td>
            <td>{c.created_at.strftime('%d.%m.%Y') if c.created_at else '-'}</td>
        </tr>
"""

    html += """
    </table>
    <p style="margin-top: 30px; font-size: 12px; color: #999;">
        Мир Самозанятых — АНО ЦПС, ИНН 9724016805
    </p>
</body>
</html>
"""

    return StreamingResponse(
        io.BytesIO(html.encode("utf-8")),
        media_type="text/html",
        headers={"Content-Disposition": "attachment; filename=clients_report.html"},
    )


@router.get("/dashboard-summary")
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Сводный отчёт для дашборда"""

    clients_count = await db.scalar(
        select(func.count(Client.id)).where(Client.user_id == current_user.id)
    )

    deals_total = await db.scalar(
        select(func.count(Deal.id)).where(Deal.user_id == current_user.id)
    )
    deals_won = await db.scalar(
        select(func.count(Deal.id)).where(
            Deal.user_id == current_user.id,
            Deal.status == "won",
        )
    )
    revenue = await db.scalar(
        select(func.sum(Deal.amount)).where(
            Deal.user_id == current_user.id,
            Deal.status == "won",
        )
    ) or 0

    pending_tasks = await db.scalar(
        select(func.count(Task.id)).where(
            Task.user_id == current_user.id,
            Task.status.in_(["pending", "in_progress"]),
        )
    )

    unpaid_invoices = await db.scalar(
        select(func.count(Invoice.id)).where(
            Invoice.user_id == current_user.id,
            Invoice.status.in_(["draft", "sent"]),
        )
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "user": current_user.full_name or current_user.email,
        "summary": {
            "clients": clients_count,
            "deals_total": deals_total,
            "deals_won": deals_won,
            "conversion_rate": round(deals_won/deals_total*100, 1) if deals_total else 0,
            "revenue": float(revenue),
            "pending_tasks": pending_tasks,
            "unpaid_invoices": unpaid_invoices,
        },
    }
