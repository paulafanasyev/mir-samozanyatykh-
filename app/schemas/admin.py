"""
Pydantic схемы для админ-панели v7.5
АНО ЦПС ИНН 9724016805
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ============ ADMIN USER MANAGEMENT ============

class AdminUserUpdate(BaseModel):
    """Схема обновления пользователя администратором"""
    full_name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_admin: Optional[bool] = None
    is_moderator: Optional[bool] = None
    subscription_tier: Optional[str] = Field(None, pattern=r"^(free|pro|business|enterprise)$")
    subscription_expires: Optional[datetime] = None


class AdminUserOut(BaseModel):
    """Полные данные пользователя для админа"""
    id: int
    email: str
    full_name: Optional[str]
    phone: Optional[str]
    inn: Optional[str]
    is_active: bool
    is_verified: bool
    is_admin: bool
    is_moderator: bool
    subscription_tier: str
    subscription_expires: Optional[datetime]
    points: int
    level: str
    failed_login_attempts: int
    locked_until: Optional[datetime]
    last_login_at: Optional[datetime]
    created_at: Optional[datetime]
    role: str

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Ответ со списком пользователей"""
    users: List[AdminUserOut]
    pagination: dict


# ============ PLATFORM STATISTICS ============

class PlatformStats(BaseModel):
    """Общая статистика платформы"""
    total_users: int
    active_users_30d: int
    new_users_today: int
    new_users_week: int
    new_users_month: int
    total_revenue: float
    paid_invoices_count: int
    subscriptions_by_tier: dict
    avg_invoices_per_user: float
    top_actions: List[dict]
    users_by_month: List[dict]


class SubscriptionDistribution(BaseModel):
    """Распределение подписок по тарифам"""
    tier: str
    count: int
    percentage: float
    revenue: float


# ============ AUDIT LOGS ============

class AuditLogOut(BaseModel):
    """Вывод аудит-лога"""
    id: int
    user_id: Optional[int]
    user_email: Optional[str]
    action: str
    resource: Optional[str]
    details: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    success: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Ответ со списком аудит-логов"""
    logs: List[AuditLogOut]
    pagination: dict


# ============ BULK OPERATIONS ============

class BulkTierUpdate(BaseModel):
    """Массовое обновление тарифов"""
    user_ids: List[int]
    tier: str = Field(..., pattern=r"^(free|pro|business|enterprise)$")
    expires_days: Optional[int] = Field(30, ge=1, le=365)
    reason: Optional[str] = None


class BulkTierResponse(BaseModel):
    """Результат массового обновления"""
    updated: int
    failed: int
    errors: List[str]
    tier: str
    expires_at: datetime


# ============ MODERATION ============

class ModerationAction(BaseModel):
    """Действие модератора"""
    action: str = Field(..., pattern=r"^(block|unblock|verify|warn|note)$")
    reason: Optional[str] = Field(None, max_length=500)
    duration_hours: Optional[int] = Field(None, ge=1, le=8760)
