import unittest
from unittest.mock import patch

from app.agents.models import AgentRole, AgentTask, TaskStatus
from app.agents.providers import ProviderAdapter, ProviderResponse
from app.agents.service import build_execution_service


class ProviderAgentIntegrationTests(unittest.TestCase):
    def test_provider_response_becomes_model_evidence(self):
        provider = ProviderAdapter(
            "mock",
            "test-model",
            lambda model, prompt: ProviderResponse("mock", model, "security analysis complete"),
        )
        service = build_execution_service([provider])
        response = ProviderResponse("mock", "test-model", "security analysis complete")

        with patch.object(service.provider_router, "run", return_value=response):
            result = service.model_handler(
                AgentTask("model-security", AgentRole.SECURITY, "check security"), {}
            )

        self.assertEqual(result.status, TaskStatus.PASSED)
        self.assertIn("model-analysis:mock:test-model", result.evidence)
        self.assertEqual(result.metadata["verification_level"], "model_analysis")


if __name__ == "__main__":
    unittest.main()
