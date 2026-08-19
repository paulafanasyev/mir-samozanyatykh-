# Runtime / Functional QA v8.4.29

## Actually executed
- Python compileall: PASS
- Security regression: 13/13 PASS
- API contract audit: PASS — 234 backend route declarations, 73 frontend literal paths, 0 missing literal API paths, 0 duplicate backend routes
- Functional integrity v8.4.28: 13/13 PASS
- Functional integrity v8.4.29: 12/12 PASS
- Alembic release gate: PASS — 5 migrations, single head v851_fns_document_integrity
- Release artifacts cleaned: PASS

## Fixed in this release
- Normalized Web API paths so calls without `/api` are routed to the actual API namespace.
- Fixed Calendar Web API namespace calls.
- Fixed Webhook create contract: JSON body with `events`, matching the `Webhook.events` model field.
- Fixed Webhook listing to expose fields expected by the Web UI.
- Added owner-scoped Webhook delivery history endpoint.
- Webhook test deliveries are persisted with status/duration metadata.
- Fixed Integrations Webhook test response handling.
- Added bounds to analytics month queries.
- Fixed analytics month arithmetic to use calendar months rather than 30-day approximations.
- Fixed UI navigation that incorrectly used `/api/admin` as a frontend route.

## Not claimed as runtime-tested
- Docker Compose startup
- Live PostgreSQL/Redis
- Alembic against a live database
- npm/Vite build
- Flutter analyze/test/APK build
- Browser E2E
- Android E2E
- External FNS/YooKassa/Bank live integrations

These require the corresponding runtime/SDK/network environment and were not marked PASS here.
