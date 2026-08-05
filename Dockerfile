FROM python:3.12-slim

LABEL maintainer="IT Laboratory <it-laboratory@bk.ru>"
LABEL version="4.2"
LABEL description="Мир Самозанятых — платформа для самозанятых"

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание непривилегированного пользователя
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

WORKDIR /app

# Копирование зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Создание директорий для данных
RUN mkdir -p /app/data /app/letsencrypt /app/logs \
    && chown -R appuser:appgroup /app

# Переключение на непривилегированного пользователя
USER appuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

EXPOSE 8000

CMD ["python", "server.py"]
