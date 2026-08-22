"""Extra dependency-free checks for the server-side Svetlana tool policy."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from app.services.agent_tools import is_allowed, policy_for


def main():
    assert is_allowed("navigate")
    assert is_allowed("read_documents")
    assert not is_allowed("create_task")
    assert is_allowed("create_task", confirmed=True)
    assert not is_allowed("delete_data")
    assert is_allowed("delete_data", confirmed=True)
    for name in ("run_shell", "exec", "shell", "python", "http_request", "__import__", ""):
        assert not is_allowed(name), name
    assert policy_for("read_documents").requires_confirmation is False
    print("AI tool policy regression tests: OK")


if __name__ == "__main__":
    main()
