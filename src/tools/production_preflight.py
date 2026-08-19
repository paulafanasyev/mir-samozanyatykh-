#!/usr/bin/env python3
import base64, os, re, sys
required = ["SECRET_KEY","BANK_ENCRYPTION_KEY","POSTGRES_PASSWORD","REDIS_PASSWORD","DOMAIN","FRONTEND_URL"]
missing=[k for k in required if not os.getenv(k)]
if missing:
    print("Missing required production variables: " + ", ".join(missing)); sys.exit(1)
if os.getenv("DEBUG","false").lower() in {"1","true","yes","on"}:
    print("DEBUG must be false in production"); sys.exit(1)
if len(os.environ["SECRET_KEY"]) < 64:
    print("SECRET_KEY must be at least 64 characters"); sys.exit(1)
try:
    raw=base64.urlsafe_b64decode(os.environ["BANK_ENCRYPTION_KEY"] + "=" * (-len(os.environ["BANK_ENCRYPTION_KEY"]) % 4))
except Exception:
    print("BANK_ENCRYPTION_KEY is not valid URL-safe base64"); sys.exit(1)
if len(raw) != 32:
    print("BANK_ENCRYPTION_KEY must decode to exactly 32 bytes"); sys.exit(1)
for k in ("POSTGRES_PASSWORD","REDIS_PASSWORD"):
    if len(os.environ[k]) < 24 or os.environ[k].startswith(("CHANGE_ME","your-","change-me")):
        print(f"{k} is too weak or still a placeholder"); sys.exit(1)
if os.getenv("ENVIRONMENT") == "production":
    domain = os.environ["DOMAIN"].strip()
    if "localhost" in domain.lower() or "127.0.0.1" in domain:
        print("DOMAIN cannot point to localhost/127.0.0.1 in production"); sys.exit(1)
    if "://" in domain or "/" in domain or any(ch.isspace() for ch in domain):
        print("DOMAIN must be a hostname without scheme, path, or whitespace"); sys.exit(1)
    if not re.match(r"^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}$", domain):
        print("DOMAIN must be a valid DNS hostname"); sys.exit(1)
    if not re.match(r"^https://[^\s/]+(?:/.*)?$", os.environ["FRONTEND_URL"]):
        print("FRONTEND_URL must use HTTPS in production"); sys.exit(1)
print("production preflight: PASS")
