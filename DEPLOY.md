# Руководство по развёртыванию — Мир Самозанятых v6.0

## Требования

- **Сервер**: Ubuntu 22.04 LTS (минимум 2 CPU, 4 GB RAM, 20 GB SSD)
- **Домен**: зарегистрированный домен с DNS A-записью на сервер
- **Порты**: 80, 443 открыты

## Быстрый старт

```bash
# 1. Клонирование репозитория
git clone https://github.com/paulafanasyev/mir-samozanyatykh-.git
cd mir-samozanyatykh-

# 2. Настройка окружения
cp .env.example .env
nano .env  # отредактируйте переменные

# 3. Запуск
chmod +x deploy.sh
./deploy.sh
```

## Ручное развёртывание

### 1. Установка Docker

```bash
# Удаление старых версий
sudo apt remove docker docker-engine docker.io containerd runc

# Установка зависимостей
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release

# Docker GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Репозиторий
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Установка
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Проверка
sudo docker --version
sudo docker compose version
```

### 2. Настройка переменных окружения

```bash
# Создание .env файла
cat > .env << 'EOF'
# Основные
APP_NAME=Мир Самозанятых
APP_VERSION=6.0.0
ENVIRONMENT=production
DEBUG=false

# Безопасность (обязательно изменить!)
SECRET_KEY=your-64-char-random-key-here-change-me-in-production

# База данных
DATABASE_URL=postgresql+asyncpg://mir_user:strong_db_password@db:5432/mir_samozanyatykh

# Redis
REDIS_URL=redis://redis:6379/0

# Email (SMTP SSL)
SMTP_HOST=smtp.yandex.ru
SMTP_PORT=465
SMTP_USER=your-email@yandex.ru
SMTP_PASSWORD=your-app-password
SMTP_FROM_NAME=Мир Самозанятых

# Домен
DOMAIN=mir-samozanyatykh.ru
FRONTEND_URL=https://mir-samozanyatykh.ru

# ЮKassa
YOOKASSA_SHOP_ID=your-shop-id
YOOKASSA_SECRET_KEY=your-secret-key

# OpenRouter (AI + CosyVoice)
OPENROUTER_API_KEY=sk-or-v1-your-key

# FNS
FNS_API_KEY=your-fns-api-key

# SMS.ru
SMS_RU_API_KEY=your-sms-api-key
EOF

# Генерация SECRET_KEY
openssl rand -hex 64
```

### 3. Запуск

```bash
# Создание сети
sudo docker network create traefik-public

# Запуск Traefik
sudo docker compose -f docker-compose.traefik.yml up -d

# Запуск приложения
sudo docker compose up -d --build

# Проверка статуса
sudo docker compose ps
sudo docker compose logs -f app
```

### 4. Инициализация БД

```bash
# Применение миграций
sudo docker compose exec app alembic upgrade head

# Создание администратора
sudo docker compose exec app python -c "
import asyncio
from app.core.database import async_session
from app.models import User
from app.core.security import get_password_hash

async def create_admin():
    async with async_session() as db:
        admin = User(
            email='admin@mir-samozanyatykh.ru',
            password_hash=get_password_hash('AdminPass123!'),
            full_name='Администратор',
            is_verified=True,
            is_admin=True,
            is_active=True,
        )
        db.add(admin)
        await db.commit()

asyncio.run(create_admin())
"
```

## Docker Compose конфигурация

### docker-compose.yml

```yaml
version: "3.8"

services:
  db:
    image: postgres:16-alpine
    restart: always
    environment:
      POSTGRES_USER: mir_user
      POSTGRES_PASSWORD: ${DB_PASSWORD:-change_me}
      POSTGRES_DB: mir_samozanyatykh
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - internal
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mir_user -d mir_samozanyatykh"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data
    networks:
      - internal
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build:
      context: .
      dockerfile: Dockerfile
    restart: always
    env_file: .env
    environment:
      DATABASE_URL: postgresql+asyncpg://mir_user:${DB_PASSWORD:-change_me}@db:5432/mir_samozanyatykh
      REDIS_URL: redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - app_uploads:/app/data/uploads
      - app_contracts:/app/data/contracts
      - app_invoices:/app/data/invoices
      - app_logs:/app/logs
    networks:
      - internal
      - traefik-public
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.app.rule=Host(`${DOMAIN}`)"
      - "traefik.http.routers.app.entrypoints=websecure"
      - "traefik.http.routers.app.tls.certresolver=letsencrypt"
      - "traefik.http.services.app.loadbalancer.server.port=8000"
      - "traefik.http.middlewares.app-compress.compress=true"
      - "traefik.http.routers.app.middlewares=app-compress"

  # Фоновые задачи (Celery)
  worker:
    build:
      context: .
      dockerfile: Dockerfile
    command: celery -A app.tasks worker --loglevel=info
    env_file: .env
    depends_on:
      - db
      - redis
    volumes:
      - app_uploads:/app/data/uploads
      - app_logs:/app/logs
    networks:
      - internal

  # Планировщик (Celery Beat)
  scheduler:
    build:
      context: .
      dockerfile: Dockerfile
    command: celery -A app.tasks beat --loglevel=info
    env_file: .env
    depends_on:
      - db
      - redis
    volumes:
      - app_logs:/app/logs
    networks:
      - internal

volumes:
  postgres_data:
  redis_data:
  app_uploads:
  app_contracts:
  app_invoices:
  app_logs:

networks:
  internal:
    driver: bridge
  traefik-public:
    external: true
```

### docker-compose.traefik.yml

```yaml
version: "3.8"

services:
  traefik:
    image: traefik:v3.0
    restart: always
    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--entrypoints.web.http.redirections.entryPoint.to=websecure"
      - "--entrypoints.web.http.redirections.entryPoint.scheme=https"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@${DOMAIN}"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--accesslog=true"
      - "--accesslog.filepath=/var/log/traefik/access.log"
      - "--log.level=INFO"
      - "--ping=true"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik_certs:/letsencrypt
      - traefik_logs:/var/log/traefik
    networks:
      - traefik-public
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.traefik.rule=Host(`traefik.${DOMAIN}`)"
      - "traefik.http.routers.traefik.entrypoints=websecure"
      - "traefik.http.routers.traefik.tls.certresolver=letsencrypt"
      - "traefik.http.routers.traefik.service=api@internal"
      - "traefik.http.routers.traefik.middlewares=auth@file"

volumes:
  traefik_certs:
  traefik_logs:

networks:
  traefik-public:
    external: true
```

### Dockerfile

```dockerfile
# Этап 1: Сборка
FROM python:3.12-slim as builder

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Этап 2: Продакшен
FROM python:3.12-slim

WORKDIR /app

# Системные зависимости (runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование зависимостей
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Копирование приложения
COPY app/ ./app/
COPY tests/ ./tests/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY pyproject.toml .

# Создание директорий
RUN mkdir -p data/uploads data/contracts data/invoices logs

# Пользователь без прав root
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Запуск
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

## Обновление

```bash
# Обновление кода
git pull origin main

# Пересборка и перезапуск
sudo docker compose down
sudo docker compose up -d --build

# Применение миграций
sudo docker compose exec app alembic upgrade head
```

## Мониторинг

```bash
# Логи приложения
sudo docker compose logs -f app

# Логи Traefik
sudo docker compose -f docker-compose.traefik.yml logs -f traefik

# Статус контейнеров
sudo docker compose ps

# Использование ресурсов
sudo docker stats
```

## Резервное копирование

```bash
# База данных
sudo docker compose exec db pg_dump -U mir_user mir_samozanyatykh > backup_$(date +%Y%m%d).sql

# Загруженные файлы
sudo tar -czf uploads_backup_$(date +%Y%m%d).tar.gz /var/lib/docker/volumes/mir-samozanyatykh_app_uploads/_data

# Автоматический бэкап через cron (ежедневно в 3:00)
# crontab -e
# 0 3 * * * cd /opt/mir-samozanyatykh && ./scripts/backup.sh
```

## Безопасность

### OWASP ZAP сканирование

```bash
# Установка ZAP
docker pull owasp/zap2docker-stable

# Базовое сканирование
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t https://mir-samozanyatykh.ru \
  -r zap-report.html

# Полное сканирование
docker run -t owasp/zap2docker-stable zap-full-scan.py \
  -t https://mir-samozanyatykh.ru \
  -r zap-full-report.html \
  -a
```

### Проверка SSL

```bash
# SSL Labs
https://www.ssllabs.com/ssltest/analyze.html?d=mir-samozanyatykh.ru

# Командная строка
openssl s_client -connect mir-samozanyatykh.ru:443 -servername mir-samozanyatykh.ru
```

## Устранение неполадок

### Приложение не запускается

```bash
# Проверка логов
sudo docker compose logs app

# Проверка подключения к БД
sudo docker compose exec app python -c "
import asyncio
from app.core.database import engine
async def test():
    async with engine.connect() as conn:
        result = await conn.execute(text('SELECT 1'))
        print(result.scalar())
asyncio.run(test())
"
```

### Ошибка SSL

```bash
# Проверка сертификатов
sudo docker compose -f docker-compose.traefik.yml logs traefik

# Пересоздание сертификатов
sudo docker compose -f docker-compose.traefik.yml down
sudo rm -f /var/lib/docker/volumes/mir-samozanyatykh_traefik_certs/_data/acme.json
sudo docker compose -f docker-compose.traefik.yml up -d
```

### Высокая нагрузка

```bash
# Масштабирование приложения
sudo docker compose up -d --scale app=3

# Или через Docker Swarm
sudo docker swarm init
sudo docker stack deploy -c docker-compose.yml mir-samozanyatykh
```

---

*АНО ЦПС «Мир Самозанятых» | ИНН 9724016805*
*Версия: 6.0.0*
