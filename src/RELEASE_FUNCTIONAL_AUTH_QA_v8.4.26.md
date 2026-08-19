# Mir Samozanyatykh v8.4.26 — Large Functional/Auth QA

## Fixed in this pass

- Web login now hydrates `/api/users/me` because `TokenResponse` intentionally contains no `user` object.
- Web 2FA login now also hydrates the current user.
- Web authentication is bootstrapped from the HttpOnly refresh cookie on page reload.
- Protected Web routes are guarded; admin routes require admin/moderator role.
- Public login/register pages are no longer wrapped in the authenticated application layout.
- Web logout now calls the server logout endpoint before clearing local in-memory state.
- Mobile refresh request now sends JSON, matching the backend mobile refresh parser.
- Mobile registration now sends `full_name` instead of the unsupported `name` field.
- Mobile registration no longer treats a successful registration as an authenticated session; email verification is required first.
- Mobile registration referral code is now accepted by the backend form and still supports the legacy `?ref=` query parameter.
- Added Web email-verification page at `/verify-email`.
- Added Web password-reset request/confirmation page at `/reset-password`.
- Corrected password-reset email text from 1 hour to the actual 15-minute backend TTL.
- Production TrustedHost no longer accepts localhost/127.0.0.1; those hosts are development-only.
- Request logging no longer records exception bodies or query strings; request IDs are UUIDs.

## Static gates

- Python compilation: PASS
- Auth flow contract checks: PASS
- Production trusted-host policy: PASS
- Mobile refresh payload contract: PASS
- Mobile registration payload contract: PASS
- Web protected-route wiring: PASS
- Web verification/reset route presence: PASS

## Runtime limitation

The current environment does not provide npm dependencies, Flutter SDK, Docker daemon, PostgreSQL or Redis runtime. Therefore a real Vite build, Flutter build, Docker startup and live database integration test are not claimed as executed here.
