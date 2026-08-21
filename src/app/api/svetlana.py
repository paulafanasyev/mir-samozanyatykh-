"""Svetlana local/offline API.

No cloud AI provider is used here. The runtime answers from the versioned local
knowledge base and exposes a stable HTTP contract for the web UI.
"""
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_optional
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models import SvetlanaChatMessage, User
from app.services.local_svetlana import answer_local, local_status

router = APIRouter(prefix="/api/svetlana", tags=["svetlana"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    context: str | None = Field(None, max_length=4000)


async def _save_message(db: AsyncSession, user_id: int, role: str, content: str) -> None:
    db.add(SvetlanaChatMessage(user_id=user_id, role=role, content=content))
    await db.commit()


@router.get("/status")
async def svetlana_status() -> dict:
    return local_status()


@router.post("/chat")
@limiter.limit("30/minute")
async def svetlana_chat(
    request: Request,
    payload: ChatRequest,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Answer locally. Authentication is optional so Svetlana works before registration."""
    if current_user:
        await _save_message(db, current_user.id, "user", payload.message)
    content = answer_local(payload.message, payload.context)
    if current_user:
        await _save_message(db, current_user.id, "assistant", content)
    return {
        "response": content,
        "user_id": current_user.id if current_user else None,
        "mode": "offline",
        "provider": "local",
    }


@router.get("/history")
async def svetlana_history(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """История диалога только текущего авторизованного пользователя."""
    if not current_user:
        return {"items": [], "total": 0, "persisted": False}
    limit = max(1, min(limit, 200))
    result = await db.execute(
        select(SvetlanaChatMessage)
        .where(SvetlanaChatMessage.user_id == current_user.id)
        .order_by(SvetlanaChatMessage.created_at.desc())
        .limit(limit)
    )
    rows = list(reversed(result.scalars().all()))
    return {
        "items": [
            {"id": r.id, "role": r.role, "content": r.content, "created_at": r.created_at}
            for r in rows
        ],
        "total": len(rows),
        "persisted": True,
    }
