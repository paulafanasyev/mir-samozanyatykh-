from pathlib import Path
import re, sys
root=Path(__file__).resolve().parents[1]
checks={}
client=(root/"frontend/src/api/client.ts").read_text()
cal=(root/"frontend/src/pages/CalendarPage.tsx").read_text()
tasks=(root/"frontend/src/pages/Tasks.tsx").read_text()
web=(root/"app/api/webhooks.py").read_text()
integ=(root/"frontend/src/pages/Integrations.tsx").read_text()
analytics=(root/"app/api/analytics.py").read_text()
checks["frontend API namespace normalization"]="config.url = `/api${config.url}`" in client
checks["frontend accepts host or /api VITE base"]="replace(/\\/api$/, '')" in client
checks["calendar uses API namespace"]="/api/calendar/view/month" in cal and "'/api/calendar/today'" in cal and "'/api/calendar/events'" in cal
checks["webhook create uses JSON schema"]="class WebhookCreate(BaseModel)" in web and "events: List[str]" in web
checks["webhook stores events field"]="events=webhook_in.events" in web and "w.events or []" in web
checks["webhook delivery endpoint exists"]='@router.get("/{webhook_id}/deliveries")' in web
checks["webhook delivery is owner scoped"]="Webhook.id == webhook_id, Webhook.user_id == current_user.id" in web
checks["webhook test records delivery"]="WebhookDelivery(webhook_id=webhook.id" in web
checks["integrations handles webhook test response"]="res.data.http_status" in integ
checks["analytics month range bounded"]="Query(6, ge=1, le=24)" in analytics
checks["analytics uses calendar month arithmetic"]="month_index = now.year * 12" in analytics
checks["frontend no unprefixed API calls"] = not any(re.search(r"api\.(?:get|post|put|delete|patch)\(\s*['\"`]/(?!api/)", Path(f).read_text()) for f in list(root.glob("frontend/src/**/*.tsx"))+list(root.glob("frontend/src/**/*.ts")))
for n,v in checks.items(): print(("PASS" if v else "FAIL")+" "+n)
print(f"RESULT: {sum(checks.values())}/{len(checks)} PASS")
sys.exit(0 if all(checks.values()) else 1)
