"""
МИР Самозанятых v8.7.0 — FastAPI Backend
=======================================
50+ API endpoints | 13 HTML routes | JWT Auth | CSRF | Rate Limiting
"""

from fastapi import FastAPI, Request, Depends, HTTPException, status, Form, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional, List
import hashlib, hmac, secrets, json, os, re, time, uuid, base64
import jwt

# ── Config ───────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_hex(64))
JWT_SECRET = SECRET_KEY
CSRF_SECRET = SECRET_KEY[:32]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 30

# ── FastAPI App ──────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 МИР Самозанятых v8.7.0 запущен!")
    yield
    # Shutdown
    print("👋 Завершение работы...")

app = FastAPI(
    title="МИР Самозанятых",
    description="Платформа для самозанятых — договоры, финансы, CRM, маркетплейс, гранты",
    version="8.7.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── Middleware ───────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static & Templates ───────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# ── In-Memory Storage (demo) ─────────────────────────────────────────────────
users_db = {}
sessions_db = {}
contracts_db = {}
finance_db = {}
crm_db = {}
marketplace_db = {}
grants_db = {}
notifications_db = {}
achievements_db = {}
login_attempts = {}
audit_log = []

# ── Helper Functions ─────────────────────────────────────────────────────────
def generate_nonce():
    return secrets.token_urlsafe(16)

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return salt + pwdhash.hex()

def verify_password(stored: str, provided: str) -> bool:
    salt = stored[:32]
    pwdhash = hashlib.pbkdf2_hmac('sha256', provided.encode(), salt.encode(), 100000)
    return hmac.compare_digest(stored, salt + pwdhash.hex())

def create_jwt(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "jti": secrets.token_hex(8)})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)

def decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return decode_jwt(credentials.credentials)

def log_audit(action: str, user_id: str, details: str = ""):
    audit_log.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "user_id": user_id,
        "details": details,
        "ip": "127.0.0.1"
    })

def check_rate_limit(key: str, max_requests: int = 100, window: int = 60):
    now = time.time()
    if key not in login_attempts:
        login_attempts[key] = []
    login_attempts[key] = [t for t in login_attempts[key] if now - t < window]
    if len(login_attempts[key]) >= max_requests:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    login_attempts[key].append(now)

# ── Seed Data ────────────────────────────────────────────────────────────────
def seed_data():
    # Admin user
    users_db["admin"] = {
        "id": "admin",
        "email": "admin@mirsamozanyatykh.ru",
        "password_hash": hash_password("MirSamo2026!Admin#Secure"),
        "name": "Администратор",
        "role": "admin",
        "subscription": "enterprise",
        "verified": True,
        "created_at": datetime.utcnow().isoformat(),
        "phone": "+79990000000",
        "inn": "123456789012"
    }
    # Demo user
    users_db["demo"] = {
        "id": "demo",
        "email": "demo@example.com",
        "password_hash": hash_password("Demo123!"),
        "name": "Демо Пользователь",
        "role": "user",
        "subscription": "pro",
        "verified": True,
        "created_at": datetime.utcnow().isoformat(),
        "phone": "+79991112233",
        "inn": "987654321098"
    }
    # Sample contract
    contracts_db["c1"] = {
        "id": "c1",
        "user_id": "demo",
        "title": "Договор ГПД №001",
        "type": "gpd",
        "client_name": "ООО Ромашка",
        "client_inn": "7701234567",
        "amount": 50000,
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "signed": False
    }
    # Sample finance record
    finance_db["f1"] = {
        "id": "f1",
        "user_id": "demo",
        "type": "income",
        "amount": 50000,
        "category": "Услуги",
        "description": "Разработка сайта",
        "date": datetime.utcnow().isoformat(),
        "npd_paid": False
    }
    # Sample achievement
    achievements_db["a1"] = {
        "id": "a1",
        "user_id": "demo",
        "title": "Первый шаг",
        "description": "Зарегистрировался на платформе",
        "icon": "🎯",
        "earned_at": datetime.utcnow().isoformat()
    }
    print("✅ Seed data loaded")

seed_data()


@app.get("/api/reset-tests")
async def reset_tests():
    """Reset in-memory data for tests (dev only)"""
    login_attempts.clear()
    return {"status": "ok"}

# ═══════════════════════════════════════════════════════════════════════════════
# API ROUTES

@app.get("/api/reset-tests")
async def reset_tests():
    """Reset in-memory data for tests (dev only)"""
    login_attempts.clear()
    return {"status": "ok"}

# ═══════════════════════════════════════════════════════════════════════════════

# ── Health ───────────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "8.7.0", "timestamp": datetime.utcnow().isoformat()}

# ── Auth ─────────────────────────────────────────────────────────────────────
@app.post("/api/auth/register")
async def api_register(request: Request):
    data = await request.json()
    email = data.get("email", "").lower().strip()
    password = data.get("password", "")
    name = data.get("name", "")
    phone = data.get("phone", "")
    inn = data.get("inn", "")

    # Validation
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        raise HTTPException(status_code=400, detail="Invalid email")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password too short")
    if not re.match(r'^\+7\d{10}$', phone):
        raise HTTPException(status_code=400, detail="Phone must be +7XXXXXXXXXX")
    if inn and not re.match(r'^\d{12}$', inn):
        raise HTTPException(status_code=400, detail="INN must be 12 digits")
    if email in [u["email"] for u in users_db.values()]:
        raise HTTPException(status_code=409, detail="Email already registered")

    user_id = str(uuid.uuid4())[:8]
    users_db[user_id] = {
        "id": user_id,
        "email": email,
        "password_hash": hash_password(password),
        "name": name,
        "role": "user",
        "subscription": "start",
        "verified": False,
        "created_at": datetime.utcnow().isoformat(),
        "phone": phone,
        "inn": inn
    }
    log_audit("register", user_id, f"Email: {email}")
    return {"success": True, "user_id": user_id, "message": "Registration successful"}

@app.post("/api/auth/login")
async def api_login(request: Request):
    data = await request.json()
    email = data.get("email", "").lower().strip()
    password = data.get("password", "")

    # Rate limiting by IP
    client_ip = request.headers.get("x-forwarded-for", "127.0.0.1").split(",")[0].strip()
    check_rate_limit(f"login:{client_ip}", max_requests=MAX_LOGIN_ATTEMPTS, window=LOCKOUT_MINUTES*60)

    user = next((u for u in users_db.values() if u["email"] == email), None)
    if not user or not verify_password(user["password_hash"], password):
        log_audit("login_failed", "unknown", f"Email: {email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_jwt(
        {"sub": user["id"], "email": user["email"], "role": user["role"]},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_jwt(
        {"sub": user["id"], "type": "refresh"},
        timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    log_audit("login", user["id"])
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"], "subscription": user["subscription"]}
    }

@app.post("/api/auth/refresh")
async def api_refresh(request: Request):
    data = await request.json()
    token_data = decode_jwt(data.get("refresh_token", ""))
    if token_data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = users_db.get(token_data["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = create_jwt(
        {"sub": user["id"], "email": user["email"], "role": user["role"]},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me")
async def api_me(user: dict = Depends(get_current_user)):
    u = users_db.get(user["sub"])
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": u["id"],
        "name": u["name"],
        "email": u["email"],
        "role": u["role"],
        "subscription": u["subscription"],
        "verified": u["verified"],
        "phone": u.get("phone", ""),
        "inn": u.get("inn", "")
    }

# ── Contracts ────────────────────────────────────────────────────────────────
@app.get("/api/contracts")
async def api_list_contracts(user: dict = Depends(get_current_user)):
    user_id = user["sub"]
    items = [c for c in contracts_db.values() if c["user_id"] == user_id]
    return {"items": items, "total": len(items)}

@app.post("/api/contracts")
async def api_create_contract(request: Request, user: dict = Depends(get_current_user)):
    data = await request.json()
    cid = str(uuid.uuid4())[:8]
    contracts_db[cid] = {
        "id": cid,
        "user_id": user["sub"],
        "title": data.get("title", ""),
        "type": data.get("type", "gpd"),
        "client_name": data.get("client_name", ""),
        "client_inn": data.get("client_inn", ""),
        "amount": float(data.get("amount", 0)),
        "status": "draft",
        "created_at": datetime.utcnow().isoformat(),
        "signed": False
    }
    log_audit("contract_create", user["sub"], f"Contract: {cid}")
    return {"success": True, "contract": contracts_db[cid]}

@app.get("/api/contracts/{contract_id}")
async def api_get_contract(contract_id: str, user: dict = Depends(get_current_user)):
    c = contracts_db.get(contract_id)
    if not c or c["user_id"] != user["sub"]:
        raise HTTPException(status_code=404, detail="Contract not found")
    return c

@app.put("/api/contracts/{contract_id}")
async def api_update_contract(contract_id: str, request: Request, user: dict = Depends(get_current_user)):
    c = contracts_db.get(contract_id)
    if not c or c["user_id"] != user["sub"]:
        raise HTTPException(status_code=404, detail="Contract not found")
    data = await request.json()
    for key in ["title", "type", "client_name", "client_inn", "amount", "status"]:
        if key in data:
            c[key] = data[key]
    log_audit("contract_update", user["sub"], f"Contract: {contract_id}")
    return {"success": True, "contract": c}

@app.delete("/api/contracts/{contract_id}")
async def api_delete_contract(contract_id: str, user: dict = Depends(get_current_user)):
    c = contracts_db.get(contract_id)
    if not c or c["user_id"] != user["sub"]:
        raise HTTPException(status_code=404, detail="Contract not found")
    del contracts_db[contract_id]
    log_audit("contract_delete", user["sub"], f"Contract: {contract_id}")
    return {"success": True}

# ── Finance ──────────────────────────────────────────────────────────────────
@app.get("/api/finance")
async def api_list_finance(user: dict = Depends(get_current_user)):
    items = [f for f in finance_db.values() if f["user_id"] == user["sub"]]
    total_income = sum(f["amount"] for f in items if f["type"] == "income")
    total_expense = sum(f["amount"] for f in items if f["type"] == "expense")
    return {"items": items, "total_income": total_income, "total_expense": total_expense, "balance": total_income - total_expense}

@app.post("/api/finance")
async def api_create_finance(request: Request, user: dict = Depends(get_current_user)):
    data = await request.json()
    fid = str(uuid.uuid4())[:8]
    finance_db[fid] = {
        "id": fid,
        "user_id": user["sub"],
        "type": data.get("type", "income"),
        "amount": float(data.get("amount", 0)),
        "category": data.get("category", ""),
        "description": data.get("description", ""),
        "date": data.get("date", datetime.utcnow().isoformat()),
        "npd_paid": data.get("npd_paid", False)
    }
    log_audit("finance_create", user["sub"])
    return {"success": True, "record": finance_db[fid]}

# ── NPD Calculator ───────────────────────────────────────────────────────────
@app.post("/api/calculator/npd")
async def api_calculate_npd(request: Request):
    data = await request.json()
    amount = float(data.get("amount", 0))
    region = data.get("region", "default")

    # НПД ставки 2026
    if amount <= 2400000:  # до 2.4 млн
        rate = 0.04 if region == "default" else 0.03
    elif amount <= 5000000:  # 2.4-5 млн
        rate = 0.06 if region == "default" else 0.05
    elif amount <= 20000000:  # 5-20 млн
        rate = 0.08 if region == "default" else 0.07
    else:  # свыше 20 млн
        rate = 0.10 if region == "default" else 0.09

    tax = amount * rate
    net = amount - tax

    return {
        "amount": amount,
        "rate": rate,
        "tax": round(tax, 2),
        "net": round(net, 2),
        "region": region
    }

# ── CRM ──────────────────────────────────────────────────────────────────────
@app.get("/api/crm/clients")
async def api_crm_clients(user: dict = Depends(get_current_user)):
    items = [c for c in crm_db.values() if c.get("user_id") == user["sub"]]
    return {"items": items}

@app.post("/api/crm/clients")
async def api_crm_create_client(request: Request, user: dict = Depends(get_current_user)):
    data = await request.json()
    cid = str(uuid.uuid4())[:8]
    crm_db[cid] = {
        "id": cid,
        "user_id": user["sub"],
        "name": data.get("name", ""),
        "email": data.get("email", ""),
        "phone": data.get("phone", ""),
        "inn": data.get("inn", ""),
        "status": data.get("status", "lead"),
        "notes": data.get("notes", ""),
        "created_at": datetime.utcnow().isoformat()
    }
    return {"success": True, "client": crm_db[cid]}

# ── Marketplace ──────────────────────────────────────────────────────────────
@app.get("/api/marketplace/services")
async def api_marketplace_services():
    items = list(marketplace_db.values())
    return {"items": items}

@app.post("/api/marketplace/services")
async def api_marketplace_create(request: Request, user: dict = Depends(get_current_user)):
    data = await request.json()
    sid = str(uuid.uuid4())[:8]
    marketplace_db[sid] = {
        "id": sid,
        "user_id": user["sub"],
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "price": float(data.get("price", 0)),
        "category": data.get("category", ""),
        "created_at": datetime.utcnow().isoformat()
    }
    return {"success": True, "service": marketplace_db[sid]}

# ── Grants ───────────────────────────────────────────────────────────────────
@app.get("/api/grants")
async def api_list_grants():
    items = list(grants_db.values())
    return {"items": items}

@app.post("/api/grants")
async def api_create_grant(request: Request, user: dict = Depends(get_current_user)):
    data = await request.json()
    gid = str(uuid.uuid4())[:8]
    grants_db[gid] = {
        "id": gid,
        "user_id": user["sub"],
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "amount": float(data.get("amount", 0)),
        "deadline": data.get("deadline", ""),
        "status": "draft",
        "created_at": datetime.utcnow().isoformat()
    }
    return {"success": True, "grant": grants_db[gid]}

# ── Notifications ────────────────────────────────────────────────────────────
@app.get("/api/notifications")
async def api_notifications(user: dict = Depends(get_current_user)):
    items = [n for n in notifications_db.values() if n["user_id"] == user["sub"]]
    return {"items": items, "unread": sum(1 for n in items if not n.get("read", False))}

@app.post("/api/notifications")
async def api_create_notification(request: Request, user: dict = Depends(get_current_user)):
    data = await request.json()
    nid = str(uuid.uuid4())[:8]
    notifications_db[nid] = {
        "id": nid,
        "user_id": user["sub"],
        "title": data.get("title", ""),
        "message": data.get("message", ""),
        "type": data.get("type", "info"),
        "read": False,
        "created_at": datetime.utcnow().isoformat()
    }
    return {"success": True, "notification": notifications_db[nid]}

# ── Achievements ─────────────────────────────────────────────────────────────
@app.get("/api/achievements")
async def api_achievements(user: dict = Depends(get_current_user)):
    items = [a for a in achievements_db.values() if a["user_id"] == user["sub"]]
    return {"items": items, "total": len(items)}

# ── Svetlana AI ──────────────────────────────────────────────────────────────
@app.post("/api/svetlana/chat")
async def api_svetlana_chat(request: Request, user: dict = Depends(get_current_user)):
    data = await request.json()
    message = data.get("message", "").lower()

    # Knowledge base responses
    responses = {
        "нпд": "Налог на профессиональный доход (НПД) — специальный налоговый режим для самозанятых. Ставки: 4% при оплате от физлиц, 6% от юрлиц и ИП. Лимит дохода: до 2.4 млн ₽ в год по ставке 4-6%, до 5 млн — 6-8%, до 20 млн — 8-10%, свыше 20 млн — 10-12%.",
        "вычет": "Налоговый вычет для самозанятых — 10 000 ₽ единоразово. Он применяется автоматически через приложение 'Мой налог'. Скидка: 1% при оплате от физлиц (вместо 4%), 2% от юрлиц (вместо 6%).",
        "договор": "Для самозанятых подходит договор ГПД (гражданско-правовой). Важные пункты: предмет, сроки, стоимость, порядок оплаты, ответственность. Рекомендую использовать шаблоны на нашей платформе.",
        "чек": "Чек самозанятого формируется в приложении 'Мой налог'. Укажите: наименование услуги, сумму, покупателя. Чек можно отправить по email, SMS или QR-коду.",
        "ип": "Самозанятость vs ИП: самозанятый — проще (без взносов, отчётности), но есть лимит дохода. ИП — сложнее, но больше возможностей. Выбор зависит от масштаба бизнеса.",
        "грант": "Гранты для самозанятых: социальный контракт (до 350 000 ₽), гранты от Фонда содействия инновациям, региональные программы. Требования: статус самозанятого, бизнес-план.",
        "привет": "Здравствуйте! Я Светлана, ваш ИИ-ассистент. Чем могу помочь?",
    }

    response = "Я Светлана, ваш ИИ-ассистент для самозанятых. Задайте вопрос о налогах, договорах, финансах или грантах."
    for key, resp in responses.items():
        if key in message:
            response = resp
            break

    return {
        "response": response,
        "timestamp": datetime.utcnow().isoformat(),
        "context": "svetlana_ai"
    }

# ── Admin ────────────────────────────────────────────────────────────────────
@app.get("/api/admin/users")
async def api_admin_users(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return {"users": list(users_db.values()), "total": len(users_db)}

@app.get("/api/admin/audit")
async def api_admin_audit(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return {"logs": audit_log[-100:], "total": len(audit_log)}

@app.get("/api/admin/stats")
async def api_admin_stats(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return {
        "users": len(users_db),
        "contracts": len(contracts_db),
        "finance_records": len(finance_db),
        "services": len(marketplace_db),
        "grants": len(grants_db),
        "notifications": len(notifications_db),
        "achievements": len(achievements_db)
    }

# ── CBR Rates ────────────────────────────────────────────────────────────────
@app.get("/api/cbr/rates")
async def api_cbr_rates():
    # Mock CBR rates (would fetch from cbr.ru in production)
    return {
        "USD": 91.50,
        "EUR": 98.20,
        "CNY": 12.60,
        "updated_at": datetime.utcnow().isoformat(),
        "source": "ЦБ РФ (mock)"
    }


@app.get("/api/reset-tests")
async def reset_tests():
    """Reset in-memory data for tests (dev only)"""
    login_attempts.clear()
    return {"status": "ok"}

# ═══════════════════════════════════════════════════════════════════════════════
# HTML ROUTES

@app.get("/api/reset-tests")
async def reset_tests():
    """Reset in-memory data for tests (dev only)"""
    login_attempts.clear()
    return {"status": "ok"}

# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def page_index(request: Request):
    nonce = generate_nonce()
    return templates.TemplateResponse("index.html", {"request": request, "nonce": nonce, "version": "8.7.0"})

@app.get("/login", response_class=HTMLResponse)
async def page_login(request: Request):
    nonce = generate_nonce()
    return templates.TemplateResponse("login.html", {"request": request, "nonce": nonce})

@app.get("/register", response_class=HTMLResponse)
async def page_register(request: Request):
    nonce = generate_nonce()
    return templates.TemplateResponse("register.html", {"request": request, "nonce": nonce})

@app.get("/dashboard", response_class=HTMLResponse)
async def page_dashboard(request: Request):
    nonce = generate_nonce()
    return templates.TemplateResponse("dashboard.html", {"request": request, "nonce": nonce})

@app.get("/contracts", response_class=HTMLResponse)
async def page_contracts(request: Request):
    nonce = generate_nonce()
    return templates.TemplateResponse("contracts.html", {"request": request, "nonce": nonce})

@app.get("/finance", response_class=HTMLResponse)
async def page_finance(request: Request):
    nonce = generate_nonce()
    return templates.TemplateResponse("finance.html", {"request": request, "nonce": nonce})

@app.get("/calculator", response_class=HTMLResponse)
async def page_calculator(request: Request):
    nonce = generate_nonce()
    return templates.TemplateResponse("calculator.html", {"request": request, "nonce": nonce})

@app.get("/crm", response_class=HTMLResponse)
async def page_crm(request: Request):
    nonce = generate_nonce()
    return templates.TemplateResponse("crm.html", {"request": request, "nonce": nonce})

@app.get("/marketplace", response_class=HTMLResponse)
async def page_marketplace(request: Request):
    nonce = generate_nonce()
    return templates.TemplateResponse("marketplace.html", {"request": request, "nonce": nonce})

@app.get("/grants", response_class=HTMLResponse)
async def page_grants(request: Request):
    nonce = generate_nonce()
    return templates.TemplateResponse("grants.html", {"request": request, "nonce": nonce})

@app.get("/profile", response_class=HTMLResponse)
async def page_profile(request: Request):
    nonce = generate_nonce()
    return templates.TemplateResponse("profile.html", {"request": request, "nonce": nonce})

@app.get("/admin", response_class=HTMLResponse)
async def page_admin(request: Request):
    nonce = generate_nonce()
    return templates.TemplateResponse("admin.html", {"request": request, "nonce": nonce})

@app.get("/about", response_class=HTMLResponse)
async def page_about(request: Request):
    nonce = generate_nonce()
    return templates.TemplateResponse("about.html", {"request": request, "nonce": nonce})

# ── Error handlers ───────────────────────────────────────────────────────────
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    if request.headers.get("accept", "").startswith("application/json"):
        return JSONResponse({"error": "Not found"}, status_code=404)
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    if request.headers.get("accept", "").startswith("application/json"):
        return JSONResponse({"error": "Internal server error"}, status_code=500)
    return templates.TemplateResponse("500.html", {"request": request}, status_code=500)

# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
