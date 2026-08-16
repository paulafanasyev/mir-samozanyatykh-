"""
Мир Самозанятых v8.7.0 — Полное FastAPI приложение
"""
import os, json, uuid, secrets
from datetime import datetime, timedelta
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    get_password_hash, verify_password, create_access_token,
    create_refresh_token, verify_token, generate_csrf_token,
    generate_nonce
)
from app.models.base import (
    get_db, create_tables, SessionLocal,
    User, Contract, FinanceRecord, Notification, Achievement,
    UserAchievement, MarketplaceItem, CRMContact, Grant,
    AuditLog, Payment, SvetlanaChat,
    UserRole, SubscriptionTier, ContractStatus, NotificationType, PaymentStatus
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    seed_achievements()
    print("🚀 Мир Самозанятых v8.7.0 запущен!")
    yield
    print("👋 Завершение работы...")

app = FastAPI(title="Мир Самозанятых", version="8.7.0", lifespan=lifespan, docs_url="/api/docs")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
security_bearer = HTTPBearer(auto_error=False)

def get_current_user_api(credentials: HTTPAuthorizationCredentials = Depends(security_bearer), db: Session = Depends(get_db)) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return user

def get_current_user_web(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = verify_token(token)
    if not payload:
        return None
    return db.query(User).filter(User.id == int(payload["sub"]), User.is_active == True).first()

def log_audit(db: Session, user_id: int, action: str, entity_type: str = None, entity_id: int = None, details: dict = None):
    db.add(AuditLog(user_id=user_id, action=action, entity_type=entity_type, entity_id=entity_id, details=details or {}))
    db.commit()

def seed_achievements():
    db = SessionLocal()
    try:
        if db.query(Achievement).count() == 0:
            db.add_all([
                Achievement(name="Первые шаги", description="Зарегистрируйтесь", icon="👋", points=10, condition_type="register", condition_value=1),
                Achievement(name="Первый договор", description="Создайте договор", icon="📝", points=20, condition_type="contracts_count", condition_value=1),
                Achievement(name="Десятка", description="10 договоров", icon="📄", points=50, condition_type="contracts_count", condition_value=10),
                Achievement(name="Первый доход", description="Запишите доход", icon="💰", points=15, condition_type="income", condition_value=1),
                Achievement(name="PRO", description="Подписка PRO", icon="⭐", points=25, condition_type="subscription", condition_value=1),
                Achievement(name="Маркетплейс", description="Первый товар", icon="🛒", points=20, condition_type="marketplace", condition_value=1),
                Achievement(name="CRM-мастер", description="5 контактов", icon="👥", points=30, condition_type="crm_contacts", condition_value=5),
                Achievement(name="AI-чат", description="10 вопросов Светлане", icon="🤖", points=20, condition_type="svetlana_chats", condition_value=10),
                Achievement(name="Верификация", description="Подтвердите данные", icon="✅", points=40, condition_type="verified", condition_value=1),
                Achievement(name="Налогоплательщик", description="Заплатите налог", icon="🏛️", points=30, condition_type="tax_paid", condition_value=1),
            ])
            db.commit()
    finally:
        db.close()

# ============ HEALTH & INFO ============
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "8.7.0", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/info")
async def api_info():
    return {"name": "Мир Самозанятых", "version": "8.7.0", "features": ["auth", "contracts", "finance", "crm", "marketplace", "grants", "svetlana", "gamification"]}

# ============ HTML ROUTES ============
@app.get("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_web(request, db)
    return templates.TemplateResponse("index.html", {"request": request, "user": user, "version": "8.7.0"})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None):
    return templates.TemplateResponse("login.html", {"request": request, "error": error})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, error: str = None):
    return templates.TemplateResponse("register.html", {"request": request, "error": error})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_web(request, db)
    if not user: return RedirectResponse("/login", status_code=302)
    cc = db.query(Contract).filter(Contract.user_id == user.id).count()
    nc = db.query(Notification).filter(Notification.user_id == user.id, Notification.is_read == False).count()
    ti = db.query(FinanceRecord).filter(FinanceRecord.user_id == user.id, FinanceRecord.type == "income").count()
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "contracts_count": cc, "notifications_count": nc, "total_income": ti})

@app.get("/contracts", response_class=HTMLResponse)
async def contracts_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_web(request, db)
    if not user: return RedirectResponse("/login", status_code=302)
    contracts = db.query(Contract).filter(Contract.user_id == user.id).order_by(Contract.created_at.desc()).all()
    return templates.TemplateResponse("contracts.html", {"request": request, "user": user, "contracts": contracts})

@app.get("/finance", response_class=HTMLResponse)
async def finance_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_web(request, db)
    if not user: return RedirectResponse("/login", status_code=302)
    records = db.query(FinanceRecord).filter(FinanceRecord.user_id == user.id).order_by(FinanceRecord.date.desc()).all()
    total_income = sum(r.amount for r in records if r.type == "income")
    total_expense = sum(r.amount for r in records if r.type == "expense")
    total_tax = sum(r.tax_amount for r in records if r.type == "income")
    return templates.TemplateResponse("finance.html", {"request": request, "user": user, "records": records, "total_income": total_income, "total_expense": total_expense, "total_tax": total_tax})

@app.get("/crm", response_class=HTMLResponse)
async def crm_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_web(request, db)
    if not user: return RedirectResponse("/login", status_code=302)
    contacts = db.query(CRMContact).filter(CRMContact.owner_id == user.id).order_by(CRMContact.created_at.desc()).all()
    return templates.TemplateResponse("crm.html", {"request": request, "user": user, "contacts": contacts})

@app.get("/marketplace", response_class=HTMLResponse)
async def marketplace_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_web(request, db)
    items = db.query(MarketplaceItem).filter(MarketplaceItem.is_active == True).order_by(MarketplaceItem.created_at.desc()).all()
    return templates.TemplateResponse("marketplace.html", {"request": request, "user": user, "items": items})

@app.get("/grants", response_class=HTMLResponse)
async def grants_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_web(request, db)
    grants = db.query(Grant).filter(Grant.status == "active").order_by(Grant.deadline.asc()).all()
    return templates.TemplateResponse("grants.html", {"request": request, "user": user, "grants": grants})

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_web(request, db)
    if not user: return RedirectResponse("/login", status_code=302)
    achievements = db.query(UserAchievement).filter(UserAchievement.user_id == user.id).all()
    return templates.TemplateResponse("profile.html", {"request": request, "user": user, "achievements": achievements})

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_web(request, db)
    if not user or user.role.value not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    return templates.TemplateResponse("admin.html", {"request": request, "user": user, "users_count": db.query(User).count(), "contracts_count": db.query(Contract).count()})

# ============ API: AUTH ============
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = None
    inn: Optional[str] = Field(None, pattern=r"^\d{12}$")

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@app.post("/api/auth/register")
async def api_register(data: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
    user = User(email=data.email, password_hash=get_password_hash(data.password), full_name=data.full_name, phone=data.phone, inn=data.inn)
    db.add(user)
    db.commit()
    db.refresh(user)
    ach = db.query(Achievement).filter(Achievement.condition_type == "register").first()
    if ach:
        db.add(UserAchievement(user_id=user.id, achievement_id=ach.id))
        db.commit()
    log_audit(db, user.id, "register", "user", user.id)
    access = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token({"sub": str(user.id)})
    response.set_cookie(key="access_token", value=access, httponly=True, max_age=1800, samesite="lax")
    response.set_cookie(key="refresh_token", value=refresh, httponly=True, max_age=604800, samesite="lax")
    return {"success": True, "user_id": user.id}

@app.post("/api/auth/login")
async def api_login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        if user:
            user.login_attempts += 1
            if user.login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            db.commit()
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(status_code=403, detail="Аккаунт заблокирован")
    user.login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    db.commit()
    access = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token({"sub": str(user.id)})
    response.set_cookie(key="access_token", value=access, httponly=True, max_age=1800, samesite="lax")
    response.set_cookie(key="refresh_token", value=refresh, httponly=True, max_age=604800, samesite="lax")
    log_audit(db, user.id, "login", "user", user.id)
    return {"success": True, "access_token": access, "refresh_token": refresh, "user": {"id": user.id, "email": user.email, "name": user.full_name, "role": user.role.value}}

@app.post("/api/auth/logout")
async def api_logout(response: Response, request: Request, db: Session = Depends(get_db)):
    user = get_current_user_web(request, db)
    if user: log_audit(db, user.id, "logout", "user", user.id)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"success": True}

@app.post("/api/auth/refresh")
async def api_refresh(response: Response, request: Request, db: Session = Depends(get_db)):
    refresh = request.cookies.get("refresh_token")
    if not refresh: raise HTTPException(status_code=401, detail="Refresh token не найден")
    payload = verify_token(refresh, token_type="refresh")  # nosec B106
    if not payload: raise HTTPException(status_code=401, detail="Недействительный refresh token")
    user = db.query(User).filter(User.id == int(payload["sub"]), User.is_active == True).first()
    if not user: raise HTTPException(status_code=401, detail="Пользователь не найден")
    access = create_access_token({"sub": str(user.id)})
    response.set_cookie(key="access_token", value=access, httponly=True, max_age=1800, samesite="lax")
    return {"success": True, "access_token": access}

# ============ API: USER ============
@app.get("/api/user/me")
async def api_user_me(user: User = Depends(get_current_user_api), db: Session = Depends(get_db)):
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "phone": user.phone, "inn": user.inn, "role": user.role.value, "subscription": user.subscription.value, "is_verified": user.is_verified}

@app.put("/api/user/me")
async def api_user_update(data: dict, user: User = Depends(get_current_user_api), db: Session = Depends(get_db)):
    for field in ["full_name", "phone", "bio", "avatar_url"]:
        if field in data: setattr(user, field, data[field])
    db.commit()
    log_audit(db, user.id, "update_profile", "user", user.id)
    return {"success": True}

# ============ API: CONTRACTS ============
class ContractCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    client_name: str = Field(..., min_length=1, max_length=255)
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    client_inn: Optional[str] = Field(None, pattern=r"^\d{12}$")
    amount: float = Field(..., gt=0)
    description: Optional[str] = None
    contract_type: str = "gpd"

@app.post("/api/contracts")
async def api_create_contract(data: ContractCreateRequest, user: User = Depends(get_current_user_api), db: Session = Depends(get_db)):
    contract = Contract(user_id=user.id, title=data.title, client_name=data.client_name, client_email=data.client_email, client_phone=data.client_phone, client_inn=data.client_inn, amount=data.amount, description=data.description, contract_type=data.contract_type)
    db.add(contract)
    db.commit()
    db.refresh(contract)
    cc = db.query(Contract).filter(Contract.user_id == user.id).count()
    for ach in db.query(Achievement).filter(Achievement.condition_type == "contracts_count").all():
        if cc >= ach.condition_value and not db.query(UserAchievement).filter(UserAchievement.user_id == user.id, UserAchievement.achievement_id == ach.id).first():
            db.add(UserAchievement(user_id=user.id, achievement_id=ach.id))
            db.commit()
    log_audit(db, user.id, "create_contract", "contract", contract.id)
    return {"success": True, "contract": {"id": contract.id, "title": contract.title, "status": contract.status.value, "amount": contract.amount}}

@app.get("/api/contracts")
async def api_list_contracts(user: User = Depends(get_current_user_api), db: Session = Depends(get_db)):
    contracts = db.query(Contract).filter(Contract.user_id == user.id).order_by(Contract.created_at.desc()).all()
    return {"contracts": [{"id": c.id, "title": c.title, "client_name": c.client_name, "amount": c.amount, "status": c.status.value, "created_at": c.created_at.isoformat()} for c in contracts]}

@app.get("/api/contracts/{contract_id}")
async def api_get_contract(contract_id: int, user: User = Depends(get_current_user_api), db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == contract_id, Contract.user_id == user.id).first()
    if not contract: raise HTTPException(status_code=404, detail="Договор не найден")
    return {"contract": {"id": contract.id, "title": contract.title, "client_name": contract.client_name, "amount": contract.amount, "status": contract.status.value, "description": contract.description}}

@app.put("/api/contracts/{contract_id}")
async def api_update_contract(contract_id: int, data: dict, user: User = Depends(get_current_user_api), db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == contract_id, Contract.user_id == user.id).first()
    if not contract: raise HTTPException(status_code=404, detail="Договор не найден")
    for field in ["title", "client_name", "client_email", "client_phone", "amount", "description", "status"]:
        if field in data: setattr(contract, field, data[field])
    db.commit()
    log_audit(db, user.id, "update_contract", "contract", contract.id)
    return {"success": True}

@app.delete("/api/contracts/{contract_id}")
async def api_delete_contract(contract_id: int, user: User = Depends(get_current_user_api), db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == contract_id, Contract.user_id == user.id).first()
    if not contract: raise HTTPException(status_code=404, detail="Договор не найден")
    db.delete(contract)
    db.commit()
    log_audit(db, user.id, "delete_contract", "contract", contract_id)
    return {"success": True}

# ============ API: FINANCE ============
@app.post("/api/finance")
async def api_create_finance(data: dict, user: User = Depends(get_current_user_api), db: Session = Depends(get_db)):
    tax_rate = data.get("tax_rate", 0.04 if data.get("type") == "income" else 0)
    tax_amount = data.get("amount", 0) * tax_rate if data.get("type") == "income" and tax_rate > 0 else 0
    record = FinanceRecord(user_id=user.id, type=data.get("type", "income"), amount=data.get("amount", 0), category=data.get("category"), description=data.get("description"), client_name=data.get("client_name"), tax_rate=tax_rate, tax_amount=tax_amount)
    db.add(record)
    db.commit()
    db.refresh(record)
    if record.type == "income":
        ach = db.query(Achievement).filter(Achievement.condition_type == "income").first()
        if ach and not db.query(UserAchievement).filter(UserAchievement.user_id == user.id, UserAchievement.achievement_id == ach.id).first():
            db.add(UserAchievement(user_id=user.id, achievement_id=ach.id))
            db.commit()
    log_audit(db, user.id, "create_finance", "finance", record.id)
    return {"success": True, "record": {"id": record.id, "type": record.type, "amount": record.amount, "tax_amount": record.tax_amount}}

@app.get("/api/finance")
async def api_list_finance(user: User = Depends(get_current_user_api), db: Session = Depends(get_db)):
    records = db.query(FinanceRecord).filter(FinanceRecord.user_id == user.id).order_by(FinanceRecord.date.desc()).all()
    total_income = sum(r.amount for r in records if r.type == "income")
    total_expense = sum(r.amount for r in records if r.type == "expense")
    total_tax = sum(r.tax_amount for r in records)
    return {"records": [{"id": r.id, "type": r.type, "amount": r.amount, "category": r.category, "description": r.description, "tax_amount": r.tax_amount, "date": r.date.isoformat()} for r in records], "summary": {"total_income": total_income, "total_expense": total_expense, "total_tax": total_tax}}

# ============ API: CRM ============
@app.post("/api/crm/contacts")
async def api_create_contact(data: dict, user: User = Depends(get_current_user_api), db: Session = Depends(get_db)):
    contact = CRMContact(owner_id=user.id, name=data.get("name"), email=data.get("email"), phone=data.get("phone"), company=data.get("company"), notes=data.get("notes"), status=data.get("status", "lead"), source=data.get("source"))
    db.add(contact)
    db.commit()
    db.refresh(contact)
    cc = db.query(CRMContact).filter(CRMContact.owner_id == user.id).count()
    for ach in db.query(Achievement).filter(Achievement.condition_type == "crm_contacts").all():
        if cc >= ach.condition_value and not db.query(UserAchievement).filter(UserAchievement.user_id == user.id, UserAchievement.achievement_id == ach.id).first():
            db.add(UserAchievement(user_id=user.id, achievement_id=ach.id))
            db.commit()
    log_audit(db, user.id, "create_contact", "crm", contact.id)
    return {"success": True, "contact": {"id": contact.id, "name": contact.name, "status": contact.status}}

@app.get("/api/crm/contacts")
async def api_list_contacts(user: User = Depends(get_current_user_api), db: Session = Depends(get_db)):
    contacts = db.query(CRMContact).filter(CRMContact.owner_id == user.id).order_by(CRMContact.created_at.desc()).all()
    return {"contacts": [{"id": c.id, "name": c.name, "email": c.email, "phone": c.phone, "company": c.company, "status": c.status, "created_at": c.created_at.isoformat()} for c in contacts]}

# ============ API: MARKETPLACE ============
@app.post("/api/marketplace/items")
async def api_create_item(data: dict, user: User = Depends(get_current_user_api), db: Session = Depends(get_db)):
    item = MarketplaceItem(seller_id=user.id, title=data.get("title"), description=data.get("description"), price=data.get("price", 0), category=data.get("category"), tags=data.get("tags", []), images=data.get("images", []))
    db.add(item)
    db.commit()
    db.refresh(item)
    ach = db.query(Achievement).filter(Achievement.condition_type == "marketplace").first()
    if ach and not db.query(UserAchievement).filter(UserAchievement.user_id == user.id, UserAchievement.achievement_id == ach.id).first():
        db.add(UserAchievement(user_id=user.id, achievement_id=ach.id))
        db.commit()
    log_audit(db, user.id, "create_marketplace_item", "marketplace", item.id)
    return {"success": True, "item": {"id": item.id, "title": item.title, "price": item.price}}

@app.get("/api/marketplace/items")
async def api_list_items(category: str = None, search: str = None, db: Session = Depends(get_db)):
    query = db.query(MarketplaceItem).filter(MarketplaceItem.is_active == True)
    if category: query = query.filter(MarketplaceItem.category == category)
    if search: query = query.filter(MarketplaceItem.title.ilike(f"%{search}%"))
    items = query.order_by(MarketplaceItem.created_at.desc()).all()
    return {"items": [{"id": i.id, "title": i.title, "price": i.price, "category": i.category, "seller_name": i.seller.full_name if i.seller else None} for i in items]}

# ============ API: GRANTS ============
@app.get("/api/grants")
async def api_list_grants(category: str = None, region: str = None, db: Session = Depends(get_db)):
    query = db.query(Grant).filter(Grant.status == "active")
    if category: query = query.filter(Grant.category == category)
    if region: query = query.filter(Grant.region == region)
    grants = query.order_by(Grant.deadline.asc()).all()
    return {"grants": [{"id": g.id, "title": g.title, "organization": g.organization, "amount_min": g.amount_min, "amount_max": g.amount_max, "deadline": g.deadline.isoformat() if g.deadline else None, "category": g.category, "region": g.region} for g in grants]}

# ============ API: NOTIFICATIONS ============
@app.get("/api/notifications")
async def api_notifications(user: User = Depends(get_current_user_api), db: Session = Depends(get_db), unread_only: bool = False):
    query = db.query(Notification).filter(Notification.user_id == user.id)
    if unread_only: query = query.filter(Notification.is_read == False)
    notifications = query.order_by(Notification.created_at.desc()).all()
    return {"notifications": [{"id": n.id, "title": n.title, "message": n.message, "type": n.type.value, "is_read": n.is_read, "created_at": n.created_at.isoformat()} for n in notifications]}

@app.post("/api/notifications/{notif_id}/read")
async def api_mark_read(notif_id: int, user: User = Depends(get_current_user_api), db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(Notification.id == notif_id, Notification.user_id == user.id).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"success": True}

# ============ API: ACHIEVEMENTS ============
@app.get("/api/achievements")
async def api_achievements(user: User = Depends(get_current_user_api), db: Session = Depends(get_db)):
    user_achs = db.query(UserAchievement).filter(UserAchievement.user_id == user.id).all()
    all_achs = db.query(Achievement).all()
    earned_ids = {ua.achievement_id for ua in user_achs}
    return {"earned": [{"id": a.achievement.id, "name": a.achievement.name, "description": a.achievement.description, "icon": a.achievement.icon, "points": a.achievement.points, "earned_at": a.earned_at.isoformat()} for a in user_achs], "available": [{"id": a.id, "name": a.name, "description": a.description, "icon": a.icon, "points": a.points} for a in all_achs if a.id not in earned_ids], "total_points": sum(a.achievement.points for a in user_achs)}

# ============ API: SVETLANA ============
@app.post("/api/svetlana/chat")
async def api_svetlana_chat(data: dict, user: User = Depends(get_current_user_api), db: Session = Depends(get_db)):
    message = data.get("message", "")
    session_id = data.get("session_id", str(uuid.uuid4()))
    responses = {
        "привет": "Здравствуйте! Я Светлана, ваш ИИ-ассистент. Чем могу помочь?",
        "налог": "Самозанятые платят НПД: 4% с физлиц, 6% с юрлиц и ИП. Налоговый вычет 10 000 ₽ применяется автоматически.",
        "вычет": "Налоговый вычет 10 000 ₽ для самозанятых. Применяется в приложении Мой налог.",
        "договор": "Я могу помочь с шаблонами: ГПД, счёт, акт выполненных работ, чек НПД.",
        "тариф": "Тарифы: START (бесплатно), PRO (300 ₽/мес), BUSINESS (990 ₽/мес), ENTERPRISE (индивидуально).",
        "регистрация": "Для регистрации самозанятым скачайте приложение Мой налог или обратитесь в ФНС.",
        "штраф": "Штраф за неуплату НПД — 20% от суммы + пени 1/300 ставки рефинансирования.",
        "ип": "Самозанятость и ИП — разные режимы. Самозанятый не платит фиксированные взносы, но имеет ограничения по доходу (2.4 млн ₽/год).",
        "грант": "В разделе Гранты вы найдёте актуальные программы поддержки.",
        "crm": "CRM помогает управлять клиентами. Добавляйте контакты, отслеживайте статусы.",
    }
    reply = "Я пока работаю в режиме базы знаний. Задайте вопрос о налогах, договорах, тарифах или грантах."
    for key, resp in responses.items():
        if key in message.lower():
            reply = resp
            break
    chat = SvetlanaChat(user_id=user.id, session_id=session_id, message=message, response=reply, category="general")
    db.add(chat)
    db.commit()
    chats_count = db.query(SvetlanaChat).filter(SvetlanaChat.user_id == user.id).count()
    for ach in db.query(Achievement).filter(Achievement.condition_type == "svetlana_chats").all():
        if chats_count >= ach.condition_value and not db.query(UserAchievement).filter(UserAchievement.user_id == user.id, UserAchievement.achievement_id == ach.id).first():
            db.add(UserAchievement(user_id=user.id, achievement_id=ach.id))
            db.commit()
    return {"reply": reply, "session_id": session_id, "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/svetlana/history")
async def api_svetlana_history(user: User = Depends(get_current_user_api), db: Session = Depends(get_db), limit: int = 50):
    chats = db.query(SvetlanaChat).filter(SvetlanaChat.user_id == user.id).order_by(SvetlanaChat.created_at.desc()).limit(limit).all()
    return {"history": [{"message": c.message, "response": c.response, "created_at": c.created_at.isoformat()} for c in chats]}

# ============ API: ADMIN ============
@app.get("/api/admin/users")
async def api_admin_users(user: User = Depends(get_current_user_api), db: Session = Depends(get_db)):
    if user.role.value not in ["admin", "moderator"]: raise HTTPException(status_code=403, detail="Доступ запрещён")
    users = db.query(User).order_by(User.created_at.desc()).all()
    return {"users": [{"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role.value, "subscription": u.subscription.value, "is_active": u.is_active, "created_at": u.created_at.isoformat()} for u in users]}

@app.get("/api/admin/stats")
async def api_admin_stats(user: User = Depends(get_current_user_api), db: Session = Depends(get_db)):
    if user.role.value != "admin": raise HTTPException(status_code=403, detail="Доступ запрещён")
    return {"users_count": db.query(User).count(), "active_users": db.query(User).filter(User.is_active == True).count(), "contracts_count": db.query(Contract).count(), "total_income": sum(r.amount for r in db.query(FinanceRecord).filter(FinanceRecord.type == "income").all()), "payments_count": db.query(Payment).filter(Payment.status == PaymentStatus.COMPLETED).count(), "marketplace_items": db.query(MarketplaceItem).filter(MarketplaceItem.is_active == True).count()}

@app.get("/api/admin/audit")
async def api_admin_audit(user: User = Depends(get_current_user_api), db: Session = Depends(get_db), limit: int = 100):
    if user.role.value != "admin": raise HTTPException(status_code=403, detail="Доступ запрещён")
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return {"logs": [{"id": l.id, "user_id": l.user_id, "action": l.action, "entity_type": l.entity_type, "details": l.details, "created_at": l.created_at.isoformat()} for l in logs]}

# ============ ERROR HANDLERS ============
@app.exception_handler(404)
async def not_found(request: Request, exc):
    if request.url.path.startswith("/api/"): return JSONResponse({"error": "Not found"}, status_code=404)
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

@app.exception_handler(500)
async def server_error(request: Request, exc):
    if request.url.path.startswith("/api/"): return JSONResponse({"error": "Internal server error"}, status_code=500)
    return templates.TemplateResponse("500.html", {"request": request}, status_code=500)
