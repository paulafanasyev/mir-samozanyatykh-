"""
API поиска v6.9
Полнотекстовый поиск по клиентам, сделкам, задачам
"""

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User, Client, Deal, Task
from app.core.auth import get_current_user, get_current_user_optional

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/")
async def search(
    q: str,
    entity: str = "all",  # all, clients, deals, tasks
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Полнотекстовый поиск"""
    results = {}
    search_term = f"%{q}%"

    if entity in ("all", "clients"):
        clients_result = await db.execute(
            select(Client).where(
                Client.user_id == current_user.id,
                or_(
                    Client.name.ilike(search_term),
                    Client.email.ilike(search_term),
                    Client.phone.ilike(search_term),
                    Client.inn.ilike(search_term),
                    Client.company.ilike(search_term),
                )
            ).limit(limit)
        )
        results["clients"] = clients_result.scalars().all()

    if entity in ("all", "deals"):
        deals_result = await db.execute(
            select(Deal).where(
                Deal.user_id == current_user.id,
                or_(
                    Deal.title.ilike(search_term),
                    Deal.description.ilike(search_term),
                    Deal.status.ilike(search_term),
                )
            ).limit(limit)
        )
        results["deals"] = deals_result.scalars().all()

    if entity in ("all", "tasks"):
        tasks_result = await db.execute(
            select(Task).where(
                Task.user_id == current_user.id,
                or_(
                    Task.title.ilike(search_term),
                    Task.description.ilike(search_term),
                    Task.status.ilike(search_term),
                )
            ).limit(limit)
        )
        results["tasks"] = tasks_result.scalars().all()

    return {
        "query": q,
        "entity": entity,
        "results": results,
        "total": sum(len(v) for v in results.values()),
    }
