import asyncio
import uuid
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.tenancy import Restaurant

async def check_secrets():
    rest_id = uuid.UUID("8584d86d-b191-4a9c-9b7f-a54f17a7abc7")
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Restaurant).where(Restaurant.id == rest_id))
        r = result.scalar_one_or_none()
        if r:
            print(f"Restaurant: {r.name}")
            print(f"  App ID: {r.whatsapp_app_id}")
            print(f"  App Secret: {'****' if r.whatsapp_app_secret else 'MISSING'}")
            print(f"  Secret value length: {len(r.whatsapp_app_secret) if r.whatsapp_app_secret else 0}")
            # Compare with .env value (I know it but I want to be sure what's in DB)
            from app.config import settings
            print(f"  Matches .env secret? {r.whatsapp_app_secret == settings.WA_APP_SECRET}")

if __name__ == "__main__":
    asyncio.run(check_secrets())
