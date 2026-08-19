"""
API договоров: генерация, подпись, PDF, verify
АНО ЦПС ИНН 9724016805
"""

import os
import json
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import generate_simple_signature, verify_simple_signature
from app.core.logging import logger, log_audit
from app.core.auth import get_current_user, get_current_user_optional
from app.models import User, ContractTemplate, SignedContract
from app.schemas.contracts import (
    ContractTemplateOut, ContractTemplateDetail,
    ContractGenerate, ContractOut, ContractSign, ContractVerifyResponse,
    CONTRACT_TYPES,
)
from app.services.pdf import pdf_service
from app.core.file_security import ensure_within_private_storage, private_storage_path


router = APIRouter(prefix="/api/contracts", tags=["contracts"])


# ============ TEMPLATES ============

@router.get("/templates", response_model=List[ContractTemplateOut])
async def list_templates(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список шаблонов договоров"""
    query = select(ContractTemplate).where(ContractTemplate.is_active == True)
    if category:
        query = query.where(ContractTemplate.category == category)
    
    result = await db.execute(query.order_by(ContractTemplate.sort_order))
    templates = result.scalars().all()
    
    # Определяем locked статус на основе подписки
    user_tier = current_user.subscription_tier or "free"
    tier_order = {"free": 0, "pro": 1, "business": 2, "enterprise": 3}
    user_level = tier_order.get(user_tier, 0)
    
    output = []
    for t in templates:
        is_locked = t.is_premium and user_level < 1
        output.append({
            **t.__dict__,
            "locked": is_locked,
        })
    return output


@router.get("/templates/{template_type}", response_model=ContractTemplateDetail)
async def get_template_detail(
    template_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Детали шаблона с полями для заполнения"""
    if template_type not in CONTRACT_TYPES:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    
    template_info = CONTRACT_TYPES[template_type]
    
    # Проверка доступа
    user_tier = current_user.subscription_tier or "free"
    tier_order = {"free": 0, "pro": 1, "business": 2, "enterprise": 3}
    
    # Проверяем есть ли шаблон в БД
    result = await db.execute(
        select(ContractTemplate).where(
            ContractTemplate.category == template_type,
            ContractTemplate.is_active == True,
        )
    )
    db_template = result.scalar_one_or_none()
    
    # Генерация sample данных из профиля пользователя
    sample = {
        "contractor_name": current_user.full_name or "",
        "contractor_inn": current_user.inn or "",
        "licensor_name": current_user.full_name or "",
        "licensor_inn": current_user.inn or "",
        "party1_name": current_user.full_name or "",
        "party1_inn": current_user.inn or "",
    }
    
    return ContractTemplateDetail(
        id=db_template.id if db_template else 0,
        name=template_info["name"],
        category=template_type,
        fields=template_info["fields"],
        sample_data=sample,
        is_premium=template_type in ("it_outsource", "license"),
        is_active=True,
        locked=(template_type in ("it_outsource", "license") and tier_order.get(user_tier, 0) < 1),
    )


# ============ CONTRACT GENERATION ============

@router.post("/generate", response_model=ContractOut, status_code=status.HTTP_201_CREATED)
async def generate_contract(
    data: ContractGenerate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Генерация договора из шаблона"""
    template_type = str(data.template_id)
    if template_type.isdigit():
        template_result = await db.execute(select(ContractTemplate).where(ContractTemplate.id == int(template_type), ContractTemplate.is_active == True))
        template = template_result.scalar_one_or_none()
        if template:
            template_type = template.category or str(template.id)
    
    if template_type not in CONTRACT_TYPES:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    
    # Проверка подписки
    user_tier = current_user.subscription_tier or "free"
    tier_order = {"free": 0, "pro": 1, "business": 2, "enterprise": 3}
    if template_type in ("it_outsource", "license") and tier_order.get(user_tier, 0) < 1:
        raise HTTPException(status_code=403, detail="Требуется подписка Pro или выше")
    
    # Валидация обязательных полей
    template_info = CONTRACT_TYPES[template_type]
    required_fields = [f.key for f in template_info["fields"] if f.required]
    missing = [f for f in required_fields if f not in data.variables or not data.variables[f]]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Не заполнены обязательные поля: {', '.join(missing)}"
        )
    
    # Генерация PDF
    pdf_bytes = pdf_service.generate_contract(
        template_type=template_type,
        data=data.variables,
    )
    
    # Сохранение PDF
    os.makedirs("data/contracts", exist_ok=True)
    filename = f"contract_{current_user.id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = private_storage_path("contracts", filename, current_user.id)
    with open(filepath, "wb") as f:
        f.write(pdf_bytes)
    
    # Создание записи
    contract = SignedContract(
        user_id=current_user.id,
        template_id=None,  # или найти в БД
        template_type=template_type,
        title=template_info["name"],
        content=json.dumps(data.variables, ensure_ascii=False),
        contract_data=data.variables,
        variables_data=data.variables,
        pdf_path=filepath,
        status="draft",
    )
    db.add(contract)
    await db.commit()
    await db.refresh(contract)
    
    await log_audit(
        action="contract_generated",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Template: {template_type}, Contract ID: {contract.id}",
    )
    
    return contract


# ============ CONTRACT SIGNING ============

@router.post("/{contract_id}/sign", response_model=ContractOut)
async def sign_contract(
    contract_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Подписание договора простой электронной подписью (ГК РФ ст. 160)"""
    result = await db.execute(
        select(SignedContract).where(
            SignedContract.id == contract_id,
            SignedContract.user_id == current_user.id,
        )
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Договор не найден")
    
    if contract.status == "signed":
        raise HTTPException(status_code=400, detail="Договор уже подписан")
    
    # Генерация подписи
    signature = generate_simple_signature(
        data=contract.contract_data,
        user_id=current_user.id,
    )
    
    contract.signature_data = signature
    contract.status = "signed"
    contract.signed_at = datetime.now(timezone.utc)
    
    # Перегенерация PDF с подписью
    if contract.pdf_path:
        pdf_path = ensure_within_private_storage(contract.pdf_path)
        if not pdf_path.is_file():
            raise HTTPException(status_code=404, detail="PDF договора не найден")
        pdf_bytes = pdf_service.generate_contract(
            template_type=contract.template_type,
            data=contract.contract_data,
            signature=signature,
        )
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
    
    await db.commit()
    await db.refresh(contract)
    
    await log_audit(
        action="contract_signed",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Contract ID: {contract_id}",
    )
    
    return contract


@router.post("/{contract_id}/cancel", response_model=ContractOut)
async def cancel_contract(
    contract_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Отмена договора"""
    result = await db.execute(
        select(SignedContract).where(
            SignedContract.id == contract_id,
            SignedContract.user_id == current_user.id,
        )
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Договор не найден")
    
    if contract.status == "signed":
        raise HTTPException(status_code=400, detail="Подписанный договор нельзя отменить")
    
    contract.status = "cancelled"
    await db.commit()
    await db.refresh(contract)
    
    await log_audit(
        action="contract_cancelled",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Contract ID: {contract_id}",
    )
    
    return contract


# ============ CONTRACT LIST & DETAIL ============

@router.get("/my", response_model=List[ContractOut])
async def list_my_contracts(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список моих договоров"""
    query = select(SignedContract).where(SignedContract.user_id == current_user.id)
    if status:
        query = query.where(SignedContract.status == status)
    
    result = await db.execute(query.order_by(SignedContract.created_at.desc()))
    return result.scalars().all()


@router.get("/{contract_id}", response_model=ContractOut)
async def get_contract(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получение договора"""
    result = await db.execute(
        select(SignedContract).where(
            SignedContract.id == contract_id,
            SignedContract.user_id == current_user.id,
        )
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Договор не найден")
    return contract


@router.get("/{contract_id}/pdf")
async def get_contract_pdf(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Скачивание PDF договора"""
    from fastapi.responses import FileResponse
    
    result = await db.execute(
        select(SignedContract).where(
            SignedContract.id == contract_id,
            SignedContract.user_id == current_user.id,
        )
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Договор не найден")
    
    if not contract.pdf_path:
        raise HTTPException(status_code=404, detail="PDF не найден")
    pdf_path = ensure_within_private_storage(contract.pdf_path)
    if not pdf_path.is_file():
        raise HTTPException(status_code=404, detail="PDF не найден")
    
    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        filename=f"Договор_{contract.template_type}_{contract_id}.pdf",
    )


# ============ VERIFY SIGNATURE ============

@router.post("/{contract_id}/verify", response_model=ContractVerifyResponse)
async def verify_contract(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Проверка подлинности электронной подписи договора"""
    result = await db.execute(
        select(SignedContract).where(
            SignedContract.id == contract_id,
            SignedContract.user_id == current_user.id,
        )
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Договор не найден")
    
    if not contract.signature_data:
        return ContractVerifyResponse(
            signed=False,
            message="Договор не подписан",
        )
    
    is_valid = verify_simple_signature(
        data=contract.contract_data,
        signature_data=contract.signature_data,
    )
    
    return ContractVerifyResponse(
        signed=True,
        valid=is_valid,
        signature_info=contract.signature_data,
        message="Подпись действительна" if is_valid else "Подпись недействительна!",
    )
