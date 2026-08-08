"""
API CRM: клиенты, сделки
"""

from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logging import log_audit
from app.models import User, Client, Deal

router = APIRouter(prefix="/api/crm", tags=["crm"])


# ============ CLIENTS ============

class ClientCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    inn: Optional[str] = None
    notes: Optional[str] = None


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    inn: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class DealCreate(BaseModel):
    client_id: int
    title: str
    amount: Optional[float] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: Optional[str] = "medium"


class DealUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[float] = None
    status: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: Optional[str] = None


from pydantic import BaseModel


@router.get("/clients", response_model=List[dict])
async def list_clients(
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список клиентов"""
    query = select(Client).where(Client.user_id == current_user.id)
    if status:
        query = query.where(Client.status == status)
    if search:
        query = query.where(Client.name.ilike(f"%{search}%"))
    
    result = await db.execute(query.order_by(Client.name))
    return result.scalars().all()


@router.post("/clients", status_code=status.HTTP_201_CREATED)
async def create_client(
    client: ClientCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Создание клиента"""
    db_client = Client(
        user_id=current_user.id,
        **client.model_dump(exclude_unset=True),
    )
    db.add(db_client)
    await db.commit()
    await db.refresh(db_client)
    
    await log_audit(
        action="client_created",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Client: {client.name}",
    )
    return db_client


@router.get("/clients/{client_id}")
async def get_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получение клиента"""
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.user_id == current_user.id,
        )
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return client


@router.put("/clients/{client_id}")
async def update_client(
    client_id: int,
    update: ClientUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Обновление клиента"""
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.user_id == current_user.id,
        )
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(client, key, value)
    
    await db.commit()
    await db.refresh(client)
    return client


@router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удаление клиента"""
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.user_id == current_user.id,
        )
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    await db.delete(client)
    await db.commit()


# ============ DEALS ============

@router.get("/deals", response_model=List[dict])
async def list_deals(
    status: Optional[str] = None,
    client_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список сделок"""
    query = select(Deal).where(Deal.user_id == current_user.id)
    if status:
        query = query.where(Deal.status == status)
    if client_id:
        query = query.where(Deal.client_id == client_id)
    
    result = await db.execute(query.order_by(Deal.created_at.desc()))
    return result.scalars().all()


@router.post("/deals", status_code=status.HTTP_201_CREATED)
async def create_deal(
    deal: DealCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Создание сделки"""
    # Проверка клиента
    client_result = await db.execute(
        select(Client).where(
            Client.id == deal.client_id,
            Client.user_id == current_user.id,
        )
    )
    if not client_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    db_deal = Deal(
        user_id=current_user.id,
        **deal.model_dump(exclude_unset=True),
    )
    db.add(db_deal)
    await db.commit()
    await db.refresh(db_deal)
    return db_deal


@router.get("/deals/{deal_id}")
async def get_deal(
    deal_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получение сделки"""
    result = await db.execute(
        select(Deal).where(
            Deal.id == deal_id,
            Deal.user_id == current_user.id,
        )
    )
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    return deal


@router.put("/deals/{deal_id}")
async def update_deal(
    deal_id: int,
    update: DealUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Обновление сделки"""
    result = await db.execute(
        select(Deal).where(
            Deal.id == deal_id,
            Deal.user_id == current_user.id,
        )
    )
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(deal, key, value)
    
    await db.commit()
    await db.refresh(deal)
    return deal


@router.delete("/deals/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deal(
    deal_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удаление сделки"""
    result = await db.execute(
        select(Deal).where(
            Deal.id == deal_id,
            Deal.user_id == current_user.id,
        )
    )
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    await db.delete(deal)
    await db.commit()


@router.get("/stats")
async def crm_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Статистика CRM"""
    clients_count = await db.scalar(
        select(func.count(Client.id)).where(Client.user_id == current_user.id)
    )
    deals_count = await db.scalar(
        select(func.count(Deal.id)).where(Deal.user_id == current_user.id)
    )
    won_deals = await db.scalar(
        select(func.count(Deal.id)).where(
            Deal.user_id == current_user.id,
            Deal.status == "won",
        )
    )
    total_revenue = await db.scalar(
        select(func.sum(Deal.amount)).where(
            Deal.user_id == current_user.id,
            Deal.status == "won",
        )
    ) or 0
    
    return {
        "clients_count": clients_count,
        "deals_count": deals_count,
        "won_deals": won_deals,
        "conversion_rate": round(won_deals / deals_count * 100, 1) if deals_count else 0,
        "total_revenue": float(total_revenue),
    }
