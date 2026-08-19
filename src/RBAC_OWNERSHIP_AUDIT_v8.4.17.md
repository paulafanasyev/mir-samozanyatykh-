# RBAC / Ownership Audit v8.4.17

- Calendar create validates client/deal/task ownership.
- Calendar CRUD is scoped by current user.
- Notifications and push subscriptions are scoped by current user.
- Search is scoped by current user.
- API keys are scoped by current user.
- Sales invoice CRUD is scoped by current user.
- Invoice -> client lookup is now owner-scoped.
- YooKassa duplicate payment lookup is bound to the target invoice.
- WhatsApp inbound webhook now requires HMAC-SHA256 (`WHATSAPP_APP_SECRET`) before processing.
- WhatsApp inbound client matching refuses ambiguous cross-tenant phone matches.
- Admin endpoints remain protected by explicit admin/moderator dependencies.

Production gate: external integration tests with two separate users should still be run against PostgreSQL/Redis before sign-off.
