# Mir Samozanykh v8.4.4 — production image
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
# The 3D Svetlana runtime is already part of this repository's frontend.
# Ship it into the API image so the server-rendered site can display the same
# authored GLB avatar instead of a replacement image or external iframe.
COPY frontend/public/svetlana/ ./static/svetlana3d/
COPY startup.sh .
COPY seed.py .
COPY tools/ ./tools/

RUN mkdir -p uploads logs data backups && chown -R appuser:appgroup /app && chmod +x startup.sh

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD sh -c 'curl -fsS "http://127.0.0.1:${PORT:-10000}/api/health" || exit 1'

EXPOSE 10000
ENTRYPOINT ["./startup.sh"]
