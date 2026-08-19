"""Svetlana AI API."""
import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.config import settings
from app.models import User, SvetlanaChatMessage
from app.core.auth import get_current_user
from app.core.rate_limit import limiter

router = APIRouter(prefix="/api/svetlana", tags=["svetlana"])

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    context: str | None = Field(None, max_length=4000)


async def _save_message(db: AsyncSession, user_id: int, role: str, content: str) -> None:
    db.add(SvetlanaChatMessage(user_id=user_id, role=role, content=content))
    await db.commit()

@router.post("/chat")
@limiter.limit("30/minute")
async def svetlana_chat(
    request: Request,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _save_message(db, current_user.id, "user", payload.message)
    if not settings.OPENROUTER_API_KEY:
        content = "Светлана сейчас работает в локальном режиме. Я получила ваше сообщение: " + payload.message
        await _save_message(db, current_user.id, "assistant", content)
        return {"response": content, "user_id": current_user.id, "mode": "local"}
    messages = [
        {"role":"system","content":"Ты Светлана — помощник платформы Мир Самозанятых. Отвечай по-русски, кратко и практично. Не выдумывай юридические или налоговые факты."},
        {"role":"user","content": payload.message},
    ]
    if payload.context:
        messages.insert(1, {"role":"system","content":"Контекст пользователя: " + payload.context})
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}", "Content-Type":"application/json", "HTTP-Referer": settings.FRONTEND_URL, "X-Title": settings.APP_NAME},
                json={"model": settings.OPENROUTER_MODEL_DEFAULT, "messages": messages, "temperature": 0.3, "max_tokens": 1200},
            )
        if r.status_code >= 400:
            raise HTTPException(status_code=502, detail="AI provider temporarily unavailable")
        data=r.json()
        content=data.get("choices", [{}])[0].get("message", {}).get("content")
        if not content:
            raise HTTPException(status_code=502, detail="AI provider returned an empty response")
        await _save_message(db, current_user.id, "assistant", content)
        return {"response": content, "user_id": current_user.id, "mode":"openrouter"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=502, detail="AI provider temporarily unavailable")


@router.get("/history")
async def svetlana_history(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """История диалога только текущего пользователя."""
    limit = max(1, min(limit, 200))
    result = await db.execute(
        select(SvetlanaChatMessage).where(SvetlanaChatMessage.user_id == current_user.id)
        .order_by(SvetlanaChatMessage.created_at.desc()).limit(limit)
    )
    rows = list(reversed(result.scalars().all()))
    return {"items": [{"id": r.id, "role": r.role, "content": r.content, "created_at": r.created_at} for r in rows], "total": len(rows), "persisted": True}
