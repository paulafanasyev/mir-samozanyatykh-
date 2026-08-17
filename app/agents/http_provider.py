"""HTTP adapter for OpenAI-compatible chat completion APIs."""
from __future__ import annotations

import json
import os
from urllib import error, request

from .providers import ProviderResponse


class HTTPProviderError(ConnectionError):
    """A provider request failed and is eligible for router fallback."""


def make_openai_compatible_call(*, provider: str, base_url: str, api_key: str,
                                 timeout: float = 45.0,
                                 extra_headers: dict[str, str] | None = None):
    endpoint = base_url.rstrip("/") + "/chat/completions"

    def call(model: str, prompt: str) -> ProviderResponse:
        if not api_key:
            raise HTTPProviderError(f"{provider}: API key is not configured")
        body = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "mir-samozanyatykh-agent-router/1.0",
        }
        if extra_headers:
            headers.update({k: v for k, v in extra_headers.items() if v})
        req = request.Request(endpoint, data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise HTTPProviderError(f"{provider}: {type(exc).__name__}: {exc}") from exc
        try:
            text = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise HTTPProviderError(f"{provider}: malformed chat completion response") from exc
        return ProviderResponse(provider, model, str(text))

    return call


def build_env_providers():
    """Build only providers explicitly configured by environment variables."""
    from .providers import ProviderAdapter
    providers = []

    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_model = os.getenv("AGENT_OPENROUTER_MODEL", "")
    if openrouter_key and openrouter_model:
        providers.append(ProviderAdapter(
            "openrouter", openrouter_model,
            make_openai_compatible_call(
                provider="openrouter",
                base_url=os.getenv("AGENT_OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
                api_key=openrouter_key,
                extra_headers={"HTTP-Referer": os.getenv("AGENT_HTTP_REFERER", "")},
            ),
        ))

    openai_key = os.getenv("OPENAI_API_KEY", "")
    openai_model = os.getenv("AGENT_OPENAI_MODEL", "")
    if openai_key and openai_model:
        providers.append(ProviderAdapter(
            "openai", openai_model,
            make_openai_compatible_call(
                provider="openai",
                base_url=os.getenv("AGENT_OPENAI_BASE_URL", "https://api.openai.com/v1"),
                api_key=openai_key,
            ),
        ))

    ollama_url = os.getenv("AGENT_OLLAMA_BASE_URL", "")
    ollama_model = os.getenv("AGENT_OLLAMA_MODEL", "")
    if ollama_url and ollama_model:
        providers.append(ProviderAdapter(
            "ollama", ollama_model,
            make_openai_compatible_call(
                provider="ollama",
                base_url=ollama_url,
                api_key=os.getenv("AGENT_OLLAMA_API_KEY", "ollama"),
            ),
        ))
    return providers
