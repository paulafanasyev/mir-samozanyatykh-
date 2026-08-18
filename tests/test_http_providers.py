import unittest
from unittest.mock import patch

from app.agents.http_providers import ProviderRateLimited, ProviderServerError, openai_compatible_call
from app.agents.providers import ProviderUnavailable


class HttpProviderTests(unittest.TestCase):
    def test_missing_key_fails_closed(self):
        with self.assertRaises(ProviderUnavailable):
            openai_compatible_call("test", "https://example.invalid/v1", "", "model", "hello", 1)

    @patch("app.agents.http_providers._post_json")
    def test_response_is_normalized(self, post):
        post.return_value = {"choices": [{"message": {"content": "hello"}}]}
        result = openai_compatible_call("test", "https://example.test/v1", "secret", "model", "hello", 1)
        self.assertEqual(result.model, "model")
        self.assertEqual(result.text, "hello")
        self.assertEqual(result.provider, "test")

    @patch("app.agents.http_providers.urllib.request.urlopen")
    def test_429_is_rate_limited(self, urlopen):
        import urllib.error
        urlopen.side_effect = urllib.error.HTTPError("https://example.test", 429, "rate", {}, None)
        with self.assertRaises(ProviderRateLimited):
            openai_compatible_call("test", "https://example.test/v1", "secret", "model", "hello", 1)

    @patch("app.agents.http_providers.urllib.request.urlopen")
    def test_5xx_is_server_error(self, urlopen):
        import urllib.error
        urlopen.side_effect = urllib.error.HTTPError("https://example.test", 503, "server", {}, None)
        with self.assertRaises(ProviderServerError):
            openai_compatible_call("test", "https://example.test/v1", "secret", "model", "hello", 1)


if __name__ == "__main__":
    unittest.main()
