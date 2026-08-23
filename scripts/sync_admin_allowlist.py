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

# Скрипт запускается напрямую из корня репозитория, а приложение находится в src/app.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (SRC, ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.services.admin_bootstrap import sync_admin_allowlist


if __name__ == "__main__":
    changed = asyncio.run(sync_admin_allowlist())
    print(f"ADMIN allowlist синхронизирован. Изменено аккаунтов: {changed}")
