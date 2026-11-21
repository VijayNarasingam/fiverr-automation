"""Initialize the database by creating all tables.

Usage:
    python scripts/init_db.py

Reads DATABASE_URL from the environment (.env) via app.config.settings.
"""

import asyncio
import sys
from pathlib import Path

# Ensure the repository root is on sys.path so `app` imports resolve when
# the script is run directly (e.g. `python scripts/init_db.py`).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import database
from app.config import settings  # noqa: E402


async def main() -> None:
    database.init_db(settings.DATABASE_URL)
    async with database.engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)
    print("Database initialized")


if __name__ == "__main__":
    asyncio.run(main())
