"""
API CRM v8.4: клиенты, сделки, воронка, звонки, задачи, автоматизация
АНО ЦПС ИНН 9724016805
"""

from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logging import logger, log_audit
from app.models import User, Client, Deal, PipelineStage, Call, Task, CRMAutomation

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
    stage_id: Optional[int] = None
    probability: Optional[int] = Field(None, ge=0, le=100)
    expected_close_date: Optional[datetime] = None
    source: Optional[str] = None


class DealUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[float] = None
    status: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: Optional[str] = None
    stage_id: Optional[int] = None
    probability: Optional[int] = Field(None, ge=0, le=100)
    expected_close_date: Optional[datetime] = None
    actual_close_date: Optional[datetime] = None
    source: Optional[str] = None


# ============ PIPELINE STAGES ============

class PipelineStageCreate(BaseModel):
    name: str
    order: int = 0
    color: str = "#1976D2"


class PipelineStageUpdate(BaseModel):
    name: Optional[str] = None
    order: Optional[int] = None
    color: Optional[str] = None


# ============ CALLS ============

class CallCreate(BaseModel):
    client_id: Optional[int] = None
    direction: str = "out"  # in, out
    duration: int = 0
    recording_url: Optional[str] = None
    notes: Optional[str] = None
    outcome: Optional[str] = None  # answered, missed, voicemail, callback


class CallUpdate(BaseModel):
    duration: Optional[int] = None
    notes: Optional[str] = None
    outcome: Optional[str] = None


# ============ TASKS ============

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    client_id: Optional[int] = None
    deal_id: Optional[int] = None
    priority: str = "medium"  # low, medium, high, urgent
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None  # pending, in_progress, completed, cancelled
    priority: Optional[str] = None
    due_date: Optional[datetime] = None


# ============ AUTOMATION ============

class CRMAutomationCreate(BaseModel):
    name: str = Field(..., max_length=255)
    trigger_type: str = Field(..., pattern=r"^(deal_stage_changed|deal_created|deal_won|deal_lost|task_overdue|client_added)$")
    trigger_config: dict = {}
    action_type: str = Field(..., pattern=r"^(send_notification|create_task|send_email|move_deal|webhook)$")
    action_config: dict = {}


class CRMAutomationUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    trigger_config: Optional[dict] = None
    action_config: Optional[dict] = None


class CRMAutomationOut(BaseModel):
    id: int
    name: str
    is_active: bool
    trigger_type: str
    trigger_config: dict
    action_type: str
    action_config: dict
    run_count: int
    last_run_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
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


# ============ PIPELINE STAGES API ============

@router.get("/pipeline-stages", response_model=List[dict])
async def list_pipeline_stages(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список этапов воронки"""
    result = await db.execute(
        select(PipelineStage)
        .where(PipelineStage.user_id == current_user.id)
        .order_by(PipelineStage.order)
    )
    return result.scalars().all()


@router.post("/pipeline-stages", status_code=status.HTTP_201_CREATED)
async def create_pipeline_stage(
    stage: PipelineStageCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Создание этапа воронки"""
    db_stage = PipelineStage(
        user_id=current_user.id,
        **stage.model_dump(exclude_unset=True),
    )
    db.add(db_stage)
    await db.commit()
    await db.refresh(db_stage)
    
    await log_audit(
        action="pipeline_stage_created",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Stage: {stage.name}",
    )
    return db_stage


@router.put("/pipeline-stages/{stage_id}")
async def update_pipeline_stage(
    stage_id: int,
    update: PipelineStageUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Обновление этапа воронки"""
    result = await db.execute(
        select(PipelineStage).where(
            PipelineStage.id == stage_id,
            PipelineStage.user_id == current_user.id,
        )
    )
    stage = result.scalar_one_or_none()
    if not stage:
        raise HTTPException(status_code=404, detail="Этап не найден")
    
    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(stage, key, value)
    
    await db.commit()
    await db.refresh(stage)
    return stage


@router.delete("/pipeline-stages/{stage_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pipeline_stage(
    stage_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удаление этапа воронки"""
    result = await db.execute(
        select(PipelineStage).where(
            PipelineStage.id == stage_id,
            PipelineStage.user_id == current_user.id,
        )
    )
    stage = result.scalar_one_or_none()
    if not stage:
        raise HTTPException(status_code=404, detail="Этап не найден")
    
    await db.delete(stage)
    await db.commit()


# ============ CALLS API ============

@router.get("/calls", response_model=List[dict])
async def list_calls(
    client_id: Optional[int] = None,
    direction: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список звонков"""
    query = select(Call).where(Call.user_id == current_user.id)
    if client_id:
        query = query.where(Call.client_id == client_id)
    if direction:
        query = query.where(Call.direction == direction)
    
    result = await db.execute(query.order_by(Call.created_at.desc()))
    return result.scalars().all()


@router.post("/calls", status_code=status.HTTP_201_CREATED)
async def create_call(
    call: CallCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Создание записи о звонке"""
    db_call = Call(
        user_id=current_user.id,
        **call.model_dump(exclude_unset=True),
    )
    db.add(db_call)
    await db.commit()
    await db.refresh(db_call)
    
    await log_audit(
        action="call_created",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Call {call.direction}, client: {call.client_id}",
    )
    return db_call


@router.get("/calls/{call_id}")
async def get_call(
    call_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получение записи о звонке"""
    result = await db.execute(
        select(Call).where(
            Call.id == call_id,
            Call.user_id == current_user.id,
        )
    )
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Звонок не найден")
    return call


@router.put("/calls/{call_id}")
async def update_call(
    call_id: int,
    update: CallUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Обновление записи о звонке"""
    result = await db.execute(
        select(Call).where(
            Call.id == call_id,
            Call.user_id == current_user.id,
        )
    )
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Звонок не найден")
    
    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(call, key, value)
    
    await db.commit()
    await db.refresh(call)
    return call


@router.delete("/calls/{call_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_call(
    call_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удаление записи о звонке"""
    result = await db.execute(
        select(Call).where(
            Call.id == call_id,
            Call.user_id == current_user.id,
        )
    )
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Звонок не найден")
    
    await db.delete(call)
    await db.commit()


# ============ TASKS API ============

@router.get("/tasks", response_model=List[dict])
async def list_tasks(
    status: Optional[str] = None,
    client_id: Optional[int] = None,
    deal_id: Optional[int] = None,
    priority: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список задач CRM"""
    query = select(Task).where(Task.user_id == current_user.id)
    if status:
        query = query.where(Task.status == status)
    if client_id:
        query = query.where(Task.client_id == client_id)
    if deal_id:
        query = query.where(Task.deal_id == deal_id)
    if priority:
        query = query.where(Task.priority == priority)
    
    result = await db.execute(query.order_by(Task.due_date.asc().nullslast(), Task.created_at.desc()))
    return result.scalars().all()


@router.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Создание задачи CRM"""
    db_task = Task(
        user_id=current_user.id,
        status="pending",
        **task.model_dump(exclude_unset=True),
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    
    await log_audit(
        action="task_created",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Task: {task.title}",
    )
    return db_task


@router.get("/tasks/{task_id}")
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получение задачи"""
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.user_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task


@router.put("/tasks/{task_id}")
async def update_task(
    task_id: int,
    update: TaskUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Обновление задачи"""
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.user_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    update_data = update.model_dump(exclude_unset=True)
    
    # Автоматическая установка completed_at при завершении
    if update_data.get("status") == "completed" and task.status != "completed":
        task.completed_at = datetime.now(timezone.utc)
    
    for key, value in update_data.items():
        setattr(task, key, value)
    
    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удаление задачи"""
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.user_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    await db.delete(task)
    await db.commit()


# ============ PIPELINE / FUNNEL ============

@router.get("/pipeline")
async def get_pipeline(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Полная воронка продаж с сделками по этапам"""
    stages_result = await db.execute(
        select(PipelineStage)
        .where(PipelineStage.user_id == current_user.id)
        .order_by(PipelineStage.order)
    )
    stages = stages_result.scalars().all()
    
    pipeline = []
    for stage in stages:
        deals_result = await db.execute(
            select(Deal)
            .where(
                Deal.user_id == current_user.id,
                Deal.stage_id == stage.id,
            )
            .order_by(Deal.created_at.desc())
        )
        deals = deals_result.scalars().all()
        
        total_amount = sum(d.amount or 0 for d in deals)
        
        pipeline.append({
            "stage": stage,
            "deals": deals,
            "deals_count": len(deals),
            "total_amount": float(total_amount),
        })
    
    return pipeline


@router.post("/deals/{deal_id}/move")
async def move_deal_stage(
    deal_id: int,
    stage_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Перемещение сделки на другой этап воронки"""
    result = await db.execute(
        select(Deal).where(
            Deal.id == deal_id,
            Deal.user_id == current_user.id,
        )
    )
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    # Проверка этапа
    stage_result = await db.execute(
        select(PipelineStage).where(
            PipelineStage.id == stage_id,
            PipelineStage.user_id == current_user.id,
        )
    )
    if not stage_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Этап не найден")
    
    old_stage = deal.stage_id
    deal.stage_id = stage_id
    
    # Если сделка перешла в "won" — установить actual_close_date
    stage_result2 = await db.execute(
        select(PipelineStage).where(PipelineStage.id == stage_id)
    )
    new_stage = stage_result2.scalar_one_or_none()
    if new_stage and "won" in new_stage.name.lower():
        deal.status = "won"
        deal.actual_close_date = datetime.now(timezone.utc)
        deal.probability = 100
    
    await db.commit()
    await db.refresh(deal)
    
    await log_audit(
        action="deal_moved",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Deal {deal_id}: stage {old_stage} -> {stage_id}",
    )
    return deal


@router.get("/stats")
async def crm_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Статистика CRM v6.6"""
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
    
    # Звонки
    calls_count = await db.scalar(
        select(func.count(Call.id)).where(Call.user_id == current_user.id)
    )
    total_call_duration = await db.scalar(
        select(func.sum(Call.duration)).where(Call.user_id == current_user.id)
    ) or 0
    
    # Задачи
    tasks_pending = await db.scalar(
        select(func.count(Task.id)).where(
            Task.user_id == current_user.id,
            Task.status == "pending",
        )
    )
    tasks_overdue = await db.scalar(
        select(func.count(Task.id)).where(
            Task.user_id == current_user.id,
            Task.status.in_(["pending", "in_progress"]),
            Task.due_date < datetime.now(timezone.utc),
        )
    )
    
    # Воронка по этапам
    stages_result = await db.execute(
        select(PipelineStage).where(PipelineStage.user_id == current_user.id).order_by(PipelineStage.order)
    )
    stages = stages_result.scalars().all()
    
    funnel = []
    for stage in stages:
        count = await db.scalar(
            select(func.count(Deal.id)).where(
                Deal.user_id == current_user.id,
                Deal.stage_id == stage.id,
            )
        )
        amount = await db.scalar(
            select(func.sum(Deal.amount)).where(
                Deal.user_id == current_user.id,
                Deal.stage_id == stage.id,
            )
        ) or 0
        funnel.append({
            "stage_id": stage.id,
            "stage_name": stage.name,
            "color": stage.color,
            "deals_count": count,
            "total_amount": float(amount),
        })
    
    return {
        "clients_count": clients_count,
        "deals_count": deals_count,
        "won_deals": won_deals,
        "conversion_rate": round(won_deals / deals_count * 100, 1) if deals_count else 0,
        "total_revenue": float(total_revenue),
        "calls_count": calls_count,
        "total_call_duration": int(total_call_duration),
        "tasks_pending": tasks_pending,
        "tasks_overdue": tasks_overdue,
        "funnel": funnel,
    }


# ============ CRM AUTOMATION API ============

@router.get("/automations", response_model=List[CRMAutomationOut])
async def list_automations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список автоматизаций CRM"""
    result = await db.execute(
        select(CRMAutomation)
        .where(CRMAutomation.user_id == current_user.id)
        .order_by(desc(CRMAutomation.created_at))
    )
    return result.scalars().all()


@router.post("/automations", status_code=status.HTTP_201_CREATED, response_model=CRMAutomationOut)
async def create_automation(
    auto: CRMAutomationCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Создать автоматизацию CRM"""
    db_auto = CRMAutomation(
        user_id=current_user.id,
        **auto.model_dump(),
    )
    db.add(db_auto)
    await db.commit()
    await db.refresh(db_auto)

    await log_audit(
        action="crm_automation_created",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Automation: {auto.name}, trigger={auto.trigger_type}, action={auto.action_type}",
    )
    return CRMAutomationOut.model_validate(db_auto)


@router.get("/automations/{auto_id}", response_model=CRMAutomationOut)
async def get_automation(
    auto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить автоматизацию"""
    result = await db.execute(
        select(CRMAutomation).where(
            CRMAutomation.id == auto_id,
            CRMAutomation.user_id == current_user.id,
        )
    )
    auto = result.scalar_one_or_none()
    if not auto:
        raise HTTPException(status_code=404, detail="Автоматизация не найдена")
    return CRMAutomationOut.model_validate(auto)


@router.put("/automations/{auto_id}", response_model=CRMAutomationOut)
async def update_automation(
    auto_id: int,
    update: CRMAutomationUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Обновить автоматизацию"""
    result = await db.execute(
        select(CRMAutomation).where(
            CRMAutomation.id == auto_id,
            CRMAutomation.user_id == current_user.id,
        )
    )
    auto = result.scalar_one_or_none()
    if not auto:
        raise HTTPException(status_code=404, detail="Автоматизация не найдена")

    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(auto, key, value)

    await db.commit()
    await db.refresh(auto)
    return CRMAutomationOut.model_validate(auto)


@router.delete("/automations/{auto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_automation(
    auto_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удалить автоматизацию"""
    result = await db.execute(
        select(CRMAutomation).where(
            CRMAutomation.id == auto_id,
            CRMAutomation.user_id == current_user.id,
        )
    )
    auto = result.scalar_one_or_none()
    if not auto:
        raise HTTPException(status_code=404, detail="Автоматизация не найдена")
    await db.delete(auto)
    await db.commit()


# ============ AUTOMATION ENGINE ============

async def run_automation_trigger(
    db: AsyncSession,
    user_id: int,
    trigger_type: str,
    trigger_data: dict,
):
    """Запустить автоматизации по триггеру"""
    result = await db.execute(
        select(CRMAutomation).where(
            CRMAutomation.user_id == user_id,
            CRMAutomation.is_active == True,
            CRMAutomation.trigger_type == trigger_type,
        )
    )
    automations = result.scalars().all()

    for auto in automations:
        config = auto.trigger_config or {}
        match = True
        for key, value in config.items():
            if trigger_data.get(key) != value:
                match = False
                break

        if not match:
            continue

        action = auto.action_config or {}
        try:
            if auto.action_type == "send_notification":
                from app.api.notifications import notify_user
                await notify_user(
                    db, user_id,
                    title=action.get("title", "CRM Автоматизация"),
                    body=action.get("body", ""),
                    notification_type="info",
                    action_url=action.get("action_url"),
                )
            elif auto.action_type == "create_task":
                task = Task(
                    user_id=user_id,
                    title=action.get("title", "Автоматическая задача"),
                    description=action.get("description", ""),
                    status="pending",
                    priority=action.get("priority", "medium"),
                    client_id=action.get("client_id"),
                    deal_id=action.get("deal_id"),
                )
                db.add(task)
            elif auto.action_type == "send_email":
                from app.services.email import email_service
                user_result = await db.execute(select(User).where(User.id == user_id))
                user = user_result.scalar_one_or_none()
                if user and user.email:
                    email_service.send_notification_email(
                        to_email=user.email,
                        subject=action.get("subject", "Уведомление CRM"),
                        body=action.get("body", ""),
                    )
            elif auto.action_type == "move_deal":
                deal_id = action.get("deal_id")
                stage_id = action.get("stage_id")
                if deal_id and stage_id:
                    deal_result = await db.execute(
                        select(Deal).where(Deal.id == deal_id, Deal.user_id == user_id)
                    )
                    deal = deal_result.scalar_one_or_none()
                    if deal:
                        deal.stage_id = stage_id

            auto.run_count += 1
            auto.last_run_at = datetime.now(timezone.utc)
            logger.info(f"Automation {auto.id} triggered: {auto.name}")
        except Exception as e:
            logger.error(f"Automation {auto.id} failed: {e}")

    await db.commit()


# ============ ENHANCED DEAL MOVE WITH AUTOMATION ============

@router.post("/deals/{deal_id}/move")
async def move_deal_stage(
    deal_id: int,
    stage_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Перемещение сделки на другой этап воронки + автоматизация"""
    result = await db.execute(
        select(Deal).where(
            Deal.id == deal_id,
            Deal.user_id == current_user.id,
        )
    )
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")

    old_stage_id = deal.stage_id

    stage_result = await db.execute(
        select(PipelineStage).where(
            PipelineStage.id == stage_id,
            PipelineStage.user_id == current_user.id,
        )
    )
    new_stage = stage_result.scalar_one_or_none()
    if not new_stage:
        raise HTTPException(status_code=404, detail="Этап не найден")

    deal.stage_id = stage_id

    stage_name_lower = new_stage.name.lower()
    if "won" in stage_name_lower:
        deal.status = "won"
        deal.actual_close_date = datetime.now(timezone.utc)
        deal.probability = 100
        await run_automation_trigger(
            db, current_user.id, "deal_won",
            {"deal_id": deal.id, "stage_id": stage_id, "old_stage_id": old_stage_id}
        )
    elif "lost" in stage_name_lower:
        deal.status = "lost"
        deal.actual_close_date = datetime.now(timezone.utc)
        deal.probability = 0
        await run_automation_trigger(
            db, current_user.id, "deal_lost",
            {"deal_id": deal.id, "stage_id": stage_id, "old_stage_id": old_stage_id}
        )
    else:
        await run_automation_trigger(
            db, current_user.id, "deal_stage_changed",
            {"deal_id": deal.id, "stage_id": stage_id, "old_stage_id": old_stage_id}
        )

    await db.commit()
    await db.refresh(deal)

    await log_audit(
        action="deal_moved",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Deal {deal_id}: stage {old_stage_id} -> {stage_id}",
    )
    return deal
