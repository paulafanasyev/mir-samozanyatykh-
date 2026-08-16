# API Documentation — МИР Самозанятых v8.7.0

## Auth
- `POST /api/auth/register` — Регистрация
- `POST /api/auth/login` — Вход
- `POST /api/auth/refresh` — Обновление токена
- `GET /api/auth/me` — Профиль

## Contracts
- `GET /api/contracts` — Список
- `POST /api/contracts` — Создать
- `GET /api/contracts/{id}` — Получить
- `PUT /api/contracts/{id}` — Обновить
- `DELETE /api/contracts/{id}` — Удалить

## Finance
- `GET /api/finance` — Список
- `POST /api/finance` — Создать

## Calculator
- `POST /api/calculator/npd` — Расчёт НПД

## CRM
- `GET /api/crm/clients` — Список клиентов
- `POST /api/crm/clients` — Создать клиента

## Marketplace
- `GET /api/marketplace/services` — Список услуг
- `POST /api/marketplace/services` — Создать услугу

## Grants
- `GET /api/grants` — Список
- `POST /api/grants` — Создать

## Notifications
- `GET /api/notifications` — Список
- `POST /api/notifications` — Создать

## Achievements
- `GET /api/achievements` — Список

## Svetlana AI
- `POST /api/svetlana/chat` — Чат с ИИ

## Admin
- `GET /api/admin/users` — Пользователи
- `GET /api/admin/audit` — Audit log
- `GET /api/admin/stats` — Статистика

## CBR
- `GET /api/cbr/rates` — Курсы валют

## Health
- `GET /api/health` — Проверка
