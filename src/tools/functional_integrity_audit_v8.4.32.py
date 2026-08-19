from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
checks=[]
def check(n,c): checks.append((n,bool(c)))
models=(ROOT/'app/models.py').read_text(); white=(ROOT/'app/api/white_label.py').read_text(); email=(ROOT/'app/api/email_campaigns.py').read_text(); sv=(ROOT/'app/api/svetlana.py').read_text(); mig=(ROOT/'alembic/versions/v852_persist_user_experience.py').read_text(); config=(ROOT/'app/core/config.py').read_text()
check('white-label settings have persistent model storage','branding_settings = Column(JSON' in models)
check('white-label PUT persists settings','current_user.branding_settings = branding' in white and 'await db.commit()' in white)
check('white-label GET reads persisted settings','dict(current_user.branding_settings or {})' in white)
check('white-label colors are validated','_validate_color' in white and '#[0-9A-Fa-f]{6}' in white)
logo=white.split('@router.post("/logo")',1)[1].split('@router.get("/logo/{filename}")',1)[0]
check('SVG logo upload disabled','.svg' not in logo)
check('white-label file security helpers imported','from app.core.file_security import validate_upload, read_limited, private_storage_path' in white)
check('Svetlana messages persisted','SvetlanaChatMessage' in sv and '_save_message' in sv)
check('Svetlana history is user scoped and bounded','SvetlanaChatMessage.user_id == current_user.id' in sv and 'min(limit, 200)' in sv)
check('email campaigns persisted','EmailCampaign' in email and 'db_campaign = EmailCampaign' in email)
check('email campaign list is user scoped','EmailCampaign.user_id == current_user.id' in email)
check('email campaign status is persisted','status="completed"' in email and 'status="failed"' in email)
check('email campaign SMTP TLS uses configured setting','settings.SMTP_TLS' in email)
check('v852 migration adds branding column','branding_settings' in mig and 'op.add_column("users"' in mig)
check('v852 migration adds Svetlana table','svetlana_chat_messages' in mig)
check('v852 migration adds email campaign table','email_campaigns' in mig)
check('version synchronized','APP_VERSION: str = "8.4.33"' in config and '"version": "8.4.33"' in (ROOT/'frontend/package.json').read_text() and 'version: 8.4.33+857' in (ROOT/'mobile/pubspec.yaml').read_text())
failed=[n for n,o in checks if not o]
for n,o in checks: print(('PASS' if o else 'FAIL')+' '+n)
print(f'RESULT: {len(checks)-len(failed)}/{len(checks)} PASS')
raise SystemExit(1 if failed else 0)
