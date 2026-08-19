# Large Functional/Security Pass v8.4.30

## Scope
This pass continued from v8.4.29 and focused on FNS, Bank, Accounting, Referrals, payment error handling and API information leakage.

## Changes actually made
- Bank import row errors no longer expose raw Python exception text.
- Referral application no longer incorrectly rejects a user merely because that user has previously invited someone else.
- Referral reward endpoint is restricted to users with `is_admin` or `is_moderator`; it is not a public self-service reward operation.
- Referral leaderboard now requires authentication and no longer returns user email addresses.
- FNS INN checksum validation no longer claims registry status when the external FNS registry was not actually queried successfully; status is `unknown` in that case.
- FNS receipt money conversion uses Decimal instead of float arithmetic.
- Removed duplicate unreachable receipt-save return.
- YooKassa payment creation no longer returns raw SDK exception text to clients.
- Product/client import errors no longer expose raw internal exception text.
- Admin bulk-operation error responses no longer expose raw exception text.

## Checks actually run
- Python `compileall`: PASS.
- Targeted static assertions for Bank/Referral/FNS changes: PASS.
- Search for raw `detail=str(e)` / error-text leaks in the targeted APIs: rechecked; remaining import/error paths were normalized where identified in this pass.
- Release cleanup performed after compilation.

## Not run / not claimed
- Docker Compose runtime.
- Live PostgreSQL/Redis.
- Alembic against a live database.
- npm/Vite build.
- Flutter/Dart build or tests.
- Browser/Android E2E.
- Live FNS, bank or YooKassa integrations.

Static PASS is not a runtime PASS.
