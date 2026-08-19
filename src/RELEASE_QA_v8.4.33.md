# Mir Samozanyatykh v8.4.33 — large functional/security pass

Date: 2026-08-17

## Changes
- Task create/update now enforce client/deal ownership consistency.
- FNS self-employed status no longer claims `active`/`true` without confirmed FNS integration; status is `unknown`.
- Corrected an erroneous tax recommendation threshold from 200,000 to 2,000,000 RUB and made the wording explicit about the 2.4M annual limit.
- Tinkoff bank connection is reported as `not_configured` unless the API token is actually configured.
- Version synchronized to 8.4.33 / mobile 8.4.33+858.
- Added v8.4.33 functional regression audit based on v8.4.32 persistence checks.

## Checks actually executed
- Python `compileall`: PASS.
- v8.4.33 functional integrity audit: 16/16 PASS.
- v8.4.32 functional integrity regression: 15/16 PASS because its audit still contained the old version expectation; the code was not changed to satisfy a stale audit. The updated v8.4.33 audit is the authoritative version check and passes 16/16.
- Security regression: 13/13 PASS after release-artifact cleanup.
- API contract: PASS — 233 backend routes, 73 frontend literal paths, no missing/phantom paths.
- ZIP integrity: verified after packaging.

## Not executed in this environment
- Docker Compose runtime.
- Live PostgreSQL/Redis.
- Alembic against a live PostgreSQL database.
- npm/Vite build.
- Flutter analyze/test/build/APK.
- Browser/Android E2E.
- Live FNS/bank/YooKassa integrations.

Those are explicitly not claimed as passed.
