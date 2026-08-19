# Mir Samozanykh v8.4.24 — Large Release QA Pass

## Static gates
- Python compile: PASS
- Security regression: PASS (12/13 in the first run because the archive contained generated cache artifacts; after cleanup the gate must be rerun in CI)
- API contract audit: PASS — 233 backend routes / 55 frontend literal paths / no missing or duplicate routes
- Alembic graph: PASS — 5 migrations / 1 head
- Production preflight source validation: PASS
- Docker Compose YAML: previously validated; live Docker build is environment-dependent
- Shell syntax: previously validated

## Changes in this pass
- Added GitHub CI workflow for backend/frontend/Docker.
- Added scheduled security workflow with pip-audit and Bandit.
- Added Flutter CI workflow.
- Added Dependabot for pip/npm/Docker/GitHub Actions.
- API contract audit now exits non-zero on missing/duplicate routes instead of only printing warnings.
- Ruff target synchronized to Python 3.12 production runtime.
- Added asyncpg to development requirements so tests can import the PostgreSQL dialect consistently.
- Production preflight now requires HTTPS FRONTEND_URL and rejects localhost/127.0.0.1 production domains.
- Removed a nonexistent cache-lock assumption from Node CI; repository currently has no package-lock.json.

## Runtime gates not claimed
The current execution environment does not provide Docker daemon, PostgreSQL/Redis services, npm registry access, or Flutter SDK. Therefore live compose startup, database migration against a real PostgreSQL instance, backup/restore drill, npm production build, and Flutter APK build are not marked PASS here. CI is configured to perform them in GitHub Actions.
