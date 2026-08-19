#!/usr/bin/env python3
"""Static regression checks for v8.4.37 large business-flow hardening."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
errors=[]
checks={
"CSV deal import verifies client ownership": 'Client.id == client_id' in (ROOT/'app/api/import_export.py').read_text() and 'Client.user_id == current_user.id' in (ROOT/'app/api/import_export.py').read_text(),
"Automation task verifies client ownership": 'Automation client does not belong to user' in (ROOT/'app/api/crm.py').read_text(),
"Automation task verifies deal ownership": 'Automation deal does not belong to user' in (ROOT/'app/api/crm.py').read_text(),
"Automation move verifies stage ownership": 'Automation stage does not belong to user' in (ROOT/'app/api/crm.py').read_text(),
"Single email is rate limited": '@rate_limit("20/minute")' in (ROOT/'app/api/email_campaigns.py').read_text(),
"Single email reports provider failure as 502": 'Почтовый сервис временно недоступен' in (ROOT/'app/api/email_campaigns.py').read_text(),
"WhatsApp send is rate limited": '@rate_limit("20/minute")' in (ROOT/'app/api/whatsapp.py').read_text(),
"WhatsApp client ownership is enforced": 'Клиент не найден' in (ROOT/'app/api/whatsapp.py').read_text(),
"WhatsApp message length bounded": 'len(data.message) > 4096' in (ROOT/'app/api/whatsapp.py').read_text(),
"Versions synchronized": all('8.4.37' in (ROOT/f).read_text() for f in ['app/core/config.py','frontend/package.json','mobile/pubspec.yaml']),
}
for n,ok in checks.items():
    if not ok: errors.append(n)
if errors:
    print('FAIL'); [print(' -',e) for e in errors]; raise SystemExit(1)
print('v8.4.37 integrity: 10/10 PASS')
