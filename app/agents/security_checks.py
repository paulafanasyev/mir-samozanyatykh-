"""Deterministic security checks for the current checkout."""
from __future__ import annotations

from pathlib import Path

from .models import AgentResult, AgentRole, AgentTask, TaskStatus


FORBIDDEN = {
    'allow_origins=["*"]': "wildcard CORS with credentials",
    'SECRET_KEY: str = os.getenv("SECRET_KEY", "mir-samozanyatykh-secret-key-2026-change-in-production")': "default production secret",
}


def security_handler(task: AgentTask, _previous: dict[str, AgentResult]) -> AgentResult:
    findings: list[str] = []
    checked: list[str] = []
    for relative in ("app/main.py", "app/core/config.py", ".env.example"):
        path = Path(relative)
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        checked.append(relative)
        for marker, description in FORBIDDEN.items():
            if marker in text:
                findings.append(f"{relative}: {description}")

    if findings:
        return AgentResult(
            task.id, AgentRole.SECURITY, TaskStatus.FAILED,
            "Static security gate found high-risk configuration.",
            findings=findings,
            evidence=[f"static-security:checked:{','.join(checked)}"],
            metadata={"verification_level": "static"},
            retryable=True,
        )

    return AgentResult(
        task.id, AgentRole.SECURITY, TaskStatus.PASSED,
        "Deterministic security checks passed.",
        evidence=[f"static-security:checked:{','.join(checked)}"],
        metadata={"verification_level": "static"},
    )
