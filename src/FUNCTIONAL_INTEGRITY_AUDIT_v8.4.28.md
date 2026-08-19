# Functional Integrity Audit v8.4.28

This release adds a large cross-resource integrity pass across Web/Mobile-facing CRM and finance APIs.

## Fixed

- Deal create/update now validates client and pipeline-stage ownership.
- CRM calls reject clients belonging to another account.
- CRM tasks validate client/deal ownership and require a task client to match its deal client.
- The dedicated Tasks API applies the same client/deal consistency rule on create/update.
- Completing an already-completed task no longer awards points again.
- Invoice numbers no longer rely on a `count()+1` race-prone sequence; a UUID segment is used before the database UNIQUE constraint.
- YooKassa webhook locks the invoice row before applying a payment state transition.
- YooKassa webhook verifies that an existing invoice payment ID matches the webhook payment ID.
- A late cancellation webhook cannot move an already-paid invoice back to cancelled.

## Verified

- Security regression: 13/13 PASS
- API contract: PASS (233 backend routes, 59 frontend literal paths)
- Functional contract audit: PASS
- Alembic release gate: PASS (5 migrations, 1 head)
- Python compilation: PASS
- Release artifact cleanup: PASS

## Runtime limitations

A real PostgreSQL/Redis/Docker runtime, npm registry, and Flutter SDK are not available in this environment. Therefore live container startup, PostgreSQL migration execution, Vite production build, and Flutter APK compilation are not represented as completed runtime tests.
