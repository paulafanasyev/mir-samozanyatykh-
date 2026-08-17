import unittest

from app.agents.providers import ProviderAdapter, ProviderResponse, ProviderRouter, ProviderUnavailable


class ProviderFallbackTests(unittest.TestCase):
    def test_primary_failure_falls_back_to_secondary(self):
        calls = []

        def primary(model, prompt):
            calls.append("primary")
            raise TimeoutError("primary timeout")

        def secondary(model, prompt):
            calls.append("secondary")
            return ProviderResponse("secondary", model, "ok")

        router = ProviderRouter([
            ProviderAdapter("primary", "model-a", primary),
            ProviderAdapter("secondary", "model-b", secondary),
        ])
        response = router.run("test")
        self.assertEqual(response.provider, "secondary")
        self.assertEqual(calls, ["primary", "secondary"])

    def test_all_providers_failed_is_explicit(self):
        def fail(model, prompt):
            raise ConnectionError("offline")

        router = ProviderRouter([
            ProviderAdapter("one", "a", fail),
            ProviderAdapter("two", "b", fail),
        ])
        with self.assertRaises(ProviderUnavailable) as ctx:
            router.run("test")
        self.assertIn("all configured providers failed", str(ctx.exception))
        self.assertIn("one", str(ctx.exception))
        self.assertIn("two", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
