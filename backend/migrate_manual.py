
import asyncio
from sqlalchemy import text
from app.database import engine

async def add_missing_columns():
    async with engine.begin() as conn:
        print("Adding missing columns to 'restaurants' table...")
        try:
            await conn.execute(text("ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS whatsapp_app_id TEXT;"))
            await conn.execute(text("ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS whatsapp_app_secret TEXT;"))
            print("Columns added successfully!")
        except Exception as e:
            print(f"Error adding columns: {e}")

if __name__ == "__main__":
    asyncio.run(add_missing_columns())
