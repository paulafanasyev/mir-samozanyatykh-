"""Svetlana API: guarded online mode plus deterministic offline fallback."""
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
import re, json
from pathlib import Path
from datetime import datetime, timezone
from app.core.rate_limit import limiter
from app.services.local_svetlana import answer_local, local_status
from app.services.agent_guard import inspect
from app.services.agent_tools import policy_for
from app.services.ai_router import chat_online, online_status
from app.core.config import settings

router=APIRouter(prefix="/api/svetlana",tags=["svetlana"])

class ChatRequest(BaseModel):
    message:str=Field(...,min_length=1,max_length=8000)
    context:str|None=Field(None,max_length=4000)
    confirmation:bool=False

class LegacyAskRequest(BaseModel):
    question:str=Field(...,min_length=1,max_length=8000)

def _knowledge()->dict:
    path=Path(__file__).resolve().parents[2]/"static"/"svetlana_knowledge_v6.json"
    try:return json.loads(path.read_text(encoding="utf-8"))
    except(OSError,json.JSONDecodeError):return {}

def _log_chat(message:str,response:str,context:str|None=None)->None:
    try:
        import redis
        client=redis.Redis.from_url(settings.REDIS_URL,decode_responses=True,socket_connect_timeout=.5,socket_timeout=.5)
        payload=json.dumps({"ts":datetime.now(timezone.utc).isoformat(),"message":message[:8000],"response":response[:12000],"context":context},ensure_ascii=False)
        client.rpush("svetlana:chatlog",payload); client.ltrim("svetlana:chatlog",-5000,-1); client.expire("svetlana:chatlog",60*60*24*90)
    except Exception: pass

def _actions(content:str)->list[dict]:
    # Model output is data, never an authorization source. Only explicitly
    # allowlisted, non-side-effecting navigation is exposed to the client.
    actions=[]
    for path in re.findall(r"NAVIGATE:(/[-\w]+)",content):
        if path in {"/dashboard","/contracts","/calendar","/tasks","/clients","/deals","/invoices","/accounting","/receipt-check","/integrations","/docs","/notifications","/profile","/svetlana","/jobs","/marketplace","/calculator"} and policy_for("navigate"):
            actions.append({"type":"navigate","path":path})
    return actions

@router.get("/status")
async def svetlana_status()->dict:
    return {**local_status(),"online":online_status()}

@router.get("/categories")
async def svetlana_categories()->dict:
    topics=_knowledge().get("topics",{}); items=[]
    if isinstance(topics,dict):
        for key,value in topics.items():
            if isinstance(value,dict):items.append({"key":key,"title":value.get("title",key)})
    return {"categories":items}

@router.post("/chat")
@limiter.limit("30/minute")
async def svetlana_chat(request:Request,payload:ChatRequest):
    guard=inspect(payload.message)
    if not guard.allowed:
        return {"response":"Я не могу выполнить этот запрос: обнаружена попытка обойти правила безопасности.","mode":"blocked","provider":"security-gateway","risk":guard.risk,"reasons":list(guard.reasons),"actions":[]}
    if guard.requires_confirmation and not payload.confirmation:
        return {"response":"Этот запрос может изменить данные или выполнить внешнее действие. Подтвердите действие явно.","mode":"confirmation_required","provider":"security-gateway","risk":guard.risk,"reasons":list(guard.reasons),"actions":[]}
    content=await chat_online(guard.sanitized_message,payload.context)
    mode="online" if content else "offline"
    if not content: content=answer_local(guard.sanitized_message,payload.context)
    _log_chat(guard.sanitized_message,content,payload.context)
    return {"response":content,"mode":mode,"provider":"openai-compatible" if mode=="online" else "local","risk":guard.risk,"actions":_actions(content)}

@router.post("/ask")
@limiter.limit("30/minute")
async def svetlana_legacy_ask(request:Request,payload:LegacyAskRequest):
    guard=inspect(payload.question)
    if not guard.allowed:
        return {"answer":"Запрос заблокирован шлюзом безопасности.","response":"Запрос заблокирован шлюзом безопасности.","mode":"blocked","provider":"security-gateway","actions":[]}
    content=answer_local(guard.sanitized_message,None)
    _log_chat(guard.sanitized_message,content,None)
    return {"answer":content,"response":content,"mode":"offline","provider":"local","actions":_actions(content)}
