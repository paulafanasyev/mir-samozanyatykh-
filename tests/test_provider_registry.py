import os
import unittest
from unittest.mock import patch

from app.agents.provider_registry import build_provider_chain


class ProviderRegistryTests(unittest.TestCase):
    def test_order_is_configurable_and_disabled_providers_are_excluded(self):
        env = {
            "AGENT_PROVIDER_ORDER": "ollama,openai,openrouter",
            "AGENT_OLLAMA_MODEL": "local-model",
            "AGENT_OPENAI_MODEL": "",
            "AGENT_OPENROUTER_MODEL": "router-model",
        }
        with patch.dict(os.environ, env, clear=False):
            chain = build_provider_chain()
        self.assertEqual([item.name for item in chain], ["ollama", "openrouter"])

    def test_default_order_is_stable(self):
        env = {
            "AGENT_PROVIDER_ORDER": "openrouter,openai,ollama",
            "AGENT_OPENROUTER_MODEL": "r",
            "AGENT_OPENAI_MODEL": "o",
            "AGENT_OLLAMA_MODEL": "l",
        }
        with patch.dict(os.environ, env, clear=False):
            chain = build_provider_chain()
        self.assertEqual([item.name for item in chain], ["openrouter", "openai", "ollama"])


if __name__ == "__main__":
    unittest.main()
