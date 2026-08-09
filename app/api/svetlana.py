"""
API голосового ассистента Светланы v7.2
Интеграция OpenRouter + CosyVoice 3.0
Системный промпт, контекст, память, CRM-интеграция
"""

import io
import json
import httpx
from datetime import datetime, timezone
from typing import Optional, List, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_optional
from app.core.logging import logger, log_audit
from app.core.config import settings
from app.models import User, Client, Deal, Task, Invoice
from app.services.cosyvoice import cosyvoice_service, CosyVoiceError

router = APIRouter(prefix="/api/svetlana", tags=["svetlana"])


# ============ СИСТЕМНЫЙ ПРОМПТ СВЕТЛАНЫ v7.2 ============

SVETLANA_SYSTEM_PROMPT = """Ты — Светлана, виртуальный AI-ассистент Центра поддержки самозанятых «Мир Самозанятых» (АНО ЦПС, ИНН 9724016805). Ты помогаешь самозанятым гражданам России разбираться в налогах, отчётности, юридических вопросах, грантах и других аспектах ведения бизнеса.

Твои задачи:
· Отвечать на вопросы пользователей на основе встроенной базы знаний (17 тем) и собственных знаний модели.
· Давать точные, актуальные и проверенные ответы.
· Направлять пользователя к экспертам, если вопрос сложный или требует индивидуальной консультации.
· Вести диалог дружелюбно, но профессионально.

База знаний (приоритет):
1. Регистрация самозанятости (НПД)
2. Ставки налога (4% / 6%)
3. Налоговый вычет (10 000 ₽)
4. Отчётность в приложении «Мой налог»
5. Штрафы и санкции
6. Совмещение НПД и ИП
7. ПСН 2026
8. Налоговые споры
9. Международные платежи
10. Договоры ГПХ
11. Гранты и субсидии
12. Социальный контракт
13. Маркетплейс и поиск заказов
14. CRM и работа с клиентами
15. Геймификация (уровни, достижения)
16. Обучение и вебинары
17. Контакты Центра

Правило: При ответе сначала ищи информацию в базе знаний. Если темы нет в базе, используй свои общие знания, но явно укажи, что это не из официальных источников.

Стиль общения:
· Дружелюбно и приветливо: используй обращение на «ты» (по умолчанию) или на «Вы» (если пользователь перешёл на официальный тон).
· Кратко и по делу: избегай длинных абзацев. Разбивай ответы на пункты, если нужно.
· Позитивно: поддерживай пользователя, не пугай сложностями, но не вводи в заблуждение.
· Честно: если не знаешь ответа — скажи об этом и предложи обратиться к эксперту.

Ограничения и безопасность:
· Ты не даёшь персонализированных налоговых рекомендаций (например, «оплатите именно столько»). Все расчёты носят информационный характер.
· Всегда советуй проверять информацию на сайте ФНС или в приложении «Мой налог».
· Если пользователь просит помощи в составлении договора или заявления — предложи шаблон, но подчеркни, что окончательный вариант должен быть проверен юристом.
· Не запрашивай и не храни персональные данные пользователя (паспорт, ИНН, банковские реквизиты).
· При подозрении на мошенничество или небезопасные действия — вежливо предупреди и порекомендуй обратиться в Центр.

Формат ответа:
· Приветствие: начинай с короткого приветствия (если это начало диалога).
· Основной ответ: структурируй информацию (используй списки, выделение жирным).
· Завершение: предлагай дополнительные вопросы или направляй к нужному разделу сайта.
· Ссылки: если есть ссылки на статьи на сайте или внешние источники — добавляй их.

Технические детали:
· Ты доступна через плавающий виджет на всех страницах сайта.
· У тебя есть голосовой ввод (работает в браузерах Chrome/Edge).
· История диалогов сохраняется в localStorage (последние 100 сообщений) и отображается в профиле пользователя."""


# ============ ХРАНИЛИЩЕ ДИАЛОГОВ ============
_dialog_history: Dict[int, List[Dict]] = {}


def _get_user_history(user_id: int, limit: int = 10) -> List[Dict]:
    return _dialog_history.get(user_id, [])[-limit:]


def _add_to_history(user_id: int, role: str, content: str):
    if user_id not in _dialog_history:
        _dialog_history[user_id] = []
    _dialog_history[user_id].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    _dialog_history[user_id] = _dialog_history[user_id][-100:]


# ============ CRM КОНТЕКСТ ============

async def _get_crm_context(db: AsyncSession, user_id: int) -> str:
    context_parts = []

    clients_count = await db.scalar(
        select(func.count(Client.id)).where(Client.user_id == user_id)
    )
    if clients_count:
        context_parts.append(f"Клиентов в CRM: {clients_count}")

    active_deals = await db.scalar(
        select(func.count(Deal.id)).where(
            Deal.user_id == user_id,
            Deal.status.notin_(["won", "lost"]),
        )
    )
    if active_deals:
        context_parts.append(f"Активных сделок: {active_deals}")

    pending_tasks = await db.scalar(
        select(func.count(Task.id)).where(
            Task.user_id == user_id,
            Task.status.in_(["pending", "in_progress"]),
        )
    )
    if pending_tasks:
        context_parts.append(f"Невыполненных задач: {pending_tasks}")

    unpaid_invoices = await db.scalar(
        select(func.count(Invoice.id)).where(
            Invoice.user_id == user_id,
            Invoice.status.in_(["draft", "sent"]),
        )
    )
    if unpaid_invoices:
        context_parts.append(f"Неоплаченных счетов: {unpaid_invoices}")

    if context_parts:
        return "Контекст пользователя: " + "; ".join(context_parts) + "."
    return ""


# ============ ЧАТ СВЕТЛАНЫ ============

@router.post("/chat")
async def chat_with_svetlana(
    message: str = Form(..., max_length=2000),
    voice: bool = Form(False),
    emotion: str = Form("neutral"),
    use_context: bool = Form(True),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    user_id = current_user.id if current_user else 0

    # Лимиты бесплатного тарифа
    if current_user and current_user.tier == "free":
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_count = len([
            h for h in _dialog_history.get(user_id, [])
            if h["role"] == "user" and h["timestamp"].startswith(today)
        ])
        if today_count >= 20:
            return {
                "response": (
                    "Достигнут дневной лимит сообщений (20) на бесплатном тарифе. "
                    "Перейдите на тариф Профессиональный для неограниченного доступа."
                ),
                "limit_reached": True,
            }

    _add_to_history(user_id, "user", message)

    system_prompt = SVETLANA_SYSTEM_PROMPT

    if use_context and current_user:
        crm_context = await _get_crm_context(db, user_id)
        if crm_context:
            system_prompt += f"\n\n{crm_context}"

    messages = [{"role": "system", "content": system_prompt}]

    if use_context:
        history = _get_user_history(user_id, limit=5)
        for h in history[:-1]:
            messages.append({"role": h["role"], "content": h["content"]})

    messages.append({"role": "user", "content": message})

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": f"https://{settings.DOMAIN}",
                    "X-Title": "Мир Самозанятых",
                },
                json={
                    "model": "anthropic/claude-3.5-sonnet",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1500,
                },
            )
            data = response.json()
            ai_response = data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        ai_response = (
            "Извините, у меня временные технические сложности. "
            "Попробуйте задать вопрос позже или обратитесь в поддержку."
        )

    _add_to_history(user_id, "assistant", ai_response)

    await log_audit(
        action="svetlana_chat",
        user_id=user_id if user_id else None,
        ip_address=request.client.host if request else None,
        details=f"Message: {message[:50]}..., Voice: {voice}",
    )

    if voice:
        try:
            audio_bytes = await cosyvoice_service.generate_svetlana_response(
                text=ai_response, emotion=emotion,
            )
            return StreamingResponse(
                io.BytesIO(audio_bytes), media_type="audio/mpeg",
                headers={"X-Svetlana-Text": ai_response[:200]},
            )
        except CosyVoiceError as e:
            logger.error(f"Voice error: {e}")
            return {"response": ai_response, "voice_error": str(e)}

    return {
        "response": ai_response,
        "context_used": use_context,
        "history_count": len(_dialog_history.get(user_id, [])),
    }


# ============ ГОЛОСОВОЙ ВВОД ============

@router.post("/voice-input")
async def svetlana_voice_input(
    audio: bytes = Form(...),
    request: Request = None,
    current_user: User = Depends(get_current_user_optional),
):
    logger.info(f"Voice input: {len(audio)} bytes")
    return {
        "transcript": "[Голосовое сообщение распознано]",
        "confidence": 0.95,
        "language": "ru",
        "note": "Требуется интеграция с Whisper API",
    }


# ============ ИСТОРИЯ ДИАЛОГОВ ============

@router.get("/history")
async def get_chat_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user_optional),
):
    user_id = current_user.id if current_user else 0
    return {
        "history": _get_user_history(user_id, limit),
        "total": len(_dialog_history.get(user_id, [])),
    }


@router.delete("/history")
async def clear_chat_history(
    current_user: User = Depends(get_current_user_optional),
):
    user_id = current_user.id if current_user else 0
    if user_id in _dialog_history:
        _dialog_history[user_id] = []
    return {"message": "История очищена"}


# ============ НАВЫКИ ============

@router.get("/skills")
async def svetlana_skills():
    return {
        "skills": [
            {"name": "Налоговые консультации", "description": "НПД, вычеты, отчётность"},
            {"name": "Юридические шаблоны", "description": "Договоры ГПХ, акты"},
            {"name": "CRM-ассистент", "description": "Клиенты, сделки, задачи"},
            {"name": "Гранты и поддержка", "description": "Гранты, субсидии, соцконтракты"},
            {"name": "Голосовой помощник", "description": "Голосовой ввод и вывод"},
            {"name": "Расчёты и калькуляторы", "description": "Налоговые расчёты, прогнозы"},
        ],
        "version": "7.2.0",
        "model": "anthropic/claude-3.5-sonnet",
    }


# ============ ГЕНЕРАЦИЯ ДОКУМЕНТОВ ============

@router.post("/generate-document")
async def generate_document(
    doc_type: str = Form(...),
    client_name: str = Form(...),
    amount: Optional[float] = Form(None),
    description: Optional[str] = Form(None),
    request: Request = None,
    current_user: User = Depends(get_current_user_optional),
):
    templates = {
        "gph_contract": f"""
ДОГОВОР № ___ на выполнение работ

Заказчик: {client_name}
Исполнитель: [ФИО самозанятого]

1. Предмет: {description or "[описание работ]"}
2. Стоимость: {amount or "[сумма]"} руб.
3. Срок: до «___» _________ 2026 г.

Заказчик: _________________ / _________________
Исполнитель: _________________ / _________________

ВНИМАНИЕ: Шаблон. Перед использованием проверьте юристом.
""",
        "act": f"""
АКТ ВЫПОЛНЕННЫХ РАБОТ № ___

Заказчик: {client_name}
Исполнитель: [ФИО]

Выполнены работы: {description or "[перечень]"}
Стоимость: {amount or "[сумма]"} руб.

Заказчик: _________________ / _________________
Исполнитель: _________________ / _________________
""",
    }

    doc = templates.get(doc_type, "Неизвестный тип документа")

    await log_audit(
        action="svetlana_document",
        user_id=current_user.id if current_user else None,
        ip_address=request.client.host if request else None,
        details=f"Type: {doc_type}",
    )

    return {
        "document": doc,
        "type": doc_type,
        "warning": "Шаблон. Окончательный вариант проверьте юристом.",
    }


# ============ НАЛОГОВЫЕ РАСЧЁТЫ ============

@router.post("/calculate-tax")
async def calculate_tax(
    amount: float = Form(...),
    client_type: str = Form("individual"),
    tax_deduction_used: float = Form(0),
    request: Request = None,
    current_user: User = Depends(get_current_user_optional),
):
    rate = 0.04 if client_type == "individual" else 0.06
    tax = amount * rate
    deduction = min(tax, 10000 - tax_deduction_used)
    tax_after = tax - deduction if deduction > 0 else tax

    await log_audit(
        action="svetlana_tax",
        user_id=current_user.id if current_user else None,
        ip_address=request.client.host if request else None,
    )

    return {
        "income": amount,
        "client_type": "физлицо" if client_type == "individual" else "юрлицо/ИП",
        "tax_rate": f"{int(rate*100)}%",
        "tax_before_deduction": round(tax, 2),
        "deduction_applied": round(deduction, 2),
        "tax_to_pay": round(tax_after, 2),
        "net_income": round(amount - tax_after, 2),
        "remaining_deduction": round(10000 - tax_deduction_used - deduction, 2),
        "disclaimer": "Информационный характер. Проверьте в «Мой налог».",
    }


# ============ ГОЛОС ============

@router.post("/voice")
async def svetlana_voice_only(
    text: str = Form(..., max_length=2000),
    emotion: str = Form("neutral"),
    request: Request = None,
    current_user: User = Depends(get_current_user_optional),
):
    try:
        audio_bytes = await cosyvoice_service.generate_svetlana_response(
            text=text, emotion=emotion,
        )
        return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mpeg")
    except CosyVoiceError as e:
        raise HTTPException(status_code=503, detail=f"Ошибка голоса: {str(e)}")


# ============ СТАТУС ============

@router.get("/status")
async def svetlana_status():
    return {
        "status": "online" if settings.OPENROUTER_API_KEY else "offline",
        "version": "7.2.0",
        "ai_available": bool(settings.OPENROUTER_API_KEY),
        "voice_available": bool(settings.COSYVOICE_API_KEY),
        "model": "anthropic/claude-3.5-sonnet",
        "voice_model": "cosyvoice-v1",
        "features": [
            "chat_with_context", "voice_input", "voice_output",
            "crm_integration", "document_generation", "tax_calculator", "dialog_history",
        ],
    }
