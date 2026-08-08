"""
Pydantic схемы для модуля продаж
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


# ============ PRODUCTS ============

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0, decimal_places=2)
    unit: str = Field(default="шт", max_length=50)
    sku: Optional[str] = Field(None, max_length=100)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    unit: Optional[str] = Field(None, max_length=50)
    sku: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class ProductOut(ProductBase):
    id: int
    user_id: int
    is_active: bool
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============ INVOICE ITEMS ============

class InvoiceItemBase(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(default=1.0, gt=0)
    unit_price: Decimal = Field(..., gt=0, decimal_places=2)
    
    @property
    def total_price(self) -> Decimal:
        return (self.quantity * self.unit_price).quantize(Decimal("0.01"))


class InvoiceItemCreate(InvoiceItemBase):
    pass


class InvoiceItemOut(InvoiceItemBase):
    id: int
    invoice_id: int
    total_price: Decimal
    
    class Config:
        from_attributes = True


# ============ INVOICES ============

class InvoiceBase(BaseModel):
    client_id: int
    due_date: Optional[date] = None
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    items: List[InvoiceItemCreate] = Field(..., min_length=1)
    
    @field_validator("items")
    @classmethod
    def validate_items(cls, v: List[InvoiceItemCreate]) -> List[InvoiceItemCreate]:
        if not v:
            raise ValueError("Счёт должен содержать минимум 1 позицию")
        return v


class InvoiceUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(draft|sent|paid|cancelled|overdue)$")
    due_date: Optional[date] = None
    notes: Optional[str] = None


class InvoiceOut(BaseModel):
    id: int
    user_id: int
    invoice_number: str
    client_id: Optional[int]
    total_amount: Decimal
    status: str
    due_date: Optional[datetime]
    notes: Optional[str]
    yookassa_payment_id: Optional[str]
    paid_at: Optional[datetime]
    pdf_path: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    items: List[InvoiceItemOut] = []
    payments: List["PaymentOut"] = []
    
    class Config:
        from_attributes = True


class InvoiceListOut(BaseModel):
    id: int
    invoice_number: str
    client_id: Optional[int]
    total_amount: Decimal
    status: str
    due_date: Optional[datetime]
    paid_at: Optional[datetime]
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============ PAYMENTS ============

class PaymentBase(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    payment_method: str = Field(default="card", pattern="^(card|sbp|cash|yookassa)$")


class PaymentCreate(PaymentBase):
    pass


class PaymentOut(PaymentBase):
    id: int
    invoice_id: int
    status: str
    yookassa_id: Optional[str]
    paid_at: Optional[datetime]
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============ YOOKASSA ============

class YookassaPaymentRequest(BaseModel):
    invoice_id: int
    return_url: Optional[str] = None


class YookassaPaymentResponse(BaseModel):
    payment_id: str
    confirmation_url: str
    status: str
    amount: Decimal
    description: str


class YookassaWebhook(BaseModel):
    event: str
    object: dict
    
    @field_validator("event")
    @classmethod
    def validate_event(cls, v: str) -> str:
        allowed = {"payment.succeeded", "payment.canceled", "payment.waiting_for_capture", "refund.succeeded"}
        if v not in allowed:
            raise ValueError(f"Неверный тип события: {v}")
        return v


# ============ SALES STATS ============

class SalesStats(BaseModel):
    total_invoices: int
    total_revenue: Decimal
    pending_amount: Decimal
    overdue_invoices: int
    paid_count: int
    sent_count: int
    draft_count: int
    average_invoice_amount: Decimal


class MonthlyRevenue(BaseModel):
    month: str
    total: Decimal
    count: int


class SalesDashboard(BaseModel):
    stats: SalesStats
    monthly_revenue: List[MonthlyRevenue]
    recent_invoices: List[InvoiceListOut]
    top_clients: List[dict]
