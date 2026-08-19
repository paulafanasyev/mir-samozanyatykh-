# Mir Samozanyatykh v8.4.13 — Financial Functional Audit

## Changes
- Manual invoice payments require an `Idempotency-Key` and return the original payment on safe retries.
- Invoice rows are locked during payment creation to prevent concurrent overpayment/race conditions.
- Manual payments cannot exceed the invoice total.
- YooKassa webhook processing is idempotent by provider payment ID.
- YooKassa webhook amount is checked against the invoice total before marking paid.
- Invoice row locking prevents concurrent success webhook races.
- Referral reward processing locks the referral and referrer rows to prevent duplicate reward crediting.
- Bank transaction identity is protected by a `(user_id, bank_transaction_id)` unique constraint.
- Added Alembic migration `v849_financial_idempotency`.

## Verification
- Python compileall: PASS
- Duplicate route scan: PASS
- ZIP integrity: PASS
- Release artifact cleanup: PASS

## Runtime gates not claimed here
Full PostgreSQL integration tests, provider sandbox tests, Flutter build, and npm build require their external runtimes/dependencies and are not represented as passed by this audit.
