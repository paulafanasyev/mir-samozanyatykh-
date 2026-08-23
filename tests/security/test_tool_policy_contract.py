"""Contract tests for the server-side Svetlana tool policy.

This file intentionally uses only the Python standard library so it can run in
minimal CI environments without pytest or application dependencies.
"""
from pathlib import Path
import sys

# The test is executed as ``python tests/security/test_tool_policy_contract.py``.
# In that mode Python puts tests/security on sys.path, not the repository root,
# so the top-level ``src`` package is otherwise not importable. Resolve the repo
# root from this file instead of relying on the runner's environment.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.app.services.agent_tools import TOOL_POLICIES, is_allowed, policy_for


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
