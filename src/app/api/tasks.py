"""
API задач (TODO) v7.9
CRUD, фильтры, Kanban, сортировка, напоминания
АНО ЦПС ИНН 9724016805
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, update, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import log_audit
from app.core.auth import get_current_user, get_current_user_optional
from app.models import User, Task, Client, Deal, Notification
from app.api.notifications import notify_task_due

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


# ============ SCHEMAS ============

class TaskCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    status: str = Field("pending", pattern=r"^(pending|in_progress|completed|cancelled)$")
    priority: str = Field("medium", pattern=r"^(low|medium|high|urgent)$")
    due_date: Optional[datetime] = None
    client_id: Optional[int] = None
    deal_id: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = Field(None, pattern=r"^(pending|in_progress|completed|cancelled)$")
    priority: Optional[str] = Field(None, pattern=r"^(low|medium|high|urgent)$")
    due_date: Optional[datetime] = None
    client_id: Optional[int] = None
    deal_id: Optional[int] = None


class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    priority: str
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    client_id: Optional[int]
    client_name: Optional[str]
    deal_id: Optional[int]
    deal_title: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_overdue: bool
    days_until_due: Optional[int]

    class Config:
        from_attributes = True


class TaskStats(BaseModel):
    total: int
    pending: int
    in_progress: int
    completed: int
    cancelled: int
    overdue: int
    due_today: int
    due_this_week: int
    by_priority: dict


class TaskBulkUpdate(BaseModel):
    task_ids: List[int]
    status: Optional[str] = Field(None, pattern=r"^(pending|in_progress|completed|cancelled)$")
    priority: Optional[str] = Field(None, pattern=r"^(low|medium|high|urgent)$")


# ============ HELPERS ============

def _task_out(task: Task) -> TaskOut:
    is_overdue = False
    days_until_due = None
    if task.due_date and task.status not in ("completed", "cancelled"):
        now = datetime.now(timezone.utc)
        if task.due_date.tzinfo is None:
            task_due = task.due_date.replace(tzinfo=timezone.utc)
        else:
            task_due = task.due_date
        is_overdue = task_due < now
        days_until_due = (task_due - now).days

    return TaskOut(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date,
        completed_at=task.completed_at,
        client_id=task.client_id,
        client_name=task.client.name if task.client else None,
        deal_id=task.deal_id,
        deal_title=task.deal.title if task.deal else None,
        created_at=task.created_at,
        updated_at=task.updated_at,
        is_overdue=is_overdue,
        days_until_due=days_until_due,
    )


# ============ CRUD ============

@router.post("/", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Создание новой задачи"""
    # Проверка клиента
    if task.client_id:
        client_res = await db.execute(
            select(Client).where(Client.id == task.client_id, Client.user_id == current_user.id)
        )
        if not client_res.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Клиент не найден")

    # Проверка сделки и согласованности клиента со сделкой
    if task.deal_id:
        deal_res = await db.execute(
            select(Deal).where(Deal.id == task.deal_id, Deal.user_id == current_user.id)
        )
        deal_obj = deal_res.scalar_one_or_none()
        if not deal_obj:
            raise HTTPException(status_code=404, detail="Сделка не найдена")
        if task.client_id is not None and deal_obj.client_id != task.client_id:
            raise HTTPException(status_code=400, detail="Клиент задачи не соответствует клиенту сделки")

    db_task = Task(
        user_id=current_user.id,
        **task.model_dump(exclude_unset=True),
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)

    await log_audit(
        action="task_created",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Task {db_task.id}: {db_task.title}",
    )
    return _task_out(db_task)


@router.get("/", response_model=List[TaskOut])
async def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    client_id: Optional[int] = None,
    deal_id: Optional[int] = None,
    overdue: Optional[bool] = None,
    due_before: Optional[datetime] = None,
    due_after: Optional[datetime] = None,
    search: Optional[str] = None,
    sort_by: str = Query("due_date", pattern=r"^(created_at|due_date|priority|status|title)$"),
    sort_order: str = Query("asc", pattern=r"^(asc|desc)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список задач с фильтрами и пагинацией"""
    query = select(Task).where(Task.user_id == current_user.id)

    if status:
        query = query.where(Task.status == status)
    if priority:
        query = query.where(Task.priority == priority)
    if client_id:
        query = query.where(Task.client_id == client_id)
    if deal_id:
        query = query.where(Task.deal_id == deal_id)
    if overdue is not None:
        now = datetime.now(timezone.utc)
        if overdue:
            query = query.where(
                Task.due_date < now,
                Task.status.notin_(["completed", "cancelled"]),
            )
        else:
            query = query.where(
                (Task.due_date >= now) | (Task.due_date.is_(None)) |
                (Task.status.in_(["completed", "cancelled"])),
            )
    if due_before:
        query = query.where(Task.due_date <= due_before)
    if due_after:
        query = query.where(Task.due_date >= due_after)
    if search:
        query = query.where(Task.title.ilike(f"%{search}%"))

    # Сортировка
    sort_col = getattr(Task, sort_by, Task.due_date)
    if sort_order == "desc":
        query = query.order_by(desc(sort_col))
    else:
        query = query.order_by(asc(sort_col))

    result = await db.execute(
        query.offset((page - 1) * per_page).limit(per_page)
    )
    tasks = result.scalars().all()
    return [_task_out(t) for t in tasks]


@router.get("/stats", response_model=TaskStats)
async def task_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Статистика задач пользователя"""
    total = await db.scalar(
        select(func.count(Task.id)).where(Task.user_id == current_user.id)
    )
    pending = await db.scalar(
        select(func.count(Task.id)).where(Task.user_id == current_user.id, Task.status == "pending")
    )
    in_progress = await db.scalar(
        select(func.count(Task.id)).where(Task.user_id == current_user.id, Task.status == "in_progress")
    )
    completed = await db.scalar(
        select(func.count(Task.id)).where(Task.user_id == current_user.id, Task.status == "completed")
    )
    cancelled = await db.scalar(
        select(func.count(Task.id)).where(Task.user_id == current_user.id, Task.status == "cancelled")
    )

    now = datetime.now(timezone.utc)
    today_end = now.replace(hour=23, minute=59, second=59)
    week_end = now + timedelta(days=7)

    overdue = await db.scalar(
        select(func.count(Task.id)).where(
            Task.user_id == current_user.id,
            Task.due_date < now,
            Task.status.notin_(["completed", "cancelled"]),
        )
    )
    due_today = await db.scalar(
        select(func.count(Task.id)).where(
            Task.user_id == current_user.id,
            Task.due_date >= now,
            Task.due_date <= today_end,
            Task.status.notin_(["completed", "cancelled"]),
        )
    )
    due_this_week = await db.scalar(
        select(func.count(Task.id)).where(
            Task.user_id == current_user.id,
            Task.due_date >= now,
            Task.due_date <= week_end,
            Task.status.notin_(["completed", "cancelled"]),
        )
    )

    by_priority = {}
    for p in ["low", "medium", "high", "urgent"]:
        count = await db.scalar(
            select(func.count(Task.id)).where(Task.user_id == current_user.id, Task.priority == p)
        )
        by_priority[p] = count

    return TaskStats(
        total=total,
        pending=pending,
        in_progress=in_progress,
        completed=completed,
        cancelled=cancelled,
        overdue=overdue,
        due_today=due_today,
        due_this_week=due_this_week,
        by_priority=by_priority,
    )


@router.get("/kanban")
async def kanban_board(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Задачи для Kanban-доски, сгруппированные по статусам"""
    statuses = ["pending", "in_progress", "completed", "cancelled"]
    columns = {}
    for status in statuses:
        result = await db.execute(
            select(Task)
            .where(Task.user_id == current_user.id, Task.status == status)
            .order_by(asc(Task.due_date))
        )
        tasks = result.scalars().all()
        columns[status] = [_task_out(t) for t in tasks]
    return {"columns": columns}


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить задачу по ID"""
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return _task_out(task)


@router.put("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: int,
    update: TaskUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Обновление задачи"""
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    update_data = update.model_dump(exclude_unset=True)

    if "client_id" in update_data and update_data["client_id"] is not None:
        client_res = await db.execute(
            select(Client).where(Client.id == update_data["client_id"], Client.user_id == current_user.id)
        )
        if not client_res.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Клиент не найден")
    if "deal_id" in update_data and update_data["deal_id"] is not None:
        deal_res = await db.execute(
            select(Deal).where(Deal.id == update_data["deal_id"], Deal.user_id == current_user.id)
        )
        deal_obj = deal_res.scalar_one_or_none()
        if not deal_obj:
            raise HTTPException(status_code=404, detail="Сделка не найдена")
        effective_client_id = update_data.get("client_id", task.client_id)
        if effective_client_id is not None and deal_obj.client_id != effective_client_id:
            raise HTTPException(status_code=400, detail="Клиент задачи не соответствует клиенту сделки")
    elif "client_id" in update_data and update_data["client_id"] is not None and task.deal_id is not None:
        deal_res = await db.execute(
            select(Deal).where(Deal.id == task.deal_id, Deal.user_id == current_user.id)
        )
        deal_obj = deal_res.scalar_one_or_none()
        if deal_obj and deal_obj.client_id != update_data["client_id"]:
            raise HTTPException(status_code=400, detail="Клиент задачи не соответствует клиенту сделки")

    # Если статус меняется на completed — ставим completed_at
    if update_data.get("status") == "completed" and task.status != "completed":
        task.completed_at = datetime.now(timezone.utc)
    elif update_data.get("status") in ("pending", "in_progress"):
        task.completed_at = None

    for key, value in update_data.items():
        setattr(task, key, value)

    await db.commit()
    await db.refresh(task)

    await log_audit(
        action="task_updated",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Task {task_id}: {update_data}",
    )
    return _task_out(task)


@router.post("/{task_id}/complete", response_model=TaskOut)
async def complete_task(
    task_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Быстрое завершение задачи"""
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    was_completed = task.status == "completed"
    if not was_completed:
        task.status = "completed"
        task.completed_at = datetime.now(timezone.utc)
        current_user.points = (current_user.points or 0) + 10
        await db.commit()
        await db.refresh(task)

    await log_audit(
        action="task_completed",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Task {task_id} completed",
    )
    return _task_out(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удаление задачи"""
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    await db.delete(task)
    await db.commit()

    await log_audit(
        action="task_deleted",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Task {task_id} deleted",
    )


@router.post("/bulk/update")
async def bulk_update_tasks(
    bulk: TaskBulkUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Массовое обновление задач"""
    query = select(Task).where(
        Task.id.in_(bulk.task_ids),
        Task.user_id == current_user.id,
    )
    result = await db.execute(query)
    tasks = result.scalars().all()

    for task in tasks:
        if bulk.status:
            task.status = bulk.status
            if bulk.status == "completed" and task.status != "completed":
                task.completed_at = datetime.now(timezone.utc)
        if bulk.priority:
            task.priority = bulk.priority

    await db.commit()

    await log_audit(
        action="tasks_bulk_updated",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Bulk updated {len(tasks)} tasks",
    )
    return {"updated": len(tasks)}


# ============ REMINDERS ============

@router.get("/reminders/overdue")
async def overdue_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Просроченные задачи"""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Task)
        .where(
            Task.user_id == current_user.id,
            Task.due_date < now,
            Task.status.notin_(["completed", "cancelled"]),
        )
        .order_by(asc(Task.due_date))
    )
    tasks = result.scalars().all()
    return [_task_out(t) for t in tasks]


@router.get("/reminders/today")
async def tasks_due_today(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Задачи на сегодня"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    result = await db.execute(
        select(Task)
        .where(
            Task.user_id == current_user.id,
            Task.due_date >= today_start,
            Task.due_date <= today_end,
            Task.status.notin_(["completed", "cancelled"]),
        )
        .order_by(asc(Task.due_date))
    )
    tasks = result.scalars().all()
    return [_task_out(t) for t in tasks]


@router.get("/reminders/upcoming")
async def upcoming_tasks(
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Предстоящие задачи"""
    now = datetime.now(timezone.utc)
    future = now + timedelta(days=days)
    result = await db.execute(
        select(Task)
        .where(
            Task.user_id == current_user.id,
            Task.due_date >= now,
            Task.due_date <= future,
            Task.status.notin_(["completed", "cancelled"]),
        )
        .order_by(asc(Task.due_date))
    )
    tasks = result.scalars().all()
    return [_task_out(t) for t in tasks]
