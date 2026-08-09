"""
API голосового ассистента Светланы
Интеграция OpenRouter + CosyVoice 3.0
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_optional
from app.core.logging import logger, log_audit
from app.models import User
from app.services.cosyvoice import cosyvoice_service, CosyVoiceError

router = APIRouter(prefix="/api/svetlana", tags=["svetlana"])


@router.post("/chat")
async def chat_with_svetlana(
    message: str = Form(..., max_length=2000),
    voice: bool = Form(False),
    emotion: str = Form("neutral"),  # neutral, friendly, professional, concerned
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """
    Чат с Светланой — AI-ассистентом для самозанятых
    
    - message: текст вопроса
    - voice: вернуть голосовой ответ (True) или текст (False)
    - emotion: эмоциональный тон ответа
    """
    user_id = current_user.id if current_user else None
    
    # Проверка лимитов для бесплатных пользователей
    if current_user and current_user.subscription_tier == "free":
        # TODO: проверка rate limit через Redis
        pass
    
    # Контекст для AI
    system_prompt = """Ты — Светлана, дружелюбный и профессиональный AI-ассистент для самозанятых на платформе «Мир Самозанятых» (АНО ЦПС, ИНН 9724016805).

Твои знания:
- Налоговое законодательство РФ для самозанятых (НПД)
- Оформление договоров ГПД, актов, счетов
- Бухгалтерия и отчётность самозанятых
- Гранты и поддержка для самозанятых
- Права и обязанности самозанятых

Правила:
- Отвечай кратко и по делу
- Если не знаешь — скажи честно
- Не давай юридических консультаций как юрист, а как информационный помощник
- Используй примеры из практики
- Будь вежливой и поддерживающей
- Отвечай на русском языке"""

    # Запрос к OpenRouter
    import httpx
    import json
    
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
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message},
                    ],
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
    
    # Аудит
    await log_audit(
        action="svetlana_chat",
        user_id=user_id,
        ip_address=request.client.host if request else None,
        details=f"Message length: {len(message)}, Voice: {voice}",
    )
    
    # Если запрошен голосовой ответ
    if voice:
        try:
            audio_bytes = await cosyvoice_service.generate_svetlana_response(
                text=ai_response,
                emotion=emotion,
            )
            
            return StreamingResponse(
                io.BytesIO(audio_bytes),
                media_type="audio/mpeg",
                headers={
                    "X-Svetlana-Text": ai_response[:200],  # первые 200 символов текста
                },
            )
            
        except CosyVoiceError as e:
            logger.error(f"Voice generation error: {e}")
            # Возвращаем текст если голос не удался
            return {"response": ai_response, "voice_error": str(e)}
    
    return {"response": ai_response}


@router.post("/voice")
async def svetlana_voice_only(
    text: str = Form(..., max_length=2000),
    emotion: str = Form("neutral"),
    request: Request = None,
    current_user: User = Depends(get_current_user_optional),
):
    """Генерация голоса Светланы из текста"""
    try:
        audio_bytes = await cosyvoice_service.generate_svetlana_response(
            text=text,
            emotion=emotion,
        )
        
        await log_audit(
            action="svetlana_voice",
            user_id=current_user.id if current_user else None,
            ip_address=request.client.host if request else None,
            details=f"Text length: {len(text)}",
        )
        
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",
        )
        
    except CosyVoiceError as e:
        logger.error(f"Voice generation error: {e}")
        raise HTTPException(status_code=503, detail=f"Ошибка генерации голоса: {str(e)}")


@router.get("/status")
async def svetlana_status():
    """Статус сервиса Светланы"""
    has_api_key = bool(settings.OPENROUTER_API_KEY)
    has_cosyvoice = bool(settings.COSYVOICE_API_KEY or settings.OPENROUTER_API_KEY)
    
    return {
        "status": "online" if has_api_key else "offline",
        "ai_available": has_api_key,
        "voice_available": has_cosyvoice,
        "model": "anthropic/claude-3.5-sonnet",
        "voice_model": "cosyvoice-v1",
        "voice_name": "svetlana",
    }


# Импорты в конце файла для избежания циклических зависимостей
import io
from app.core.config import settings
