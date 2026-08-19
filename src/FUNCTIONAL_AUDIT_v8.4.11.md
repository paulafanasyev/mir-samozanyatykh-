# Functional Audit v8.4.11

- Web auth uses form-encoded login/register compatible with FastAPI Form endpoints.
- Native mobile auth identifies itself with `X-Client-Type: mobile`.
- Mobile login receives a refresh token in the response and stores it in secure storage.
- Mobile refresh submits the refresh token in the request body and receives a rotated refresh token.
- Browser refresh continues to use HttpOnly cookie + CSRF double-submit protection.
- 2FA pending tokens use a dedicated JWT type and cannot authenticate API requests.
- Mobile 2FA login endpoint is wired through ApiClient and AuthRepository.
- Mobile registration no longer pretends that a registration response is an authenticated session when email verification is required.
- Version identifiers synchronized to 8.4.11.

Environment limitation: Flutter SDK and npm registry access are not available in this execution environment, so `flutter analyze/build` and a fresh npm lockfile generation are not claimed as executed.
