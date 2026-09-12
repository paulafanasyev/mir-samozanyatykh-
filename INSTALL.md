# Установка и запуск «Мир Самозанятых» со Светланой NextGen

## 🚀 Быстрый старт

### 1. Установка зависимостей
```bash
pip install fastapi uvicorn sqlalchemy python-jose passlib python-multipart
```

### 2. Запуск сервера
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Открыть в браузере
- Главная: http://localhost:8000/
- Дашборд: http://localhost:8000/dashboard

## 🤖 Светлана NextGen

### Режимы работы AI:

#### Бесплатный режим (офлайн)
- Использует локальную модель **Svetlana-2.0**
- Работает без интернета
- Не требует API ключей

**Установка локальной модели:**
1. Скачайте модель в формате GGUF (например, Llama-3-8B или Mistral-7B)
2. Переименуйте в `svetlana-2.0.gguf`
3. Поместите в папку `/workspace/models/`
4. Установите библиотеку: `pip install llama-cpp-python`

```bash
# Пример для Linux/Mac
pip install llama-cpp-python
# Модель автоматически загрузится при наличии файла
```

#### Premium режим (онлайн)
- Использует внешние API (AnyModel, APINEX)
- Более качественные ответы
- Требует API ключи

**Настройка API ключей:**
Добавьте в GitHub Secrets или `.env` файл:
```
ANYMODEL_API_KEY=your_key_here
# или
APINEX_API_KEY=your_key_here
```

## 📁 Структура проекта

```
/workspace/
├── app/
│   ├── main.py              # FastAPI приложение
│   └── local_ai_engine.py   # Локальный AI движок
├── static/
│   ├── js/                  # JavaScript модули Светланы
│   │   ├── avatar-state.js
│   │   ├── canvas-avatar.js
│   │   ├── image-avatar.js
│   │   ├── avatar-renderer.js
│   │   ├── lip-sync.js
│   │   └── svetlana-main.js
│   ├── images/svetlana/     # Изображения аватара
│   └── models/svetlana/     # 3D модели (GLB/GLTF)
├── templates/
│   └── index.html           # Главная страница
├── docs/
│   └── svetlana-nextgen.md  # Документация
├── scripts/blender/
│   └── create_svetlana_avatar.py  # Скрипт для 3D модели
└── models/                  # Папка для AI моделей
    └── svetlana-2.0.gguf    # (опционально)
```

## 🎯 Функционал Светланы

### Состояния:
- **IDLE** — готова к общению
- **LISTENING** — слушает пользователя
- **THINKING** — обрабатывает запрос
- **SPEAKING** — отвечает с анимацией губ
- **ERROR** — ошибка

### Возможности:
- Голосовой ввод (Web Speech API)
- Озвучка ответов (TTS)
- Lip-sync синхронизация
- Light/Dark темы
- Адаптивный дизайн

## 🧪 Тестирование

Проверка backend:
```bash
python -c "from app.main import app; print('Backend OK')"
```

Проверка JS:
```bash
node --check static/js/*.js
```

Проверка AI:
```bash
python -c "from app.local_ai_engine import local_engine; print(local_engine.get_status())"
```

## 📝 Лицензия
Проект «Мир Самозанятых» — платформа для самозанятых России.
