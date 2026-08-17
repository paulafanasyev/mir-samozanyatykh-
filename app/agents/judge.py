"""Final acceptance gate for the agent loop."""
from __future__ import annotations

from .models import AgentResult, AgentRole, AgentTask, TaskStatus


def judge_handler(task: AgentTask, previous: dict[str, AgentResult]) -> AgentResult:
    required = [AgentRole.SECURITY, AgentRole.QA, AgentRole.RUNTIME]
    missing = [role.value for role in required if not any(r.role == role for r in previous.values())]
    failed = [r.role.value for r in previous.values() if r.status != TaskStatus.PASSED]
    runtime = next((r for r in previous.values() if r.role == AgentRole.RUNTIME), None)

    if missing or failed or runtime is None or runtime.metadata.get("verification_level") != "runtime":
        findings = []
        if missing:
            findings.append("missing critical results: " + ", ".join(missing))
        if failed:
            findings.append("non-passing critical results: " + ", ".join(failed))
        if runtime is not None:
            findings.append("runtime result does not contain verified runtime evidence")
        return AgentResult(
            task.id,
            AgentRole.JUDGE,
            TaskStatus.FAILED,
            "Project change is not accepted by the evidence gate.",
            findings=findings,
            metadata={"verification_level": "judge"},
            retryable=True,
        )

    return AgentResult(
        task.id,
        AgentRole.JUDGE,
        TaskStatus.PASSED,
        "Critical agents passed and live runtime evidence is present.",
        evidence=["judge:critical-agents-passed", "judge:runtime-evidence-present"],
        metadata={"verification_level": "verified"},
    )
