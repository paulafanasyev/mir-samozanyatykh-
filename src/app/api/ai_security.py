from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from app.core.rate_limit import limiter
from app.services.ai_security_gateway import chat, inspect_input, AISecurityError, routes

router = APIRouter(prefix="/api/ai", tags=["ai-security"])

class AgentRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=12000)
    system: str = Field("", max_length=6000)

class DocumentPrecheck(BaseModel):
    text: str = Field(..., min_length=1, max_length=30000)

@router.get("/status")
async def status():
    return {"gateway": "enabled", "routes": [r.name for r in routes()], "offline_fallback": True}

@router.post("/chat")
@limiter.limit("20/minute")
async def safe_chat(request: Request, payload: AgentRequest):
    try:
        return await chat(payload.message, system=payload.system)
    except AISecurityError as exc:
        return {"ok": False, "blocked": True, "mode": "offline", "reason": str(exc)}

@router.post("/document/precheck")
@limiter.limit("10/minute")
async def document_precheck(request: Request, payload: DocumentPrecheck):
    """Deterministic first pass before optional AI analysis."""
    text = payload.text
    flags = []
    if len(text) < 40: flags.append("Документ содержит мало текста для уверенной проверки")
    if "паспорт" in text.lower() and not any(ch.isdigit() for ch in text): flags.append("Похоже, отсутствуют цифровые реквизиты")
    if re.search(r"ignore\s+(all|previous)\s+instructions", text, re.I): flags.append("Обнаружены инструкции, не относящиеся к содержанию документа")
    return {"ok": True, "safe_for_ai": not flags, "flags": flags, "next_step": "human_review" if flags else "ai_analysis"}

import re
