# Release Final Checklist v8.4.23

## Security
- Production DB and Redis have no host port mappings.
- Application has no host port mapping; ingress is nginx only.
- Production secrets are mandatory and preflight rejects placeholders/weak values.
- Password schemas require 12+ characters.
- BANK_ENCRYPTION_KEY must decode to 32 bytes.
- DEBUG must be false.
- HSTS is enabled on HTTPS ingress.
- Prometheus/Grafana image tags are pinned.

## Runtime
- Production has separate `app` and `frontend` services.
- Public nginx routes `/api/*` to backend and `/` to React SPA.
- Frontend production API defaults to same-origin `/api`.
- Startup runs production preflight before Alembic.

## Verification limits
- Docker runtime/build and live PostgreSQL/Redis integration require a Docker-enabled environment.
- npm lockfile generation requires registry access.
