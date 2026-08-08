"""
Pydantic схемы для договоров
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


# ============ CONTRACT TEMPLATES ============

class ContractTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., max_length=100)
    content: str = Field(..., min_length=50)
    variables: Optional[List[str]] = None
    is_premium: bool = False
    is_active: bool = True


class ContractTemplateOut(BaseModel):
    id: int
    name: str
    category: str
    variables: Optional[List[str]]
    is_premium: bool
    is_active: bool
    locked: bool = False  # вычисляется на основе подписки
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============ SIGNED CONTRACTS ============

class ContractGenerate(BaseModel):
    template_id: int
    variables: Dict[str, Any] = Field(..., min_length=1)
    sign: bool = False


class ContractSign(BaseModel):
    contract_id: int
    sign_data: Optional[Dict[str, Any]] = None


class ContractOut(BaseModel):
    id: int
    user_id: int
    template_id: Optional[int]
    template_type: str
    title: Optional[str]
    content: Optional[str]
    contract_data: Optional[Dict[str, Any]]
    signature_data: Optional[Dict[str, Any]]
    pdf_path: Optional[str]
    status: str
    signed_at: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ContractVerifyResponse(BaseModel):
    signed: bool
    valid: Optional[bool] = None
    signature_info: Optional[Dict[str, Any]] = None
    message: str


# ============ CONTRACT VARIABLES (для фронтенда) ============

class ContractVariable(BaseModel):
    key: str
    label: str
    type: str = "text"  # text / number / date / select
    required: bool = True
    options: Optional[List[str]] = None
    default: Optional[str] = None


class ContractTemplateDetail(ContractTemplateOut):
    fields: List[ContractVariable]
    sample_data: Optional[Dict[str, Any]] = None


# ============ CONTRACT TYPES ENUM ============

CONTRACT_TYPES = {
    "gpd": {
        "name": "Договор ГПД (гражданско-правовой)",
        "description": "Стандартный договор подряда/оказания услуг",
        "fields": [
            ContractVariable(key="contractor_name", label="ФИО исполнителя", required=True),
            ContractVariable(key="contractor_inn", label="ИНН исполнителя", required=True),
            ContractVariable(key="client_name", label="ФИО/название заказчика", required=True),
            ContractVariable(key="client_inn", label="ИНН заказчика", required=False),
            ContractVariable(key="subject", label="Предмет договора", required=True),
            ContractVariable(key="price", label="Стоимость (₽)", type="number", required=True),
            ContractVariable(key="deadline", label="Срок выполнения", type="date", required=True),
            ContractVariable(key="payment_terms", label="Условия оплаты", required=False, default="100% по факту выполнения"),
        ]
    },
    "it_outsource": {
        "name": "Договор IT-аутсорсинга",
        "description": "Договор на обслуживание IT-инфраструктуры",
        "fields": [
            ContractVariable(key="contractor_name", label="Исполнитель", required=True),
            ContractVariable(key="contractor_inn", label="ИНН исполнителя", required=True),
            ContractVariable(key="client_name", label="Заказчик", required=True),
            ContractVariable(key="client_inn", label="ИНН заказчика", required=True),
            ContractVariable(key="services", label="Перечень услуг", required=True),
            ContractVariable(key="monthly_fee", label="Ежемесячная плата (₽)", type="number", required=True),
            ContractVariable(key="contract_term", label="Срок договора (мес)", type="number", required=True),
            ContractVariable(key="response_time", label="Время реакции (ч)", type="number", default="4"),
            ContractVariable(key="sla_level", label="Уровень SLA", type="select", options=["Базовый", "Стандарт", "Премиум"], default="Стандарт"),
        ]
    },
    "nda": {
        "name": "Соглашение о конфиденциальности (NDA)",
        "description": "Договор о неразглашении коммерческой тайны",
        "fields": [
            ContractVariable(key="party1_name", label="Сторона 1", required=True),
            ContractVariable(key="party1_inn", label="ИНН стороны 1", required=True),
            ContractVariable(key="party2_name", label="Сторона 2", required=True),
            ContractVariable(key="party2_inn", label="ИНН стороны 2", required=True),
            ContractVariable(key="confidential_info", label="Описание конфиденциальной информации", required=True),
            ContractVariable(key="term_years", label="Срок действия (лет)", type="number", default="3"),
            ContractVariable(key="jurisdiction", label="Подсудность", default="город Москва"),
        ]
    },
    "license": {
        "name": "Лицензионный договор",
        "description": "Передача прав на использование ПО/контента",
        "fields": [
            ContractVariable(key="licensor_name", label="Лицензиар", required=True),
            ContractVariable(key="licensor_inn", label="ИНН лицензиара", required=True),
            ContractVariable(key="licensee_name", label="Лицензиат", required=True),
            ContractVariable(key="licensee_inn", label="ИНН лицензиата", required=True),
            ContractVariable(key="object_description", label="Объект лицензии", required=True),
            ContractVariable(key="license_type", label="Тип лицензии", type="select", options=["исключительная", "простая", "сублицензия"], default="простая"),
            ContractVariable(key="territory", label="Территория", default="Российская Федерация"),
            ContractVariable(key="license_fee", label="Размер лицензионного вознаграждения (₽)", type="number", required=True),
            ContractVariable(key="term_months", label="Срок (мес)", type="number", required=True),
        ]
    },
    "services": {
        "name": "Договор оказания услуг",
        "description": "Общий договор на оказание услуг",
        "fields": [
            ContractVariable(key="contractor_name", label="Исполнитель", required=True),
            ContractVariable(key="contractor_inn", label="ИНН исполнителя", required=True),
            ContractVariable(key="client_name", label="Заказчик", required=True),
            ContractVariable(key="client_inn", label="ИНН заказчика", required=False),
            ContractVariable(key="service_list", label="Перечень услуг", required=True),
            ContractVariable(key="total_price", label="Общая стоимость (₽)", type="number", required=True),
            ContractVariable(key="deadline", label="Срок оказания", type="date", required=True),
            ContractVariable(key="payment_schedule", label="График платежей", default="50% предоплата, 50% по факту"),
        ]
    },
    "act": {
        "name": "Акт выполненных работ",
        "description": "Акт приёмки-передачи выполненных работ",
        "fields": [
            ContractVariable(key="contractor_name", label="Исполнитель", required=True),
            ContractVariable(key="contractor_inn", label="ИНН исполнителя", required=True),
            ContractVariable(key="client_name", label="Заказчик", required=True),
            ContractVariable(key="client_inn", label="ИНН заказчика", required=False),
            ContractVariable(key="works_description", label="Описание выполненных работ", required=True),
            ContractVariable(key="total", label="Стоимость (₽)", type="number", required=True),
            ContractVariable(key="act_date", label="Дата акта", type="date", required=True),
            ContractVariable(key="contract_number", label="№ договора", required=False),
        ]
    },
}
