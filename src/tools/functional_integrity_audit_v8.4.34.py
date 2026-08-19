from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
checks=[]
def check(n,c): checks.append((n,bool(c)))
imp=(ROOT/"app/api/import_data.py").read_text()
ref=(ROOT/"app/api/referrals.py").read_text()
tasks=(ROOT/"app/api/tasks.py").read_text()
config=(ROOT/"app/core/config.py").read_text()
frontend=(ROOT/"frontend/package.json").read_text()
mobile=(ROOT/"mobile/pubspec.yaml").read_text()

check("CSV preview requires authentication", 'current_user: User = Depends(get_current_user)' in imp and 'async def preview_import' in imp)
check("CSV preview rows bounded", 'max_rows: int = Query(10, ge=1, le=100)' in imp)
check("product import uses Decimal", 'from decimal import Decimal, InvalidOperation' in imp and 'price = Decimal(price_str)' in imp)
check("referral apply locks referred user", 'select(User).where(User.id == current_user.id).with_for_update()' in ref)
check("referral apply handles uniqueness race", 'except IntegrityError:' in ref and 'status_code=409' in ref)
check("referral reward locks referral", 'select(Referral).where(Referral.id == referral_id).with_for_update()' in ref)
check("referral reward credits actual referrer", 'User.id == referral.referrer_id' in ref)
check("task creation validates client ownership", 'Client.id == task.client_id, Client.user_id == current_user.id' in tasks)
check("task creation validates deal ownership", 'Deal.id == task.deal_id, Deal.user_id == current_user.id' in tasks)
check("version synchronized", 'APP_VERSION: str = "8.4.35"' in config and '"version": "8.4.35"' in frontend and 'version: 8.4.35+859' in mobile)
failed=[n for n,o in checks if not o]
for n,o in checks: print(("PASS" if o else "FAIL")+" "+n)
print(f"RESULT: {len(checks)-len(failed)}/{len(checks)} PASS")
raise SystemExit(1 if failed else 0)
