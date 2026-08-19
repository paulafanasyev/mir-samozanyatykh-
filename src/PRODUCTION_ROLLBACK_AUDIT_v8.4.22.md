# Production Rollback / Migration Safety Audit — v8.4.22

## Result

- Alembic revisions: **5**
- Single head: `v851_fns_document_integrity`
- Migration graph: **connected, no cycles**
- Production `create_all`: **baseline only**
- Destructive upgrade operations: **only the intentional v8.4 security invalidation**
- Baseline downgrade: **disabled**
- Security cleanup downgrade: **disabled**
- Pre-deploy DB backup: **enabled when an existing Alembic database is detected**
- Deployment readiness probe: **runs inside the app container**

## Rollback policy

Application rollback is **redeploy-first**, not `alembic downgrade`.

If the new application is incompatible with the upgraded schema, the previous application image may be restored only when its code remains compatible with the current schema. If the database itself must be recovered, restore a verified PostgreSQL backup into an isolated database first, validate it, and then switch traffic.

The security migration deliberately cannot be downgraded because doing so would recreate the legacy plaintext token schema. The baseline migration cannot be downgraded because that would drop the complete application schema.

## Pre-release sequence

1. Verify secrets.
2. Start PostgreSQL and Redis.
3. If an existing Alembic database is detected, create a custom-format backup and SHA-256 checksum.
4. Build and start the application.
5. Run `alembic upgrade head`.
6. Verify readiness from inside the application container.
7. Run smoke/regression tests.
8. Keep the pre-release backup outside the application host for disaster recovery.
