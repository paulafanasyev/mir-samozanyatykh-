"""Public safety inspection endpoint for AI-agent requests.

This endpoint is intentionally non-agentic: it classifies and sanitizes a
request but never executes tools, changes data, or calls external providers.
"""
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from app.core.rate_limit import limiter
from app.services.agent_guard import inspect

router = APIRouter(prefix="/api/ai", tags=["ai-security"])

class GuardRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    confirmation: bool = False

@router.post("/guard")
@limiter.limit("60/minute")
async def guard(request: Request, payload: GuardRequest):
    result = inspect(payload.message)
    if result.requires_confirmation and not payload.confirmation:
        allowed = False
        decision = "confirmation_required"
    else:
        allowed = result.allowed
        decision = "allow" if allowed else "deny"
    return {
        "allowed": allowed,
        "decision": decision,
        "risk": result.risk,
        "reasons": list(result.reasons),
        "sanitized_message": result.sanitized_message,
        "requires_confirmation": result.requires_confirmation,
        "tool_execution": False,
    }

@router.get("/security-status")
async def security_status():
    return {
        "agent_gateway": "enabled",
        "tool_execution": "disabled-by-default",
        "confirmation_for_side_effects": True,
        "prompt_injection_blocking": True,
        "secret_redaction": True,
    }
