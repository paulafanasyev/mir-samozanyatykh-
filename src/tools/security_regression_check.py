from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []
def check(name, condition): checks.append((name, bool(condition)))

auth=(ROOT/"app/api/auth.py").read_text(); security=(ROOT/"app/core/security.py").read_text()
store=(ROOT/"frontend/src/stores/authStore.ts").read_text(); nginx=(ROOT/"nginx/nginx.conf").read_text(); bank=(ROOT/"app/api/bank.py").read_text()
enc=(ROOT/"app/services/encryption.py").read_text(); config=(ROOT/"app/core/config.py").read_text(); mfa=(ROOT/"app/api/mfa.py").read_text()
check("hashed email verification", "email_verification_token_hash=hash_token" in auth and "email_verification_expires_at" in auth)
check("hashed password reset", "password_reset_token_hash = hash_token" in auth and "password_reset_expires_at" in auth)
check("access token not persisted by Zustand", "persist(" not in store and "localStorage.setItem" not in store)
check("legacy HTML auth token storage removed", not any("localStorage.getItem('access_token')" in (ROOT/'templates'/n).read_text() for n in ['login.html','dashboard.html','marketplace.html','finance.html','crm.html','grants.html','achievements.html']))
check("CSP legacy unsafe-inline removed from nginx", "unsafe-inline" not in nginx)
check("legacy XSS header removed", "X-XSS-Protection" not in nginx and "X-XSS-Protection" not in (ROOT/'app/core/middleware.py').read_text())
check("bank tokens use AES-GCM service", "get_token_encryption().encrypt" in bank and "base64.b64encode(token.encode())" not in bank)
check("separate 32-byte bank key", "BANK_ENCRYPTION_KEY" in enc and "BANK_ENCRYPTION_KEY must decode to exactly 32 bytes" in config)
check("refresh rotation uses row lock", ".with_for_update()" in auth)
check("2FA pending tokens rejected", "2fa_pending" in security and "cannot access protected resources" in security)
check("backup codes hashed", "get_password_hash(code)" in mfa and "verify_password(verify.code" in mfa)
check("accounting dashboard returns real counts", "pending_invoices=pending_invoices" in (ROOT/'app/api/accounting.py').read_text() and "transactions_count=transactions_count" in (ROOT/'app/api/accounting.py').read_text())
check("production artifacts absent", not any(p.name in {'.git','__pycache__','.pytest_cache','test.db'} or p.suffix in {'.pyc','.pyo','.log'} for p in ROOT.rglob('*')))
failed=[n for n,ok in checks if not ok]
for n,ok in checks: print(("PASS" if ok else "FAIL")+" "+n)
print(f"RESULT: {len(checks)-len(failed)}/{len(checks)} PASS")
raise SystemExit(1 if failed else 0)
