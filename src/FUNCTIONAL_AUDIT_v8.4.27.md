# Functional Contract Audit v8.4.27

## Scope
Large Web + Mobile + API contract pass focused on screens whose UI payloads previously diverged from backend schemas.

## Fixed

1. Web invoices now send the actual `InvoiceCreate` contract: `client_id`, `due_date`, `notes`, and at least one `items[]` entry with `description`, `quantity`, and `unit_price`.
2. Web invoice list now unwraps the backend paginated `{invoices, pagination}` response instead of treating the whole object as an array.
3. Web invoice PDF actions now call the authenticated PDF endpoint and create a blob URL; they no longer open the JSON invoice endpoint.
4. Web deal creation now selects a real user-owned client instead of asking the user to type an arbitrary client ID.
5. CRM deal money fields now use `Decimal` instead of `float`, matching PostgreSQL `Numeric(15,2)`.
6. Mobile invoice creation now requires a real client and a valid invoice item.
7. Mobile deal creation now requires a real client.
8. Mobile deal stage movement now matches backend `stage_id` query parameter instead of sending an unsupported JSON `stage` field.
9. Mobile tax reports now correctly normalise the backend list response and derive summary totals from report records.
10. Mobile detail screens no longer create raw Dio clients. They use the shared `ApiClient`, so authentication refresh/rotation is available consistently.
11. Mobile bank and receipt-check flows also use the shared API client instead of bypassing refresh/auth handling.
12. Mobile API refresh was changed from a boolean lock to a shared Future so concurrent 401 responses wait for the same refresh operation instead of failing while another request is refreshing.
13. Mobile refresh requests are explicitly excluded from the 401 retry path to avoid recursive refresh loops.
14. Removed unused direct Dio imports from presentation screens.
15. Version synchronized to `8.4.27` (mobile build `+852`).

## Static verification

- Functional contract audit: PASS
- Python compileall: PASS
- No raw Dio imports remain in mobile presentation screens: PASS
- Web invoice list contract: PASS
- Web invoice creation contract: PASS
- Mobile invoice creation contract: PASS
- Mobile deal creation contract: PASS
- Mobile deal move contract: PASS
- Mobile tax report response normalization: PASS
- Release version consistency: PASS

## Runtime limitations

The current environment does not contain `aiosqlite`, npm dependencies/node_modules, Flutter SDK, or a Docker daemon. Therefore pytest, Vite production build, Flutter analysis/build, and live PostgreSQL/Redis/Docker scenarios are not represented as passed here.

The existing CI workflows remain responsible for those runtime checks in an environment with the required SDKs/services.
