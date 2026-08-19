# Functional audit v8.4.10

- Fixed web login/register to submit `application/x-www-form-urlencoded`, matching FastAPI `Form(...)` endpoints.
- Added web 2FA login UI and submission flow for `/api/auth/login/2fa`.
- Password minimum in React registration and legacy registration template synchronized to 12 characters.
- Backend Python compilation: PASS.
- Frontend TypeScript syntax: Login.tsx no longer has JSX parse errors; full typecheck requires installed npm dependencies.
- Runtime integration/build remains a gate requiring installed npm/Flutter dependencies and PostgreSQL/Redis.
