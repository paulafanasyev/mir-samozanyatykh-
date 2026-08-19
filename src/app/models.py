"""
ORM models SQLAlchemy for Mir Samozanyatykh v8.1
ANO CPS INN 9724016805
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Numeric,
    ForeignKey, JSON, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    inn = Column(String(20), nullable=True, index=True)
    branding_settings = Column(JSON, default=dict, nullable=False)

    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    is_moderator = Column(Boolean, default=False)

    subscription_tier = Column(String(20), default="free")
    subscription_expires = Column(DateTime(timezone=True), nullable=True)

    points = Column(Integer, default=0)
    level = Column(String(20), default="beginner")

    # Реферальная система
    referral_code = Column(String(20), unique=True, nullable=True, index=True)
    referred_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    referral_count = Column(Integer, default=0)
    referral_earnings = Column(Numeric(15, 2), default=Decimal("0"))

    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    mfa = relationship("UserMFA", back_populates="user", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="user", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="user", cascade="all, delete-orphan")
    clients = relationship("Client", back_populates="user", cascade="all, delete-orphan")
    deals = relationship("Deal", back_populates="user", cascade="all, delete-orphan")
    contracts = relationship("SignedContract", back_populates="user", cascade="all, delete-orphan")
    calls = relationship("Call", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    events = relationship("CalendarEvent", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    referrals = relationship("Referral", foreign_keys="Referral.referrer_id", back_populates="referrer", cascade="all, delete-orphan")

    @property
    def user_tier(self):
        return self.subscription_tier or "free"

    @property
    def role(self):
        if self.is_admin:
            return "admin"
        if self.is_moderator:
            return "moderator"
        return "user"


    # Password reset fields (SECURITY: hashed + TTL)
    password_reset_token_hash = Column(String(255))
    password_reset_expires_at = Column(DateTime(timezone=True))
    password_reset_created_at = Column(DateTime(timezone=True))

    # Email verification fields (SECURITY: hashed + TTL)
    email_verification_token_hash = Column(String(255))
    email_verification_expires_at = Column(DateTime(timezone=True))

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    jti = Column(String(255), unique=True, nullable=False, index=True)
    token_type = Column(String(20), nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="sessions")


class UserMFA(Base):
    __tablename__ = "user_mfa"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    totp_secret = Column(String(255), nullable=False)
    backup_codes = Column(Text, default="[]")
    is_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="mfa")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    success = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="audit_logs")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(15, 2), nullable=False)
    unit = Column(String(50), default="sht")
    sku = Column(String(100), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="products")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_number = Column(String(100), nullable=False, unique=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True)
    total_amount = Column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    status = Column(String(20), default="draft", nullable=False, index=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    yookassa_payment_id = Column(String(255), nullable=True, index=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    pdf_path = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="invoices")
    client = relationship("Client", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(15, 4), nullable=False, default=Decimal("1"))
    unit_price = Column(Numeric(15, 2), nullable=False)
    total_price = Column(Numeric(15, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    invoice = relationship("Invoice", back_populates="items")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    payment_method = Column(String(20), default="card", nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    yookassa_id = Column(String(255), nullable=True, index=True)
    idempotency_key = Column(String(255), nullable=True, unique=True, index=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    invoice = relationship("Invoice", back_populates="payments")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    company = Column(String(255), nullable=True)
    inn = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(20), default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="clients")
    invoices = relationship("Invoice", back_populates="client")
    deals = relationship("Deal", back_populates="client")


class PipelineStage(Base):
    __tablename__ = "pipeline_stages"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    order = Column(Integer, default=0, nullable=False)
    color = Column(String(7), default="#1976D2", nullable=False)  # hex color
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")
    deals = relationship("Deal", back_populates="stage")


class Deal(Base):
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True)
    stage_id = Column(Integer, ForeignKey("pipeline_stages.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    amount = Column(Numeric(15, 2), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="new", nullable=False)
    priority = Column(String(20), default="medium", nullable=False)
    probability = Column(Integer, default=0, nullable=False)  # 0-100%
    expected_close_date = Column(DateTime(timezone=True), nullable=True)
    actual_close_date = Column(DateTime(timezone=True), nullable=True)
    source = Column(String(50), nullable=True)  # referral, direct, social, etc.
    deadline = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="deals")
    client = relationship("Client", back_populates="deals")
    stage = relationship("PipelineStage", back_populates="deals")


class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True)
    direction = Column(String(10), default="out", nullable=False)  # in, out
    duration = Column(Integer, default=0, nullable=False)  # seconds
    recording_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    outcome = Column(String(50), nullable=True)  # answered, missed, voicemail, callback
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="calls")
    client = relationship("Client")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True)
    deal_id = Column(Integer, ForeignKey("deals.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="pending", nullable=False)  # pending, in_progress, completed, cancelled
    priority = Column(String(20), default="medium", nullable=False)  # low, medium, high, urgent
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="tasks")
    client = relationship("Client")
    deal = relationship("Deal")


class ContractTemplate(Base):
    __tablename__ = "contract_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    content = Column(Text, nullable=False)
    variables = Column(JSON, default=list)
    is_premium = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SignedContract(Base):
    __tablename__ = "signed_contracts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    template_id = Column(Integer, ForeignKey("contract_templates.id", ondelete="SET NULL"), nullable=True)
    template_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    contract_data = Column(JSON, default=dict)
    variables_data = Column(JSON, default=dict)
    signature_data = Column(JSON, nullable=True)
    pdf_path = Column(String(500), nullable=True)
    status = Column(String(20), default="draft", nullable=False)
    signed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="contracts")
    template = relationship("ContractTemplate")


class WebSocketConnection(Base):
    __tablename__ = "websocket_connections"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    connection_id = Column(String(255), unique=True, nullable=False, index=True)
    channel = Column(String(100), nullable=False, default="general")
    ip_address = Column(String(45), nullable=True)
    connected_at = Column(DateTime(timezone=True), server_default=func.now())
    last_ping = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    event_type = Column(String(50), default="meeting")
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True)
    deal_id = Column(Integer, ForeignKey("deals.id", ondelete="SET NULL"), nullable=True, index=True)
    is_all_day = Column(Boolean, default=False)
    location = Column(String(255), nullable=True)
    reminder_minutes = Column(Integer, default=15)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="events")
    client = relationship("Client")
    deal = relationship("Deal")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    notification_type = Column(String(50), default="info")
    is_read = Column(Boolean, default=False)
    action_url = Column(String(500), nullable=True)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="notifications")


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True)
    referrer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    referred_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    status = Column(String(20), default="registered", nullable=False)  # registered, active, paid
    reward_amount = Column(Numeric(15, 2), default=Decimal("0"))
    reward_paid = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    converted_at = Column(DateTime(timezone=True), nullable=True)

    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="referrals")
    referred = relationship("User", foreign_keys=[referred_id])


class DocumentTemplate(Base):
    __tablename__ = "document_templates"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, default="general")
    content = Column(Text, nullable=False)
    variables = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    key_prefix = Column(String(8), nullable=False)
    scopes = Column(JSON, default=list)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")


class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    events = Column(JSON, default=list)
    secret = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    failure_count = Column(Integer, default=0)
    last_delivered_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(Integer, primary_key=True)
    webhook_id = Column(Integer, ForeignKey("webhooks.id", ondelete="CASCADE"), nullable=False, index=True)
    event = Column(String(100), nullable=False)
    payload = Column(JSON, default=dict)
    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    success = Column(Boolean, default=False)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    webhook = relationship("Webhook")


class Transaction(Base):
    """Бухгалтерская проводка — доходы и расходы"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # Связь со счетом (если доход от счета)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True, index=True)

    transaction_type = Column(String(20), nullable=False, index=True)  # income, expense
    category = Column(String(100), nullable=False, index=True)  # salary, service, rent, tax, etc.
    subcategory = Column(String(100), nullable=True)

    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="RUB", nullable=False)

    # Описание
    description = Column(Text, nullable=True)
    counterparty = Column(String(255), nullable=True)  # С кем операция
    counterparty_inn = Column(String(20), nullable=True)
    counterparty_type = Column(String(20), nullable=True)  # individual, legal_entity, unknown

    # Даты
    transaction_date = Column(DateTime(timezone=True), nullable=False, index=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)

    # Документы
    document_type = Column(String(50), nullable=True)  # receipt, invoice, act, contract
    document_number = Column(String(100), nullable=True)
    document_path = Column(String(500), nullable=True)  # путь к скану/фото чека

    # Налоговые данные
    tax_amount = Column(Numeric(15, 2), nullable=True)  # НДС или налог НПД
    tax_rate = Column(Numeric(5, 2), nullable=True)  # Ставка налога
    tax_deductible = Column(Boolean, default=False)  # Можно ли вычесть из налога

    # Метаданные
    source = Column(String(50), default="manual")  # manual, bank, fns, yookassa
    bank_transaction_id = Column(String(255), nullable=True, index=True)
    fns_receipt_id = Column(String(255), nullable=True, index=True)

    # Статус
    status = Column(String(20), default="confirmed", nullable=False)  # pending, confirmed, cancelled

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")
    invoice = relationship("Invoice")

    __table_args__ = (
        Index("ix_transactions_user_date", "user_id", "transaction_date"),
        Index("ix_transactions_user_type", "user_id", "transaction_type"),
        UniqueConstraint("user_id", "bank_transaction_id", name="uq_transactions_user_bank_id"),
    )


class TaxReport(Base):
    """Налоговый отчёт / декларация"""
    __tablename__ = "tax_reports"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    report_type = Column(String(50), nullable=False, index=True)  # npd_quarterly, ndfl_annual, usn
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # Финансовые показатели
    total_income = Column(Numeric(15, 2), default=Decimal("0"))
    total_expense = Column(Numeric(15, 2), default=Decimal("0"))
    taxable_amount = Column(Numeric(15, 2), default=Decimal("0"))
    tax_amount = Column(Numeric(15, 2), default=Decimal("0"))
    tax_rate_applied = Column(Numeric(5, 2), nullable=True)  # 4%, 6%, 13% и т.д.

    # Вычеты
    deductions = Column(JSON, default=dict)  # {professional: 10000, social: 5000}
    deduction_total = Column(Numeric(15, 2), default=Decimal("0"))

    # Статус отчёта
    status = Column(String(20), default="draft", nullable=False)  # draft, submitted, accepted, rejected
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)

    # Документы
    declaration_path = Column(String(500), nullable=True)  # PDF декларации
    fns_response = Column(Text, nullable=True)
    fns_status = Column(String(50), nullable=True)

    # AI-анализ
    ai_recommendations = Column(Text, nullable=True)
    risk_level = Column(String(20), default="low")  # low, medium, high

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")


class TaxDeduction(Base):
    """Налоговый вычет"""
    __tablename__ = "tax_deductions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    deduction_type = Column(String(50), nullable=False, index=True)  # professional, social, property, investment
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    amount = Column(Numeric(15, 2), nullable=False)
    max_amount = Column(Numeric(15, 2), nullable=True)  # Максимальная сумма по закону

    # Документы
    document_path = Column(String(500), nullable=True)
    document_number = Column(String(100), nullable=True)

    # Статус
    status = Column(String(20), default="active", nullable=False)  # active, used, expired
    used_in_report_id = Column(Integer, ForeignKey("tax_reports.id", ondelete="SET NULL"), nullable=True)

    year = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")


class FNSReceipt(Base):
    """Чек из ФНС (проверка через API ФНС)"""
    __tablename__ = "fns_receipts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Данные чека
    fns_id = Column(String(255), nullable=False, index=True)  # ID чека в ФНС
    fiscal_document_number = Column(String(50), nullable=True)
    fiscal_sign = Column(String(50), nullable=True)
    receipt_date = Column(DateTime(timezone=True), nullable=False)

    # Суммы
    total_amount = Column(Numeric(15, 2), nullable=False)
    cash_amount = Column(Numeric(15, 2), default=Decimal("0"))
    ecash_amount = Column(Numeric(15, 2), default=Decimal("0"))

    # Продавец
    seller_name = Column(String(255), nullable=True)
    seller_inn = Column(String(20), nullable=True, index=True)

    # Покупатель (если чек выдан самозанятому)
    buyer_name = Column(String(255), nullable=True)
    buyer_inn = Column(String(20), nullable=True)

    # Товары/услуги в чеке
    items = Column(JSON, default=list)  # [{name, price, quantity, sum}]

    # Статус
    status = Column(String(20), default="verified", nullable=False)  # verified, cancelled, refund
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Связь с транзакцией
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    transaction = relationship("Transaction")

    __table_args__ = (
        Index("ix_fns_receipts_user_date", "user_id", "receipt_date"),
        UniqueConstraint("user_id", "fns_id", name="uq_fns_receipts_user_fns_id"),
    )


class BudgetCategory(Base):
    """Категория бюджета (планирование)"""
    __tablename__ = "budget_categories"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(100), nullable=False)
    category_type = Column(String(20), nullable=False)  # income, expense
    color = Column(String(7), default="#1976D2", nullable=False)
    icon = Column(String(50), default="dollar-sign", nullable=True)
    monthly_limit = Column(Numeric(15, 2), nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")


class BankConnection(Base):
    """Подключение банковского счета"""
    __tablename__ = "bank_connections"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    bank_name = Column(String(50), nullable=False, index=True)
    account_number = Column(String(50), nullable=True)
    account_name = Column(String(255), nullable=True)

    api_token_encrypted = Column(Text, nullable=True)
    refresh_token_encrypted = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_sync_status = Column(String(20), default="pending")
    last_sync_error = Column(Text, nullable=True)
    total_synced = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")


class PushSubscription(Base):
    """Push-уведомления Web Push"""
    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    endpoint = Column(String(500), nullable=False)
    p256dh = Column(String(255), nullable=False)
    auth = Column(String(255), nullable=False)

    device_info = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")


class NotificationPreference(Base):
    """Настройки уведомлений пользователя"""
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    email_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=True)
    telegram_enabled = Column(Boolean, default=False)
    telegram_chat_id = Column(String(100), nullable=True)

    invoice_paid = Column(Boolean, default=True)
    invoice_overdue = Column(Boolean, default=True)
    new_client = Column(Boolean, default=True)
    deal_won = Column(Boolean, default=True)
    deal_lost = Column(Boolean, default=True)
    task_reminder = Column(Boolean, default=True)
    task_overdue = Column(Boolean, default=True)
    bank_sync = Column(Boolean, default=True)
    tax_reminder = Column(Boolean, default=True)
    marketing = Column(Boolean, default=False)

    quiet_hours_start = Column(Integer, nullable=True)
    quiet_hours_end = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")


class CRMAutomation(Base):
    """Автоматизация CRM — триггеры и действия"""
    __tablename__ = "crm_automations"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)

    trigger_type = Column(String(50), nullable=False)
    trigger_config = Column(JSON, default=dict)

    action_type = Column(String(50), nullable=False)
    action_config = Column(JSON, default=dict)

    run_count = Column(Integer, default=0)
    last_run_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")


# ============================================================
# ADDITIONAL MODELS FOR RENDER DEPLOYMENT
# ANO TsPS INN 9724016805
# ============================================================

class SubscriptionTier(Base):
    """Subscription pricing tiers"""
    __tablename__ = "subscription_tiers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    price = Column(Integer, default=0)
    description = Column(Text)
    features = Column(Text)  # JSON string
    max_contracts = Column(Integer, default=5)
    max_clients = Column(Integer, default=10)
    ai_requests_per_day = Column(Integer, default=10)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Achievement(Base):
    """Gamification achievements"""
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    icon = Column(String(50), default="star")
    points = Column(Integer, default=10)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserAchievement(Base):
    """User achievements mapping"""
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    earned_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint('user_id', 'achievement_id', name='uq_user_achievement'),)


class FAQ(Base):
    """Frequently Asked Questions"""
    __tablename__ = "faqs"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(50), default="General")
    order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    views = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class BlogPost(Base):
    """Blog articles"""
    __tablename__ = "blog_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    excerpt = Column(Text)
    author = Column(String(100), default="ANO TsPS")
    category = Column(String(50), default="General")
    tags = Column(Text)  # JSON string
    featured_image = Column(String(255))
    is_published = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    published_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class BlogComment(Base):
    """Blog post comments"""
    __tablename__ = "blog_comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("blog_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    author_name = Column(String(100))
    author_email = Column(String(100))
    content = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=False)
    parent_id = Column(Integer, ForeignKey("blog_comments.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())




class SvetlanaChatMessage(Base):
    __tablename__ = "svetlana_chat_messages"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user / assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class EmailCampaign(Base):
    __tablename__ = "email_campaigns"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default="queued")  # queued/sending/completed/failed
    recipient_count = Column(Integer, nullable=False, default=0)
    sent_count = Column(Integer, nullable=False, default=0)
    opened_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

class SvetlanaKnowledge(Base):
    """AI Svetlana knowledge base"""
    __tablename__ = "svetlana_knowledge"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String(100), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(50), default="General")
    keywords = Column(Text)  # JSON string
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class MarketplaceItem(Base):
    """Marketplace products/services"""
    __tablename__ = "marketplace_items"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text)
    price = Column(Numeric(12, 2), nullable=False)
    category = Column(String(50))
    tags = Column(Text)  # JSON string
    images = Column(Text)  # JSON string
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    views = Column(Integer, default=0)
    sales_count = Column(Integer, default=0)
    rating = Column(Numeric(2, 1), default=5.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Grant(Base):
    """Available grants"""
    __tablename__ = "grants"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text)
    organization = Column(String(200))
    amount_min = Column(Numeric(12, 2))
    amount_max = Column(Numeric(12, 2))
    deadline = Column(DateTime(timezone=True))
    requirements = Column(Text)
    category = Column(String(50))
    region = Column(String(100))
    is_active = Column(Boolean, default=True)
    ai_score = Column(Numeric(3, 2))  # AI relevance score
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class UserGrantApplication(Base):
    """User grant applications"""
    __tablename__ = "user_grant_applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    grant_id = Column(Integer, ForeignKey("grants.id"), nullable=False)
    status = Column(String(20), default="draft")  # draft, submitted, review, approved, rejected
    application_data = Column(Text)  # JSON string
    ai_recommendation = Column(Text)
    submitted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (UniqueConstraint('user_id', 'grant_id', name='uq_user_grant'),)
