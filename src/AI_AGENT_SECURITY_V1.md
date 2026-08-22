# AI Agent Security v1

## Implemented
- Security gateway between Svetlana/clients and online model providers.
- Provider routing through `AI_ROUTES`; secrets remain environment variables.
- Offline fallback when no online provider is available.
- Input size limits and baseline prompt-injection detection.
- Deterministic document precheck before optional AI analysis.
- Rate limits on AI endpoints.
- Regression tests for the security boundary.

## Architecture
`user -> Svetlana -> /api/ai -> security gateway -> provider router -> model`

The model never receives unrestricted application credentials. Future tools must be explicit allowlisted operations with per-user authorization and audit events.

## Environment
Example:
`AI_ROUTES=openrouter|OPENROUTER_API_KEY|https://openrouter.ai/api/v1|<model>,bai|BAI_API_KEY|<openai-compatible-base>|<model>`

Do not commit real keys.

## Required production controls
1. Tool allowlist and RBAC for agent actions.
2. Human confirmation for irreversible operations.
3. Redacted audit trail for tool calls and provider failures.
4. E2E tests for authentication, documents, marketplace and Svetlana.
5. OWASP GenAI/LLM and AI Testing Guide regression suite.
6. Local model integration for offline mode where hardware permits.
7. Provider health/circuit-breaker metrics and automatic fallback.

This follows the current OWASP GenAI security/testing direction; the current OWASP LLM Top 10 release is 2026 and the AI Testing Guide defines repeatable tests across application, model, infrastructure and data layers.
