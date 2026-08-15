.PHONY: help install dev test lint format docker-build docker-up docker-down migrate seed clean

help:
	@echo "Мир Самозанятых — Доступные команды:"
	@echo "  make install      Установка зависимостей"
	@echo "  make dev          Запуск в development режиме"
	@echo "  make test         Запуск тестов"
	@echo "  make lint         Проверка кода"
	@echo "  make format       Форматирование кода"
	@echo "  make docker-up    Запуск в Docker (production)"
	@echo "  make docker-down  Остановка Docker"
	@echo "  make migrate      Применение миграций"
	@echo "  make seed         Заполнение тестовыми данными"
	@echo "  make clean        Очистка"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v --cov=app --cov-report=term-missing

lint:
	flake8 app/ tests/
	mypy app/

format:
	black app/ tests/
	isort app/ tests/

docker-build:
	docker-compose -f docker-compose.prod.yml build

docker-up:
	docker-compose -f docker-compose.prod.yml up -d

docker-down:
	docker-compose -f docker-compose.prod.yml down

docker-logs:
	docker-compose -f docker-compose.prod.yml logs -f app

migrate:
	alembic upgrade head

seed:
	python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
