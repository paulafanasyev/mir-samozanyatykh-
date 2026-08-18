import unittest

from app.agents.models import AgentRole, AgentTask, TaskStatus
from app.agents.orchestrator import AgentOrchestrator


class RuntimeRetryTests(unittest.TestCase):
    def test_runtime_failure_is_retryable_and_does_not_pass(self):
        calls = {"runtime": 0}

        def security(task, previous):
            from app.agents.models import AgentResult
            return AgentResult(task.id, task.role, TaskStatus.PASSED, "ok", evidence=["static-security:scan:passed"], metadata={"verification_level": "static"})

        def qa(task, previous):
            from app.agents.models import AgentResult
            return AgentResult(task.id, task.role, TaskStatus.PASSED, "ok", evidence=["qa:tests:passed"], metadata={"verification_level": "static"})

        def runtime(task, previous):
            from app.agents.models import AgentResult
            calls["runtime"] += 1
            if calls["runtime"] == 1:
                return AgentResult(task.id, task.role, TaskStatus.FAILED, "health failed", evidence=["runtime:http:500"], metadata={"verification_level": "runtime"}, retryable=True)
            return AgentResult(task.id, task.role, TaskStatus.PASSED, "health passed", evidence=["runtime:http:200"], metadata={"verification_level": "runtime"})

        def judge(task, previous):
            from app.agents.judge import judge_handler
            return judge_handler(task, previous)

        handlers = {
            AgentRole.SECURITY: security,
            AgentRole.QA: qa,
            AgentRole.RUNTIME: runtime,
            AgentRole.JUDGE: judge,
        }
        tasks = [
            AgentTask("security", AgentRole.SECURITY, "security", critical=True),
            AgentTask("qa", AgentRole.QA, "qa", critical=True),
            AgentTask("runtime", AgentRole.RUNTIME, "runtime", critical=True),
            AgentTask("judge", AgentRole.JUDGE, "judge", critical=True),
        ]

        report = AgentOrchestrator(handlers, max_iterations=2).run(tasks)
        self.assertEqual(calls["runtime"], 2)
        self.assertEqual(report.status, TaskStatus.PASSED)
        self.assertGreaterEqual(report.iterations, 2)


if __name__ == "__main__":
    unittest.main()
