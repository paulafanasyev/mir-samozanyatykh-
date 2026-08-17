"""Model-backed execution service for the multi-agent loop."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .judge import judge_handler
from .models import AgentResult, AgentRole, AgentTask, TaskStatus
from .orchestrator import AgentOrchestrator
from .providers import ProviderAdapter, ProviderRouter, ProviderUnavailable
from .qa_checks import qa_handler
from .router import build_plan
from .runtime import runtime_handler
from .security_checks import security_handler


@dataclass
class AgentExecutionService:
    provider_router: ProviderRouter

    def _prompt(self, task: AgentTask, previous: Dict[str, AgentResult]) -> str:
        prior = "\n".join(
            f"[{result.role.value}] {result.status.value}: {result.summary}"
            for result in previous.values()
        )
        return (
            "You are one specialist in the Mir Samozanykh multi-agent engineering loop.\n"
            f"Role: {task.role.value}\n"
            f"Objective: {task.objective}\n"
            "Project policy: never claim runtime verification unless an actual runtime check was performed.\n"
            "Return concise findings, risks, recommended actions, and explicitly label assumptions.\n"
            f"Previous specialist results:\n{prior or '(none)'}"
        )

    def model_handler(self, task: AgentTask, previous: Dict[str, AgentResult]) -> AgentResult:
        try:
            response = self.provider_router.run(self._prompt(task, previous))
        except ProviderUnavailable as exc:
            return AgentResult(
                task.id, task.role, TaskStatus.BLOCKED,
                "No configured AI provider was available.",
                findings=[str(exc)], metadata={"verification_level": "none"}, retryable=True,
            )
        return AgentResult(
            task.id, task.role, TaskStatus.PASSED, response.text,
            evidence=[f"model-analysis:{response.provider}:{response.model}"],
            metadata={"provider": response.provider, "model": response.model, "verification_level": "model_analysis"},
        )

    def run(self, task_id: str, objective: str, max_iterations: int = 3):
        plan = build_plan(task_id, objective)
        handlers = {role: self.model_handler for role in AgentRole}
        handlers[AgentRole.SECURITY] = security_handler
        handlers[AgentRole.QA] = qa_handler
        handlers[AgentRole.RUNTIME] = runtime_handler
        handlers[AgentRole.JUDGE] = judge_handler
        return AgentOrchestrator(handlers, max_iterations=max_iterations).run(plan)


def build_execution_service(providers: list[ProviderAdapter]) -> AgentExecutionService:
    if not providers:
        raise ProviderUnavailable("no AI providers configured")
    return AgentExecutionService(ProviderRouter(providers))
