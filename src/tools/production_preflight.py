#!/usr/bin/env python3
"""Validate the environment required before starting the production API."""
import base64
import os
import re
import sys


def fail(message: str) -> None:
    print(message)
    sys.exit(1)


required = [
    "SECRET_KEY",
    "BANK_ENCRYPTION_KEY",
    "DATABASE_URL",
    "REDIS_URL",
    "DOMAIN",
    "FRONTEND_URL",
]
missing = [key for key in required if not os.getenv(key)]
if missing:
    fail("Missing required production variables: " + ", ".join(missing))

if os.getenv("DEBUG", "false").lower() in {"1", "true", "yes", "on"}:
    fail("DEBUG must be false in production")

if len(os.environ["SECRET_KEY"]) < 64:
    fail("SECRET_KEY must be at least 64 characters")

try:
    raw = base64.urlsafe_b64decode(
        os.environ["BANK_ENCRYPTION_KEY"]
        + "=" * (-len(os.environ["BANK_ENCRYPTION_KEY"]) % 4)
    )
except Exception:
    fail("BANK_ENCRYPTION_KEY is not valid URL-safe base64")

if len(raw) != 32:
    fail("BANK_ENCRYPTION_KEY must decode to exactly 32 bytes")

# Render may provide a PostgreSQL connection URL in a driver-specific form.
# Do not second-guess the exact URI syntax here: SQLAlchemy/asyncpg and the
# Alembic migration below are the authoritative checks for credentials,
# hostname, SSL options, driver, and actual database connectivity.
database_url = os.environ["DATABASE_URL"].strip()
if not database_url or any(ch.isspace() for ch in database_url):
    fail("DATABASE_URL must be a non-empty connection URL without whitespace")

redis_url = os.environ["REDIS_URL"].strip()
if not redis_url or any(ch.isspace() for ch in redis_url):
    fail("REDIS_URL must be a non-empty connection URL without whitespace")

if os.getenv("ENVIRONMENT") == "production":
    domain = os.environ["DOMAIN"].strip()
    if "localhost" in domain.lower() or "127.0.0.1" in domain:
        fail("DOMAIN cannot point to localhost/127.0.0.1 in production")
    if "://" in domain or "/" in domain or any(ch.isspace() for ch in domain):
        fail("DOMAIN must be a hostname without scheme, path, or whitespace")
    if not re.match(
        r"^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}$",
        domain,
    ):
        fail("DOMAIN must be a valid DNS hostname")
    if not re.match(r"^https://[^\s/]+(?:/.*)?$", os.environ["FRONTEND_URL"]):
        fail("FRONTEND_URL must use HTTPS in production")

print("production preflight: PASS")
