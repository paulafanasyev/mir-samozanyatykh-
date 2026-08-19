"""Optional development seed entry point. Production startup never seeds demo data."""
import asyncio
from app.core.database import init_db

if __name__ == "__main__":
    asyncio.run(init_db())
