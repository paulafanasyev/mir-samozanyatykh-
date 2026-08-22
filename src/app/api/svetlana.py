"""Svetlana local/offline API with knowledge and safe navigation actions."""
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
import re, json
from pathlib import Path
from app.core.rate_limit import limiter
from app.services.local_svetlana import answer_local, local_status

router=APIRouter(prefix="/api/svetlana",tags=["svetlana"])

class ChatRequest(BaseModel):
    message:str=Field(...,min_length=1,max_length=8000)
    context:str|None=Field(None,max_length=4000)

def _knowledge()->dict:
    path=Path(__file__).resolve().parents[2]/"static"/"svetlana_knowledge_v6.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except(OSError,json.JSONDecodeError):
        return {}

@router.get("/status")
async def svetlana_status()->dict:
    return local_status()

@router.get("/categories")
async def svetlana_categories()->dict:
    topics=_knowledge().get("topics",{})
    items=[]
    if isinstance(topics,dict):
        for key,value in topics.items():
            if isinstance(value,dict):
                items.append({"key":key,"title":value.get("title",key)})
    return {"categories":items}

@router.post("/chat")
@limiter.limit("30/minute")
async def svetlana_chat(request:Request,payload:ChatRequest):
    """Public text chat must work even when DB/session storage is unavailable.
    Conversation persistence is deliberately handled separately by authenticated
    history features; the assistant itself is local/offline and must not depend
    on a database round-trip just to answer a question.
    """
    content=answer_local(payload.message,payload.context)
    allowed={"/dashboard","/contracts","/calendar","/tasks","/clients","/deals","/invoices","/accounting","/receipt-check","/integrations","/docs","/notifications","/profile","/svetlana","/jobs","/marketplace","/calculator"}
    actions=[]
    for path in re.findall(r"NAVIGATE:(/[-\w]+)",content):
        if path in allowed:
            actions.append({"type":"navigate","path":path})
    return {"response":content,"mode":"offline","provider":"local","actions":actions}
