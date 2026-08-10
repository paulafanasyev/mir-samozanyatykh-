"""
Pydantic схемы для пользователей и аутентификации
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, field_validator

from app.core.security import validate_password_strength, validate_email, validate_phone, validate_inn


# ============ AUTH ============

class UserRegister(BaseModel):
    email: EmailStr = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    inn: Optional[str] = Field(None, max_length=20)
    
    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        is_valid, msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(msg)
        return v
    
    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and not validate_phone(v):
            raise ValueError("Телефон должен быть в формате +7XXXXXXXXXX")
        return v
    
    @field_validator("inn")
    @classmethod
    def check_inn(cls, v: Optional[str]) -> Optional[str]:
        if v and not validate_inn(v):
            raise ValueError("Неверный ИНН физического лица (12 цифр)")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    tier: str


class TokenPayload(BaseModel):
    sub: str
    email: Optional[str] = None
    jti: str
    type: str
    exp: datetime
    iat: datetime


# ============ USER PROFILE ============

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None
    inn: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    inn: Optional[str] = Field(None, max_length=20)
    
    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and not validate_phone(v):
            raise ValueError("Телефон должен быть в формате +7XXXXXXXXXX")
        return v
    
    @field_validator("inn")
    @classmethod
    def check_inn(cls, v: Optional[str]) -> Optional[str]:
        if v and not validate_inn(v):
            raise ValueError("Неверный ИНН")
        return v


class UserOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    phone: Optional[str]
    inn: Optional[str]
    is_verified: bool
    is_admin: bool
    tier: str
    points: int = 0
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserAdminOut(UserOut):
    is_active: bool
    is_moderator: bool
    subscription_tier: str
    subscription_expires: Optional[datetime]
    failed_login_attempts: int
    locked_until: Optional[datetime]
    role: str


# ============ MFA ============

class MFASetupResponse(BaseModel):
    qr_code: str
    secret: str
    backup_codes: List[str]
    message: str


class MFAVerify(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)


# ============ PASSWORD ============

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator("new_password")
    @classmethod
    def check_password(cls, v: str) -> str:
        is_valid, msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(msg)
        return v


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator("new_password")
    @classmethod
    def check_password(cls, v: str) -> str:
        is_valid, msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(msg)
        return v
