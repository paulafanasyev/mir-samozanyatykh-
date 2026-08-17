"""Backward-compatible HTTP provider helpers.

Provider construction is centralized in provider_registry.py. This module keeps
its low-level OpenAI-compatible call helper for existing imports and tests.
"""
from __future__ import annotations

import json
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
        body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "User-Agent": "mir-samozanyatykh-agent-router/1.0"}
        if extra_headers:
            headers.update({k: v for k, v in extra_headers.items() if v})
        req = request.Request(endpoint, data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise HTTPProviderError(f"{provider}: {type(exc).__name__}") from exc
        try:
            text = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise HTTPProviderError(f"{provider}: malformed chat completion response") from exc
        return ProviderResponse(provider, model, str(text))

    return call


def build_env_providers():
    """Compatibility entry point; canonical construction lives in provider_registry."""
    from .provider_registry import build_provider_chain
    return build_provider_chain()
