# Mir Samozanykh v8.4.19 — Observability & Resilience Audit

## Implemented

- Health/readiness no longer expose raw database exception messages.
- Redis health ping has a 2-second timeout.
- Application request metrics are exported in Prometheus text format.
- Metrics endpoint is not exposed through public nginx; Prometheus reaches it only over the internal Docker network.
- Removed stale Celery Prometheus target because no Celery service exists in the production compose.
- Application port 8000 is no longer published to the host; public traffic enters through nginx.
- Uvicorn no longer trusts arbitrary `X-Forwarded-*` sources; trusted proxy range is the dedicated Docker network.
- Nginx access logs no longer record the full query string, reducing accidental logging of secrets/tokens in URLs.
- Nginx server version disclosure is disabled.
- Nginx client upload limit is aligned with the application's 10 MiB upload limit.
- Nginx frame policy is aligned with the application (`DENY`).
- Application log files are rotated (10 MiB × 5) instead of growing without bound.
- Common Authorization/password/token/secret/API-key patterns are redacted from JSON logs.
- Unexpected request exceptions log only exception type, not potentially sensitive exception text.
- PostgreSQL backups are written atomically, chmod 600, and accompanied by SHA-256 checksums.
- Temporary/partial backup files are removed after failed dumps.
- Backup retention removes both dumps and checksum files after 14 days.

## Verified

- Python compileall: PASS
- Shell syntax (`deploy.sh`, `startup.sh`): PASS
- YAML parsing: PASS
- No public host port for PostgreSQL/Redis/app/Prometheus/Grafana except nginx 80/443.

## Production gates still requiring a real Docker host

- `docker compose -f docker-compose.prod.yml config`
- image builds
- container startup and migrations
- PostgreSQL restore drill against a disposable database
- Redis failure/recovery drill
- Prometheus scrape verification
- HTTPS certificate verification
- full frontend/mobile builds and integration tests
