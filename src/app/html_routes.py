"""
HTML Page Routes — Mir Samozanyatykh v8.4
АНО ЦПС ИНН 9724016805
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path
import os
router=APIRouter(tags=["pages"])
templates=Jinja2Templates(directory="templates",context_processors=[lambda request:{"csp_nonce":getattr(request.state,"csp_nonce","")}])
# Work Russia sphere-of-activity dictionary used by the marketplace. The portal exposes vacancy filtering by sphere/industry; we use the same established names for our vacancy/service forms.
MARKETPLACE_DIRECTIONS=[
 "Автомобильный бизнес","Административный персонал","Банки, инвестиции, лизинг","Безопасность","Бухгалтерия, управленческий учет, финансы предприятия","Высший менеджмент","Государственная служба, некоммерческие организации","Добыча сырья","Домашний персонал","Закупки","Инсталляция и сервис","Информационные технологии, интернет, телеком","Искусство, развлечения, масс-медиа","Консультирование","Логистика","Маркетинг, реклама, PR","Медицина, фармацевтика","Наука, образование","Продажи","Производство","Рабочий персонал","Сельское хозяйство","Строительство, недвижимость","Транспорт, логистика","Туризм, гостиницы, рестораны","Управление персоналом, тренинги","Юристы","Начало карьеры, студенты","Работы, не требующие квалификации","Продажи и бытовое обслуживание","Финансы","Управление персоналом","Здравоохранение","Искусство, культура и развлечения","Сельское хозяйство, экология, ветеринария","Финансы, кредит, страхование","Юриспруденция","Услуги населению"
]
# preserve order while removing repeated legacy labels
MARKETPLACE_DIRECTIONS=list(dict.fromkeys(MARKETPLACE_DIRECTIONS))
@router.get("/",response_class=HTMLResponse)
async def index(request:Request):return templates.TemplateResponse("index.html",{"request":request})
@router.get("/downloads",response_class=HTMLResponse)
async def downloads_page(request:Request):
 android_path=Path("downloads/mir-samozanyatykh-android.apk");ios_url=os.getenv("IOS_APP_URL","");return templates.TemplateResponse("downloads.html",{"request":request,"android_available":android_path.is_file(),"ios_url":ios_url})
@router.get("/api/downloads/status")
async def downloads_status():
 android_path=Path("downloads/mir-samozanyatykh-android.apk");return {"android_available":android_path.is_file(),"ios_url":os.getenv("IOS_APP_URL","")}
@router.get("/downloads/android")
async def android_download():
 path=Path("downloads/mir-samozanyatykh-android.apk")
 if not path.is_file():raise HTTPException(status_code=404,detail="Android APK is not published")
 return FileResponse(path,media_type="application/vnd.android.package-archive",filename=path.name)
@router.get("/login",response_class=HTMLResponse)
async def login_page(request:Request):return templates.TemplateResponse("login.html",{"request":request})
@router.get("/register",response_class=HTMLResponse)
async def register_page(request:Request):return templates.TemplateResponse("register.html",{"request":request})
@router.get("/about",response_class=HTMLResponse)
async def about_page(request:Request):return templates.TemplateResponse("about.html",{"request":request})
@router.get("/dashboard",response_class=HTMLResponse)
async def dashboard_page(request:Request):return templates.TemplateResponse("dashboard.html",{"request":request})
@router.get("/profile",response_class=HTMLResponse)
async def profile_page(request:Request):
 user={"name":"","email":"","activity":"","level":None,"status":"Не авторизован","total_income":None,"total_tax":None,"clients":None,"achievements":None};return templates.TemplateResponse("profile.html",{"request":request,"user":user})
@router.get("/svetlana",response_class=HTMLResponse)
async def svetlana_page(request:Request):return templates.TemplateResponse("svetlana.html",{"request":request})
@router.get("/contracts",response_class=HTMLResponse)
async def contracts_page(request:Request):return templates.TemplateResponse("contracts.html",{"request":request})
@router.get("/crm",response_class=HTMLResponse)
async def crm_page(request:Request):return templates.TemplateResponse("crm.html",{"request":request})
@router.get("/finance",response_class=HTMLResponse)
async def finance_page(request:Request):return templates.TemplateResponse("finance.html",{"request":request})
@router.get("/calendar",response_class=HTMLResponse)
async def calendar_page(request:Request):return templates.TemplateResponse("calendar.html",{"request":request})
@router.get("/marketplace",response_class=HTMLResponse)
async def marketplace_page(request:Request):return templates.TemplateResponse("marketplace.html",{"request":request,"marketplace_directions":MARKETPLACE_DIRECTIONS})
@router.get("/education",response_class=HTMLResponse)
async def education_page(request:Request):return templates.TemplateResponse("education.html",{"request":request})
@router.get("/grants",response_class=HTMLResponse)
async def grants_page(request:Request):return templates.TemplateResponse("grants.html",{"request":request})
@router.get("/achievements",response_class=HTMLResponse)
async def achievements_page(request:Request):return templates.TemplateResponse("achievements.html",{"request":request})
@router.get("/blog",response_class=HTMLResponse)
async def blog_page(request:Request):return templates.TemplateResponse("blog.html",{"request":request})
@router.get("/faq",response_class=HTMLResponse)
async def faq_page(request:Request):return templates.TemplateResponse("faq.html",{"request":request})
@router.get("/support",response_class=HTMLResponse)
async def support_page(request:Request):return templates.TemplateResponse("support.html",{"request":request})
@router.get("/contacts",response_class=HTMLResponse)
async def contacts_page(request:Request):return templates.TemplateResponse("contacts.html",{"request":request})
@router.get("/privacy",response_class=HTMLResponse)
async def privacy_page(request:Request):return templates.TemplateResponse("privacy.html",{"request":request})
@router.get("/terms",response_class=HTMLResponse)
async def terms_page(request:Request):return templates.TemplateResponse("terms.html",{"request":request})
@router.get("/calculator",response_class=HTMLResponse)
async def calculator_page(request:Request):return templates.TemplateResponse("calculator.html",{"request":request})
@router.get("/projects",response_class=HTMLResponse)
async def projects_page(request:Request):return templates.TemplateResponse("projects.html",{"request":request})
