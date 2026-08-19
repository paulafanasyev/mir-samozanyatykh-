"""
PDF Reports API v7.3
Генерация отчётов и документов в PDF
"""

import io
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import log_audit
from app.core.auth import get_current_user, get_current_user_optional
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

    # Реальная генерация PDF через ReportLab.
    pdf_buffer = io.BytesIO()
    font_path = "app/assets/fonts/DejaVuSans.ttf"
    pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
    pdf = canvas.Canvas(pdf_buffer, pagesize=(595, 842))
    pdf.setFont("DejaVuSans", 18)
    pdf.drawString(50, 790, "Отчёт по выручке")
    pdf.setFont("DejaVuSans", 10)
    pdf.drawString(50, 768, f"Пользователь: {current_user.full_name or current_user.email}")
    pdf.drawString(50, 750, f"Период: {period} ({start.strftime('%d.%m.%Y')} — {now.strftime('%d.%m.%Y')})")
    pdf.setFont("DejaVuSans", 13)
    pdf.drawString(50, 700, f"Общая выручка: {float(revenue):,.2f} ₽")
    pdf.drawString(50, 675, f"Закрытых сделок: {deals_count}")
    avg = float(revenue) / deals_count if deals_count else 0
    pdf.drawString(50, 650, f"Средний чек: {avg:,.2f} ₽")
    pdf.setFont("DejaVuSans", 9)
    pdf.drawString(50, 610, f"Сгенерировано: {now.strftime('%d.%m.%Y %H:%M')}")
    pdf.drawString(50, 590, "Мир Самозанятых — АНО ЦПС, ИНН 9724016805")
    pdf.save()
    pdf_buffer.seek(0)

    await log_audit(
        action="report_generated",
        user_id=current_user.id,
        details=f"Revenue report, period: {period}",
    )
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=revenue_{period}.pdf"},
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

    pdf_buffer = io.BytesIO()
    font_path = "app/assets/fonts/DejaVuSans.ttf"
    pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
    pdf = canvas.Canvas(pdf_buffer, pagesize=(595, 842))
    pdf.setFont("DejaVuSans", 18)
    pdf.drawString(50, 790, "Отчёт по клиентам")
    pdf.setFont("DejaVuSans", 11)
    pdf.drawString(50, 765, f"Всего клиентов: {len(clients)}")
    y = 735
    pdf.setFont("DejaVuSans", 9)
    for i, c in enumerate(clients, 1):
        if y < 60:
            pdf.showPage()
            pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
            pdf.setFont("DejaVuSans", 9)
            y = 790
        name = (c.name or "-")[:55]
        email = (c.email or "-")[:45]
        pdf.drawString(50, y, f"{i}. {name} | {email}")
        y -= 16
    pdf.setFont("DejaVuSans", 8)
    pdf.drawString(50, 35, "Мир Самозанятых — АНО ЦПС, ИНН 9724016805")
    pdf.save()
    pdf_buffer.seek(0)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=clients_report.pdf"},
    )

