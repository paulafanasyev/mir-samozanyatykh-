"""Protected HTTP entry point for the multi-agent engineering loop."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.agents.http_provider import build_env_providers
from app.agents.models import TaskStatus
from app.agents.service import build_execution_service
from app.core.config import settings

# Imported lazily by the module at the end of app.main, after dependencies exist.
from app.main import get_current_user_api

router = APIRouter(prefix="/api/agents", tags=["agents"])


class AgentRunRequest(BaseModel):
    objective: str = Field(..., min_length=5, max_length=12000)
    task_id: str | None = Field(default=None, max_length=120)
    max_iterations: int = Field(default=3, ge=1, le=5)


@router.get("/status")
async def agent_status():
    providers = build_env_providers()
    return {
        "enabled": bool(providers),
        "providers": [provider.name for provider in providers],
        "runtime_verification_configured": bool(__import__("os").getenv("AGENT_RUNTIME_BASE_URL")),
    }


@router.post("/run")
async def run_agent_loop(data: AgentRunRequest, user=Depends(get_current_user_api)):
    if user.role.value not in {"admin", "moderator"}:
        raise HTTPException(status_code=403, detail="Только администратор или модератор может запускать инженерный цикл")

    providers = build_env_providers()
    if not providers:
        raise HTTPException(status_code=503, detail="AI-провайдеры не настроены: задайте API key и явную модель")

    task_id = data.task_id or f"web-{uuid.uuid4().hex[:12]}"
    try:
        report = build_execution_service(providers).run(
            task_id, data.objective, max_iterations=data.max_iterations
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "task_id": task_id,
        "status": report.status.value,
        "passed": report.passed,
        "iterations": report.iterations,
        "blocked_reasons": report.blocked_reasons,
        "results": [
            {
                "task_id": result.task_id,
                "role": result.role.value,
                "status": result.status.value,
                "summary": result.summary,
                "findings": result.findings,
                "evidence": result.evidence,
                "artifacts": result.artifacts,
                "metadata": result.metadata,
                "retryable": result.retryable,
            }
            for result in report.task_results
        ],
        "project_version": settings.APP_VERSION,
    }
