# DEPLOY.md — Mir Samozanyatykh v7.2

## ANO CPS INN 9724016805

### Stack
- **Backend:** Python 3.12 + FastAPI + SQLAlchemy 2.0 (async) + Alembic + PostgreSQL 16 + Redis 7
- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui + Zustand
- **Mobile:** Flutter 3 + Riverpod + GoRouter + Firebase + Hive + WebRTC
- **Infra:** Docker + Docker Compose + Traefik + Let's Encrypt
- **Integrations:** OpenRouter CosyVoice 3.0, Yookassa, SMTP SSL
- **Security:** JWT jti, CSRF, rate limiting (5 attempts), 2FA TOTP
- **Testing:** pytest + pytest-asyncio + coverage

---

## Quick Start (Local)

```bash
# 1. Clone
git clone https://github.com/paulafanasyev/mir-samozanyatykh-.git
cd mir-samozanyatykh-

# 2. Environment
cp .env.example .env
# Edit .env

# 3. Backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 4. Database (PostgreSQL + Redis required)
# Or use SQLite for dev: DATABASE_URL=sqlite+aiosqlite:///./dev.db

# 5. Migrations
alembic upgrade head

# 6. Seed data (contract templates)
python -c "import asyncio; from app.core.database import init_db; asyncio.run(init_db())"

# 7. Run backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 8. Frontend (new terminal)
cd frontend
npm install
npm run dev
```

---

## Docker Compose (Production)

```bash
# 1. Environment
cp .env.example .env
# Fill all required variables

# 2. Start all services
docker compose up -d

# 3. Run migrations
docker compose exec backend alembic upgrade head

# 4. Check logs
docker compose logs -f backend

# 5. Stop
docker compose down
```

### Services
| Service | Port | Description |
|---------|------|-------------|
| PostgreSQL | 5432 | Main database |
| Redis | 6379 | Cache + sessions |
| Backend | 8000 | FastAPI app |
| Frontend | 3000 | React app (nginx) |
| Traefik | 80/443 | Reverse proxy + SSL |

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | — | 32+ chars random string |
| `DATABASE_URL` | Yes | — | PostgreSQL async URL |
| `REDIS_URL` | Yes | — | Redis URL |
| `ENVIRONMENT` | No | `development` | development/staging/production |
| `YOOKASSA_SHOP_ID` | For payments | — | Yookassa shop ID |
| `YOOKASSA_SECRET_KEY` | For payments | — | Yookassa secret key |
| `SMTP_HOST` | For email | — | SMTP server host |
| `SMTP_PORT` | No | `465` | SMTP port |
| `SMTP_USER` | For email | — | SMTP login |
| `SMTP_PASSWORD` | For email | — | SMTP password |
| `OPENROUTER_API_KEY` | For Svetlana | — | OpenRouter API key |
| `ACME_EMAIL` | For SSL | — | Let's Encrypt email |

---

## API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

---

## Testing

```bash
# All tests
pytest -v

# With coverage
pytest --cov=app --cov-report=html

# Specific module
pytest tests/test_security.py -v
```

---

## Security Checklist

- [ ] Change default `SECRET_KEY` (32+ random chars)
- [ ] Set strong `POSTGRES_PASSWORD`
- [ ] Configure SMTP with SSL/TLS
- [ ] Enable 2FA for admin accounts
- [ ] Set up OWASP ZAP scans
- [ ] Configure rate limiting per endpoint
- [ ] Enable audit logging
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure CORS origins
- [ ] Enable HTTPS (Traefik + Let's Encrypt)

---

## Mobile App (Flutter)

```bash
cd mobile
flutter pub get
flutter run
```

---

## License

MIT © ANO CPS INN 9724016805
