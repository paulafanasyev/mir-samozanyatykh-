"""Final acceptance gate for the agent loop."""
from __future__ import annotations

from .models import AgentResult, AgentRole, AgentTask, TaskStatus


REQUIRED_VERIFICATION = {
    AgentRole.SECURITY: "static",
    AgentRole.QA: "static",
    AgentRole.RUNTIME: "runtime",
}


def _verified(result: AgentResult, level: str, prefix: str) -> bool:
    return (
        result.status == TaskStatus.PASSED
        and result.metadata.get("verification_level") == level
        and any(item.startswith(prefix) for item in result.evidence)
    )


def judge_handler(task: AgentTask, previous: dict[str, AgentResult]) -> AgentResult:
    findings: list[str] = []
    results_by_role = {result.role: result for result in previous.values()}
    evidence_prefixes = {
        AgentRole.SECURITY: "static-security:",
        AgentRole.QA: "qa:",
        AgentRole.RUNTIME: "runtime:",
    }

    for role, level in REQUIRED_VERIFICATION.items():
        result = results_by_role.get(role)
        if result is None:
            findings.append(f"missing critical result: {role.value}")
        elif not _verified(result, level, evidence_prefixes[role]):
            findings.append(f"{role.value} lacks explicit {level} evidence")

    if findings:
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
        "Critical agents passed with explicit evidence classes.",
        evidence=["judge:critical-agents-passed", "judge:evidence-classes-verified"],
        metadata={"verification_level": "verified"},
    )
