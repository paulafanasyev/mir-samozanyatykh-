# Production Deployment Audit v8.4.18

## Исправлено
- `/api/health/ready` теперь проверяет PostgreSQL и Redis, а не возвращает безусловный `ready=true`.
- Redis health errors больше переводят общий health в degraded/503.
- `deploy.sh` приведён к `docker compose -f docker-compose.prod.yml` и реальным именам сервисов (`app`, `db`, `redis`, `nginx`).
- Удалены устаревшие проверки `/health` и `localhost:3000` из deployment script.
- Добавлен безопасный PostgreSQL backup/restore workflow с custom-format dump и SHA-256 для ручных backup-файлов.
- Production compose получил отдельный backup service с 14-дневной retention policy.
- Backup API больше не заявляет несуществующий Celery/RQ scheduler.
- Удалён дублирующий mount `/app/static` в nginx.
- Production secrets остаются обязательными через Compose variable validation.

## Проверки
- docker-compose.prod.yml YAML: PASS
- docker-compose.yml YAML: PASS
- Python compileall: PASS
- deploy.sh shell syntax: PASS

## Ограничения
Docker daemon/registry недоступны в текущей среде, поэтому фактический `docker compose build/up` не объявляется пройденным. Перед production запуском выполнить `./deploy.sh production deploy`, затем проверить `/api/health/ready`, backup и test restore на отдельной БД.
