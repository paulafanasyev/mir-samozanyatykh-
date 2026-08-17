import tempfile
import unittest
from pathlib import Path

from app.agents.artifacts import verify_artifacts
from app.agents.models import AgentResult, AgentRole, TaskStatus
from app.agents.orchestrator import AgentOrchestrator
from app.agents.policy import inspect_instruction
from app.agents.providers import ProviderAdapter, ProviderResponse, ProviderRouter
from app.agents.router import build_plan


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

    def test_provider_router_falls_back(self):
        def broken(model, prompt):
            raise ConnectionError("offline")

        def healthy(model, prompt):
            return ProviderResponse("secondary", model, "ok")

        router = ProviderRouter([
            ProviderAdapter("primary", "m1", broken),
            ProviderAdapter("secondary", "m2", healthy),
        ])
        self.assertEqual(router.run("hello").provider, "secondary")

    def test_artifact_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            existing = Path(tmp) / "result.txt"
            existing.write_text("verified", encoding="utf-8")
            checks = verify_artifacts([str(existing), str(Path(tmp) / "missing.txt")])
            self.assertTrue(checks[0].passed)
            self.assertFalse(checks[1].passed)


if __name__ == "__main__":
    unittest.main()
