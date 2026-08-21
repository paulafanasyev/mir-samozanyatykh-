"""
HTML Page Routes — Mir Samozanyatykh v8.3.3
АНО ЦПС ИНН 9724016805
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path
import os

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(
    directory="templates",
    context_processors=[lambda request: {"csp_nonce": getattr(request.state, "csp_nonce", "")}],
)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/downloads", response_class=HTMLResponse)
async def downloads_page(request: Request):
    android_path = Path("downloads/mir-samozanyatykh-android.apk")
    ios_url = os.getenv("IOS_APP_URL", "")
    return templates.TemplateResponse("downloads.html", {"request": request, "android_available": android_path.is_file(), "ios_url": ios_url})

@router.get("/api/downloads/status")
async def downloads_status():
    android_path = Path("downloads/mir-samozanyatykh-android.apk")
    return {"android_available": android_path.is_file(), "ios_url": os.getenv("IOS_APP_URL", "")}

@router.get("/downloads/android")
async def android_download():
    path = Path("downloads/mir-samozanyatykh-android.apk")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Android APK is not published")
    return FileResponse(path, media_type="application/vnd.android.package-archive", filename=path.name)

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    user = {"name": "", "email": "", "activity": "", "level": None, "status": "Не авторизован", "total_income": None, "total_tax": None, "clients": None, "achievements": None}
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})

@router.get("/svetlana", response_class=HTMLResponse)
async def svetlana_page(request: Request):
    return templates.TemplateResponse("svetlana.html", {"request": request})

@router.post("/api/svetlana/chat")
async def public_svetlana_chat(request: Request):
    """Public, offline-first Svetlana endpoint. No external model/provider is called here."""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    message = str((payload or {}).get("message", "")).strip()
    if not message:
        raise HTTPException(status_code=422, detail="message is required")
    text = message.lower()
    if any(x in text for x in ("налог", "ндп", "ндфл")):
        answer = "По НПД базовая ставка — 4% с доходов от физических лиц и 6% с доходов от организаций и ИП. Для точной суммы используйте калькулятор и проверяйте итог в ФНС."
    elif any(x in text for x in ("регистра", "войти", "аккаунт")):
        answer = "Для начала работы зарегистрируйтесь. После авторизации откроется Личный кабинет с вашими рабочими разделами."
    elif any(x in text for x in ("маркет", "заказ", "услуг", "ваканс")):
        answer = "В Маркетплейсе работодатели и самозанятые могут размещать вакансии, услуги, проектные задачи и предложения о партнёрстве."
    elif any(x in text for x in ("документ", "договор", "акт")):
        answer = "Я могу помочь выбрать подходящий документ и объяснить, какие данные нужны для его подготовки."
    elif any(x in text for x in ("светлана", "ты кто", "кто ты")):
        answer = "Я Светлана — локальный ИИ-помощник «Мира Самозанятых». На публичной странице я работаю в офлайн-first режиме."
    else:
        answer = "Я Светлана. Расскажите, что нужно сделать: налоги, регистрация, документы, услуги, поиск работы или работа с платформой."
    return {"response": answer, "mode": "offline-first"}

@router.get("/contracts", response_class=HTMLResponse)
async def contracts_page(request: Request):
    return templates.TemplateResponse("contracts.html", {"request": request})

@router.get("/crm", response_class=HTMLResponse)
async def crm_page(request: Request):
    return templates.TemplateResponse("crm.html", {"request": request})

@router.get("/finance", response_class=HTMLResponse)
async def finance_page(request: Request):
    return templates.TemplateResponse("finance.html", {"request": request})

@router.get("/marketplace", response_class=HTMLResponse)
async def marketplace_page(request: Request):
    return templates.TemplateResponse("marketplace.html", {"request": request})

@router.get("/grants", response_class=HTMLResponse)
async def grants_page(request: Request):
    return templates.TemplateResponse("grants.html", {"request": request})

@router.get("/achievements", response_class=HTMLResponse)
async def achievements_page(request: Request):
    return templates.TemplateResponse("achievements.html", {"request": request})

@router.get("/blog", response_class=HTMLResponse)
async def blog_page(request: Request):
    return templates.TemplateResponse("blog.html", {"request": request})

@router.get("/calculator", response_class=HTMLResponse)
async def calculator_page(request: Request):
    return templates.TemplateResponse("calculator.html", {"request": request})

@router.get("/projects", response_class=HTMLResponse)
async def projects_page(request: Request):
    return templates.TemplateResponse("projects.html", {"request": request})
