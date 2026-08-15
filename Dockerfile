# Dockerfile - MIR Samozanyatykh v8.4
# Optimized for Render.com deployment
# ANO TsPS INN 9724016805

FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY seed.py .
COPY startup.sh .

# Create directories
RUN mkdir -p uploads logs data

# Make startup executable
RUN chmod +x startup.sh

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/health || exit 1

EXPOSE 8000

CMD ["./startup.sh"]
