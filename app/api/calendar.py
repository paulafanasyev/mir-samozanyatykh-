"""
API календаря v6.9
События, напоминания, интеграция с задачами
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logging import log_audit
from app.models import User, CalendarEvent

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    event_type: str = "meeting"  # meeting, call, deadline, reminder
    client_id: Optional[int] = None
    deal_id: Optional[int] = None
    is_all_day: bool = False
    location: Optional[str] = None
    reminder_minutes: int = 15


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    event_type: Optional[str] = None
    client_id: Optional[int] = None
    deal_id: Optional[int] = None
    is_all_day: Optional[bool] = None
    location: Optional[str] = None
    reminder_minutes: Optional[int] = None


@router.get("/events")
async def list_events(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    event_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список событий календаря"""
    query = select(CalendarEvent).where(CalendarEvent.user_id == current_user.id)

    if start:
        query = query.where(CalendarEvent.start_time >= start)
    if end:
        query = query.where(CalendarEvent.start_time <= end)
    if event_type:
        query = query.where(CalendarEvent.event_type == event_type)

    result = await db.execute(query.order_by(CalendarEvent.start_time.asc()))
    return result.scalars().all()


@router.post("/events", status_code=status.HTTP_201_CREATED)
async def create_event(
    event: EventCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Создание события в календаре"""
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
        details=f"Event: {event.title}",
    )
    return db_event


@router.get("/events/{event_id}")
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получение события"""
    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == current_user.id,
        )
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    return event


@router.put("/events/{event_id}")
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

    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(event, key, value)

    await db.commit()
    await db.refresh(event)
    return event


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


@router.get("/today")
async def today_events(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """События на сегодня"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.user_id == current_user.id,
            CalendarEvent.start_time >= today_start,
            CalendarEvent.start_time < today_end,
        ).order_by(CalendarEvent.start_time.asc())
    )
    return result.scalars().all()


@router.get("/upcoming")
async def upcoming_events(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Предстоящие события"""
    now = datetime.now(timezone.utc)
    future = now + timedelta(days=days)

    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.user_id == current_user.id,
            CalendarEvent.start_time >= now,
            CalendarEvent.start_time <= future,
        ).order_by(CalendarEvent.start_time.asc())
    )
    return result.scalars().all()
