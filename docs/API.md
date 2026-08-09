# API Документация — Мир Самозанятых v8.1

АНО ЦПС «Мир Самозанятых» | ИНН 9724016805

## Базовый URL

```
Production: https://mir-samozanyatykh.ru/api
Local:      http://localhost:8000/api
```

## Аутентификация

Все защищённые endpoints требуют Bearer токен в заголовке:
```
Authorization: Bearer <access_token>
```

### Регистрация
```http
POST /api/auth/register
Content-Type: application/x-www-form-urlencoded

email=test@example.com&password=StrongPass123!&full_name=Иван+Иванов&phone=+79001234567&inn=123456789012
```

**Ответ:**
```json
{
  "message": "Регистрация успешна. Проверьте email.",
  "email_sent": true,
  "user_id": 1
}
```

### Вход
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

email=test@example.com&password=StrongPass123!
```

**Ответ:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800,
  "tier": "business"
}
```

### Выход
```http
POST /api/auth/logout
Authorization: Bearer <token>
```

### Обновление токена
```http
POST /api/auth/refresh
Content-Type: application/x-www-form-urlencoded

refresh_token=<refresh_token>
```

---

## 2FA (Двухфакторная аутентификация)

### Настройка
```http
POST /api/auth/2fa/setup
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "qr_code": "data:image/png;base64,...",
  "secret": "BASE32SECRET",
  "backup_codes": ["code1", "code2", ...],
  "message": "Сохраните резервные коды!"
}
```

### Подтверждение
```http
POST /api/auth/2fa/verify
Authorization: Bearer <token>
Content-Type: application/x-www-form-urlencoded

code=123456
```

### Отключение
```http
POST /api/auth/2fa/disable
Authorization: Bearer <token>
Content-Type: application/x-www-form-urlencoded

password=CurrentPass123!
```

---

## Пользователи

### Профиль
```http
GET /api/users/me
Authorization: Bearer <token>
```

### Обновление профиля
```http
PUT /api/users/me
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "Новое Имя",
  "phone": "+79001234567",
  "inn": "123456789012"
}
```

### Смена пароля
```http
POST /api/users/me/password
Authorization: Bearer <token>
Content-Type: application/json

{
  "current_password": "OldPass123!",
  "new_password": "NewStrongPass123!"
}
```

---

## Модуль продаж

### Услуги/Товары

#### Список
```http
GET /api/sales/products
Authorization: Bearer <token>
```

#### Создание
```http
POST /api/sales/products
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Разработка сайта",
  "description": "Landing page",
  "price": 50000.00,
  "unit": "шт",
  "sku": "DEV-001"
}
```

#### Обновление
```http
PUT /api/sales/products/{id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Обновлённое название",
  "price": 60000.00
}
```

#### Удаление
```http
DELETE /api/sales/products/{id}
Authorization: Bearer <token>
```

### Счета

#### Список с фильтрацией
```http
GET /api/sales/invoices?status=draft&client_id=1&page=1&per_page=20
Authorization: Bearer <token>
```

#### Создание
```http
POST /api/sales/invoices
Authorization: Bearer <token>
Content-Type: application/json

{
  "client_id": 1,
  "due_date": "2026-02-15",
  "notes": "Оплатить до 15 февраля",
  "items": [
    {
      "description": "Разработка сайта",
      "quantity": 1,
      "unit_price": 50000.00
    },
    {
      "description": "Настройка SEO",
      "quantity": 1,
      "unit_price": 15000.00
    }
  ]
}
```

#### Получение
```http
GET /api/sales/invoices/{id}
Authorization: Bearer <token>
```

#### Обновление
```http
PUT /api/sales/invoices/{id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "sent",
  "notes": "Обновлённые примечания"
}
```

#### Удаление (только draft)
```http
DELETE /api/sales/invoices/{id}
Authorization: Bearer <token>
```

#### Отправка клиенту
```http
POST /api/sales/invoices/{id}/send
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "message": "Счёт отправлен",
  "invoice_number": "СЧ-1-20260115-0001",
  "email_sent": true,
  "pdf_generated": true
}
```

#### Скачивание PDF
```http
GET /api/sales/invoices/{id}/pdf
Authorization: Bearer <token>
```

### Платежи

#### Ручное создание
```http
POST /api/sales/invoices/{id}/payments
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": 50000.00,
  "payment_method": "cash"
}
```

#### Список платежей
```http
GET /api/sales/invoices/{id}/payments
Authorization: Bearer <token>
```

### ЮKassa интеграция

#### Создание онлайн-платежа
```http
POST /api/sales/invoices/{id}/yookassa
Authorization: Bearer <token>
Content-Type: application/json

{
  "invoice_id": 1,
  "return_url": "https://mir-samozanyatykh.ru/payment/success"
}
```

**Ответ:**
```json
{
  "payment_id": "2a1b2c3d-4e5f-6g7h-8i9j-0k1l2m3n4o5p",
  "confirmation_url": "https://yoomoney.ru/checkout/payments/...",
  "status": "pending",
  "amount": 65000.00,
  "description": "Оплата счёта СЧ-1-20260115-0001"
}
```

#### Webhook (серверный)
```http
POST /api/sales/yookassa/webhook
Content-Type: application/json

{
  "event": "payment.succeeded",
  "object": {
    "id": "2a1b2c3d-...",
    "status": "succeeded",
    "amount": {"value": "65000.00", "currency": "RUB"},
    "metadata": {"invoice_id": "1"}
  }
}
```

### Статистика

#### Общая статистика
```http
GET /api/sales/stats
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "total_invoices": 15,
  "total_revenue": 450000.00,
  "pending_amount": 120000.00,
  "overdue_invoices": 2,
  "paid_count": 10,
  "sent_count": 3,
  "draft_count": 2,
  "average_invoice_amount": 30000.00
}
```

#### Дашборд
```http
GET /api/sales/dashboard
Authorization: Bearer <token>
```

---

## Договоры

### Шаблоны

#### Список
```http
GET /api/contracts/templates?category=gpd
Authorization: Bearer <token>
```

#### Детали шаблона
```http
GET /api/contracts/templates/gpd
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "id": 0,
  "name": "Договор ГПД (гражданско-правовой)",
  "category": "gpd",
  "fields": [
    {"key": "contractor_name", "label": "ФИО исполнителя", "type": "text", "required": true},
    {"key": "price", "label": "Стоимость (₽)", "type": "number", "required": true}
  ],
  "sample_data": {
    "contractor_name": "Иванов И.И.",
    "contractor_inn": "123456789012"
  },
  "is_premium": false,
  "locked": false
}
```

### Генерация
```http
POST /api/contracts/generate
Authorization: Bearer <token>
Content-Type: application/json

{
  "template_id": "gpd",
  "variables": {
    "contractor_name": "Иванов Иван Иванович",
    "contractor_inn": "123456789012",
    "client_name": "ООО Ромашка",
    "client_inn": "987654321098",
    "subject": "Разработка сайта",
    "price": "50000",
    "deadline": "2026-03-01"
  },
  "sign": false
}
```

### Подписание
```http
POST /api/contracts/{id}/sign
Authorization: Bearer <token>
```

### Проверка подписи
```http
POST /api/contracts/{id}/verify
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "signed": true,
  "valid": true,
  "signature_info": {
    "signature": "a1b2c3d4...",
    "timestamp": "2026-01-15T10:30:00+00:00",
    "algorithm": "HMAC-SHA256",
    "legal_basis": "ГК РФ ст. 160"
  },
  "message": "Подпись действительна"
}
```

### Скачивание PDF
```http
GET /api/contracts/{id}/pdf
Authorization: Bearer <token>
```

---

## CRM

### Клиенты

#### Список
```http
GET /api/crm/clients?search=ромашка&status=active
Authorization: Bearer <token>
```

#### Создание
```http
POST /api/crm/clients
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "ООО Ромашка",
  "email": "info@romashka.ru",
  "phone": "+74951234567",
  "company": "ООО Ромашка",
  "inn": "7701234567",
  "notes": "Крупный клиент"
}
```

### Сделки

#### Список
```http
GET /api/crm/deals?status=negotiation&client_id=1
Authorization: Bearer <token>
```

#### Создание
```http
POST /api/crm/deals
Authorization: Bearer <token>
Content-Type: application/json

{
  "client_id": 1,
  "title": "Разработка CRM",
  "amount": 150000,
  "description": "Полная разработка",
  "deadline": "2026-06-01",
  "priority": "high"
}
```

#### Статистика
```http
GET /api/crm/stats
Authorization: Bearer <token>
```

---

## AI Ассистент Светлана

### Текстовый чат
```http
POST /api/svetlana/chat
Authorization: Bearer <token>
Content-Type: application/x-www-form-urlencoded

message=Какие+налоги+платит+самозанятый?&voice=false&emotion=neutral
```

**Ответ:**
```json
{
  "response": "Самозанятые платят налог на профессиональный доход (НПД)..."
}
```

### Голосовой ответ
```http
POST /api/svetlana/chat
Authorization: Bearer <token>
Content-Type: application/x-www-form-urlencoded

message=Расскажи+про+вычеты&voice=true&emotion=friendly
```

**Ответ:** `audio/mpeg` поток

### Только голос
```http
POST /api/svetlana/voice
Authorization: Bearer <token>
Content-Type: application/x-www-form-urlencoded

text=Здравствуйте!+Я+Светлана,+ваш+помощник.&emotion=professional
```

### Статус
```http
GET /api/svetlana/status
```

---

## Задачи и Календарь (v7.7+)

### Задачи

#### Список
```http
GET /api/tasks?page=1&per_page=20&status=pending&priority=high
Authorization: Bearer <token>
```

#### Создание
```http
POST /api/tasks
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Подготовить договор",
  "description": "Составить ГПД для клиента ООО Ромашка",
  "due_date": "2026-02-20T10:00:00",
  "priority": "high",
  "status": "pending",
  "tags": ["договор", "срочно"]
}
```

#### Обновление
```http
PUT /api/tasks/{id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "in_progress",
  "progress": 50
}
```

#### Удаление
```http
DELETE /api/tasks/{id}
Authorization: Bearer <token>
```

#### Kanban — перемещение
```http
POST /api/tasks/{id}/move
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "completed"
}
```

### Календарь

#### Список событий
```http
GET /api/calendar/events?start=2026-02-01&end=2026-02-28
Authorization: Bearer <token>
```

#### Создание события
```http
POST /api/calendar/events
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Встреча с клиентом",
  "description": "Обсуждение проекта",
  "start_time": "2026-02-15T14:00:00",
  "end_time": "2026-02-15T15:30:00",
  "location": "Офис",
  "reminder_minutes": 30,
  "color": "#1976D2"
}
```

#### Обновление
```http
PUT /api/calendar/events/{id}
Authorization: Bearer <token>
```

#### Удаление
```http
DELETE /api/calendar/events/{id}
Authorization: Bearer <token>
```

---

## Реферальная система (v7.6+)

### Получение реферальной ссылки
```http
GET /api/referrals/link
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "referral_code": "ABC123",
  "referral_link": "https://mir-samozanyatykh.ru/register?ref=ABC123",
  "total_referrals": 5,
  "total_earnings": 2500.00,
  "tier_discount": 10
}
```

### Список рефералов
```http
GET /api/referrals?status=active
Authorization: Bearer <token>
```

---

## Уведомления (v7.6+)

### Список
```http
GET /api/notifications?page=1&per_page=20&unread_only=true
Authorization: Bearer <token>
```

### Отметить прочитанным
```http
POST /api/notifications/{id}/read
Authorization: Bearer <token>
```

### Отметить все прочитанными
```http
POST /api/notifications/read-all
Authorization: Bearer <token>
```

### Настройки
```http
GET /api/notifications/settings
Authorization: Bearer <token>
```

```http
PUT /api/notifications/settings
Authorization: Bearer <token>
Content-Type: application/json

{
  "email_enabled": true,
  "push_enabled": true,
  "invoice_reminders": true,
  "task_reminders": true
}
```

---

## API Ключи (v7.8+)

### Список
```http
GET /api/api-keys
Authorization: Bearer <token>
```

### Создание
```http
POST /api/api-keys
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Интеграция с CRM",
  "scopes": ["sales:read", "clients:read"],
  "expires_days": 90
}
```

**Ответ:**
```json
{
  "id": 1,
  "name": "Интеграция с CRM",
  "key": "msk_abc123...",
  "scopes": ["sales:read", "clients:read"],
  "created_at": "2026-01-15T10:00:00",
  "expires_at": "2026-04-15T10:00:00"
}
```

**Важно:** ключ показывается только один раз при создании!

### Отзыв
```http
DELETE /api/api-keys/{id}
Authorization: Bearer <token>
```

### Использование
```http
GET /api/sales/products
X-API-Key: msk_abc123...
```

---

## Вебхуки (v7.8+)

### Список подписок
```http
GET /api/webhooks
Authorization: Bearer <token>
```

### Создание подписки
```http
POST /api/webhooks
Authorization: Bearer <token>
Content-Type: application/json

{
  "url": "https://my-crm.ru/webhook",
  "events": ["invoice.paid", "invoice.sent"],
  "secret": "my_webhook_secret",
  "active": true
}
```

### Обновление
```http
PUT /api/webhooks/{id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "events": ["invoice.paid", "invoice.sent", "contract.signed"],
  "active": true
}
```

### Удаление
```http
DELETE /api/webhooks/{id}
Authorization: Bearer <token>
```

### Доставка вебхука
```json
{
  "event": "invoice.paid",
  "timestamp": "2026-01-15T10:30:00+00:00",
  "data": {
    "invoice_id": 1,
    "invoice_number": "СЧ-1-20260115-0001",
    "amount": 50000.00,
    "client_id": 1
  },
  "signature": "sha256=..."
}
```

---

## Экспорт данных (v7.8+)

### Экспорт CSV
```http
GET /api/export/{module}/csv?format=csv
Authorization: Bearer <token>
```

Модули: `invoices`, `products`, `clients`, `deals`, `contracts`, `tasks`, `payments`

### Экспорт Excel
```http
GET /api/export/{module}/excel?format=excel
Authorization: Bearer <token>
```

### Экспорт PDF
```http
GET /api/export/{module}/pdf?format=pdf
Authorization: Bearer <token>
```

---

## Импорт данных (v7.8+)

### Загрузка CSV/Excel
```http
POST /api/import/{module}
Authorization: Bearer <token>
Content-Type: multipart/form-data

file=<CSV или Excel файл>
```

Модули: `clients`, `products`

**Ответ:**
```json
{
  "imported": 25,
  "errors": 2,
  "details": [
    {"row": 3, "error": "Неверный email"},
    {"row": 7, "error": "Дубликат ИНН"}
  ]
}
```

---

## Аналитика

### Общая
```http
GET /api/analytics/overview
Authorization: Bearer <token>
```

### AI-аналитика
```http
POST /api/ai/analytics
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "Какие клиенты приносят больше всего дохода?",
  "period": "last_30_days"
}
```

---

## Админ-панель (v7.5+)

### Статистика платформы
```http
GET /api/admin/stats
Authorization: Bearer <token>
```

### Список пользователей
```http
GET /api/admin/users?search=&tier=&status=&page=1
Authorization: Bearer <token>
```

### Управление пользователем
```http
PUT /api/admin/users/{id}/tier
Authorization: Bearer <token>
Content-Type: application/json

{
  "tier": "business",
  "reason": "Платёж подтверждён"
}
```

```http
POST /api/admin/users/{id}/block
Authorization: Bearer <token>
Content-Type: application/json

{
  "reason": "Нарушение правил",
  "duration_hours": 24
}
```

### Audit логи
```http
GET /api/admin/audit-logs?action=&user_id=&page=1
Authorization: Bearer <token>
```

---

## Подписки

### Тарифы
```http
GET /api/subscriptions/tiers
```

### Текущая подписка
```http
GET /api/subscriptions/me
Authorization: Bearer <token>
```

### Создание платежа
```http
POST /api/subscriptions/create-payment
Authorization: Bearer <token>
Content-Type: application/json

{
  "tier": "business",
  "period": "monthly"
}
```

---

## Поиск (v7.4+)

### Глобальный поиск
```http
GET /api/search?q=ромашка&limit=20
Authorization: Bearer <token>
```

---

## WebRTC (v7.3+)

### Создание комнаты
```http
POST /api/webrtc/rooms
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Встреча с клиентом",
  "max_participants": 4
}
```

---

## Коды ошибок

| Код | Описание |
|-----|----------|
| 400 | Неверный запрос |
| 401 | Не авторизован |
| 403 | Доступ запрещён |
| 404 | Не найдено |
| 409 | Конфликт (дубликат) |
| 422 | Ошибка валидации |
| 423 | Аккаунт заблокирован |
| 429 | Слишком много запросов |
| 500 | Внутренняя ошибка сервера |
| 502 | Ошибка внешнего сервиса |
| 503 | Сервис временно недоступен |

### Формат ошибки
```json
{
  "error": true,
  "status": 400,
  "message": "Описание ошибки",
  "path": "/api/sales/invoices",
  "timestamp": "2026-01-15T10:30:00+00:00"
}
```

---

## Rate Limits

| Endpoint | Лимит |
|----------|-------|
| `/health` | 60/мин |
| `/` | 30/мин |
| `/api/auth/login` | 5/мин |
| `/api/auth/register` | 3/мин |
| `/api/sales/*` | 60/мин |
| `/api/svetlana/chat` | 30/мин (free), 120/мин (pro+) |
| `/api/api-keys/*` | 30/мин |
| `/api/webhooks/*` | 60/мин |
| `/api/export/*` | 10/мин |
| `/api/import/*` | 10/мин |

---

## WebSocket

### Уведомления
```javascript
const ws = new WebSocket('wss://mir-samozanyatykh.ru/ws/notifications');
ws.onmessage = (event) => {
  const notification = JSON.parse(event.data);
  console.log(notification.title, notification.message);
};
```

---

## Безопасность

- Все пароли хешируются bcrypt
- JWT с jti (JSON Token Identifier) для отзыва
- CSRF защита на всех формах
- Rate limiting на всех endpoints
- CSP (Content Security Policy) с nonce
- HSTS, X-Frame-Options, X-Content-Type-Options
- 5 попыток входа → блокировка на 30 мин

---

*АНО ЦПС «Мир Самозанятых» | ИНН 9724016805*
*Версия API: 7.9.0*
