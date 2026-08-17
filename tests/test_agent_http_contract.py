import os
import unittest

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret")
os.environ.setdefault("AGENT_PROVIDER_ORDER", "openrouter")
os.environ.setdefault("AGENT_OPENROUTER_API_KEY", "")
os.environ.setdefault("AGENT_OPENROUTER_MODEL", "test-model")

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


class AgentHttpContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_status_is_protected(self):
        response = self.client.get("/api/agents/status")
        self.assertEqual(response.status_code, 401)

    def test_run_is_protected(self):
        response = self.client.post(
            "/api/agents/run",
            json={"objective": "verify agent runtime"},
        )
        self.assertEqual(response.status_code, 401)

    def test_invalid_token_fails_closed(self):
        response = self.client.post(
            "/api/agents/run",
            headers={"Authorization": "Bearer invalid-test-token"},
            json={"objective": "verify agent runtime"},
        )
        self.assertIn(response.status_code, (401, 403))

    def test_invalid_payload_does_not_execute(self):
        response = self.client.post(
            "/api/agents/run",
            json={"objective": "x"},
        )
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
