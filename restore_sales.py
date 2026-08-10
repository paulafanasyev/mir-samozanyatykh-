with open('server.py', 'r') as f:
    c = f.read()

sales_api = '''
# ============ SALES MODULE API ============

class InvoiceCreate(BaseModel):
    client_id: int
    due_date: Optional[date] = None
    notes: Optional[str] = None
    items: List[dict] = []

class InvoiceUpdate(BaseModel):
    status: Optional[str] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None

class PaymentCreate(BaseModel):
    amount: float
    payment_method: str = "card"

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    unit: str = "шт"

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    unit: Optional[str] = None
    is_active: Optional[bool] = None

@app.get("/api/sales/products")
async def list_products(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Product).where(Product.user_id == current_user.id, Product.is_active == True).order_by(Product.name))
    products = result.scalars().all()
    return [{"id": p.id, "name": p.name, "description": p.description, "price": p.price, "unit": p.unit, "is_active": p.is_active, "created_at": p.created_at.isoformat() if p.created_at else None} for p in products]

@app.post("/api/sales/products")
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_product = Product(user_id=current_user.id, name=product.name, description=product.description, price=product.price, unit=product.unit)
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    await log_audit(db=db, action="product_created", user_id=current_user.id, details=f"Product: {product.name}")
    return {"id": db_product.id, "name": db_product.name, "price": db_product.price}

@app.put("/api/sales/products/{product_id}")
async def update_product(product_id: int, product: ProductUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Product).where(Product.id == product_id, Product.user_id == current_user.id))
    db_product = result.scalar_one_or_none()
    if not db_product:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    for key, value in product.model_dump(exclude_unset=True).items():
        setattr(db_product, key, value)
    await db.commit()
    return {"id": db_product.id, "name": db_product.name, "price": db_product.price}

@app.delete("/api/sales/products/{product_id}")
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Product).where(Product.id == product_id, Product.user_id == current_user.id))
    db_product = result.scalar_one_or_none()
    if not db_product:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    await db.delete(db_product)
    await db.commit()
    return {"message": "Услуга удалена"}

@app.get("/api/sales/invoices")
async def list_invoices(status: Optional[str] = None, page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=50), db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = select(Invoice).where(Invoice.user_id == current_user.id)
    if status:
        query = query.where(Invoice.status == status)
    total = await db.scalar(select(func.count(Invoice.id)).where(Invoice.user_id == current_user.id))
    result = await db.execute(query.order_by(Invoice.created_at.desc()).offset((page - 1) * per_page).limit(per_page))
    invoices = result.scalars().all()
    return {"invoices": [{"id": i.id, "invoice_number": i.invoice_number, "client_id": i.client_id, "total_amount": i.total_amount, "status": i.status, "due_date": i.due_date.isoformat() if i.due_date else None, "paid_at": i.paid_at.isoformat() if i.paid_at else None, "created_at": i.created_at.isoformat() if i.created_at else None} for i in invoices], "pagination": {"page": page, "per_page": per_page, "total": total, "total_pages": (total + per_page - 1) // per_page}}

@app.post("/api/sales/invoices")
async def create_invoice(invoice: InvoiceCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = datetime.now(timezone.utc)
    count = await db.scalar(select(func.count(Invoice.id)).where(Invoice.user_id == current_user.id, Invoice.created_at >= today.replace(hour=0, minute=0, second=0, microsecond=0)))
    invoice_number = f"СЧ-{current_user.id}-{today.strftime('%Y%m%d')}-{count + 1:04d}"
    total = sum(item.get("quantity", 1) * item.get("unit_price", 0) for item in invoice.items)
    db_invoice = Invoice(user_id=current_user.id, invoice_number=invoice_number, client_id=invoice.client_id, total_amount=total, due_date=datetime.combine(invoice.due_date, datetime.min.time()).replace(tzinfo=timezone.utc) if invoice.due_date else None, notes=invoice.notes, status="draft")
    db.add(db_invoice)
    await db.flush()
    for item in invoice.items:
        db_item = InvoiceItem(invoice_id=db_invoice.id, description=item.get("description", ""), quantity=item.get("quantity", 1), unit_price=item.get("unit_price", 0), total_price=item.get("quantity", 1) * item.get("unit_price", 0))
        db.add(db_item)
    await db.commit()
    await db.refresh(db_invoice)
    await log_audit(db=db, action="invoice_created", user_id=current_user.id, details=f"Invoice: {invoice_number}, Amount: {total}")
    return {"id": db_invoice.id, "invoice_number": db_invoice.invoice_number, "total_amount": db_invoice.total_amount, "status": db_invoice.status}

@app.get("/api/sales/invoices/{invoice_id}")
async def get_invoice(invoice_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == current_user.id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    items_result = await db.execute(select(InvoiceItem).where(InvoiceItem.invoice_id == invoice_id))
    items = items_result.scalars().all()
    payments_result = await db.execute(select(Payment).where(Payment.invoice_id == invoice_id))
    payments = payments_result.scalars().all()
    return {"id": invoice.id, "invoice_number": invoice.invoice_number, "client_id": invoice.client_id, "total_amount": invoice.total_amount, "status": invoice.status, "due_date": invoice.due_date.isoformat() if invoice.due_date else None, "notes": invoice.notes, "yookassa_payment_id": invoice.yookassa_payment_id, "paid_at": invoice.paid_at.isoformat() if invoice.paid_at else None, "created_at": invoice.created_at.isoformat() if invoice.created_at else None, "items": [{"id": i.id, "description": i.description, "quantity": i.quantity, "unit_price": i.unit_price, "total_price": i.total_price} for i in items], "payments": [{"id": p.id, "amount": p.amount, "status": p.status, "payment_method": p.payment_method, "paid_at": p.paid_at.isoformat() if p.paid_at else None} for p in payments]}

@app.put("/api/sales/invoices/{invoice_id}")
async def update_invoice(invoice_id: int, invoice_update: InvoiceUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == current_user.id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    for key, value in invoice_update.model_dump(exclude_unset=True).items():
        if key == "due_date" and value:
            value = datetime.combine(value, datetime.min.time()).replace(tzinfo=timezone.utc)
        setattr(invoice, key, value)
    await db.commit()
    return {"id": invoice.id, "status": invoice.status}

@app.delete("/api/sales/invoices/{invoice_id}")
async def delete_invoice(invoice_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == current_user.id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    await db.delete(invoice)
    await db.commit()
    return {"message": "Счёт удалён"}

@app.post("/api/sales/invoices/{invoice_id}/send")
async def send_invoice(invoice_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == current_user.id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    if invoice.status != "draft":
        raise HTTPException(status_code=400, detail="Счёт уже отправлен или оплачен")
    invoice.status = "sent"
    await db.commit()
    await log_audit(db=db, action="invoice_sent", user_id=current_user.id, details=f"Invoice: {invoice.invoice_number}")
    return {"message": "Счёт отправлен клиенту", "invoice_number": invoice.invoice_number}

@app.post("/api/sales/invoices/{invoice_id}/payments")
async def create_payment(invoice_id: int, payment: PaymentCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == current_user.id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    db_payment = Payment(invoice_id=invoice_id, amount=payment.amount, payment_method=payment.payment_method, status="pending")
    db.add(db_payment)
    await db.commit()
    await db.refresh(db_payment)
    payments_result = await db.execute(select(func.sum(Payment.amount)).where(Payment.invoice_id == invoice_id, Payment.status == "completed"))
    total_paid = payments_result.scalar() or 0
    if total_paid >= invoice.total_amount:
        invoice.status = "paid"
        invoice.paid_at = datetime.now(timezone.utc)
        await db.commit()
    await log_audit(db=db, action="payment_created", user_id=current_user.id, details=f"Invoice: {invoice.invoice_number}, Amount: {payment.amount}")
    return {"id": db_payment.id, "amount": db_payment.amount, "status": db_payment.status}

@app.get("/api/sales/invoices/{invoice_id}/payments")
async def list_payments(invoice_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == current_user.id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    payments_result = await db.execute(select(Payment).where(Payment.invoice_id == invoice_id).order_by(Payment.created_at.desc()))
    payments = payments_result.scalars().all()
    return [{"id": p.id, "amount": p.amount, "status": p.status, "payment_method": p.payment_method, "paid_at": p.paid_at.isoformat() if p.paid_at else None, "created_at": p.created_at.isoformat() if p.created_at else None} for p in payments]

@app.get("/api/sales/stats")
async def sales_stats(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_invoices = await db.scalar(select(func.count(Invoice.id)).where(Invoice.user_id == current_user.id))
    total_revenue = await db.scalar(select(func.sum(Invoice.total_amount)).where(Invoice.user_id == current_user.id, Invoice.status == "paid")) or 0
    pending_amount = await db.scalar(select(func.sum(Invoice.total_amount)).where(Invoice.user_id == current_user.id, Invoice.status.in_(["sent", "draft"]))) or 0
    overdue = await db.scalar(select(func.count(Invoice.id)).where(Invoice.user_id == current_user.id, Invoice.status == "sent", Invoice.due_date < datetime.now(timezone.utc)))
    return {"total_invoices": total_invoices, "total_revenue": float(total_revenue), "pending_amount": float(pending_amount), "overdue_invoices": overdue}
'''

marker = '# ============ CONTRACT TEMPLATES DATA ============'
if marker in c and '# ============ SALES MODULE API' not in c:
    c = c.replace(marker, sales_api + '\\n' + marker)
    print("Sales API restored!")
else:
    print("Sales API already present or marker not found")

with open('server.py', 'w') as f:
    f.write(c)

print("Done!")
