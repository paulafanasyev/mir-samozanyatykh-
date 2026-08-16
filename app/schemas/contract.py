"""Contract schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ContractBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    client_name: str = Field(..., min_length=1, max_length=255)
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    client_inn: Optional[str] = Field(None, pattern=r"^\d{12}$")
    amount: float = Field(..., gt=0)
    description: Optional[str] = None
    contract_type: str = Field(default="gpd")

class ContractCreate(ContractBase):
    pass

class ContractUpdate(BaseModel):
    title: Optional[str] = None
    client_name: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    status: Optional[str] = None

class ContractResponse(ContractBase):
    id: int
    user_id: int
    status: str
    content: Optional[str] = None
    qr_code: Optional[str] = None
    pdf_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
