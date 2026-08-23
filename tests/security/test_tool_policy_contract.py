"""Contract tests for the server-side Svetlana tool policy.

This file intentionally uses only the Python standard library so it can run in
minimal CI environments without pytest or application dependencies.
"""
from pathlib import Path
import sys

# The test is executed directly from GitHub Actions. The application uses a
# src-layout, so <repo>/src must be importable before importing app.
REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
for path in (REPO_ROOT, SRC_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.services.agent_tools import TOOL_POLICIES, is_allowed, policy_for


def main() -> None:
    assert policy_for("navigate") is not None
    assert is_allowed("navigate")

    for name in ("run_shell", "shell", "exec", "python", "http_request", "__import__"):
        assert policy_for(name) is None, name
        assert not is_allowed(name), name

    for name in ("create_task", "create_calendar_event", "send_message", "create_payment", "delete_data"):
        assert not is_allowed(name), name
        assert is_allowed(name, confirmed=True), name
        assert policy_for(name).requires_confirmation is True

    for name in ("read_profile", "read_calendar", "read_tasks", "read_clients", "read_documents"):
        assert is_allowed(name), name
        assert policy_for(name).requires_confirmation is False

    assert all(p.allowed for p in TOOL_POLICIES.values())
    print("tool policy contract: OK")


if __name__ == "__main__":
    main()
