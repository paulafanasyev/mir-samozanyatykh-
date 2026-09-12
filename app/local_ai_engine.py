"""
Local AI Engine for Svetlana-2.0
Загружает и выполняет инференс встроенной офлайн-модели.
Используется как основной движок для бесплатной версии.
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# Попытка импорта библиотек для локального инференса
# Для продакшена рекомендуется использовать llama-cpp-python или onnxruntime
try:
    # Пример использования llama-cpp-python (требует установки: pip install llama-cpp-python)
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False
    logging.warning("llama-cpp-python not installed. Local AI will use mock response until model is configured.")

logger = logging.getLogger(__name__)

class SvetlanaLocalEngine:
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or os.getenv("SVETLANA_MODEL_PATH", "models/svetlana-2.0.gguf")
        self.model: Optional[Any] = None
        self.is_loaded = False
        self.is_available = LLAMA_AVAILABLE
        
        # Путь к модели в проекте
        base_dir = Path(__file__).parent.parent
        self.full_model_path = base_dir / self.model_path
        
        if not self.is_available:
            logger.warning("Local AI library not found. Install llama-cpp-python to enable offline mode.")
        elif not self.full_model_path.exists():
            logger.warning(f"Model file not found at {self.full_model_path}. Offline mode disabled.")
        else:
            self.load_model()

    def load_model(self):
        """Загружает модель в память"""
        if not self.is_available:
            return
            
        if not self.full_model_path.exists():
            logger.error(f"Model file missing: {self.full_model_path}")
            return

        try:
            logger.info(f"Loading Svetlana-2.0 from {self.full_model_path}...")
            # Настройки для оптимизации под CPU/GPU
            self.model = Llama(
                model_path=str(self.full_model_path),
                n_ctx=2048,          # Контекст
                n_threads=4,         # Потоки CPU
                n_gpu_layers=0,      # 0 для CPU, >0 для GPU (если есть)
                verbose=False
            )
            self.is_loaded = True
            logger.info("Svetlana-2.0 loaded successfully!")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.is_loaded = False

    def generate_response(self, prompt: str, history: list = None) -> str:
        """Генерирует ответ используя локальную модель"""
        if not self.is_loaded or not self.model:
            return self._get_fallback_response(prompt)

        try:
            # Формирование промпта с учетом истории диалога (если нужно)
            # Формат промпта зависит от конкретной модели (Llama, Mistral, etc.)
            system_prompt = "Ты Светлана, полезный ассистент для самозанятых в России. Твои задачи: помогать с налогами, документами, поиском клиентов и планированием. Отвечай кратко, доброжелательно и по делу."
            
            full_prompt = f"<|system|>\n{system_prompt}</s>\n<|user|>\n{prompt}</s>\n<|assistant|>\n"
            
            output = self.model(
                full_prompt,
                max_tokens=512,
                stop=["</s>", "<|user|>"],
                echo=False,
                temperature=0.7,
                top_p=0.9
            )
            
            response_text = output['choices'][0]['text'].strip()
            return response_text if response_text else "Извините, я пока обдумываю ваш вопрос."
            
        except Exception as e:
            logger.error(f"Inference error: {e}")
            return "Произошла ошибка при обработке запроса локальной моделью."

    def _get_fallback_response(self, prompt: str) -> str:
        """Заглушка, если модель не загружена (для тестов интерфейса)"""
        logger.debug("Using fallback response")
        
        # Простая эвристика для демонстрации работы без модели
        p = prompt.lower()
        if "привет" in p or "здравствуй" in p:
            return "Здравствуйте! Я Светлана, ваш помощник. Чем могу помочь в работе?"
        elif "налог" in p or "нпд" in p:
            return "Как самозанятый, вы платите 4% с доходов от физлиц и 6% от юрлиц. Налог считается автоматически в приложении 'Мой налог'."
        elif "документ" in p or "договор" in p:
            return "Я могу помочь составить договор оказания услуг. Просто скажите, какие условия вам нужны."
        elif "клиент" in p or "заказ" in p:
            return "Для поиска клиентов рекомендую заполнить профиль в разделе 'Работа' и откликаться на заказы."
        else:
            return "Я понимаю вас. Чтобы я могла ответить точнее, убедитесь, что модель Svetlana-2.0 загружена в папку models/."

    def get_status(self) -> Dict[str, Any]:
        """Возвращает статус локальной модели"""
        return {
            "mode": "local",
            "loaded": self.is_loaded,
            "model_path": str(self.full_model_path),
            "library_available": self.is_available,
            "message": "Svetlana-2.0 Online" if self.is_loaded else "Model loading required"
        }

# Глобальный экземпляр движка
local_engine = SvetlanaLocalEngine()
