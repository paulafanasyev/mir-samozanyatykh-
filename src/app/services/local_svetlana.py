"""Offline Svetlana runtime backed by official-source knowledge bases and dynamic updates."""
from __future__ import annotations
import json,re,random
from pathlib import Path
from typing import Any
from app.core.config import settings

KNOWLEDGE_PATHS=(Path(__file__).resolve().parents[2]/"static"/"svetlana_knowledge_v4.json",Path(__file__).resolve().parents[2]/"static"/"svetlana_knowledge_v5.json",Path(__file__).resolve().parents[2]/"static"/"svetlana_knowledge_v6.json")

def _load_data()->list[dict[str,Any]]:
 result=[]
 for p in KNOWLEDGE_PATHS:
  try:data=json.loads(p.read_text(encoding="utf-8"))
  except(OSError,json.JSONDecodeError):continue
  result.append(data)
 return result

def _load_dynamic_topics()->list[dict[str,Any]]:
 try:
  import redis
  client=redis.Redis.from_url(settings.REDIS_URL,decode_responses=True,socket_connect_timeout=.4,socket_timeout=.4)
  raw=client.get("svetlana:dynamic_knowledge")
  if not raw:return []
  data=json.loads(raw)
  return [x for x in data if isinstance(x,dict)][:100] if isinstance(data,list) else []
 except Exception:
  return []

def _load_topics()->list[dict[str,Any]]:
 result=[]
 for data in _load_data():
  topics=data.get("topics",{})
  if isinstance(topics,dict):
   for key,value in topics.items():
    if isinstance(value,dict):result.append({"id":key,**value})
 result.extend({"id":str(x.get("id") or f"dynamic_{i}"),**x} for i,x in enumerate(_load_dynamic_topics()))
 return result

def _load_jokes()->list[str]:
 jokes=[]
 for data in _load_data():
  for item in data.get("jokes",[]):
   if isinstance(item,dict) and str(item.get("text","")).strip():jokes.append(str(item["text"]).strip())
 return list(dict.fromkeys(jokes))

def _tokens(text:str)->set[str]:return {t.lower() for t in re.findall(r"[\wА-Яа-яЁё]+",text) if len(t)>2}

def _rank_topics(message:str)->list[tuple[int,dict[str,Any]]]:
 q=_tokens(message);ranked=[]
 if not q:return ranked
 for topic in _load_topics():
  keywords=" ".join(str(x) for x in topic.get("keywords",[]));questions=" ".join(str(x) for x in topic.get("questions",[]));title=str(topic.get("title",""));content=str(topic.get("content",""));directions=" ".join(str(x) for x in topic.get("directions",[]));score=len(q&_tokens(keywords))*5+len(q&_tokens(questions))*7+len(q&_tokens(title))*3+min(5,len(q&_tokens(content+" "+directions)))
  if score:ranked.append((score,topic))
 ranked.sort(key=lambda x:x[0],reverse=True);return ranked

def _source_line(topic:dict[str,Any])->str:
 sources=[str(x) for x in topic.get("sources",[]) if str(x).strip()]
 return "\n\nИсточник: "+"; ".join(sources) if sources else ""

def _workflow_answer(message:str)->str|None:
 text=message.lower()
 if any(x in text for x in ("расскажи шутку","пошути","есть шутка","анекдот","юмор")):
  jokes=_load_jokes();return "😄 "+(random.choice(jokes) if jokes else "Самозанятый планирует отдых так же тщательно, как дедлайн: с надеждой и календарём.")
 if any(x in text for x in ("создай договор","составь договор","нужен договор","сделай договор","создай акт","составь акт")):return "Конечно. Я помогу собрать данные для договора или акта и передать их в модуль документов. Откройте раздел «Документы», выберите шаблон, заполните стороны, предмет, стоимость и сроки. Перед подписанием проверьте реквизиты и юридические условия.\n\nДокументы: /contracts"
 if any(x in text for x in ("добавь в календарь","поставь в календарь","в календарь","напомни мне","встречу")):return "Помогу организовать рабочий план. Для встречи или дедлайна нужны дата, время, название и при необходимости клиент/проект.\n\nNAVIGATE:/calendar"
 if any(x in text for x in ("добавь клиента","новый клиент","в crm","карточку клиента","сделку")):return "Для ведения клиента используйте CRM: карточка клиента → контактные данные → сделка → статус → следующая задача.\n\nNAVIGATE:/clients"
 if any(x in text for x in ("найди работу","найди ваканси","работа для самозан","подходящ","предложени")):return "Открою раздел предложений для самозанятых.\n\nNAVIGATE:/jobs"
 if any(x in text for x in ("маркетплейс","направлени","сфера деятельности","разместить ваканси","разместить услугу")):return "Для вакансий и услуг на Маркетплейсе используется единый справочник основных сфер деятельности. Для самозанятых он такой же, как для работодателей. Если вы презентуете свой проект или ищете партнёра, направление можно не выбирать.\n\nNAVIGATE:/marketplace"
 if any(x in text for x in ("налог посчитай","рассчитай налог","калькулятор","сколько налога")):return "Для ориентировочного расчёта НПД откройте калькулятор: /calculator. Ставка зависит от категории заказчика."
 return None

def answer_local(message:str,context:str|None=None)->str:
 message=str(message or "").strip()
 if not message:return "Сформулируйте вопрос — я помогу с НПД, документами, клиентами, календарём, поддержкой или развитием проекта."
 workflow=_workflow_answer(message)
 if workflow:return workflow
 ranked=_rank_topics(message)
 if ranked:
  selected=[topic for score,topic in ranked[:2] if score>=5];parts=[]
  for topic in selected:
   content=str(topic.get("content","")).strip()
   if topic.get("directions") and not content:content="\n".join(f"• {x}" for x in topic["directions"])
   parts.append(f"{str(topic.get('title','Ответ Светланы')).strip()}\n\n{content}{_source_line(topic)}")
  if parts:return "\n\n---\n\n".join(parts)
 text=message.lower()
 if any(word in text for word in ("привет","здравств","добрый","доброе")):return "Здравствуйте! Я Светлана — локальный помощник «Мира Самозанятых». Могу рассказать об организации и сайте, помочь с НПД, документами, клиентами, календарём, поддержкой и поиском предложений."
 return "Я Светлана, локальный ИИ-помощник «Мира Самозанятых». Я не буду придумывать нормативные сведения: если данных недостаточно, прямо скажу об этом."

def local_status()->dict[str,Any]:
 topics=_load_topics();return {"mode":"offline","provider":"local","network_required":False,"knowledge_base":[p.name for p in KNOWLEDGE_PATHS],"dynamic_knowledge":len([x for x in topics if str(x.get('id','')).startswith('dynamic_')]),"knowledge_topics":len(topics),"jokes":len(_load_jokes()),"llm_runtime":"local_knowledge_runtime","documents_repository":"genoffice","message":"Светлана работает локально. Динамические знания обновляются по расписанию из анализа диалогов."}
