# Mir Samozanyatykh v6.7

## ANO CPS INN 9724016805

Platforma dlya samozanyatykh: scheta, dogovory, klienty, golosovoy assistent Svetlana.

### Stack
| Layer | Tech |
|-------|------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL, Redis |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, Zustand |
| Mobile | Flutter 3, Riverpod, GoRouter, Firebase, Hive, WebRTC |
| Infra | Docker, Traefik, Let's Encrypt |

### Features
- **Prodazhi:** produkty, scheta, oplata cherez Yookassa
- **CRM:** klienty, sdelki, vortonka
- **Dogovory:** GPH, IT-autsorsing, NDA, akt — s elektronoy podpisyyu
- **Svetlana:** golosovoy assistent na baze CosyVoice 3.0
- **Bezopasnost:** JWT jti, CSRF, rate limit, 2FA TOTP, audit log

### Quick Start
```bash
git clone https://github.com/paulafanasyev/mir-samozanyatykh-.git
cd mir-samozanyatykh-
docker compose up -d
```

### API
- Swagger: `/docs`
- ReDoc: `/redoc`

### Links
- [DEPLOY.md](DEPLOY.md) — deployment guide
- License: MIT
