# Mir Samozanykh v8.4.3 — production image
FROM python:3.12-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN groupadd --system appgroup && useradd --system --gid appgroup --create-home appuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY templates/ ./templates/
COPY static/ ./static/
COPY startup.sh .
COPY seed.py .
COPY tools/ ./tools/

RUN mkdir -p uploads logs data backups && chown -R appuser:appgroup /app && chmod +x startup.sh

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -fsS http://localhost:${PORT:-8000}/api/health || exit 1

EXPOSE 8000
ENTRYPOINT ["./startup.sh"]
