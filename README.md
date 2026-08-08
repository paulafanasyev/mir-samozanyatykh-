# Мир Самозанятых v6.3

> Платформа поддержки самозанятых граждан с ИИ-ассистентом, налоговым калькулятором, CRM, маркетплейсом, грантами, блогом и real-time уведомлениями.

## Возможности

### Для самозанятых
- **ИИ-ассистент Светлана** — плавающий виджет, 17 тем, голосовой ввод, история
- **Налоговый калькулятор** — НПД с учётом вычетов, лимитов, проверка ИНН
- **CRM** — клиенты, сделки, задачи
- **Финансовый трекер** — доходы/расходы, графики, CBR курсы валют
- **Генератор договоров** — ГПД, счета, акты, чеки НПД + ЭЦП (ГК РФ ст. 160) + QR-код
- **Маркетплейс** — поиск заказов, размещение услуг
- **Гранты** — каталог с ИИ-оценкой
- **Блог** — статьи, комментарии, модерация, OG-теги, похожие статьи

### Технологии v6.3
- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, Alembic
- **Async:** Celery + Redis для фоновых задач
- **Real-time:** WebSocket уведомления
- **AI:** OpenRouter (Светлана)
- **Payments:** YooKassa интеграция
- **SMS:** SMS.ru интеграция
- **Finance:** CBR (ЦБ РФ) курсы валют с кэшированием
- **Security:** JWT, CSRF, CSP, Rate Limiting, RBAC, Audit Log, IP Whitelist
- **DevOps:** Docker, Docker Compose, Nginx

## Быстрый старт

```bash
git clone https://github.com/paulafanasyev/mir-samozanyatykh-.git
cd mir-samozanyatykh-
cp .env.example .env
# Настройте .env (см. ниже)
docker-compose up -d
```

## Переменные окружения (.env)

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/mir_samozanyatykh

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-64-char-hex-key

# AI (OpenRouter)
OPENROUTER_API_KEY=sk-or-v1-...

# Payments (YooKassa)
YOOKASSA_SHOP_ID=...
YOOKASSA_SECRET_KEY=...

# SMS (SMS.ru)
SMS_API_KEY=...

# Email (SMTP)
SMTP_HOST=smtp.yandex.ru
SMTP_PORT=465
SMTP_USER=...
SMTP_PASS=...
```

## Celery (фоновые задачи)

```bash
celery -A server.celery_app worker --loglevel=info
celery -A server.celery_app beat --loglevel=info
```

## Лицензия

© 2026 IT-Laboratory. Все права защищены.
