# API Документация — Мир Самозанятых v6.0

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

*АНО ЦПС «Мир Самозанятых» | ИНН 9724016805*
*Версия API: 6.0.0*
