#!/bin/bash
# Startup script for Render.com
# MIR Samozanyatykh v8.4 - ANO TsPS INN 9724016805

set -e

echo "Starting MIR Samozanyatykh v8.4 on Render.com"
echo "Date: $(date)"
echo "Environment: ${ENVIRONMENT:-production}"

# Create directories
mkdir -p /app/uploads /app/logs /app/data

# Run migrations
echo "Running database migrations..."
alembic upgrade head || echo "Migration warning (first deploy)"

# Seed database
echo "Seeding database..."
python seed.py || echo "Seed warning (already seeded)"

# Start app
echo "Starting uvicorn on port ${PORT:-8000}"
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
