"""Синхронизация ADMIN-аккаунтов с явным allowlist.

Безопасные свойства:
- пароли не читаются и не меняются;
- адреса нормализуются;
- операция идемпотентна;
- только подтверждённые и активные пользователи из ADMIN_EMAILS получают is_admin;
- остальные пользователи теряют is_admin, но is_moderator не меняется.

Запуск из корня проекта:
    python scripts/sync_admin_allowlist.py

Используется только в окружении с настроенным DATABASE_URL.
"""

import asyncio
import sys
from pathlib import Path

# Позволяет запускать скрипт напрямую из корня репозитория.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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


async def sync_admins() -> int:
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


if __name__ == "__main__":
    changed = asyncio.run(sync_admins())
    print(f"ADMIN allowlist синхронизирован. Изменено аккаунтов: {changed}")
