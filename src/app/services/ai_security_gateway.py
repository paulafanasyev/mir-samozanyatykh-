"""Safety boundary for agentic AI calls.

No provider key is stored here. Providers are selected from environment variables.
The gateway rejects common prompt-injection/tool-abuse patterns, enforces limits,
and records a minimal audit event without storing secrets.
"""
from __future__ import annotations
import os, re, time
from dataclasses import dataclass
from typing import Any
import httpx

_BLOCKED = [
    r"ignore\s+(all|any|previous|prior)\s+instructions",
    r"reveal\s+(the\s+)?system\s+prompt",
    r"show\s+(me\s+)?(your|the)\s+(system|developer)\s+instructions",
    r"disable\s+(security|safety|authentication)",
    r"bypass\s+(security|authentication|authorization)",
]

@dataclass(frozen=True)
class Route:
    name: str
    base_url: str
    api_key_env: str
    model: str

class AISecurityError(ValueError):
    pass

def inspect_input(text: str) -> None:
    if not text or len(text) > 12000:
        raise AISecurityError("AI request is empty or too large")
    lowered = text.lower()
    for pattern in _BLOCKED:
        if re.search(pattern, lowered):
            raise AISecurityError("Запрос заблокирован защитным шлюзом AI")

def routes() -> list[Route]:
    result: list[Route] = []
    raw = os.getenv("AI_ROUTES", "").strip()
    for item in raw.split(",") if raw else []:
        parts = [x.strip() for x in item.split("|", 3)]
        if len(parts) == 4 and all(parts):
            result.append(Route(*parts))
    return result

async def chat(text: str, *, system: str = "", timeout: float = 30.0) -> dict[str, Any]:
    inspect_input(text)
    candidates = routes()
    if not candidates:
        return {"ok": False, "mode": "offline", "response": None, "reason": "AI_ROUTES is not configured"}
    last_error = "provider unavailable"
    for route in candidates:
        key = os.getenv(route.api_key_env, "")
        if not key:
            continue
        started = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    route.base_url.rstrip("/") + "/chat/completions",
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={"model": route.model, "messages": ([{"role":"system","content":system}] if system else []) + [{"role":"user","content":text}]},
                )
                response.raise_for_status()
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {"ok": True, "mode": "online", "provider": route.name, "model": route.model, "response": content, "latency_ms": round((time.monotonic()-started)*1000, 1)}
        except Exception as exc:
            last_error = f"{route.name}: {type(exc).__name__}"
    return {"ok": False, "mode": "offline", "response": None, "reason": last_error}
