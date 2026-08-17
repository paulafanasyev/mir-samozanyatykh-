import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.agents.judge import judge_handler
from app.agents.models import AgentResult, AgentRole, AgentTask, TaskStatus
from app.agents.runtime import runtime_handler
from app.agents.security_checks import security_handler


class AgentGateTests(unittest.TestCase):
    def test_judge_rejects_model_only_runtime_claim(self):
        results = {
            "security": AgentResult("security", AgentRole.SECURITY, TaskStatus.PASSED, "ok", evidence=["static"], metadata={"verification_level": "static"}),
            "qa": AgentResult("qa", AgentRole.QA, TaskStatus.PASSED, "ok", evidence=["qa"], metadata={"verification_level": "static"}),
            "runtime": AgentResult("runtime", AgentRole.RUNTIME, TaskStatus.PASSED, "claimed", evidence=["model-analysis"], metadata={"verification_level": "model_analysis"}),
        }
        result = judge_handler(AgentTask("judge", AgentRole.JUDGE, "judge", critical=True), results)
        self.assertEqual(result.status, TaskStatus.FAILED)

    def test_runtime_blocks_without_target(self):
        with patch.dict(os.environ, {}, clear=True):
            result = runtime_handler(AgentTask("runtime", AgentRole.RUNTIME, "health"), {})
        self.assertEqual(result.status, TaskStatus.BLOCKED)

    def test_security_gate_detects_wildcard_and_static_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app").mkdir()
            (root / "app/main.py").write_text('allow_origins=["*"]', encoding="utf-8")
            (root / "app/core").mkdir(parents=True)
            (root / "app/core/config.py").write_text('SECRET_KEY: str = os.getenv("SECRET_KEY", "mir-samozanyatykh-secret-key-2026-change-in-production")', encoding="utf-8")
            (root / ".env.example").write_text('', encoding="utf-8")
            old = Path.cwd()
            try:
                os.chdir(root)
                result = security_handler(AgentTask("security", AgentRole.SECURITY, "scan"), {})
            finally:
                os.chdir(old)
        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertGreaterEqual(len(result.findings), 2)


if __name__ == "__main__":
    unittest.main()
