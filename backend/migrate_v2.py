import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import engine
from sqlalchemy import text

async def migrate():
    async with engine.begin() as conn:
        print("Adding columns to restaurants table...")
        try:
            await conn.execute(text('ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS max_branches INTEGER DEFAULT 1'))
            await conn.execute(text('ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE'))
            print("✅ Columns added successfully!")
        except Exception as e:
            print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
