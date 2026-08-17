import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from app.agents.models import AgentRole, AgentTask, TaskStatus
from app.agents.runtime import runtime_handler


class HealthHandler(BaseHTTPRequestHandler):
    healthy = True

    def do_GET(self):
        if self.path != "/health":
            self.send_response(404)
            self.end_headers()
            return
        body = json.dumps({"status": "healthy" if self.healthy else "unhealthy"}).encode()
        self.send_response(200 if self.healthy else 503)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


class RuntimeHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), HealthHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=2)

    def task(self):
        return AgentTask("runtime-http", AgentRole.RUNTIME, "check runtime")

    def test_real_http_health_evidence_passes(self):
        HealthHandler.healthy = True
        with patch.dict("os.environ", {"AGENT_RUNTIME_BASE_URL": self.base_url, "AGENT_RUNTIME_TIMEOUT": "3"}, clear=False):
            result = runtime_handler(self.task(), {})
        self.assertEqual(result.status, TaskStatus.PASSED)
        self.assertIn("runtime:http:200", result.evidence)
        self.assertIn("runtime:health:healthy", result.evidence)
        self.assertEqual(result.metadata["verification_level"], "runtime")

    def test_unhealthy_http_response_fails_closed(self):
        HealthHandler.healthy = False
        with patch.dict("os.environ", {"AGENT_RUNTIME_BASE_URL": self.base_url, "AGENT_RUNTIME_TIMEOUT": "3"}, clear=False):
            result = runtime_handler(self.task(), {})
        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertIn("runtime:http:503", result.evidence)
        self.assertEqual(result.metadata["verification_level"], "runtime")
        HealthHandler.healthy = True


if __name__ == "__main__":
    unittest.main()
