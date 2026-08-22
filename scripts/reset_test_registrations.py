#!/usr/bin/env python3
"""One-shot test reset: remove registered test users and their owned data.

Keeps administrators/moderators intact. Intended for an explicit pre-E2E test
reset, never for normal application startup.
"""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sqlalchemy import delete, func, select

from app.core.database import async_session
from app.models import User


async def main() -> None:
    async with async_session() as session:
        count = await session.scalar(
            select(func.count(User.id)).where(
                User.is_admin.is_(False),
                User.is_moderator.is_(False),
            )
        )
        print(f"Test registrations to remove: {int(count or 0)}")
        if not count:
            return

        await session.execute(
            delete(User).where(
                User.is_admin.is_(False),
                User.is_moderator.is_(False),
            )
        )
        await session.commit()
        print("Test registrations reset successfully.")


if __name__ == "__main__":
    asyncio.run(main())
