# Mir Samozanyatykh v8.4.34 — large security/business-integrity pass

## Implemented
- Authenticated CSV import preview with bounded `max_rows`.
- Product CSV prices parsed as Decimal and negative prices rejected.
- Referral application serializes the referred user row and handles uniqueness races with HTTP 409.
- Referral reward operation locks the referral row and credits the actual referral owner, not the admin actor.
- Version synchronized to 8.4.34 / mobile 8.4.34+859.
- Release gate updated to use the v8.4.34 integrity audit.

## Verified in this environment
- Security regression: 13/13 PASS.
- API contract: PASS; backend registered/audited routes 233, frontend literal paths 73, missing/phantom 0.
- Functional contract audit: PASS.
- Existing functional integrity v8.4.28: 13/13 PASS.
- New v8.4.34 integrity audit: 10/10 PASS.
- Python compilation: PASS.
- Release gate: PASS.
- Release artifact cleanup: PASS.

## Not claimed as runtime-tested
- Docker Compose startup.
- Live PostgreSQL/Redis.
- Alembic against a live PostgreSQL instance.
- npm/Vite build.
- Flutter analyze/test/build/APK.
- Browser/Android E2E.
- Real FNS/bank/YooKassa integrations.

These require external runtime/SDKs/services unavailable in the current environment.
