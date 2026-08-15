#!/bin/bash
# Startup script for Render.com
# Мир Самозанятых v8.4

set -e

echo "🚀 Starting Мир Самозанятых v8.4 on Render.com"
echo "📅 $(date)"

# Run database migrations
echo "📊 Running database migrations..."
alembic upgrade head || echo "⚠️ Migration warning (may be first deploy)"

# Create upload directory
mkdir -p /app/uploads /app/logs

# Start application
echo "🌐 Starting uvicorn server on port ${PORT:-8000}"
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
