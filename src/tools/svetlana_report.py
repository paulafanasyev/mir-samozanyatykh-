"""Twice-daily Svetlana dialog analysis.

Reads the Redis chat buffer, creates a report, and updates dynamic knowledge.
The job is intentionally idempotent and stores reports/knowledge in Redis because
Render cron containers have ephemeral filesystems.
"""
from __future__ import annotations
import hashlib, json, os, re
from collections import Counter
from datetime import datetime, timezone

import httpx
import redis

REDIS_URL=os.getenv("REDIS_URL","")
OPENROUTER_API_KEY=os.getenv("OPENROUTER_API_KEY","")
MODEL=os.getenv("OPENROUTER_MODEL_DEFAULT","anthropic/claude-3.5-sonnet")


def redact(text:str)->str:
    text=re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}","[email]",text)
    text=re.sub(r"(?<!\d)\d{10,12}(?!\d)","[number]",text)
    text=re.sub(r"\+?\d[\d\s().-]{8,}\d","[phone]",text)
    return text[:12000]


def normalize_question(text:str)->str:
    value=re.sub(r"\s+"," ",redact(text).strip().lower())
    return value[:500]


def heuristic(items:list[dict])->dict:
    counts=Counter(normalize_question(x.get("message","")) for x in items if x.get("message"))
    top=[{"question":q,"count":n} for q,n in counts.most_common(10)]
    additions=[]
    for q,n in counts.most_common(8):
        if n<2: continue
        candidates=[x for x in items if normalize_question(x.get("message",""))==q and x.get("response")]
        if not candidates: continue
        answer=candidates[-1]["response"]
        ident="auto_"+hashlib.sha1(q.encode()).hexdigest()[:12]
        additions.append({"id":ident,"title":"Частый вопрос Светлане","keywords":re.findall(r"[А-Яа-яЁёA-Za-z]{4,}",q)[:15],"questions":[q],"content":redact(answer),"sources":[]})
    return {"summary":"Автоматический отчёт без внешнего ИИ: повторяющиеся вопросы выделены по частоте.","top_questions":top,"knowledge_additions":additions}


def llm_analyze(items:list[dict])->dict|None:
    if not OPENROUTER_API_KEY or not items:return None
    transcript="\n\n".join(f"Пользователь: {redact(x.get('message',''))}\nСветлана: {redact(x.get('response',''))}" for x in items[-300:])
    prompt=("Ты аналитик базы знаний ассистента Светланы проекта «Мир Самозанятых». "
            "Проанализируй диалоги, не придумывай нормативные факты. Верни ТОЛЬКО JSON с полями "
            "summary (строка), top_questions (массив объектов question/count), "
            "knowledge_additions (массив объектов id,title,keywords,questions,content,sources). "
            "Добавляй в knowledge_additions только то, что можно безопасно вывести из диалогов или "
            "уже присутствующих ответов; для нормативных утверждений оставляй sources пустым, если "
            "источник не указан в диалоге.\n\nДИАЛОГИ:\n"+transcript)
    try:
        with httpx.Client(timeout=35) as client:
            r=client.post("https://openrouter.ai/api/v1/chat/completions",headers={"Authorization":f"Bearer {OPENROUTER_API_KEY}","Content-Type":"application/json"},json={"model":MODEL,"temperature":0.1,"messages":[{"role":"user","content":prompt}]})
            r.raise_for_status()
            content=r.json()["choices"][0]["message"]["content"]
        content=re.sub(r"^```json\s*|\s*```$","",content.strip(),flags=re.I)
        data=json.loads(content)
        if isinstance(data,dict):return data
    except Exception as exc:
        print(f"LLM analysis failed: {type(exc).__name__}: {exc}")
    return None


def main()->None:
    if not REDIS_URL:
        raise SystemExit("REDIS_URL is required")
    client=redis.Redis.from_url(REDIS_URL,decode_responses=True,socket_connect_timeout=3,socket_timeout=10)
    raw=client.lrange("svetlana:chatlog",0,-1)
    items=[]
    for row in raw:
        try:
            data=json.loads(row)
            if isinstance(data,dict):items.append(data)
        except Exception:continue
    now=datetime.now(timezone.utc).isoformat()
    report=llm_analyze(items) or heuristic(items)
    report["generated_at"]=now
    report["messages_analyzed"]=len(items)

    reports=[]
    old=client.lrange("svetlana:reports",-89,-1)
    for row in old:
        try:reports.append(json.loads(row))
        except Exception:pass
    reports.append(report)
    client.delete("svetlana:reports")
    for row in reports[-90:]:client.rpush("svetlana:reports",json.dumps(row,ensure_ascii=False))
    client.expire("svetlana:reports",60*60*24*180)

    current=[]
    try:
        stored=json.loads(client.get("svetlana:dynamic_knowledge") or "[]")
        if isinstance(stored,list):current=stored
    except Exception:pass
    additions=report.get("knowledge_additions") if isinstance(report.get("knowledge_additions"),list) else []
    merged={str(x.get("id")):x for x in current if isinstance(x,dict) and x.get("id")}
    for item in additions:
        if not isinstance(item,dict):continue
        if not item.get("content") or not item.get("questions"):continue
        item={k:item.get(k) for k in ("id","title","keywords","questions","content","sources","directions") if item.get(k) is not None}
        item["id"]=str(item.get("id") or "auto_"+hashlib.sha1(json.dumps(item,ensure_ascii=False).encode()).hexdigest()[:12])
        merged[item["id"]]=item
    dynamic=list(merged.values())[-100:]
    client.set("svetlana:dynamic_knowledge",json.dumps(dynamic,ensure_ascii=False),ex=60*60*24*365)
    client.set("svetlana:last_report",json.dumps(report,ensure_ascii=False),ex=60*60*24*180)
    print(json.dumps({"generated_at":now,"messages_analyzed":len(items),"knowledge_entries":len(dynamic)},ensure_ascii=False))


if __name__=="__main__":main()
