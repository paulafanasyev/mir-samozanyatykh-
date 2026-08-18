import unittest
from unittest.mock import patch

from app.agents.models import AgentRole, AgentTask, TaskStatus
from app.agents.providers import ProviderResponse
from app.agents.service import make_agent_handler


class ProviderAgentIntegrationTests(unittest.TestCase):
    def test_provider_response_becomes_agent_evidence(self):
        response = ProviderResponse(provider="mock", model="test-model", text="security analysis complete")
        with patch("app.agents.service.provider_router.run", return_value=response):
            handler = make_agent_handler(AgentRole.SECURITY)
            result = handler(AgentTask("security", AgentRole.SECURITY, "check security"), {})

        self.assertEqual(result.status, TaskStatus.PASSED)
        self.assertIn("provider:mock", result.evidence)
        self.assertIn("model:test-model", result.evidence)
        self.assertEqual(result.metadata["verification_level"], "static")


if __name__ == "__main__":
    unittest.main()
