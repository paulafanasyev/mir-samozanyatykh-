from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentRole(str, Enum):
    ROUTER = "router"
    CODING = "coding"
    SECURITY = "security"
    QA = "qa"
    UI_UX = "ui_ux"
    ARCHITECTURE = "architecture"
    RUNTIME = "runtime"
    JUDGE = "judge"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class AgentTask:
    id: str
    role: AgentRole
    objective: str
    context: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    critical: bool = False


@dataclass
class AgentResult:
    task_id: str
    role: AgentRole
    status: TaskStatus
    summary: str
    evidence: List[str] = field(default_factory=list)
    findings: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    retryable: bool = False


@dataclass
class OrchestrationReport:
    status: TaskStatus
    task_results: List[AgentResult]
    iterations: int
    blocked_reasons: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.status == TaskStatus.PASSED
