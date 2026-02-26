import asyncio
import uuid
from sqlalchemy import update
from app.database import AsyncSessionLocal
from app.models.tenancy import Restaurant
from app.config import settings

async def sync_token():
    rest_id = uuid.UUID("8584d86d-b191-4a9c-9b7f-a54f17a7abc7")
    async with AsyncSessionLocal() as db:
        print(f"Syncing new token for Big King...")
        await db.execute(
            update(Restaurant)
            .where(Restaurant.id == rest_id)
            .values(whatsapp_access_token=settings.WA_ACCESS_TOKEN)
        )
        await db.commit()
        print("Successfully updated database with new token from .env")

if __name__ == "__main__":
    asyncio.run(sync_token())
