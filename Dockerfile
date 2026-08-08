# Мир Самозанятых v6.0 — Dockerfile
# Мультистейдж сборка для production

# ==================== Этап 1: Сборка ====================
FROM python:3.12-slim as builder

WORKDIR /app

# Установка системных зависимостей для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ==================== Этап 2: Продакшен ====================
FROM python:3.12-slim

LABEL maintainer="АНО ЦПС Мир Самозанятых <dev@mir-samozanyatykh.ru>"
LABEL version="6.0.0"
LABEL description="Платформа для самозанятых"

WORKDIR /app

# Системные зависимости (runtime only)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Копирование Python зависимостей из builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Копирование приложения
COPY app/ ./app/
COPY tests/ ./tests/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY pyproject.toml .
COPY pytest.ini .

# Создание директорий для данных
RUN mkdir -p \
    data/uploads \
    data/contracts \
    data/invoices \
    data/grants \
    logs \
    && chmod -R 755 data logs

# Создание непривилегированного пользователя
RUN groupadd -r appuser -g 1000 \
    && useradd -r -u 1000 -g appuser appuser \
    && chown -R appuser:appuser /app

USER appuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -fsS http://localhost:8000/health > /dev/null || exit 1

# Порт
EXPOSE 8000

# Запуск с 4 workers (оптимально для 2 CPU)
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--proxy-headers", "--forwarded-allow-ips", "*"]
