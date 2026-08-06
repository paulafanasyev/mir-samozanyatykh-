# Мир Самозанятых v5.0

Платформа для самозанятых — безопасная версия с полным набором исправлений.

## Возможности

- 🔐 JWT-аутентификация с jti и типом токена
- 📧 Подтверждение email через SMTP
- 🛡️ CSRF-защита, rate limiting, account lockout
- 📝 Audit log всех действий
- 🤖 ИИ-ассистент Светлана с внешней базой знаний
- 📄 Шаблоны договоров
- 📤 Загрузка файлов с валидацией
- 🔍 Healthcheck API
- 🐳 Docker + Traefik + Let's Encrypt

## Технологии

- Python 3.12
- FastAPI + SQLAlchemy async
- Alembic миграции
- Jinja2 шаблоны
- Traefik reverse proxy
- PostgreSQL (с поддержкой SQLite для dev) (async)

## Лицензия

MIT


## PostgreSQL (v5.0+)

Проект мигрирован на PostgreSQL для production-использования.

### Локальная разработка (SQLite)
```bash
DATABASE_URL=sqlite+aiosqlite:///./data/mir_samozanyatykh.db
```

### Production (PostgreSQL)
```bash
# Docker Compose запускает PostgreSQL автоматически
DATABASE_URL=postgresql+asyncpg://mir_user:пароль@postgres:5432/mir_samozanyatykh
```

### Миграции
```bash
# Создать миграцию
alembic revision --autogenerate -m "init"

# Применить миграции
alembic upgrade head
```

### Переход с SQLite на PostgreSQL
1. Запустите PostgreSQL: `docker-compose up -d postgres`
2. Примените миграции: `alembic upgrade head`
3. Запустите приложение: `docker-compose up -d app`
