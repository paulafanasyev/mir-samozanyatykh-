# Мир Самозанятых v8.4.3 — Security & Production Hardening

Дата: 16 августа 2026

## Выполнено

1. Access JWT больше не сохраняется в localStorage/Zustand persist; legacy HTML pages используют memory-only auth bridge.
2. Refresh token хранится только в HttpOnly/Secure/SameSite cookie и ротируется при refresh.
3. Refresh session блокируется на уровне строки БД (`FOR UPDATE`) для защиты от concurrent refresh race.
4. 2FA-pending JWT не может использоваться как обычный access token.
5. Email verification token хранится только как SHA-256 hash и имеет TTL 30 минут.
6. Password reset token хранится только как SHA-256 hash и имеет TTL 15 минут; после reset все сессии отзываются.
7. Password reset повторно проверяет password policy.
8. Банковские токены шифруются AES-256-GCM отдельным `BANK_ENCRYPTION_KEY`; Base64 больше не используется как шифрование.
9. Production startup валидирует `BANK_ENCRYPTION_KEY` как 32-byte URL-safe base64 key.
10. CSP больше не содержит `unsafe-inline` в nginx; HTML получает динамический nonce от application middleware. Inline script/style tags получили nonce.
11. `X-XSS-Protection` удалён.
12. Webhook secrets генерируются криптографически случайно, хранятся зашифрованными и выдаются автоматически сгенерированный secret только один раз.
13. Webhook delivery использует HMAC-SHA256, timestamp и запрет redirects; ownership проверяется.
14. SSRF validation блокирует private/link-local/metadata/non-global адреса, URL credentials и опасные numeric encodings.
15. 2FA backup codes хранятся как bcrypt hashes и удаляются после использования.
16. Dashboard accounting statistics больше не возвращают фиктивные нулевые `pending_invoices`/`transactions_count`.
17. Production Dockerfile теперь действительно собирается, содержит `requirements.txt`, `startup.sh`, migrations и работает non-root.
18. Production compose больше не требует отсутствующих `init.sql`, `seed.py`/`startup.sh` — они присутствуют; отсутствующие Celery services удалены до появления реального scheduler implementation.
19. PostgreSQL/Redis/Prometheus/Grafana наружу не публикуются на всех интерфейсах; Redis защищён паролем.
20. Frontend source files с повреждённым whitespace/import formatting восстановлены до синтаксически корректного TypeScript/TSX.
21. Release artifacts (`.git`, `.pyc`, `__pycache__`, logs, test DB, stale audit reports) удаляются из production archive.

## Проверки

- Standalone security regression checker: **13/13 PASS**.
- Python `compileall` для `app`, `tests`, `tools`: **PASS**.
- Jinja template parsing: **PASS**.
- Docker Compose YAML parsing: **PASS**.
- Frontend TypeScript syntax после восстановления: parser больше не выдаёт syntax errors; полный `tsc`/Vite build не завершён, потому что `node_modules` отсутствуют.
- Full pytest: не завершён, потому что runtime среды не содержит `asyncpg` и внешний package index недоступен.

## Production gates

Перед production необходимо выполнить в CI/на сервере:

1. `pip install -r requirements.txt`.
2. `pip install -r requirements-dev.txt`.
3. `pytest tests/ -v`.
4. `npm ci && npm run build` в `frontend/`.
5. `alembic upgrade head` на тестовой PostgreSQL.
6. Реальный двухпользовательский IDOR/RBAC integration test.
7. Dependency audit после установки зависимостей.
8. Secret scan Git history.
9. Проверка реальных TLS certificates перед запуском nginx.
10. Установка production `SECRET_KEY`, `BANK_ENCRYPTION_KEY`, `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `GRAFANA_PASSWORD`.

**Статус:** security hardening существенно завершён; полное production sign-off ожидает выполнения внешних integration/build tests в окружении с доступными зависимостями и PostgreSQL/Redis.
