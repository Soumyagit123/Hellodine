
import asyncio
from app.database import AsyncSessionLocal
from app.models.tenancy import Restaurant
from app.config import settings
from sqlalchemy import select

async def list_restaurants():
    print(f"Using DB URL: {settings.DATABASE_URL}")
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Restaurant))
            rows = result.scalars().all()
            print(f"Found {len(rows)} restaurants:")
            for r in rows:
                print(f"- {r.name} (ID: {r.id}, WA_ID: {r.whatsapp_phone_number_id})")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(list_restaurants())
