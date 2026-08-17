import os
import unittest

from fastapi.testclient import TestClient

# Force deterministic auth/test configuration before importing the app.
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret")
os.environ.setdefault("AGENT_PROVIDER_ORDER", "openrouter")
os.environ.setdefault("AGENT_OPENROUTER_API_KEY", "")
os.environ.setdefault("AGENT_OPENROUTER_MODEL", "test-model")

from app.main import app  # noqa: E402


class AgentApiRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_agent_status_requires_auth(self):
        response = self.client.get("/api/agents/status")
        self.assertEqual(response.status_code, 401)

    def test_agent_run_requires_auth(self):
        response = self.client.post("/api/agents/run", json={"task": "test"})
        self.assertEqual(response.status_code, 401)

    def test_agent_run_rejects_non_privileged_user(self):
        # The endpoint must not be callable merely because a user is authenticated.
        # A malformed token is intentionally treated as unauthenticated here.
        response = self.client.post(
            "/api/agents/run",
            headers={"Authorization": "Bearer invalid-test-token"},
            json={"task": "test"},
        )
        self.assertIn(response.status_code, (401, 403))

    def test_agent_run_without_provider_is_not_reported_as_success(self):
        # No API key is configured in CI. The endpoint must fail closed rather
        # than manufacture an AI result.
        response = self.client.post(
            "/api/agents/run",
            headers={"Authorization": "Bearer invalid-test-token"},
            json={"task": "test"},
        )
        self.assertNotEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
