# Security Report — МИР Самозанятых v8.7.0

## Проверки
- [x] JWT authentication
- [x] Password hashing (PBKDF2-SHA256)
- [x] Rate limiting
- [x] Input validation (email, phone, INN)
- [x] CSRF protection
- [x] Audit logging
- [x] Role-based access control (RBAC)

## Рекомендации
- Перейти на PostgreSQL в production
- Настроить HTTPS через Traefik
- Добавить 2FA для админов
- Настроить бэкапы БД
