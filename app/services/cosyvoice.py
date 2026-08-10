"""
Интеграция CosyVoice 3.0 через OpenRouter
Голосовой ассистент Светлана
"""

import base64
import io
from typing import Optional, BinaryIO

import httpx

from app.core.config import settings
from app.core.logging import logger


class CosyVoiceError(Exception):
    """Ошибка генерации речи"""
    pass


class CosyVoiceService:
    """
    Сервис для генерации речи через CosyVoice 3.0
    Использует OpenRouter API для доступа к модели
    """
    
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.api_url = settings.COSYVOICE_API_URL or "https://api.openrouter.ai/v1/audio/speech"
        self.model = settings.COSYVOICE_MODEL or "cosyvoice-v1"
        self.voice = settings.COSYVOICE_VOICE or "svetlana"
        
        if not self.api_key:
            logger.warning("OpenRouter API key not configured for CosyVoice")
    
    async def generate_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        format: str = "mp3",
    ) -> bytes:
        """
        Генерация речи из текста
        
        Args:
            text: Текст для озвучки (макс ~4000 символов)
            voice: Голос (svetlana, alexey, maria, etc.)
            speed: Скорость речи (0.5 - 2.0)
            format: Формат аудио (mp3, wav, opus)
        
        Returns:
            bytes: Аудио данные
        """
        if not self.api_key:
            raise CosyVoiceError("OpenRouter API key not configured")
        
        if len(text) > 4000:
            text = text[:4000]
            logger.warning("Text truncated to 4000 chars for TTS")
        
        voice = voice or self.voice
        
        payload = {
            "model": self.model,
            "input": text,
            "voice": voice,
            "speed": max(0.5, min(2.0, speed)),
            "response_format": format,
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": f"https://{settings.DOMAIN}",
            "X-Title": "Мир Самозанятых",
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload,
            )
            
            if response.status_code != 200:
                logger.error(f"CosyVoice error: {response.status_code} - {response.text[:500]}")
                raise CosyVoiceError(f"Speech generation failed: {response.status_code}")
            
            logger.info(f"CosyVoice generated speech: {len(response.content)} bytes")
            return response.content
    
    async def generate_svetlana_response(
        self,
        text: str,
        emotion: str = "neutral",  # neutral, friendly, professional, concerned
    ) -> bytes:
        """
        Генерация ответа Светланы с эмоциональной окраской
        
        Args:
            text: Текст ответа
            emotion: Эмоциональный тон
        """
        # Добавляем эмоциональные маркеры в текст
        emotion_prefixes = {
            "friendly": "Привет! ",
            "professional": "", 
            "concerned": "Обращаю ваше внимание: ",
            "neutral": "",
        }
        
        prefixed_text = emotion_prefixes.get(emotion, "") + text
        
        return await self.generate_speech(
            text=prefixed_text,
            voice="svetlana",
            speed=1.0 if emotion == "professional" else 1.1,
        )
    
    def get_audio_mime_type(self, format: str) -> str:
        """Получение MIME-типа для аудио формата"""
        types = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "opus": "audio/opus",
            "aac": "audio/aac",
        }
        return types.get(format, "audio/mpeg")
    
    async def stream_speech(self, text: str) -> Optional[bytes]:
        """Потоковая генерация речи (для WebSocket)"""
        try:
            return await self.generate_speech(text, format="opus")
        except CosyVoiceError as e:
            logger.error(f"Stream speech error: {e}")
            return None


# Singleton
cosyvoice_service = CosyVoiceService()
