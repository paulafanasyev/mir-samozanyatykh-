"""Svetlana local/offline API with knowledge and safe navigation actions."""
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
import re, json
from pathlib import Path
from datetime import datetime, timezone

from app.core.rate_limit import limiter
from app.services.local_svetlana import answer_local, local_status
from app.core.config import settings

router=APIRouter(prefix="/api/svetlana",tags=["svetlana"])

class ChatRequest(BaseModel):
    message:str=Field(...,min_length=1,max_length=8000)
    context:str|None=Field(None,max_length=4000)

class LegacyAskRequest(BaseModel):
    question:str=Field(...,min_length=1,max_length=8000)

def _knowledge()->dict:
    path=Path(__file__).resolve().parents[2]/"static"/"svetlana_knowledge_v6.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except(OSError,json.JSONDecodeError):
        return {}

def _log_chat(message:str,response:str,context:str|None=None)->None:
    """Best-effort persistent dialog log for twice-daily Svetlana analysis."""
    try:
        import redis
        client=redis.Redis.from_url(settings.REDIS_URL,decode_responses=True,socket_connect_timeout=.5,socket_timeout=.5)
        payload=json.dumps({"ts":datetime.now(timezone.utc).isoformat(),"message":message[:8000],"response":response[:12000],"context":context},ensure_ascii=False)
        client.rpush("svetlana:chatlog",payload)
        client.ltrim("svetlana:chatlog",-5000,-1)
        client.expire("svetlana:chatlog",60*60*24*90)
    except Exception:
        pass

def _actions(content:str)->list[dict]:
    allowed={"/dashboard","/contracts","/calendar","/tasks","/clients","/deals","/invoices","/accounting","/receipt-check","/integrations","/docs","/notifications","/profile","/svetlana","/jobs","/marketplace","/calculator"}
    return [{"type":"navigate","path":path} for path in re.findall(r"NAVIGATE:(/[-\w]+)",content) if path in allowed]

@router.get("/status")
async def svetlana_status()->dict:
    return local_status()

@router.get("/categories")
async def svetlana_categories()->dict:
    topics=_knowledge().get("topics",{})
    items=[]
    if isinstance(topics,dict):
        for key,value in topics.items():
            if isinstance(value,dict): items.append({"key":key,"title":value.get("title",key)})
    return {"categories":items}

@router.post("/chat")
@limiter.limit("30/minute")
async def svetlana_chat(request:Request,payload:ChatRequest):
    content=answer_local(payload.message,payload.context)
    _log_chat(payload.message,content,payload.context)
    return {"response":content,"mode":"offline","provider":"local","actions":_actions(content)}

@router.post("/ask")
@limiter.limit("30/minute")
async def svetlana_legacy_ask(request:Request,payload:LegacyAskRequest):
    """Compatibility endpoint used by the global floating chat in base.html."""
    content=answer_local(payload.question,None)
    _log_chat(payload.question,content,None)
    return {"answer":content,"response":content,"mode":"offline","provider":"local","actions":_actions(content)}
