# Multi-agent runtime configuration

The engineering loop is now wired into the FastAPI application at `/api/agents`.

## Provider configuration

Configure at least one explicit provider/model pair:

- `OPENROUTER_API_KEY` + `AGENT_OPENROUTER_MODEL`
- `OPENAI_API_KEY` + `AGENT_OPENAI_MODEL`
- `AGENT_OLLAMA_BASE_URL` + `AGENT_OLLAMA_MODEL`

Providers are attempted in configuration order and eligible connection/timeout
failures fall through to the next provider. Credentials are read only from the
server environment.

## Verification

Set `AGENT_RUNTIME_BASE_URL` to a deployed/test instance. The runtime agent
performs a live `GET /health` and requires HTTP 200 plus `{"status":"healthy"}`.
Model output is never accepted as runtime proof.

`/api/agents/run` is restricted to admin/moderator users. The final judge
requires static security evidence, passing regression tests, and live runtime
evidence before returning `passed=true`.
