# Mir Samozanykh v8.4.21 — Production Release Candidate Audit

## Исправлено

- Production startup больше не вызывает `SQLAlchemy create_all`; схема production управляется Alembic.
- Исправлен baseline migration `render_v84`: на чистой PostgreSQL он создаёт полный текущий SQLAlchemy schema.
- Incremental migrations v849/v850/v851 сделаны идемпотентными относительно baseline: существующие columns/indexes/constraints не создаются повторно.
- Исправлена production-конфигурация `BANK_ENCRYPTION_KEY`: пример и CI теперь используют корректный URL-safe base64 ключ, декодирующийся ровно в 32 байта.
- Сохранён development/test `create_all` для локальных сценариев.

## Проверено

- Security regression: 13/13 PASS.
- API contract audit: 233 backend routes / 55 frontend literal API paths; phantom/missing paths: 0.
- Deterministic release gate: PASS.
- Shell syntax: PASS.
- Python compilation: PASS.
- Production artifacts cleanup: PASS.

## Что ещё требует внешнего runtime

В текущей среде отсутствуют Docker daemon и внешний package registry, поэтому не выдаются за PASS реальные `docker compose up`, PostgreSQL migration against a live server, backup/restore drill, npm build и Flutter APK build. Эти проверки выполняются GitHub Actions/production staging.
