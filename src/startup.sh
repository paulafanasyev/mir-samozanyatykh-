#!/bin/sh
set -eu

# Database schema must be current before the API accepts traffic.
python tools/production_preflight.py
alembic upgrade head

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers --forwarded-allow-ips="172.30.0.0/24" --no-server-header
