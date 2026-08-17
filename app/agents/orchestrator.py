from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List

from .models import AgentResult, AgentRole, AgentTask, OrchestrationReport, TaskStatus
from .policy import require_evidence


AgentHandler = Callable[[AgentTask, Dict[str, AgentResult]], AgentResult]


@dataclass
class AgentOrchestrator:
    handlers: Dict[AgentRole, AgentHandler]
    max_iterations: int = 3

    def run(self, tasks: Iterable[AgentTask]) -> OrchestrationReport:
        task_list = list(tasks)
        results: Dict[str, AgentResult] = {}
        blocked: List[str] = []

        for iteration in range(1, self.max_iterations + 1):
            progress = False
            for task in task_list:
                if task.id in results and results[task.id].status == TaskStatus.PASSED:
                    continue

                missing = [dep for dep in task.dependencies if dep not in results or results[dep].status != TaskStatus.PASSED]
                if missing:
                    continue

                handler = self.handlers.get(task.role)
                if handler is None:
                    results[task.id] = AgentResult(task.id, task.role, TaskStatus.BLOCKED,
                                                   "No handler registered", findings=["handler missing"])
                    blocked.append(f"{task.id}: handler missing")
                    progress = True
                    continue

                result = handler(task, results)
                results[task.id] = result
                progress = True

                if task.critical and result.status == TaskStatus.PASSED:
                    evidence_check = require_evidence(result.evidence)
                    if not evidence_check.allowed:
                        result.status = TaskStatus.FAILED
                        result.findings.append(evidence_check.reason)

            if all(r.status == TaskStatus.PASSED for r in results.values()) and len(results) == len(task_list):
                return OrchestrationReport(TaskStatus.PASSED, list(results.values()), iteration, blocked)

            if not progress:
                break

        final_results = list(results.values())
        critical_failures = [r for r in final_results if r.status in (TaskStatus.FAILED, TaskStatus.BLOCKED)]
        status = TaskStatus.FAILED if critical_failures or len(final_results) != len(task_list) else TaskStatus.PASSED
        return OrchestrationReport(status, final_results, self.max_iterations, blocked)
