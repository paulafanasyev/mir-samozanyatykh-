"""Server-side allowlist for Svetlana tool calls.

The model can request only named, non-arbitrary tools. Authorization remains
outside the model and side-effecting tools require explicit confirmation.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ToolPolicy:
    name: str
    requires_confirmation: bool
    allowed: bool = True

# Keep this list deliberately small. Add a tool only after implementing its
# server-side authorization and input validation.
TOOL_POLICIES: dict[str, ToolPolicy] = {
    "navigate": ToolPolicy("navigate", False),
    "read_profile": ToolPolicy("read_profile", False),
    "read_calendar": ToolPolicy("read_calendar", False),
    "read_tasks": ToolPolicy("read_tasks", False),
    "read_clients": ToolPolicy("read_clients", False),
    "read_documents": ToolPolicy("read_documents", False),
    "create_task": ToolPolicy("create_task", True),
    "create_calendar_event": ToolPolicy("create_calendar_event", True),
    "send_message": ToolPolicy("send_message", True),
    "create_payment": ToolPolicy("create_payment", True),
    "delete_data": ToolPolicy("delete_data", True),
}

def policy_for(tool_name: str) -> ToolPolicy | None:
    return TOOL_POLICIES.get(str(tool_name or "").strip())

def is_allowed(tool_name: str, confirmed: bool = False) -> bool:
    policy = policy_for(tool_name)
    if policy is None or not policy.allowed:
        return False
    return not policy.requires_confirmation or confirmed
