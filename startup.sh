#!/bin/bash
# Startup script for Render.com
# Запускает миграции и сервер

set -e

echo "========================================"
echo "  Мир Самозанятых — Starting up"
echo "  Environment: $ENVIRONMENT"
echo "  Version: 8.6.5"
echo "========================================"

# Run database migrations
echo "[1/3] Running Alembic migrations..."
alembic upgrade head || {
    echo "WARNING: Migration failed, attempting to create tables..."
    python -c "
import asyncio
from app.core.database import engine, Base
async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(init())
"
}

# Seed data on first run (optional)
if [ "$SEED_DATA" = "true" ]; then
    echo "[2/3] Seeding database..."
    python -c "
import asyncio
from app.core.database import init_db
asyncio.run(init_db())
" || echo "WARNING: Seed failed, continuing..."
else
    echo "[2/3] Skipping seed (set SEED_DATA=true for first run)"
fi

# Start application
echo "[3/3] Starting Uvicorn server..."
echo "Server will be available at: http://0.0.0.0:$PORT"
echo "Health check: /health"
echo "========================================"

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --workers 1 \
    --loop uvloop \
    --http h11 \
    --proxy-headers \
    --forwarded-allow-ips '*'
