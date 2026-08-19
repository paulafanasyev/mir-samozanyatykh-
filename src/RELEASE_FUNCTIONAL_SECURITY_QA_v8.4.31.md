# Mir Samozanykh v8.4.31 — Functional/Security QA

## Implemented in this pass

- Mobile Svetlana screen now calls the real `/api/svetlana/chat` API; fabricated client-side responses were removed.
- Mobile Analytics now loads `/api/analytics/dashboard` and `/api/analytics/revenue-chart`; hardcoded chart/stat values were removed.
- Mobile Integrations now loads API keys and webhooks and supports API-key creation/revocation through the authenticated API client.
- Bank provider error responses no longer expose raw provider HTTP status details.
- Legacy public HTML profile no longer exposes fabricated demo email/financial/account statistics.
- Revenue and client report endpoints now emit actual PDF bytes using ReportLab instead of returning HTML with a `.html` filename from endpoints named `/pdf`.
- Bundled DejaVu Sans font is used for Cyrillic PDF text.
- Release gate includes a dedicated v8.4.31 functional-integrity audit.

## Verified locally/static in this environment

- Python compileall: PASS
- Security regression: 13/13 PASS
- API contract: PASS (233 registered/audited backend routes; 73 frontend literal paths; no missing/phantom paths)
- Existing functional integrity audit: 13/13 PASS
- v8.4.31 functional integrity audit: 13/13 PASS
- Release gate: PASS
- ReportLab PDF smoke generation: PASS

## Not claimed as runtime-tested

The current environment does not provide a full production runtime/SDK stack. The following are NOT claimed as passed here:

- Docker Compose startup
- live PostgreSQL/Redis
- live Alembic migrations against PostgreSQL
- backup/restore drill
- npm/Vite build
- Flutter analyze/test/build/APK
- browser E2E
- Android E2E
- live FNS/bank/YooKassa integrations

Static PASS must not be interpreted as production runtime PASS.
