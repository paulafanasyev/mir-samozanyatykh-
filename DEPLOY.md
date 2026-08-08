# Деплой Мир Самозанятых v4.2

## Требования
- Docker 24+
- Docker Compose 2+
- Домен с DNS-записями

## Быстрый старт

```bash
# 1. Клонировать репозиторий
git clone https://github.com/paulafanasyev/mir-samozanyatykh-.git
cd mir-samozanyatykh-

# 2. Создать .env
cp .env.example .env
# Отредактировать .env:
# - SECRET_KEY=$(openssl rand -hex 64)
# - SMTP_* настройки
# - DOMAIN=ваш-домен.рф

# 3. Запустить
docker-compose up --build -d

# 4. Проверить
curl https://ваш-домен.рф/api/health
```

## Миграции Alembic

```bash
# Создать миграцию
docker-compose exec app alembic revision --autogenerate -m "init"

# Применить
docker-compose exec app alembic upgrade head
```

## HTTPS
Let's Encrypt настраивается автоматически через Traefik.
