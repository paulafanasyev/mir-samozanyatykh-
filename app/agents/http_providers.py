"""HTTP adapters for OpenAI-compatible model APIs.

Secrets are read only from the server environment. Responses are normalized
into ProviderResponse and provider failures are mapped to safe retryable
exceptions. Request logs must never include credentials.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .providers import ProviderAdapter, ProviderResponse, ProviderUnavailable


class ProviderRateLimited(ProviderUnavailable):
    """Provider returned a rate-limit response."""


class ProviderServerError(ProviderUnavailable):
    """Provider returned a server-side failure."""


def _post_json(base_url: str, api_key: str, model: str, prompt: str, timeout: float) -> dict:
    url = base_url.rstrip("/") + "/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise ProviderRateLimited(f"rate limited: HTTP {exc.code}") from exc
        if exc.code >= 500:
            raise ProviderServerError(f"provider server error: HTTP {exc.code}") from exc
        raise ProviderUnavailable(f"provider request rejected: HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ConnectionError("provider connection failed") from exc


def openai_compatible_call(base_url: str, api_key: str, model: str, prompt: str, timeout: float) -> ProviderResponse:
    if not api_key:
        raise ProviderUnavailable("provider API key is not configured")
    data = _post_json(base_url, api_key, model, prompt, timeout)
    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderUnavailable("provider returned an invalid response") from exc
    return ProviderResponse(provider=base_url, model=model, text=str(text))


def build_openrouter_adapter() -> ProviderAdapter:
    return ProviderAdapter(
        name="openrouter",
        model=os.getenv("AGENT_OPENROUTER_MODEL", ""),
        call=lambda model, prompt: openai_compatible_call(
            os.getenv("AGENT_OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            os.getenv("AGENT_OPENROUTER_API_KEY", os.getenv("OPENROUTER_API_KEY", "")),
            model,
            prompt,
            float(os.getenv("AGENT_PROVIDER_TIMEOUT", "30")),
        ),
        enabled=bool(os.getenv("AGENT_OPENROUTER_MODEL", "")),
    )


def build_openai_adapter() -> ProviderAdapter:
    return ProviderAdapter(
        name="openai",
        model=os.getenv("AGENT_OPENAI_MODEL", ""),
        call=lambda model, prompt: openai_compatible_call(
            os.getenv("AGENT_OPENAI_BASE_URL", "https://api.openai.com/v1"),
            os.getenv("AGENT_OPENAI_API_KEY", ""),
            model,
            prompt,
            float(os.getenv("AGENT_PROVIDER_TIMEOUT", "30")),
        ),
        enabled=bool(os.getenv("AGENT_OPENAI_MODEL", "")),
    )
