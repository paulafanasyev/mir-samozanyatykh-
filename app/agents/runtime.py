"""Runtime checks that produce verifiable evidence instead of model claims."""
from __future__ import annotations

import json
import os
from urllib import error, request

from .models import AgentResult, AgentRole, AgentTask, TaskStatus


def runtime_handler(task: AgentTask, _previous: dict[str, AgentResult]) -> AgentResult:
    base_url = os.getenv("AGENT_RUNTIME_BASE_URL", "").rstrip("/")
    if not base_url:
        return AgentResult(
            task.id,
            AgentRole.RUNTIME,
            TaskStatus.BLOCKED,
            "Runtime verification is not configured.",
            findings=["set AGENT_RUNTIME_BASE_URL to a deployed/test instance"],
            metadata={"verification_level": "none"},
            retryable=True,
        )

    url = base_url + "/health"
    req = request.Request(url, headers={"User-Agent": "mir-samozanyatykh-runtime-check/1.0"})
    try:
        with request.urlopen(req, timeout=float(os.getenv("AGENT_RUNTIME_TIMEOUT", "10"))) as response:
            body = response.read().decode("utf-8", errors="replace")
            status = response.status
    except error.HTTPError as exc:
        return AgentResult(
            task.id,
            AgentRole.RUNTIME,
            TaskStatus.FAILED,
            "Runtime health check returned an HTTP error.",
            findings=[f"HTTP {exc.code}"],
            evidence=[f"runtime:http:{exc.code}"],
            metadata={"verification_level": "runtime"},
            retryable=True,
        )
    except (error.URLError, TimeoutError, ValueError) as exc:
        return AgentResult(
            task.id,
            AgentRole.RUNTIME,
            TaskStatus.FAILED,
            "Runtime health check failed.",
            findings=[f"{type(exc).__name__}: {exc}"],
            metadata={"verification_level": "runtime"},
            retryable=True,
        )

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        payload = {}

    if status != 200 or payload.get("status") != "healthy":
        return AgentResult(
            task.id,
            AgentRole.RUNTIME,
            TaskStatus.FAILED,
            "Runtime responded, but health contract was not satisfied.",
            findings=[f"HTTP {status}", f"payload_status={payload.get('status', 'missing')}"],
            evidence=[f"runtime:http:{status}"],
            metadata={"verification_level": "runtime"},
            retryable=True,
        )

    return AgentResult(
        task.id,
        AgentRole.RUNTIME,
        TaskStatus.PASSED,
        "Live /health check passed.",
        evidence=[f"runtime:http:{status}", "runtime:health:healthy"],
        metadata={"verification_level": "runtime", "url": url},
    )
