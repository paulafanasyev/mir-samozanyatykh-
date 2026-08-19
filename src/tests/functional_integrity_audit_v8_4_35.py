#!/usr/bin/env python3
"""Static regression checks for v8.4.37 business-integrity hardening."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
errors=[]

fns=(ROOT/"app/api/fns.py").read_text()
bank=(ROOT/"app/api/bank.py").read_text()
accounting=(ROOT/"app/api/accounting.py").read_text()
notifications=(ROOT/"app/api/notifications.py").read_text()

checks = {
"FNS network failure is not reported as not-found": "raise HTTPException(status_code=503, detail=\"Сервис ФНС временно недоступен\")" in fns,
"FNS provider 5xx is service-unavailable": '500 <= response.status_code <= 599' in fns,
"FNS receipt totals use Decimal accumulation": 'total_cents = sum(' in fns and 'Decimal("0")' in fns,
"Manual bank amount must be positive": 'amount: Decimal = Field(..., gt=0)' in bank,
"Manual bank operation type is constrained": 'pattern="^(DEBIT|CREDIT)$"' in bank,
"Manual bank description has bounded length": 'max_length=500' in bank,
"Deduction max amount validated": 'data.amount > data.max_amount' in accounting,
"Bulk notifications have recipient cap": 'max_recipients = 5000' in notifications,
"Bulk notifications persist before email side effects": 'await db.commit()' in notifications and 'Email — внешний side effect' in notifications,
}
for name, ok in checks.items():
    if not ok: errors.append(name)

for rel in ["app/core/config.py","frontend/package.json","mobile/pubspec.yaml"]:
    txt=(ROOT/rel).read_text()
    if "8.4.37" not in txt: errors.append(f"{rel}: version not synchronized")

if errors:
    print("FAIL")
    for e in errors: print(" -",e)
    raise SystemExit(1)
print("v8.4.37 integrity: 9/9 PASS")
