import asyncio
import uuid
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.tenancy import Restaurant

async def check_verify_token():
    rest_id = uuid.UUID("8584d86d-b191-4a9c-9b7f-a54f17a7abc7")
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Restaurant).where(Restaurant.id == rest_id))
        r = res.scalar_one_or_none()
        if r:
            print(f"Verify Token in DB: {r.whatsapp_verify_token}")
        else:
            print("Restaurant not found")

if __name__ == "__main__":
    asyncio.run(check_verify_token())
