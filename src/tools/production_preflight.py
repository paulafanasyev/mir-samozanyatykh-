#!/usr/bin/env python3
"""Validate the environment required before starting the production API."""
import base64
import os
import re
import sys
from urllib.parse import urlparse


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

# Render supplies PostgreSQL connection strings. Validate only the URI
# contract here; the real credential, SSL, host, and database checks belong to
# SQLAlchemy/asyncpg during Alembic migration. Over-validating urlparse() here
# can reject otherwise valid connection strings containing escaped credentials.
database_url = os.environ["DATABASE_URL"].strip()
database = urlparse(database_url)
if database.scheme not in {"postgresql", "postgres"}:
    fail("DATABASE_URL must be a valid PostgreSQL connection URL")
if not database_url.startswith(("postgresql://", "postgres://")):
    fail("DATABASE_URL must be a valid PostgreSQL connection URL")

redis_url = os.environ["REDIS_URL"].strip()
redis = urlparse(redis_url)
if redis.scheme not in {"redis", "rediss"}:
    fail("REDIS_URL must be a valid Redis connection URL")
if not redis_url.startswith(("redis://", "rediss://")):
    fail("REDIS_URL must be a valid Redis connection URL")

if any(ch.isspace() for ch in database_url):
    fail("DATABASE_URL must not contain whitespace")
if any(ch.isspace() for ch in redis_url):
    fail("REDIS_URL must not contain whitespace")

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
