# Mir Samozanyatykh v8.4.35 — large business integrity pass

## Implemented
- FNS receipt verification now distinguishes "not found" from provider/network failure and returns 502/503 on service errors.
- FNS receipt item totals accumulate using Decimal rather than float.
- Manual bank transaction import validates positive amount, RUB-compatible 3-letter currency shape, bounded description, and DEBIT/CREDIT operation type.
- Tax deduction creation rejects non-positive max_amount and amounts exceeding max_amount.
- Admin bulk notifications have a 5,000-recipient hard cap.
- In-app notifications are committed before email side effects, preventing a DB rollback from making already-sent email notifications inconsistent with stored state.
- Email failures are logged and counted without rolling back stored in-app notifications.
- Versions synchronized to 8.4.35.
- Regression audit added.

## Actually executed
- Python compileall: PASS (then transient __pycache__ artifacts were removed from release).
- v8.4.35 integrity audit: 9/9 PASS.
- API contract audit: PASS — BACKEND_ROUTES=233, FRONTEND_LITERAL_PATHS=73.
- Updated previous functional integrity audit: 10/10 PASS.
- Security regression: 13/13 PASS after cleanup.
- Release artifact cleanup: PASS — no .pyc/.pyo/__pycache__/test.db/log artifacts included.

## Not executed / not claimed
The current environment does not provide the runtime needed to honestly claim:
- Docker Compose startup;
- live PostgreSQL/Redis;
- Alembic against a live PostgreSQL;
- npm/Vite build;
- Flutter analyze/test/build/APK;
- browser/Android E2E;
- real FNS, bank or YooKassa integrations.

The release therefore contains static/regression QA results, not a claim of production runtime validation.
