# Руководство по развёртыванию — Мир Самозанятых v8.6.3

## Системные требования

### Минимальные
- **CPU**: 2 ядра
- **RAM**: 4 GB
- **Disk**: 20 GB SSD
- **OS**: Ubuntu 22.04 LTS / Debian 12 / CentOS 9
- **Docker**: 24.0+
- **Docker Compose**: 2.20+

### Рекомендуемые
- **CPU**: 4 ядра
- **RAM**: 8 GB
- **Disk**: 50 GB SSD
- **Network**: 100 Mbps

## Быстрый старт

### 1. Клонирование репозитория

```bash
git clone https://github.com/paulafanasyev/mir-samozanyatykh-.git
cd mir-samozanyatykh-
```

### 2. Настройка окружения

```bash
# Копируем пример конфигурации
cp .env.example .env

# Редактируем .env (обязательно заполните SECRET_KEY!)
nano .env
```

**Обязательные переменные:**
- `SECRET_KEY` — минимум 64 символа, hex-формат
- `DATABASE_URL` — для production используйте PostgreSQL
- `OPENROUTER_API_KEY` — для работы Светланы
- `SMTP_*` — для отправки email
- `YOOKASSA_*` — для приёма платежей

### 3. Запуск (Production)

```bash
# Сборка и запуск
make docker-build
make docker-up

# Или напрямую:
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Проверка

```bash
# Healthcheck
curl https://api.mir-samozanyatykh.ru/api/health

# Должен вернуть:
# {"status":"healthy","version":"8.6.3",...}
```

### 5. Миграции

```bash
# Применить миграции БД
docker-compose -f docker-compose.prod.yml exec app alembic upgrade head

# Заполнить тестовыми данными (опционально)
docker-compose -f docker-compose.prod.yml exec app python -m app.seed
```

## Структура сервисов

```
┌─────────────────────────────────────────┐
│              Nginx (80/443)             │
│  - SSL termination                      │
│  - Rate limiting                        │
│  - Static files                         │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│         FastAPI App (8000)              │
│  - REST API                             │
│  - WebSocket                            │
│  - AI (Светлана)                        │
└─────────────┬───────────────────────────┘
              │
    ┌─────────┼─────────┐
    │         │         │
┌───▼──┐ ┌───▼──┐ ┌───▼──┐
│Postgre│ │Redis │ │Celery│
│SQL    │ │      │ │      │
└───────┘ └───────┘ └───────┘
```

## Мониторинг

### Prometheus
- **URL**: http://your-server:9090
- **Метрики**: CPU, memory, requests, latency

### Grafana
- **URL**: http://your-server:3000
- **Login**: admin / [GRAFANA_PASSWORD из .env]
- **Дашборды**: System, Application, Business

### Healthcheck endpoints

| Endpoint | Описание |
|----------|----------|
| `/api/health` | Общий статус |
| `/api/health/ready` | Готовность к трафику |
| `/api/health/live` | Живость сервиса |
| `/api/health/metrics` | Системные метрики |
| `/api/metrics/prometheus` | Prometheus формат |

## Обновление

```bash
# Pull новых изменений
git pull origin main

# Пересборка
make docker-build
make docker-up

# Миграции
docker-compose -f docker-compose.prod.yml exec app alembic upgrade head
```

## Резервное копирование

```bash
# База данных
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres mir_samozanyatykh > backup_$(date +%Y%m%d).sql

# Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli SAVE
docker cp mir-samozanyatykh-redis:/data/dump.rdb ./backup/redis_$(date +%Y%m%d).rdb
```

## SSL сертификаты

### Let's Encrypt (рекомендуется)

```bash
# Установка certbot
sudo apt install certbot

# Получение сертификата
sudo certbot certonly --standalone -d mir-samozanyatykh.ru -d www.mir-samozanyatykh.ru

# Копирование в nginx
sudo cp /etc/letsencrypt/live/mir-samozanyatykh.ru/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/mir-samozanyatykh.ru/privkey.pem nginx/ssl/

# Автообновление
sudo certbot renew --dry-run
```

## Устранение неполадок

### Сервис не запускается

```bash
# Проверка логов
docker-compose -f docker-compose.prod.yml logs -f app

# Проверка статуса
docker-compose -f docker-compose.prod.yml ps

# Перезапуск
make docker-down
make docker-up
```

### Ошибка подключения к БД

```bash
# Проверка PostgreSQL
docker-compose -f docker-compose.prod.yml exec db pg_isready -U postgres

# Пересоздание БД (⚠️ удалит данные!)
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d db
```

### Высокая загрузка CPU

```bash
# Мониторинг
docker stats

# Масштабирование Celery workers
docker-compose -f docker-compose.prod.yml up -d --scale celery=4
```

## Поддержка

- **Email**: it-laboratory@bk.ru
- **GitHub Issues**: https://github.com/paulafanasyev/mir-samozanyatykh-/issues
- **Документация API**: https://api.mir-samozanyatykh.ru/docs
- **Статус**: https://api.mir-samozanyatykh.ru/api/health

---

АНО ЦПС «Мир Самозанятых» | ИНН 9724016805 | Версия 8.6.3
