"""Build the configured provider chain without exposing credentials to tasks."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .http_providers import openai_compatible_call
from .providers import ProviderAdapter, ProviderResponse, ProviderUnavailable


def ollama_call(base_url: str, model: str, prompt: str, timeout: float) -> ProviderResponse:
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    request = urllib.request.Request(
        base_url.rstrip("/") + "/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ProviderUnavailable(f"ollama request rejected: HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ConnectionError("ollama connection failed") from exc
    try:
        return ProviderResponse("ollama", model, str(data["response"]))
    except (KeyError, TypeError) as exc:
        raise ProviderUnavailable("ollama returned an invalid response") from exc


def build_provider_chain():
    timeout = float(os.getenv("AGENT_PROVIDER_TIMEOUT", "30"))
    adapters = {
        "openrouter": ProviderAdapter(
            "openrouter", os.getenv("AGENT_OPENROUTER_MODEL", ""),
            lambda model, prompt: openai_compatible_call(
                "openrouter",
                os.getenv("AGENT_OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
                os.getenv("AGENT_OPENROUTER_API_KEY", os.getenv("OPENROUTER_API_KEY", "")),
                model, prompt, timeout,
            ),
            enabled=bool(os.getenv("AGENT_OPENROUTER_MODEL", "")),
        ),
        "openai": ProviderAdapter(
            "openai", os.getenv("AGENT_OPENAI_MODEL", ""),
            lambda model, prompt: openai_compatible_call(
                "openai",
                os.getenv("AGENT_OPENAI_BASE_URL", "https://api.openai.com/v1"),
                os.getenv("AGENT_OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", "")),
                model, prompt, timeout,
            ),
            enabled=bool(os.getenv("AGENT_OPENAI_MODEL", "")),
        ),
        "ollama": ProviderAdapter(
            "ollama", os.getenv("AGENT_OLLAMA_MODEL", ""),
            lambda model, prompt: ollama_call(
                os.getenv("AGENT_OLLAMA_BASE_URL", "http://127.0.0.1:11434"), model, prompt, timeout
            ),
            enabled=bool(os.getenv("AGENT_OLLAMA_MODEL", "")),
        ),
    }
    order = [x.strip().lower() for x in os.getenv("AGENT_PROVIDER_ORDER", "openrouter,openai,ollama").split(",") if x.strip()]
    return [adapters[name] for name in order if name in adapters and adapters[name].enabled]
