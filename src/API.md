# API Documentation — Мир Самозанятых v8.6.1

## Базовый URL

```
Production:  https://api.mir-samozanyatykh.ru
Development: https://dev.mir-samozanyatykh.ru
```

## Аутентификация

Все endpoints требуют Bearer токен (кроме `/api/auth/*`):

```http
Authorization: Bearer <access_token>
```

Получить токен:
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

email=user%40example.com&password=secure_password
```

## Endpoints

### Auth
| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/api/auth/login` | Вход |
| POST | `/api/auth/register` | Регистрация |
| POST | `/api/auth/refresh` | Обновление токена |
| POST | `/api/auth/logout` | Выход |
| POST | `/api/auth/biometric` | Biometric auth |

### Users
| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/users/me` | Текущий пользователь |
| PUT | `/api/users/me` | Обновить профиль |
| POST | `/api/users/verify` | Верификация |

### CRM
| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/crm/clients` | Список клиентов |
| POST | `/api/crm/clients` | Создать клиента |
| GET | `/api/crm/clients/{id}` | Клиент по ID |
| PUT | `/api/crm/clients/{id}` | Обновить клиента |
| DELETE | `/api/crm/clients/{id}` | Удалить клиента |
| GET | `/api/crm/deals` | Список сделок |
| POST | `/api/crm/deals` | Создать сделку |
| PATCH | `/api/crm/deals/{id}/move` | Переместить стадию |

### Sales
| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/sales/invoices` | Список счетов |
| POST | `/api/sales/invoices` | Создать счёт |
| GET | `/api/sales/invoices/{id}` | Счёт по ID |
| GET | `/api/sales/invoices/{id}/pdf` | PDF счёта |

### Accounting
| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/accounting/transactions` | Транзакции |
| POST | `/api/accounting/transactions` | Создать транзакцию |
| GET | `/api/accounting/tax-reports` | Налоговые отчёты |
| GET | `/api/accounting/deductions` | Вычеты |

### Svetlana (AI)
| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/svetlana/status` | Статус локального runtime |
| POST | `/api/svetlana/chat` | Отправить сообщение в локальный runtime |
| GET | `/api/svetlana/history` | История чата |

### Notifications
| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/notifications` | Уведомления |
| PUT | `/api/notifications/{id}/read` | Прочитать |
| PUT | `/api/notifications/read-all` | Прочитать все |
| GET | `/api/notifications/unread-count` | Непрочитанные |

### Bank
| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/bank/connections` | Подключения |
| POST | `/api/bank/connect` | Подключить банк |
| GET | `/api/bank/transactions` | Банковские транзакции |

### FNS
| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/api/fns/receipt-check` | Проверить чек |

### Admin
| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/admin/stats` | Статистика |
| GET | `/api/admin/users` | Пользователи |
| GET | `/api/admin/audit-logs` | Аудит-логи |

### Health
| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/health` | Healthcheck |
| GET | `/api/health/ready` | Readiness probe |
| GET | `/api/health/live` | Liveness probe |
| GET | `/api/health/metrics` | Системные метрики |

## Коды ответов

| Код | Описание |
|-----|----------|
| 200 | OK |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

## Rate Limiting

- **Auth**: 5 запросов/минуту
- **API**: 100 запросов/минуту
- **Svetlana**: 30 запросов/минуту

## Webhooks

Подписка на события:
```http
POST /api/webhooks
Content-Type: application/json

{
  "url": "https://your-app.com/webhook",
  "events": ["invoice.paid", "deal.won"],
  "secret": "your_secret"
}
```

## SDK

- **Python**: `pip install mir-samozanyatykh`
- **JavaScript**: `npm install @mirsamozanyatykh/sdk`
- **Dart/Flutter**: `flutter pub add mir_samozanyatykh`
