from __future__ import annotations

from typing import List

from .models import AgentRole, AgentTask
from .policy import inspect_instruction


def build_plan(task_id: str, objective: str) -> List[AgentTask]:
    """Create a deterministic review plan for a product change.

    The plan is intentionally provider-agnostic: model/provider selection is
    handled by the adapter layer, while the project controls task ordering and
    acceptance criteria.
    """
    decision = inspect_instruction(objective)
    if not decision.allowed:
        raise ValueError(decision.reason)

    return [
        AgentTask(task_id + ":architecture", AgentRole.ARCHITECTURE,
                  "Check architecture, boundaries, dependencies and rollback plan.", critical=True),
        AgentTask(task_id + ":coding", AgentRole.CODING,
                  "Implement the smallest complete change that satisfies the objective.",
                  dependencies=[task_id + ":architecture"], critical=True),
        AgentTask(task_id + ":security", AgentRole.SECURITY,
                  "Review authentication, authorization, secrets, injection, data exposure and abuse paths.",
                  dependencies=[task_id + ":coding"], critical=True),
        AgentTask(task_id + ":qa", AgentRole.QA,
                  "Run or define functional, regression and negative-path checks.",
                  dependencies=[task_id + ":coding"], critical=True),
        AgentTask(task_id + ":runtime", AgentRole.RUNTIME,
                  "Verify the changed artifact in a real runtime where available.",
                  dependencies=[task_id + ":security", task_id + ":qa"], critical=True),
        AgentTask(task_id + ":judge", AgentRole.JUDGE,
                  "Reject unsupported claims and accept only when critical evidence is sufficient.",
                  dependencies=[task_id + ":security", task_id + ":qa", task_id + ":runtime"], critical=True),
    ]
