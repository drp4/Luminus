"""Children Growth OS — Application Entry Point

Usage:
    python run.py              # Start the server
    python run.py --init-db    # Initialize database tables + seed data
"""

from __future__ import annotations

import asyncio
import sys

import uvicorn

from config import settings


def main() -> None:
    if "--init-db" in sys.argv:
        async def _init():
            from services.database import init_db, seed_defaults
            print("Initializing database...")
            await init_db()
            print("Seeding default data...")
            await seed_defaults()
            print("Done.")
        asyncio.run(_init())
        return

    uvicorn.run(
        "services.gateway.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app_debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
