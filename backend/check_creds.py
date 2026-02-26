import asyncio
import uuid
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.tenancy import Restaurant

async def check_creds():
    rest_id = uuid.UUID("8584d86d-b191-4a9c-9b7f-a54f17a7abc7")
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Restaurant).where(Restaurant.id == rest_id))
        r = res.scalar_one_or_none()
        if r:
            print(f"Restaurant: {r.name}")
            print(f"Phone ID: {r.whatsapp_phone_number_id}")
            print(f"Display Num: {r.whatsapp_display_number}")
            print(f"Token (First 20): {r.whatsapp_access_token[:20] if r.whatsapp_access_token else 'NONE'}")
        else:
            print("Restaurant not found")

if __name__ == "__main__":
    asyncio.run(check_creds())
