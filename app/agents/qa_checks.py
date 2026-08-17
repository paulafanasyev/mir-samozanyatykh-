"""Run the repository's Python regression suite as an agent check."""
from __future__ import annotations

import os
import subprocess
import sys

from .models import AgentResult, AgentRole, AgentTask, TaskStatus


def qa_handler(task: AgentTask, _previous: dict[str, AgentResult]) -> AgentResult:
    if os.getenv("AGENT_RUN_TESTS", "true").lower() != "true":
        return AgentResult(
            task.id, AgentRole.QA, TaskStatus.BLOCKED,
            "Automated regression tests are disabled by configuration.",
            findings=["set AGENT_RUN_TESTS=true to enable the QA gate"],
            metadata={"verification_level": "none"}, retryable=True,
        )

    try:
        completed = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
            capture_output=True, text=True, timeout=int(os.getenv("AGENT_TEST_TIMEOUT", "120")),
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return AgentResult(
            task.id, AgentRole.QA, TaskStatus.FAILED,
            "Regression suite could not be executed.",
            findings=[f"{type(exc).__name__}: {exc}"],
            metadata={"verification_level": "static"}, retryable=True,
        )

    output = (completed.stdout + "\n" + completed.stderr).strip()
    if completed.returncode != 0:
        return AgentResult(
            task.id, AgentRole.QA, TaskStatus.FAILED,
            "Regression suite failed.",
            findings=[output[-4000:] if output else f"exit={completed.returncode}"],
            evidence=[f"qa:unittest:exit:{completed.returncode}"],
            metadata={"verification_level": "static"}, retryable=True,
        )

    return AgentResult(
        task.id, AgentRole.QA, TaskStatus.PASSED,
        "Regression suite passed.",
        evidence=["qa:unittest:exit:0"],
        metadata={"verification_level": "static"},
    )
