"""Script to manually add missing columns to the production database."""
import asyncio
import uuid
from sqlalchemy import text
from app.database import engine

async def sync_db():
    print("Connecting to database...")
    async with engine.begin() as conn:
        # Check if columns exist and add them if not
        print("Checking for missing columns in 'restaurants' table...")
        
        # We use raw SQL for adding columns to avoid migration complexities for this quick fix
        try:
            await conn.execute(text("ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS whatsapp_access_token TEXT;"))
            print("Successfully checked/added 'whatsapp_access_token'")
        except Exception as e:
            print(f"Error adding whatsapp_access_token: {e}")

        try:
            await conn.execute(text("ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS whatsapp_verify_token TEXT DEFAULT 'hellodine';"))
            # If the column already existed without the default, update it
            await conn.execute(text("UPDATE restaurants SET whatsapp_verify_token = 'hellodine' WHERE whatsapp_verify_token IS NULL;"))
            await conn.execute(text("ALTER TABLE restaurants ALTER COLUMN whatsapp_verify_token SET NOT NULL;"))
            print("Successfully checked/added/updated 'whatsapp_verify_token'")
        except Exception as e:
            print(f"Error adding whatsapp_verify_token: {e}")

    print("Sync complete.")

if __name__ == "__main__":
    asyncio.run(sync_db())
