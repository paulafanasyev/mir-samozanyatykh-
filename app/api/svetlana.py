"""
Svetlana AI API - Security Hardened v8.4.1
ANO TsPS INN 9724016805
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.core.security import get_current_user
from app.models import User

router = APIRouter(prefix="/api/svetlana", tags=["svetlana"])


@router.post("/chat")
async def svetlana_chat(
    message: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Chat with AI Svetlana - REQUIRES AUTHENTICATION

    Each user has isolated conversation history.
    Anonymous access is NOT allowed for privacy protection.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to use AI Svetlana"
        )

    # Check AI request limits based on subscription
    # ... (existing logic)

    return {"response": "Svetlana response", "user_id": current_user.id}
