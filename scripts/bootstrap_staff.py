"""Create or repair dedicated administrator and moderator accounts.

Usage (run inside the backend container):
  ADMIN_EMAIL=admin@example.org ADMIN_PASSWORD='...' python scripts/bootstrap_staff.py
  ADMIN_EMAIL=... ADMIN_PASSWORD='...' MODERATOR_EMAIL=... MODERATOR_PASSWORD='...' python scripts/bootstrap_staff.py

Passwords are supplied only through the environment and are never printed.
Existing accounts are updated by role; no password is changed unless a password
variable is supplied. The script never creates an account with a hard-coded
credential.
"""
import asyncio
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash, validate_password_strength
from app.models import User

async def ensure(email: str|None, password: str|None, *, admin: bool, moderator: bool):
    if not email:
        return None
    email=email.strip().lower()
    if not password:
        raise RuntimeError(f"Password is required for {email} when bootstrapping a staff account")
    ok,msg=validate_password_strength(password)
    if not ok:
        raise RuntimeError(f"Invalid password for {email}: {msg}")
    async with AsyncSessionLocal() as db:
        result=await db.execute(select(User).where(User.email==email))
        user=result.scalar_one_or_none()
        if user is None:
            user=User(email=email,password_hash=get_password_hash(password),full_name="Мир Самозанятых",is_active=True,is_verified=True,is_admin=admin,is_moderator=moderator)
            db.add(user)
        else:
            user.is_active=True
            user.is_verified=True
            user.is_admin=admin
            user.is_moderator=moderator
            user.password_hash=get_password_hash(password)
        await db.commit()
        role="admin" if admin else "moderator"
        print(f"Staff account ready: {email} ({role})")
        return email

async def main():
    admin_email=os.getenv("ADMIN_EMAIL")
    admin_password=os.getenv("ADMIN_PASSWORD")
    moderator_email=os.getenv("MODERATOR_EMAIL")
    moderator_password=os.getenv("MODERATOR_PASSWORD")
    if not admin_email and not moderator_email:
        raise SystemExit("Set ADMIN_EMAIL/ADMIN_PASSWORD and/or MODERATOR_EMAIL/MODERATOR_PASSWORD")
    await ensure(admin_email,admin_password,admin=True,moderator=False)
    await ensure(moderator_email,moderator_password,admin=False,moderator=True)

if __name__=="__main__":
    asyncio.run(main())
