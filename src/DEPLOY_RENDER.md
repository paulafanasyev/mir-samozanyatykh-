# 🚀 Деплой на Render.com — Мир Самозанятых v8.4
## АНО ЦПС ИНН 9724016805

### Blueprint ID: `exs-da08tgtbedkc73a743pg`

---

## 📋 Предварительные требования

1. Аккаунт на [Render.com](https://render.com)
2. Репозиторий на GitHub: `paulafanasyev/mir-samozanyatykh-`
3. GitHub токен с доступом к репозиторию

---

## 🚀 Способ 1: Blueprint (Автоматический)

### Шаг 1: Создать Blueprint Instance

1. Зайди в [Render Dashboard](https://dashboard.render.com)
2. Нажми **New +** → **Blueprint**
3. Выбери репозиторий `paulafanasyev/mir-samozanyatykh-`
4. Нажми **Apply**

Render автоматически создаст:
- ✅ PostgreSQL базу данных
- ✅ Redis кэш
- ✅ Backend API (FastAPI)
- ✅ Frontend (Static Site)

### Шаг 2: Настроить переменные окружения

После создания сервисов, зайди в каждый сервис → **Environment**:

#### Backend API (`mirsamozanyatykh-api`):

| Переменная | Значение |
|------------|----------|
| `SMTP_HOST` | `smtp.yandex.ru` |
| `SMTP_USER` | `it-laboratory@bk.ru` |
| `SMTP_PASSWORD` | *(твой пароль)* |
| `OPENROUTER_API_KEY` | *(твой ключ)* |
| `YOOKASSA_SHOP_ID` | *(твой shop ID)* |
| `YOOKASSA_SECRET_KEY` | *(твой secret)* |
| `FNS_API_KEY` | *(твой FNS ключ)* |
| `TELEGRAM_BOT_TOKEN` | *(твой токен)* |
| `SMS_RU_API_KEY` | *(твой SMS.ru ключ)* |

> **Важно:** Переменные с `sync: false` в `render.yaml` НЕ будут скопированы из репозитория. Их нужно ввести вручную в Dashboard.

### Шаг 3: Запустить миграции

1. Открой **Shell** для backend сервиса
2. Выполни:
   ```bash
   alembic upgrade head
   ```

### Шаг 4: Проверить деплой

- **API Health:** `https://mirsamozanyatykh-api.onrender.com/api/health`
- **API Docs:** `https://mirsamozanyatykh-api.onrender.com/docs`
- **Frontend:** `https://mirsamozanyatykh.onrender.com`

---

## 🔧 Способ 2: Ручное создание сервисов

Если Blueprint не сработал, создай сервисы вручную:

### 1. PostgreSQL
- **New +** → **PostgreSQL**
- Name: `mirsamozanyatykh-db`
- Plan: Starter ($7/мес)

### 2. Redis
- **New +** → **Redis**
- Name: `mirsamozanyatykh-redis`
- Plan: Starter ($7/мес)

### 3. Web Service (Backend)
- **New +** → **Web Service**
- Connect repo → выбери `mir-samozanyatykh-`
- Runtime: **Docker**
- Plan: Starter ($7/мес)
- Docker Command: *(оставь пустым, используется CMD из Dockerfile)*

### 4. Static Site (Frontend)
- **New +** → **Static Site**
- Connect repo → выбери `mir-samozanyatykh-`
- Build Command: `cd frontend && npm install && npm run build`
- Publish Directory: `frontend/dist`

---

## 💰 Стоимость на Render.com

| Сервис | Free | Starter |
|--------|------|---------|
| Web Service | $0 (спит) | $7/мес |
| PostgreSQL | $0 (1GB) | $7/мес |
| Redis | $0 (спит) | $7/мес |
| **Итого** | **$0** | **$21/мес** |

---

## 🔄 Автодеплой

При каждом `git push` в `main`:
1. Render автоматически пересобирает сервисы
2. Запускает health check
3. Переключает трафик на новую версию

---

## 🛠️ Troubleshooting

### Сервис не стартует
```bash
# Проверь логи в Render Dashboard → Logs
# Проверь health endpoint
curl https://mirsamozanyatykh-api.onrender.com/api/health
```

### Ошибка подключения к БД
```bash
# Проверь DATABASE_URL в Environment
# Должен быть вида: postgresql+asyncpg://...
```

### Frontend не загружается
```bash
# Проверь VITE_API_URL в Environment Static Site
# Должен указывать на backend URL
```

---

## 📞 Поддержка

- **Email:** it-laboratory@bk.ru
- **GitHub:** [paulafanasyev/mir-samozanyatykh-](https://github.com/paulafanasyev/mir-samozanyatykh-)
- **Render Docs:** [render.com/docs](https://render.com/docs)

---

*Последнее обновление: 16.08.2026*
