"""Svetlana local/offline API with knowledge and safe navigation actions."""
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.auth import get_current_user_optional
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models import SvetlanaChatMessage, User
from app.services.local_svetlana import answer_local, local_status
import re,json
from pathlib import Path
router=APIRouter(prefix="/api/svetlana",tags=["svetlana"])
class ChatRequest(BaseModel):
 message:str=Field(...,min_length=1,max_length=8000);context:str|None=Field(None,max_length=4000)
def _knowledge()->dict:
 path=Path(__file__).resolve().parents[2]/"static"/"svetlana_knowledge_v6.json"
 try:return json.loads(path.read_text(encoding="utf-8"))
 except(OSError,json.JSONDecodeError):return {}
async def _save_message(db:AsyncSession,user_id:int,role:str,content:str)->None:db.add(SvetlanaChatMessage(user_id=user_id,role=role,content=content));await db.commit()
@router.get("/status")
async def svetlana_status()->dict:return local_status()
@router.get("/categories")
async def svetlana_categories()->dict:
 topics=_knowledge().get("topics",{});items=[]
 if isinstance(topics,dict):
  for key,value in topics.items():
   if isinstance(value,dict):items.append({"key":key,"title":value.get("title",key)})
 return {"categories":items}
@router.post("/chat")
@limiter.limit("30/minute")
async def svetlana_chat(request:Request,payload:ChatRequest,current_user:User|None=Depends(get_current_user_optional),db:AsyncSession=Depends(get_db)):
 if current_user:await _save_message(db,current_user.id,"user",payload.message)
 content=answer_local(payload.message,payload.context)
 if current_user:await _save_message(db,current_user.id,"assistant",content)
 allowed={"/dashboard","/contracts","/calendar","/tasks","/clients","/deals","/invoices","/accounting","/receipt-check","/integrations","/docs","/notifications","/profile","/svetlana","/jobs","/marketplace"}
 actions=[]
 for path in re.findall(r"NAVIGATE:(/[-\w]+)",content):
  if path in allowed:actions.append({"type":"navigate","path":path})
 return {"response":content,"user_id":current_user.id if current_user else None,"mode":"offline","provider":"local","actions":actions}
@router.get("/history")
async def svetlana_history(limit:int=100,db:AsyncSession=Depends(get_db),current_user:User|None=Depends(get_current_user_optional)):
 if not current_user:return {"items":[],"total":0,"persisted":False}
 limit=max(1,min(limit,200));result=await db.execute(select(SvetlanaChatMessage).where(SvetlanaChatMessage.user_id==current_user.id).order_by(SvetlanaChatMessage.created_at.desc()).limit(limit));rows=list(reversed(result.scalars().all()))
 return {"items":[{"id":r.id,"role":r.role,"content":r.content,"created_at":r.created_at} for r in rows],"total":len(rows),"persisted":True}
