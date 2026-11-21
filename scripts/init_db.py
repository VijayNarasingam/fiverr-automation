"""Initialize the database by creating all tables.

Usage:
    python scripts/init_db.py

Reads DATABASE_URL from the environment (.env) via app.config.settings.
"""

import asyncio

from app.config import settings
from app.database import Base, engine, init_db


async def main() -> None:
    init_db(settings.DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database initialized")


if __name__ == "__main__":
    asyncio.run(main())
