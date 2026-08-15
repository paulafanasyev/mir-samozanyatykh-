<div align="center">

# Мир Самозанятых

[![Version](https://img.shields.io/badge/version-8.6.3-blue.svg)](https://github.com/paulafanasyev/mir-samozanyatykh-)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green.svg)](https://fastapi.tiangolo.com)
[![Flutter](https://img.shields.io/badge/Flutter-3.24+-blue.svg)](https://flutter.dev)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-124%2F125-brightgreen.svg)](tests/)

**Платформа для самозанятых, фрилансеров и малого бизнеса**

[🌐 Сайт](https://mir-samozanyatykh.ru) • [📱 Мобильное приложение](https://github.com/paulafanasyev/mir-samozanyatykh-/releases) • [📖 Документация](API.md) • [🚀 Развёртывание](DEPLOY.md)

</div>

---


# Мир Самозанятых v8.1

**АНО ЦПС «Мир Самозанятых» | ИНН 9724016805**

Платформа для самозанятых и фрилансеров: счета, договоры, клиенты, задачи, календарь, AI-ассистент Светлана, аналитика, реферальная система, API и вебхуки.

## Стек

| Слой | Технологии |
|------|-----------|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL, Redis |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, Zustand |
| **Mobile** | Flutter 3, Riverpod, GoRouter, Firebase, Hive, WebRTC |
| **Infra** | Docker, Traefik, Let's Encrypt |

## Быстрый старт

```bash
# Клонировать репозиторий
git clone https://github.com/paulafanasyev/mir-samozanyatykh-.git
cd mir-samozanyatykh-

# Настроить окружение
cp .env.example .env
# Отредактировать .env (SECRET_KEY, БД, SMTP и т.д.)

# Запуск через Docker
./deploy.sh

# Или вручную:
docker compose up -d
```

## Модули

| Модуль | Описание | Версия |
|--------|----------|--------|
| 🔐 **Аутентификация** | JWT + jti, 2FA TOTP, OAuth (Google, Яндекс, Telegram) | v6.0 |
| 📊 **Продажи** | Товары/услуги, счета, платежи, PDF, ЮKassa | v6.0 |
| 📝 **Договоры** | ГПХ, ИТ, услуги, акты — с электронной подписью | v6.0 |
| 👥 **CRM** | Клиенты, сделки, воронка продаж | v6.0 |
| 🤖 **Светлана** | AI-ассистент (OpenRouter + CosyVoice 3.0) | v6.0 |
| 📅 **Задачи** | Kanban-доска, приоритеты, теги, дедлайны | v7.7 |
| 📆 **Календарь** | События, напоминания, интеграция с задачами | v7.7 |
| 🔔 **Уведомления** | Email, push, WebSocket, настройки | v7.6 |
| 👥 **Рефералы** | Реферальные ссылки, скидки, статистика | v7.6 |
| 👮 **Админ-панель** | Статистика, пользователи, audit logs, модерация | v7.5 |
| 🔑 **API ключи** | Генерация, scopes, rate limit | v7.8 |
| 🪝 **Вебхуки** | Подписка на события, retry-логика, подпись | v7.8 |
| 📤 **Экспорт** | CSV, Excel, PDF для всех модулей | v7.8 |
| 📥 **Импорт** | Загрузка клиентов и товаров из CSV/Excel | v7.8 |
| 📈 **Аналитика** | AI-аналитика, отчеты, дашборд | v7.4 |
| 💬 **WebRTC** | Видеозвонки, конференции | v7.3 |
| 💬 **Telegram бот** | Уведомления, команды | v7.3 |
| 🔍 **Поиск** | Глобальный поиск по всем данным | v7.4 |

## Безопасность

- **JWT** с jti (JSON Token Identifier) для отзыва токенов
- **CSRF** защита на всех формах
- **Rate limiting** — 5 попыток входа, блокировка на 30 мин
- **CSP** (Content Security Policy) с nonce
- **HSTS**, X-Frame-Options, X-Content-Type-Options
- **OWASP ZAP** тестирование
- **pytest** — полный набор тестов

## API

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **Полная документация:** [`docs/API.md`](docs/API.md)
- **Встроенная справка:** `/docs` (в frontend)

### Пример запроса

```bash
# Вход
curl -X POST http://localhost:8000/api/auth/login \
  -d "email=test@example.com&password=StrongPass123!"

# Создание счета
curl -X POST http://localhost:8000/api/sales/invoices \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": 1,
    "due_date": "2026-02-15",
    "items": [{"description": "Разработка", "quantity": 1, "unit_price": 50000}]
  }'
```

## Тестирование

```bash
# Все тесты
pytest

# С покрытием
pytest --cov=app --cov-report=html

# Конкретный модуль
pytest tests/test_api_keys.py -v
```

## Деплой

```bash
# Полный деплой с бэкапом и миграциями
./deploy.sh production

# Команды:
./deploy.sh backup    # Бэкап БД
./deploy.sh migrate   # Миграции
./deploy.sh logs      # Логи
./deploy.sh stop      # Остановка
./deploy.sh status    # Статус
./deploy.sh update    # Обновление
```

## Структура проекта

```
mir-samozanyatykh-/
├── app/                    # Backend FastAPI
│   ├── api/               # Роутеры (auth, sales, crm, ...)
│   ├── core/              # Config, database, security, logging
│   ├── models.py          # SQLAlchemy модели
│   └── main.py            # Точка входа
├── frontend/              # React + TypeScript
│   ├── src/
│   │   ├── pages/        # Страницы
│   │   ├── components/   # Компоненты
│   │   └── api/          # API клиент
│   └── package.json
├── tests/                 # Pytest тесты
├── docs/                  # Документация
├── alembic/              # Миграции БД
├── deploy.sh             # Скрипт деплоя
├── docker-compose.yml    # Docker конфиг
└── DEPLOY.md             # Подробный гайд деплоя
```

## Интеграции

| Сервис | Назначение |
|--------|-----------|
| **OpenRouter** | AI-модели для Светланы |
| **CosyVoice 3.0** | Голосовой синтез |
| **ЮKassa** | Онлайн-платежи |
| **SMTP SSL** | Email-уведомления |
| **Telegram Bot API** | Бот-уведомления |
| **WebRTC** | Видеозвонки |

## Переменные окружения

Ключевые переменные (см. `.env.example`):

```bash
SECRET_KEY=              # Минимум 32 символа
DATABASE_URL=            # PostgreSQL
REDIS_URL=               # Redis
SMTP_HOST=               # Email сервер
OPENROUTER_API_KEY=      # AI API
YOOKASSA_SHOP_ID=        # Платежи
YOOKASSA_SECRET_KEY=     # Платежи
TELEGRAM_BOT_TOKEN=      # Telegram бот
```

## Лицензия

**АНО ЦПС «Мир Самозанятых»**

ИНН: 9724016805

---

*Версия: 7.9.0 | Последнее обновление: 2026-08-09*
