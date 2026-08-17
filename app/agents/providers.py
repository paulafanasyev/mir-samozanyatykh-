"""Provider-neutral model adapter with explicit fallback semantics.

Adapters are intentionally small. They receive no credentials from task
context; production wiring should read secrets from the server environment.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Optional


@dataclass(frozen=True)
class ProviderResponse:
    provider: str
    model: str
    text: str


ProviderCall = Callable[[str, str], ProviderResponse]


class ProviderUnavailable(RuntimeError):
    pass


@dataclass
class ProviderAdapter:
    name: str
    model: str
    call: ProviderCall
    enabled: bool = True

    def run(self, prompt: str) -> ProviderResponse:
        if not self.enabled:
            raise ProviderUnavailable(f"provider disabled: {self.name}")
        return self.call(self.model, prompt)


class ProviderRouter:
    def __init__(self, providers: Iterable[ProviderAdapter]):
        self.providers = list(providers)

    def run(self, prompt: str) -> ProviderResponse:
        errors = []
        for provider in self.providers:
            try:
                return provider.run(prompt)
            except (ProviderUnavailable, TimeoutError, ConnectionError) as exc:
                errors.append(f"{provider.name}: {type(exc).__name__}: {exc}")
        raise ProviderUnavailable("all configured providers failed: " + " | ".join(errors))
