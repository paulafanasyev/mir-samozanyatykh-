import os
import unittest
from unittest.mock import patch

from app.agents.provider_registry import build_provider_chain
from app.agents.providers import ProviderResponse, ProviderRouter


class ProviderIntegrationTests(unittest.TestCase):
    def test_registry_chain_runs_through_provider_router(self):
        env = {
            "AGENT_PROVIDER_ORDER": "openrouter,openai,ollama",
            "AGENT_OPENROUTER_MODEL": "router-model",
            "AGENT_OPENAI_MODEL": "",
            "AGENT_OLLAMA_MODEL": "",
            "OPENROUTER_API_KEY": "test-key",
        }
        with patch.dict(os.environ, env, clear=False):
            chain = build_provider_chain()
            self.assertEqual([p.name for p in chain], ["openrouter"])
            chain[0].call = lambda model, prompt: ProviderResponse("openrouter", model, "integration-ok")
            result = ProviderRouter(chain).run("integration test")
        self.assertEqual(result.text, "integration-ok")
        self.assertEqual(result.provider, "openrouter")
        self.assertEqual(result.model, "router-model")

    def test_registry_skips_unconfigured_primary_and_uses_next_provider(self):
        env = {
            "AGENT_PROVIDER_ORDER": "openrouter,ollama",
            "AGENT_OPENROUTER_MODEL": "",
            "AGENT_OLLAMA_MODEL": "ollama-model",
            "AGENT_OLLAMA_BASE_URL": "http://127.0.0.1:11434",
        }
        with patch.dict(os.environ, env, clear=False):
            chain = build_provider_chain()
        self.assertEqual([p.name for p in chain], ["ollama"])


if __name__ == "__main__":
    unittest.main()
