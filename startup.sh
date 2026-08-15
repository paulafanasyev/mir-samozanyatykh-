#!/bin/bash
# Startup script for Render.com free tier
# Keeps the service alive by pinging healthcheck

echo "Starting Mir Samozanyatykh API..."

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Seed data if needed (first run)
if [ "$SEED_DATA" = "true" ]; then
    echo "Seeding database..."
    python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"
fi

# Start the application
echo "Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
