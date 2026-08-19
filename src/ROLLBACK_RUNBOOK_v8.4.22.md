# Production rollback runbook

1. **Do not run `alembic downgrade` as the normal application rollback mechanism.** Application rollback must use the previous container/image against a schema that remains backward compatible.
2. Before every production migration, create and checksum a PostgreSQL custom-format backup.
3. Deploy the new application and run `alembic upgrade head` once.
4. Verify readiness and smoke tests.
5. If application code fails but schema is compatible, redeploy the previous image without downgrading the database.
6. If data/schema corruption occurred, stop writes, restore the last known-good database backup into an isolated database, verify it, then switch the application to the restored database. This is a recovery procedure, not an in-place downgrade.
7. Never restore a backup over the live database until its checksum and `pg_restore --list` have been verified.
8. Keep at least 14 backup sets and retain one known-good pre-release backup outside the application host.
9. Migrations in this release have defensive downgrades for local/test rollback, but production rollback is backup/redeploy-first.
