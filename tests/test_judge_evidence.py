import unittest

from app.agents.judge import judge_handler
from app.agents.models import AgentResult, AgentRole, AgentTask, TaskStatus


class JudgeEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.task = AgentTask("judge-1", AgentRole.JUDGE, "accept change")

    def result(self, role, level, evidence, status=TaskStatus.PASSED):
        return AgentResult(
            task_id=role.value,
            role=role,
            status=status,
            summary="verified",
            evidence=evidence,
            metadata={"verification_level": level},
        )

    def test_model_analysis_cannot_be_runtime_evidence(self):
        previous = {
            "security": self.result(AgentRole.SECURITY, "static", ["static-security:checked:app/main.py"]),
            "qa": self.result(AgentRole.QA, "static", ["qa:unittest:exit:0"]),
            "runtime": self.result(AgentRole.RUNTIME, "model_analysis", ["model-analysis:healthy"]),
        }
        result = judge_handler(self.task, previous)
        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertIn("runtime lacks explicit runtime evidence", result.findings)

    def test_all_explicit_evidence_classes_can_pass(self):
        previous = {
            "security": self.result(AgentRole.SECURITY, "static", ["static-security:checked:app/main.py"]),
            "qa": self.result(AgentRole.QA, "static", ["qa:unittest:exit:0"]),
            "runtime": self.result(AgentRole.RUNTIME, "runtime", ["runtime:http:200"]),
        }
        result = judge_handler(self.task, previous)
        self.assertEqual(result.status, TaskStatus.PASSED)


if __name__ == "__main__":
    unittest.main()
