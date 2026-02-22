import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import engine
from sqlalchemy import text

async def update_enum():
    async with engine.begin() as conn:
        print("Updating staffrole enum in database...")
        try:
            # PostgreSQL command to add a value to an existing enum type
            # We use ALTER TYPE ... ADD VALUE ...
            # Note: This cannot be run inside a transaction block in some PG versions, 
            # but usually 'engine.begin()' is fine or we can use 'conn.execution_options(isolation_level="AUTOCOMMIT")'
            await conn.execute(text("ALTER TYPE staffrole ADD VALUE IF NOT EXISTS 'SYSTEM_ADMIN'"))
            print("✅ Enum updated successfully!")
        except Exception as e:
            # If it's not a PostgreSQL enum (e.g. if it's just a VARCHAR check constraint in SQLite), 
            # this might fail, but since we are targeting Render/Production/Postgres, this is the correct way.
            print(f"ℹ️ Enum update skipped or failed (might already exist): {e}")

if __name__ == "__main__":
    asyncio.run(update_enum())
