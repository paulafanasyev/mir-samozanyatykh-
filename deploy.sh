#!/bin/bash
# Deploy script for Mir Samozanyatykh v7.9
# ANO TsPS INN 9724016805
# Usage: ./deploy.sh [environment]
# Environments: production (default), staging, dev

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ENV=${1:-production}
APP_NAME="mir-samozanyatykh"
VERSION="7.9.0"
DOCKER_COMPOSE_FILE="docker-compose.yml"

log() {
    echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    command -v docker >/dev/null 2>&1 || error "Docker is required but not installed"
    command -v docker-compose >/dev/null 2>&1 || error "Docker Compose is required but not installed"
    command -v git >/dev/null 2>&1 || error "Git is required but not installed"

    # Check .env file
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            warn ".env not found, copying from .env.example"
            cp .env.example .env
            warn "Please edit .env with your actual values before deploying!"
            exit 1
        else
            error ".env file not found and .env.example is missing"
        fi
    fi

    # Validate SECRET_KEY
    SECRET_KEY=$(grep "SECRET_KEY" .env | cut -d= -f2 | tr -d '"' || true)
    if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "change-me-in-production" ]; then
        error "SECRET_KEY is not set or is default value. Please set a strong SECRET_KEY in .env"
    fi

    success "Prerequisites OK"
}

# Backup database
backup_database() {
    log "Creating database backup..."

    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    if docker-compose ps | grep -q postgres; then
        docker-compose exec -T postgres pg_dump \
            -U "${POSTGRES_USER:-mir_user}" \
            -d "${POSTGRES_DB:-mir_samozanyatykh}" \
            > "$BACKUP_DIR/db_backup.sql" 2>/dev/null || warn "Could not backup database, continuing..."
        success "Database backup saved to $BACKUP_DIR/db_backup.sql"
    else
        warn "PostgreSQL container not running, skipping backup"
    fi
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."

    docker-compose run --rm backend alembic upgrade head || error "Migrations failed"
    success "Migrations completed"
}

# Build and deploy
build_and_deploy() {
    log "Building and deploying $APP_NAME v$VERSION ($ENV)..."

    # Pull latest code if in production
    if [ "$ENV" = "production" ]; then
        log "Pulling latest code from git..."
        git pull origin main || warn "Could not pull latest code"
    fi

    # Build containers
    log "Building Docker containers..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" build --no-cache || error "Build failed"

    # Stop existing containers
    log "Stopping existing containers..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans || true

    # Start new containers
    log "Starting containers..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d || error "Failed to start containers"

    success "Containers started"
}

# Health check
health_check() {
    log "Running health checks..."

    MAX_RETRIES=30
    RETRY_DELAY=2

    for i in $(seq 1 $MAX_RETRIES); do
        if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
            success "Backend is healthy"
            break
        fi

        if [ $i -eq $MAX_RETRIES ]; then
            error "Health check failed after $MAX_RETRIES attempts"
        fi

        log "Waiting for backend... ($i/$MAX_RETRIES)"
        sleep $RETRY_DELAY
    done

    # Check frontend
    if curl -sf http://localhost:3000 >/dev/null 2>&1; then
        success "Frontend is accessible"
    else
        warn "Frontend health check failed (may need more time)"
    fi

    # Check PostgreSQL
    if docker-compose exec -T postgres pg_isready -U "${POSTGRES_USER:-mir_user}" >/dev/null 2>&1; then
        success "PostgreSQL is ready"
    else
        warn "PostgreSQL health check failed"
    fi

    # Check Redis
    if docker-compose exec -T redis redis-cli ping | grep -q PONG; then
        success "Redis is ready"
    else
        warn "Redis health check failed"
    fi
}

# Cleanup
cleanup() {
    log "Cleaning up..."

    # Remove dangling images
    docker image prune -f >/dev/null 2>&1 || true

    # Remove old backups (keep last 10)
    if [ -d "backups" ]; then
        ls -t backups/ | tail -n +11 | xargs -I {} rm -rf "backups/{}" 2>/dev/null || true
    fi

    success "Cleanup completed"
}

# Show status
show_status() {
    echo ""
    echo -e "${GREEN}=================================${NC}"
    echo -e "${GREEN}  $APP_NAME v$VERSION deployed!${NC}"
    echo -e "${GREEN}=================================${NC}"
    echo ""
    echo -e "${BLUE}Environment:${NC} $ENV"
    echo -e "${BLUE}Backend:${NC}    http://localhost:8000"
    echo -e "${BLUE}Frontend:${NC}   http://localhost:3000"
    echo -e "${BLUE}API Docs:${NC}   http://localhost:8000/docs"
    echo -e "${BLUE}Health:${NC}     http://localhost:8000/health"
    echo ""
    echo -e "${BLUE}Docker containers:${NC}"
    docker-compose ps
    echo ""
    echo -e "${YELLOW}Logs:${NC} docker-compose logs -f"
    echo -e "${YELLOW}Stop:${NC}  docker-compose down"
}

# Rollback function
rollback() {
    error "Deployment failed! Rolling back..."
    docker-compose down || true
    # Restore from backup if available
    LATEST_BACKUP=$(ls -t backups/*/db_backup.sql 2>/dev/null | head -1 || true)
    if [ -n "$LATEST_BACKUP" ]; then
        log "Restoring database from $LATEST_BACKUP..."
        docker-compose up -d postgres
        sleep 5
        docker-compose exec -T postgres psql -U "${POSTGRES_USER:-mir_user}" -d "${POSTGRES_DB:-mir_samozanyatykh}" < "$LATEST_BACKUP" || warn "Restore failed"
    fi
    exit 1
}

# Main deployment flow
main() {
    echo -e "${GREEN}=================================${NC}"
    echo -e "${GREEN}  $APP_NAME Deploy Script v$VERSION${NC}"
    echo -e "${GREEN}=================================${NC}"
    echo ""

    # Set trap for rollback on error
    trap rollback ERR

    check_prerequisites
    backup_database
    build_and_deploy
    run_migrations
    health_check
    cleanup
    show_status

    success "Deployment completed successfully!"
}

# Handle commands
case "${1:-deploy}" in
    deploy)
        main
        ;;
    backup)
        check_prerequisites
        backup_database
        ;;
    migrate)
        check_prerequisites
        run_migrations
        ;;
    logs)
        docker-compose logs -f
        ;;
    stop)
        docker-compose down
        success "Containers stopped"
        ;;
    restart)
        docker-compose restart
        success "Containers restarted"
        ;;
    status)
        docker-compose ps
        ;;
    update)
        git pull origin main
        main
        ;;
    help|--help|-h)
        echo "Usage: ./deploy.sh [command]"
        echo ""
        echo "Commands:"
        echo "  deploy    Deploy the application (default)"
        echo "  backup    Create database backup"
        echo "  migrate   Run database migrations"
        echo "  logs      Show container logs"
        echo "  stop      Stop all containers"
        echo "  restart   Restart all containers"
        echo "  status    Show container status"
        echo "  update    Pull latest code and deploy"
        echo "  help      Show this help message"
        echo ""
        echo "Environments:"
        echo "  production (default)"
        echo "  staging"
        echo "  dev"
        ;;
    *)
        ENV=$1
        main
        ;;
esac
