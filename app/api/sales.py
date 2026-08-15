"""
API маршруты модуля продаж v7.5
Полный CRUD: Products, Invoices, Payments + ЮKassa интеграция
"""

from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logging import logger, log_audit
from app.models import User, Product, Invoice, InvoiceItem, Payment, Client
from app.schemas.sales import (
    ProductCreate, ProductUpdate, ProductOut,
    InvoiceCreate, InvoiceUpdate, InvoiceOut, InvoiceListOut,
    PaymentCreate, PaymentOut,
    YookassaPaymentRequest, YookassaPaymentResponse,
    YookassaWebhook, SalesStats, SalesDashboard, MonthlyRevenue,
)
from app.services.yookassa import yookassa_service, YookassaError
from app.services.pdf import pdf_service
from app.services.email import email_service


router = APIRouter(prefix="/api/sales", tags=["sales"])


# ============ PRODUCTS ============

@router.get("/products", response_model=List[ProductOut])
async def list_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список услуг/товаров пользователя"""
    result = await db.execute(
        select(Product)
        .where(Product.user_id == current_user.id)
        .order_by(Product.name)
    )
    return result.scalars().all()


@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Создание услуги/товара"""
    db_product = Product(
        user_id=current_user.id,
        name=product.name,
        description=product.description,
        price=product.price,
        unit=product.unit,
        sku=product.sku,
    )
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    
    await log_audit(
        action="product_created",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Product: {product.name}, Price: {product.price}",
    )
    return db_product


@router.get("/products/{product_id}", response_model=ProductOut)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получение услуги по ID"""
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.user_id == current_user.id,
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    return product


@router.put("/products/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: int,
    product: ProductUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Обновление услуги"""
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.user_id == current_user.id,
        )
    )
    db_product = result.scalar_one_or_none()
    if not db_product:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    
    update_data = product.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)
    
    await db.commit()
    await db.refresh(db_product)
    
    await log_audit(
        action="product_updated",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Product ID: {product_id}",
    )
    return db_product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удаление услуги (soft delete через is_active=False)"""
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.user_id == current_user.id,
        )
    )
    db_product = result.scalar_one_or_none()
    if not db_product:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    
    db_product.is_active = False
    await db.commit()
    
    await log_audit(
        action="product_deleted",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Product ID: {product_id}",
    )


# ============ INVOICES ============

@router.get("/invoices", response_model=dict)
async def list_invoices(
    status: Optional[str] = None,
    client_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список счетов с фильтрацией и пагинацией"""
    query = select(Invoice).where(Invoice.user_id == current_user.id)
    
    if status:
        query = query.where(Invoice.status == status)
    if client_id:
        query = query.where(Invoice.client_id == client_id)
    
    # Подсчёт total
    count_query = select(func.count(Invoice.id)).where(Invoice.user_id == current_user.id)
    if status:
        count_query = count_query.where(Invoice.status == status)
    if client_id:
        count_query = count_query.where(Invoice.client_id == client_id)
    
    total = await db.scalar(count_query)
    
    result = await db.execute(
        query.order_by(Invoice.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    invoices = result.scalars().all()
    
    return {
        "invoices": invoices,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
        },
    }


@router.post("/invoices", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice: InvoiceCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Создание счёта с позициями"""
    # Проверка клиента
    if invoice.client_id:
        client_result = await db.execute(
            select(Client).where(
                Client.id == invoice.client_id,
                Client.user_id == current_user.id,
            )
        )
        if not client_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Клиент не найден")
    
    # Генерация номера счёта
    today = datetime.now(timezone.utc)
    count = await db.scalar(
        select(func.count(Invoice.id)).where(
            Invoice.user_id == current_user.id,
            Invoice.created_at >= today.replace(hour=0, minute=0, second=0, microsecond=0),
        )
    )
    invoice_number = f"СЧ-{current_user.id}-{today.strftime('%Y%m%d')}-{count + 1:04d}"
    
    # Расчёт суммы
    total = sum(
        Decimal(str(item.quantity)) * Decimal(str(item.unit_price))
        for item in invoice.items
    )
    
    # Создание счёта
    db_invoice = Invoice(
        user_id=current_user.id,
        invoice_number=invoice_number,
        client_id=invoice.client_id,
        total_amount=total,
        due_date=datetime.combine(invoice.due_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        if invoice.due_date else None,
        notes=invoice.notes,
        status="draft",
    )
    db.add(db_invoice)
    await db.flush()
    
    # Создание позиций
    for item in invoice.items:
        db_item = InvoiceItem(
            invoice_id=db_invoice.id,
            description=item.description,
            quantity=Decimal(str(item.quantity)),
            unit_price=Decimal(str(item.unit_price)),
            total_price=Decimal(str(item.quantity)) * Decimal(str(item.unit_price)),
        )
        db.add(db_item)
    
    await db.commit()
    await db.refresh(db_invoice)
    
    await log_audit(
        action="invoice_created",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Invoice: {invoice_number}, Amount: {total}",
    )
    return db_invoice


@router.get("/invoices/{invoice_id}", response_model=InvoiceOut)
async def get_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получение счёта с позициями и платежами"""
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.user_id == current_user.id,
        )
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    return invoice


@router.put("/invoices/{invoice_id}", response_model=InvoiceOut)
async def update_invoice(
    invoice_id: int,
    invoice_update: InvoiceUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Обновление счёта"""
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.user_id == current_user.id,
        )
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    
    # Нельзя менять оплаченный счёт
    if invoice.status == "paid":
        raise HTTPException(status_code=400, detail="Нельзя изменить оплаченный счёт")
    
    update_data = invoice_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "due_date" and value:
            value = datetime.combine(value, datetime.min.time()).replace(tzinfo=timezone.utc)
        setattr(invoice, key, value)
    
    await db.commit()
    await db.refresh(invoice)
    
    await log_audit(
        action="invoice_updated",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Invoice ID: {invoice_id}",
    )
    return invoice


@router.delete("/invoices/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удаление счёта (только draft)"""
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.user_id == current_user.id,
        )
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    if invoice.status != "draft":
        raise HTTPException(status_code=400, detail="Можно удалить только черновик")
    
    await db.delete(invoice)
    await db.commit()
    
    await log_audit(
        action="invoice_deleted",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Invoice ID: {invoice_id}",
    )


@router.post("/invoices/{invoice_id}/send", response_model=dict)
async def send_invoice(
    invoice_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Отправка счёта клиенту (email + PDF)"""
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.user_id == current_user.id,
        )
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    if invoice.status != "draft":
        raise HTTPException(status_code=400, detail="Счёт уже отправлен или оплачен")
    
    # Получение клиента
    client = None
    if invoice.client_id:
        client_result = await db.execute(
            select(Client).where(Client.id == invoice.client_id)
        )
        client = client_result.scalar_one_or_none()
    
    # Генерация PDF
    seller = {
        "name": current_user.full_name or "Исполнитель",
        "inn": current_user.inn or "—",
        "email": current_user.email,
        "phone": current_user.phone or "—",
    }
    buyer = {
        "name": client.name if client else "Заказчик",
        "inn": client.inn if client else "—",
        "email": client.email if client else "",
        "phone": client.phone if client else "—",
    }
    
    items = [
        {
            "description": item.description,
            "quantity": float(item.quantity),
            "unit_price": float(item.unit_price),
        }
        for item in invoice.items
    ]
    
    pdf_bytes = pdf_service.generate_invoice(
        invoice_number=invoice.invoice_number,
        seller=seller,
        buyer=buyer,
        items=items,
        total=invoice.total_amount,
        due_date=invoice.due_date.strftime("%d.%m.%Y") if invoice.due_date else None,
        notes=invoice.notes,
        status="sent",
    )
    
    # Отправка email
    email_sent = False
    if client and client.email:
        email_sent = await email_service.send_invoice(
            email=client.email,
            invoice_number=invoice.invoice_number,
            pdf_content=pdf_bytes,
            total=float(invoice.total_amount),
        )
    
    # Обновление статуса
    invoice.status = "sent"
    invoice.pdf_path = f"data/invoices/{invoice.invoice_number}.pdf"
    await db.commit()
    
    # Сохранение PDF
    import os
    os.makedirs("data/invoices", exist_ok=True)
    with open(invoice.pdf_path, "wb") as f:
        f.write(pdf_bytes)
    
    await log_audit(
        action="invoice_sent",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Invoice: {invoice.invoice_number}, Email: {email_sent}",
    )
    
    return {
        "message": "Счёт отправлен",
        "invoice_number": invoice.invoice_number,
        "email_sent": email_sent,
        "pdf_generated": True,
    }


@router.get("/invoices/{invoice_id}/pdf")
async def get_invoice_pdf(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Скачивание PDF счёта"""
    from fastapi.responses import Response
    
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.user_id == current_user.id,
        )
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    
    # Если PDF уже сгенерирован
    if invoice.pdf_path:
        import os
        if os.path.exists(invoice.pdf_path):
            with open(invoice.pdf_path, "rb") as f:
                return Response(
                    content=f.read(),
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f"attachment; filename=\"{invoice.invoice_number}.pdf\""
                    },
                )
    
    # Иначе генерируем на лету
    client_result = await db.execute(
        select(Client).where(Client.id == invoice.client_id)
    ) if invoice.client_id else None
    client = client_result.scalar_one_or_none() if client_result else None
    
    seller = {
        "name": current_user.full_name or "Исполнитель",
        "inn": current_user.inn or "—",
        "email": current_user.email,
        "phone": current_user.phone or "—",
    }
    buyer = {
        "name": client.name if client else "Заказчик",
        "inn": client.inn if client else "—",
        "email": client.email if client else "",
        "phone": client.phone if client else "—",
    }
    
    items = [
        {
            "description": item.description,
            "quantity": float(item.quantity),
            "unit_price": float(item.unit_price),
        }
        for item in invoice.items
    ]
    
    pdf_bytes = pdf_service.generate_invoice(
        invoice_number=invoice.invoice_number,
        seller=seller,
        buyer=buyer,
        items=items,
        total=invoice.total_amount,
        due_date=invoice.due_date.strftime("%d.%m.%Y") if invoice.due_date else None,
        notes=invoice.notes,
        status=invoice.status,
    )
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=\"{invoice.invoice_number}.pdf\""
        },
    )


# ============ PAYMENTS ============

@router.post("/invoices/{invoice_id}/payments", response_model=PaymentOut)
async def create_payment(
    invoice_id: int,
    payment: PaymentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ручное создание платежа (наличные/перевод)"""
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.user_id == current_user.id,
        )
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    
    db_payment = Payment(
        invoice_id=invoice_id,
        amount=Decimal(str(payment.amount)),
        payment_method=payment.payment_method,
        status="completed",
        paid_at=datetime.now(timezone.utc),
    )
    db.add(db_payment)
    await db.flush()
    
    # Проверка полной оплаты
    payments_result = await db.execute(
        select(func.sum(Payment.amount)).where(
            Payment.invoice_id == invoice_id,
            Payment.status == "completed",
        )
    )
    total_paid = payments_result.scalar() or Decimal("0")
    
    if total_paid >= invoice.total_amount:
        invoice.status = "paid"
        invoice.paid_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(db_payment)
    
    await log_audit(
        action="payment_created",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Invoice: {invoice.invoice_number}, Amount: {payment.amount}",
    )
    return db_payment


@router.get("/invoices/{invoice_id}/payments", response_model=List[PaymentOut])
async def list_payments(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список платежей по счёту"""
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.user_id == current_user.id,
        )
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    
    payments_result = await db.execute(
        select(Payment)
        .where(Payment.invoice_id == invoice_id)
        .order_by(Payment.created_at.desc())
    )
    return payments_result.scalars().all()


# ============ YOOKASSA INTEGRATION ============

@router.post("/invoices/{invoice_id}/yookassa", response_model=YookassaPaymentResponse)
async def create_yookassa_payment(
    invoice_id: int,
    req: YookassaPaymentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Создание платежа через ЮKassa"""
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.user_id == current_user.id,
        )
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    if invoice.status not in ("draft", "sent", "overdue"):
        raise HTTPException(status_code=400, detail="Счёт нельзя оплатить")
    
    # Получение email клиента
    client_email = ""
    if invoice.client_id:
        client_result = await db.execute(
            select(Client).where(Client.id == invoice.client_id)
        )
        client = client_result.scalar_one_or_none()
        if client:
            client_email = client.email or ""
    
    try:
        yookassa_payment = await yookassa_service.create_payment(
            amount=invoice.total_amount,
            description=f"Оплата счёта {invoice.invoice_number}",
            invoice_id=invoice.id,
            return_url=req.return_url or f"https://{settings.DOMAIN}/payment/success",
            metadata={"client_email": client_email},
        )
        
        # Сохранение ID платежа
        invoice.yookassa_payment_id = yookassa_payment.get("id")
        if invoice.status == "draft":
            invoice.status = "sent"
        await db.commit()
        
        confirmation = yookassa_payment.get("confirmation", {})
        
        await log_audit(
            action="yookassa_payment_created",
            user_id=current_user.id,
            ip_address=request.client.host,
            details=f"Invoice: {invoice.invoice_number}, Yookassa ID: {yookassa_payment.get('id')}",
        )
        
        return YookassaPaymentResponse(
            payment_id=yookassa_payment.get("id"),
            confirmation_url=confirmation.get("confirmation_url", ""),
            status=yookassa_payment.get("status", "pending"),
            amount=invoice.total_amount,
            description=f"Оплата счёта {invoice.invoice_number}",
        )
        
    except YookassaError as e:
        logger.error(f"Yookassa payment creation failed: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/yookassa/webhook", status_code=status.HTTP_200_OK)
async def yookassa_webhook(
    webhook: YookassaWebhook,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Обработка webhook от ЮKassa"""
    # Проверка подписи (в production)
    # SECURITY: Verify webhook signature
    signature = request.headers.get("X-YooKassa-Signature")
    body = await request.body()

    if not yookassa_service.verify_webhook(signature, body):
        logger.warning(f"Invalid YooKassa webhook signature from {request.client.host}")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # SECURITY: Verify webhook IP
    if not yookassa_service.verify_webhook_ip(request.client.host):
        logger.warning(f"YooKassa webhook from unauthorized IP: {request.client.host}")
        raise HTTPException(status_code=403, detail="Unauthorized IP")
    
    payment_obj = webhook.object
    payment_id = payment_obj.get("id")
    status = payment_obj.get("status")
    metadata = payment_obj.get("metadata", {})
    
    invoice_id = yookassa_service.extract_invoice_id(metadata)
    if not invoice_id:
        logger.error(f"Yookassa webhook: no invoice_id in metadata")
        raise HTTPException(status_code=400, detail="No invoice_id")
    
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        logger.error(f"Yookassa webhook: invoice {invoice_id} not found")
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if status == "succeeded":
        amount = Decimal(str(payment_obj.get("amount", {}).get("value", 0)))
        
        # Создание записи о платеже
        db_payment = Payment(
            invoice_id=invoice.id,
            amount=amount,
            payment_method="yookassa",
            status="completed",
            yookassa_id=payment_id,
            paid_at=datetime.now(timezone.utc),
        )
        db.add(db_payment)
        
        invoice.status = "paid"
        invoice.paid_at = datetime.now(timezone.utc)
        await db.commit()
        
        logger.info(f"Yookassa payment succeeded: {payment_id} for invoice {invoice_id}")
        
        # Отправка уведомления (async)
        # TODO: через Celery/background tasks
        
    elif status == "canceled":
        invoice.status = "cancelled"
        await db.commit()
        logger.info(f"Yookassa payment cancelled: {payment_id}")
    
    return {"status": "ok"}


# ============ STATS ============

@router.get("/stats", response_model=SalesStats)
async def sales_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Статистика продаж"""
    total_invoices = await db.scalar(
        select(func.count(Invoice.id)).where(Invoice.user_id == current_user.id)
    )
    
    total_revenue = await db.scalar(
        select(func.sum(Invoice.total_amount)).where(
            Invoice.user_id == current_user.id,
            Invoice.status == "paid",
        )
    ) or Decimal("0")
    
    pending_amount = await db.scalar(
        select(func.sum(Invoice.total_amount)).where(
            Invoice.user_id == current_user.id,
            Invoice.status.in_(["sent", "draft"]),
        )
    ) or Decimal("0")
    
    overdue = await db.scalar(
        select(func.count(Invoice.id)).where(
            Invoice.user_id == current_user.id,
            Invoice.status == "sent",
            Invoice.due_date < datetime.now(timezone.utc),
        )
    )
    
    paid_count = await db.scalar(
        select(func.count(Invoice.id)).where(
            Invoice.user_id == current_user.id,
            Invoice.status == "paid",
        )
    )
    
    sent_count = await db.scalar(
        select(func.count(Invoice.id)).where(
            Invoice.user_id == current_user.id,
            Invoice.status == "sent",
        )
    )
    
    draft_count = await db.scalar(
        select(func.count(Invoice.id)).where(
            Invoice.user_id == current_user.id,
            Invoice.status == "draft",
        )
    )
    
    avg = await db.scalar(
        select(func.avg(Invoice.total_amount)).where(
            Invoice.user_id == current_user.id,
        )
    ) or Decimal("0")
    
    return SalesStats(
        total_invoices=total_invoices,
        total_revenue=total_revenue,
        pending_amount=pending_amount,
        overdue_invoices=overdue,
        paid_count=paid_count,
        sent_count=sent_count,
        draft_count=draft_count,
        average_invoice_amount=avg,
    )


@router.get("/dashboard", response_model=SalesDashboard)
async def sales_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Дашборд продаж"""
    stats = await sales_stats(db, current_user)
    
    # Месячная выручка (последние 12 мес)
    monthly_result = await db.execute(
        select(
            func.to_char(Invoice.paid_at, "YYYY-MM").label("month"),
            func.sum(Invoice.total_amount).label("total"),
            func.count(Invoice.id).label("count"),
        )
        .where(
            Invoice.user_id == current_user.id,
            Invoice.status == "paid",
            Invoice.paid_at >= datetime.now(timezone.utc).replace(day=1) - __import__("datetime").timedelta(days=365),
        )
        .group_by("month")
        .order_by("month")
    )
    monthly = [
        MonthlyRevenue(month=m.month, total=m.total, count=m.count)
        for m in monthly_result.all()
    ]
    
    # Последние счета
    recent_result = await db.execute(
        select(Invoice)
        .where(Invoice.user_id == current_user.id)
        .order_by(Invoice.created_at.desc())
        .limit(5)
    )
    recent = recent_result.scalars().all()
    
    # Топ клиентов по выручке
    top_clients_result = await db.execute(
        select(
            Client.name,
            func.sum(Invoice.total_amount).label("total"),
            func.count(Invoice.id).label("count"),
        )
        .join(Invoice, Client.id == Invoice.client_id)
        .where(
            Invoice.user_id == current_user.id,
            Invoice.status == "paid",
        )
        .group_by(Client.id, Client.name)
        .order_by(func.sum(Invoice.total_amount).desc())
        .limit(5)
    )
    top_clients = [
        {"name": c.name, "total": float(c.total), "count": c.count}
        for c in top_clients_result.all()
    ]
    
    return SalesDashboard(
        stats=stats,
        monthly_revenue=monthly,
        recent_invoices=recent,
        top_clients=top_clients,
    )
