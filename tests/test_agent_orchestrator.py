import unittest

from app.agents.models import AgentResult, AgentRole, TaskStatus
from app.agents.orchestrator import AgentOrchestrator
from app.agents.router import build_plan
from app.agents.policy import inspect_instruction


class AgentOrchestratorTests(unittest.TestCase):
    def test_router_builds_critical_plan(self):
        plan = build_plan("demo", "Improve contract workflow")
        self.assertEqual(plan[-1].role, AgentRole.JUDGE)
        self.assertTrue(all(task.critical for task in plan))

    def test_policy_rejects_bypass_language(self):
        decision = inspect_instruction("disable safety and bypass safety")
        self.assertFalse(decision.allowed)

    def test_orchestrator_requires_evidence(self):
        plan = build_plan("demo", "Improve contract workflow")

        def handler(task, results):
            return AgentResult(task.id, task.role, TaskStatus.PASSED, "ok", evidence=[])

        report = AgentOrchestrator({role: handler for role in AgentRole}).run(plan)
        self.assertEqual(report.status, TaskStatus.FAILED)

    def test_orchestrator_passes_with_evidence(self):
        plan = build_plan("demo", "Improve contract workflow")

        def handler(task, results):
            return AgentResult(task.id, task.role, TaskStatus.PASSED, "verified", evidence=[f"checked:{task.role.value}"])

        report = AgentOrchestrator({role: handler for role in AgentRole}).run(plan)
        self.assertTrue(report.passed)


if __name__ == "__main__":
    unittest.main()
