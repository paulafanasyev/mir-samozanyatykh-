# Mir Samozanykh v8.4.25 — Large Runtime/Release QA

Date: 2026-08-16

## Completed in this pass

- Re-audited the v8.4.24 release archive.
- Re-ran security regression: 13/13 PASS.
- Re-ran API contract audit: 233 backend routes / 55 frontend literal paths / 0 missing or phantom paths.
- Re-ran release gate: PASS.
- Recompiled all Python application, test and tooling modules: PASS.
- Validated all three Compose YAML files: PASS.
- Validated startup shell syntax: PASS.
- Removed sensitive mobile logging of FCM tokens and deep-link identifiers.
- Fixed production startup configuration: `POSTGRES_PASSWORD` is now passed to the app container because production preflight requires it.
- Added frontend container healthcheck and made nginx wait for both app and frontend health.
- Restricted production TrustedHostMiddleware to configured production host(s); localhost is now development-only.
- Hardened production DOMAIN validation.
- Synced project version to 8.4.25.
- Kept production schema management on Alembic; no new create_all usage was introduced.

## Runtime gates not falsely marked PASS

The current execution environment has no Docker daemon, Flutter SDK, npm registry access, `asyncpg`, or `aiosqlite` installed. Therefore the following require CI/real runtime execution:

- Docker compose build/up.
- PostgreSQL migration against a real PostgreSQL instance.
- PostgreSQL backup/restore drill.
- Redis failure/recovery drill.
- npm install/build/lint.
- Flutter analyze/test/build.
- Full HTTP end-to-end tests against live services.

A failed local `pytest` invocation was caused by missing `asyncpg`/`aiosqlite` in this execution environment, not by a test assertion failure. The test configuration was corrected so the SQLite test URL is selected before importing the application database module.
