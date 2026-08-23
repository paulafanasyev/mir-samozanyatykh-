"""Безопасная синхронизация человеческих ADMIN-аккаунтов при старте приложения."""

from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models import User


def allowed_admin_emails() -> set[str]:
    return {
        email.strip().lower()
        for email in settings.ADMIN_EMAILS.split(",")
        if email.strip()
    }


async def sync_admin_allowlist() -> int:
    """Синхронизирует is_admin только для активных подтверждённых аккаунтов.

    Пароли, is_moderator и другие поля пользователя не изменяются.
    """
    allowed = allowed_admin_emails()
    if not allowed:
        raise RuntimeError("ADMIN_EMAILS не должен быть пустым")

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        changed = 0
        for user in users:
            should_be_admin = (
                user.email.strip().lower() in allowed
                and bool(user.is_verified)
                and bool(user.is_active)
            )
            if bool(user.is_admin) != should_be_admin:
                user.is_admin = should_be_admin
                changed += 1
        await db.commit()
        return changed
