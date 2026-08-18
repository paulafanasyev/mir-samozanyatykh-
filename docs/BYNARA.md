# Bynara provider

Bynara is supported as an OpenAI-compatible provider in the Agent Provider Router.

Set these variables in the deployment environment (never commit the API key):

```env
AGENT_BYNARA_API_KEY=<secret>
AGENT_BYNARA_MODEL=agnes-2.0-flash
AGENT_BYNARA_BASE_URL=https://router.bynara.id/v1
AGENT_PROVIDER_ORDER=bynara,openrouter,openai,ollama
AGENT_PROVIDER_TIMEOUT=30
```

The adapter sends `POST /chat/completions` and normalizes `choices[0].message.content` into the internal `ProviderResponse` contract. Credentials are read only from environment variables and are not passed through agent task context.

If the Bynara request fails with a retryable provider/network error, the existing provider router may fall back to the next enabled provider.

## Security

Do not put a real Bynara API key in Git, `.env.example`, tests, logs, or documentation. If a key has been pasted into chat or any other potentially exposed location, rotate it at the provider and replace it in the deployment secret store.
