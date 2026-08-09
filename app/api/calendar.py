"""
API календаря v7.9
События, интеграция с задачами, напоминания
АНО ЦПС ИНН 9724016805
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, update, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logging import log_audit
from app.models import User, CalendarEvent, Task, Client, Deal

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


# ============ SCHEMAS ============

class EventCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    event_type: str = Field("meeting", pattern=r"^(meeting|call|task|deadline|reminder|other)$")
    start_time: datetime
    end_time: Optional[datetime] = None
    all_day: bool = False
    location: Optional[str] = Field(None, max_length=500)
    client_id: Optional[int] = None
    deal_id: Optional[int] = None
    task_id: Optional[int] = None
    color: Optional[str] = Field(None, max_length=7)  # hex
    reminder_minutes: Optional[int] = Field(15, ge=0, le=1440)


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    event_type: Optional[str] = Field(None, pattern=r"^(meeting|call|task|deadline|reminder|other)$")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    all_day: Optional[bool] = None
    location: Optional[str] = Field(None, max_length=500)
    client_id: Optional[int] = None
    deal_id: Optional[int] = None
    task_id: Optional[int] = None
    color: Optional[str] = Field(None, max_length=7)
    reminder_minutes: Optional[int] = Field(None, ge=0, le=1440)


class EventOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    event_type: str
    start_time: datetime
    end_time: Optional[datetime]
    all_day: bool
    location: Optional[str]
    client_id: Optional[int]
    client_name: Optional[str]
    deal_id: Optional[int]
    deal_title: Optional[str]
    task_id: Optional[int]
    task_title: Optional[str]
    color: Optional[str]
    reminder_minutes: int
    created_at: datetime

    class Config:
        from_attributes = True


class CalendarView(BaseModel):
    date: str
    events: List[EventOut]
    tasks_due: List[dict]


# ============ CRUD ============

@router.post("/events", response_model=EventOut, status_code=status.HTTP_201_CREATED)
async def create_event(
    event: EventCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Создание события в календаре"""
    # Валидация связей
    if event.client_id:
        client_res = await db.execute(
            select(Client).where(Client.id == event.client_id, Client.user_id == current_user.id)
        )
        if not client_res.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Клиент не найден")
    if event.deal_id:
        deal_res = await db.execute(
            select(Deal).where(Deal.id == event.deal_id, Deal.user_id == current_user.id)
        )
        if not deal_res.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Сделка не найдена")
    if event.task_id:
        task_res = await db.execute(
            select(Task).where(Task.id == event.task_id, Task.user_id == current_user.id)
        )
        if not task_res.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Задача не найдена")

    db_event = CalendarEvent(
        user_id=current_user.id,
        **event.model_dump(exclude_unset=True),
    )
    db.add(db_event)
    await db.commit()
    await db.refresh(db_event)

    await log_audit(
        action="calendar_event_created",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Event {db_event.id}: {db_event.title}",
    )
    return _event_out(db_event)


def _event_out(event: CalendarEvent) -> EventOut:
    return EventOut(
        id=event.id,
        title=event.title,
        description=event.description,
        event_type=event.event_type,
        start_time=event.start_time,
        end_time=event.end_time,
        all_day=event.all_day,
        location=event.location,
        client_id=event.client_id,
        client_name=event.client.name if event.client else None,
        deal_id=event.deal_id,
        deal_title=event.deal.title if event.deal else None,
        task_id=event.task_id,
        task_title=event.task.title if event.task else None,
        color=event.color,
        reminder_minutes=event.reminder_minutes or 15,
        created_at=event.created_at,
    )


@router.get("/events", response_model=List[EventOut])
async def list_events(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    event_type: Optional[str] = None,
    client_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список событий за период"""
    if not start:
        start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0)
    if not end:
        end = start + timedelta(days=31)

    query = select(CalendarEvent).where(
        CalendarEvent.user_id == current_user.id,
        CalendarEvent.start_time >= start,
        CalendarEvent.start_time <= end,
    )
    if event_type:
        query = query.where(CalendarEvent.event_type == event_type)
    if client_id:
        query = query.where(CalendarEvent.client_id == client_id)

    query = query.order_by(asc(CalendarEvent.start_time))
    result = await db.execute(query)
    events = result.scalars().all()
    return [_event_out(e) for e in events]


@router.get("/events/{event_id}", response_model=EventOut)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить событие по ID"""
    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == current_user.id,
        )
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    return _event_out(event)


@router.put("/events/{event_id}", response_model=EventOut)
async def update_event(
    event_id: int,
    update: EventUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Обновление события"""
    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == current_user.id,
        )
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")

    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(event, key, value)

    await db.commit()
    await db.refresh(event)

    await log_audit(
        action="calendar_event_updated",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Event {event_id} updated",
    )
    return _event_out(event)


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удаление события"""
    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == current_user.id,
        )
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")

    await db.delete(event)
    await db.commit()

    await log_audit(
        action="calendar_event_deleted",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Event {event_id} deleted",
    )


# ============ CALENDAR VIEW ============

@router.get("/view/month")
async def month_view(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Календарь на месяц — события + задачи"""
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc)

    # События
    events_result = await db.execute(
        select(CalendarEvent)
        .where(
            CalendarEvent.user_id == current_user.id,
            CalendarEvent.start_time >= start,
            CalendarEvent.start_time < end,
        )
        .order_by(asc(CalendarEvent.start_time))
    )
    events = events_result.scalars().all()

    # Задачи с дедлайном
    tasks_result = await db.execute(
        select(Task)
        .where(
            Task.user_id == current_user.id,
            Task.due_date >= start,
            Task.due_date < end,
            Task.status.notin_(["completed", "cancelled"]),
        )
        .order_by(asc(Task.due_date))
    )
    tasks = tasks_result.scalars().all()

    # Группировка по дням
    days = {}
    current = start
    while current < end:
        date_str = current.strftime("%Y-%m-%d")
        days[date_str] = {
            "date": date_str,
            "events": [],
            "tasks_due": [],
        }
        current += timedelta(days=1)

    for event in events:
        date_str = event.start_time.strftime("%Y-%m-%d")
        if date_str in days:
            days[date_str]["events"].append(_event_out(event))

    for task in tasks:
        date_str = task.due_date.strftime("%Y-%m-%d")
        if date_str in days:
            days[date_str]["tasks_due"].append({
                "id": task.id,
                "title": task.title,
                "priority": task.priority,
                "status": task.status,
            })

    return {
        "year": year,
        "month": month,
        "days": list(days.values()),
    }


@router.get("/view/week")
async def week_view(
    date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Календарь на неделю"""
    if date:
        base = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        base = datetime.now(timezone.utc)

    # Начало недели (понедельник)
    weekday = base.weekday()
    week_start = base - timedelta(days=weekday)
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)

    # События
    events_result = await db.execute(
        select(CalendarEvent)
        .where(
            CalendarEvent.user_id == current_user.id,
            CalendarEvent.start_time >= week_start,
            CalendarEvent.start_time < week_end,
        )
        .order_by(asc(CalendarEvent.start_time))
    )
    events = events_result.scalars().all()

    # Задачи
    tasks_result = await db.execute(
        select(Task)
        .where(
            Task.user_id == current_user.id,
            Task.due_date >= week_start,
            Task.due_date < week_end,
            Task.status.notin_(["completed", "cancelled"]),
        )
        .order_by(asc(Task.due_date))
    )
    tasks = tasks_result.scalars().all()

    # Группировка по дням недели
    week_days = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        week_days.append({
            "date": day_str,
            "day_name": day.strftime("%A"),
            "events": [_event_out(e) for e in events if e.start_time.strftime("%Y-%m-%d") == day_str],
            "tasks_due": [
                {"id": t.id, "title": t.title, "priority": t.priority, "status": t.status}
                for t in tasks if t.due_date.strftime("%Y-%m-%d") == day_str
            ],
        })

    return {
        "week_start": week_start.strftime("%Y-%m-%d"),
        "week_end": (week_end - timedelta(days=1)).strftime("%Y-%m-%d"),
        "days": week_days,
    }


@router.get("/today")
async def today_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Сводка на сегодня: события + задачи"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    # События сегодня
    events_result = await db.execute(
        select(CalendarEvent)
        .where(
            CalendarEvent.user_id == current_user.id,
            CalendarEvent.start_time >= today_start,
            CalendarEvent.start_time <= today_end,
        )
        .order_by(asc(CalendarEvent.start_time))
    )
    events = events_result.scalars().all()

    # Задачи на сегодня
    tasks_result = await db.execute(
        select(Task)
        .where(
            Task.user_id == current_user.id,
            Task.due_date >= today_start,
            Task.due_date <= today_end,
            Task.status.notin_(["completed", "cancelled"]),
        )
        .order_by(asc(Task.due_date))
    )
    tasks = tasks_result.scalars().all()

    # Просроченные задачи
    overdue_result = await db.execute(
        select(Task)
        .where(
            Task.user_id == current_user.id,
            Task.due_date < today_start,
            Task.status.notin_(["completed", "cancelled"]),
        )
        .order_by(asc(Task.due_date))
    )
    overdue = overdue_result.scalars().all()

    return {
        "date": now.strftime("%Y-%m-%d"),
        "events": [_event_out(e) for e in events],
        "tasks_due": [
            {"id": t.id, "title": t.title, "priority": t.priority, "status": t.status}
            for t in tasks
        ],
        "overdue": [
            {"id": t.id, "title": t.title, "priority": t.priority, "days_overdue": (today_start - t.due_date).days}
            for t in overdue
        ],
        "total_events": len(events),
        "total_tasks": len(tasks),
        "total_overdue": len(overdue),
    }
