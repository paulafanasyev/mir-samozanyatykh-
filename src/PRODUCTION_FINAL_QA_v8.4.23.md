# Production Final QA v8.4.23

- Backend password schemas: minimum 12 characters.
- Production Compose: app has no published port; PostgreSQL/Redis have no published ports.
- Production Compose passes DOMAIN/FRONTEND_URL into the app and requires production secrets.
- Nginx frontend proxies `/api/` to the actual `app` service, not a nonexistent `backend` service.
- Prometheus/Grafana image tags are pinned rather than `latest`.
- Production startup runs `tools/production_preflight.py` before Alembic.
- BANK_ENCRYPTION_KEY must decode to exactly 32 bytes.
- DEBUG must be false.
- Placeholder/weak DB and Redis passwords are rejected.
