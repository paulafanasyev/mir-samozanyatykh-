#!/bin/sh
set -eu

ENV="${1:-production}"
COMPOSE="docker compose -f docker-compose.prod.yml"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
umask 077

need() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: $1 is required" >&2; exit 1; }; }
need docker
[ -f .env ] || { echo "ERROR: .env is required" >&2; exit 1; }

set -a
. ./.env
set +a

: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"
: "${REDIS_PASSWORD:?REDIS_PASSWORD is required}"
: "${SECRET_KEY:?SECRET_KEY is required}"
: "${BANK_ENCRYPTION_KEY:?BANK_ENCRYPTION_KEY is required}"
: "${GRAFANA_PASSWORD:?GRAFANA_PASSWORD is required}"

case "$ENV" in
  production) COMPOSE="$COMPOSE" ;;
  *) echo "Only production deployment is supported by this release script" >&2; exit 1 ;;
esac

backup() {
  mkdir -p "$BACKUP_DIR"
  chmod 700 "$BACKUP_DIR"
  ts="$(date -u +%Y%m%dT%H%M%SZ)"
  file="$BACKUP_DIR/db_${ts}.dump"
  $COMPOSE exec -T db pg_dump -Fc -U "${POSTGRES_USER:-mir_app}" -d "${POSTGRES_DB:-mir_samozanyatykh}" > "$file"
  chmod 600 "$file"
  sha256sum "$file" > "$file.sha256"
  # Keep 14 backup sets.
  ls -1t "$BACKUP_DIR"/db_*.dump 2>/dev/null | tail -n +15 | while read -r old; do rm -f "$old" "$old.sha256"; done
  echo "Backup: $file"
}

health() {
  i=0
  while [ "$i" -lt 60 ]; do
    if $COMPOSE exec -T app curl -fsS http://127.0.0.1:8000/api/health/ready >/dev/null 2>&1; then
      echo "Backend ready"
      return 0
    fi
    i=$((i+1)); sleep 2
  done
  echo "ERROR: backend readiness timeout" >&2
  $COMPOSE ps
  exit 1
}

case "${2:-deploy}" in
  backup) $COMPOSE up -d db; backup ;;
  restore)
    file="${3:-}"
    [ -n "$file" ] && [ -f "$file" ] || { echo "Usage: ./deploy.sh production restore backups/db_*.dump" >&2; exit 1; }
    $COMPOSE up -d db
    PGPASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set}" $COMPOSE exec -T db pg_restore --clean --if-exists --no-owner --no-privileges -U "${POSTGRES_USER:-mir_app}" -d "${POSTGRES_DB:-mir_samozanyatykh}" < "$file"
    ;;
  deploy)
    $COMPOSE up -d db redis
    # Best-effort pre-release backup. Fresh databases have no application tables yet.
    if $COMPOSE exec -T db pg_isready -U "${POSTGRES_USER:-mir_app}" -d "${POSTGRES_DB:-mir_samozanyatykh}" >/dev/null 2>&1; then
      if $COMPOSE exec -T db psql -U "${POSTGRES_USER:-mir_app}" -d "${POSTGRES_DB:-mir_samozanyatykh}" -tAc "SELECT to_regclass('public.alembic_version')" 2>/dev/null | grep -q alembic_version; then
        backup
      fi
    fi
    $COMPOSE up -d --build
    $COMPOSE exec -T app alembic upgrade head
    health
    echo "Deployment completed"
    ;;
  stop) $COMPOSE down ;;
  restart) $COMPOSE restart ;;
  status) $COMPOSE ps ;;
  logs) $COMPOSE logs -f ;;
  *) echo "Usage: ./deploy.sh production [deploy|backup|restore <dump>|stop|restart|status|logs]" >&2; exit 1 ;;
esac
