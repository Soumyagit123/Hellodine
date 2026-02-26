
import asyncio
import uuid
from app.database import AsyncSessionLocal
from app.models.tenancy import Restaurant
from sqlalchemy import select

async def update_big_king():
    async with AsyncSessionLocal() as db:
        # Find Big King
        result = await db.execute(select(Restaurant).where(Restaurant.name == 'Big King'))
        restaurant = result.scalar_one_or_none()
        
        if not restaurant:
            print("Big King not found. Listing all restaurants:")
            all_r = await db.execute(select(Restaurant))
            for r in all_r.scalars().all():
                print(f"- {r.name} (ID: {r.id})")
            return

        print(f"Updating Restaurant: {restaurant.name} ({restaurant.id})")
        
        # Values from .env
        restaurant.whatsapp_phone_number_id = "+1 555 153 9633"
        restaurant.whatsapp_display_number = "BigKing"
        restaurant.whatsapp_access_token = "EAANNT1FcZBDMBQ378GbPG7fY5skKH9rZCrpoAQlgEtX6ZAvnyRgOJbkcOfxGZAOjwqRO1Dq3gCRyBjmAOEhYyReMVMZCBut66g5E9bN7ZA8lKTH2dXpaZCB3vINhWHlctft1jRPK2iQcNySLVUNxpfAYEalZCGjZCgV4KVzv8FPRwDpCS6eT9FzqUKUlFyrMg4ueiU6mUoVGPLi21ucN1mQlFpxGbyzEmB14palKxcywrzmWABB0YZBQDo9IjovSLCEMV5eIb06ZArheMh8lXjF3AEtWo1iuLlN"
        restaurant.whatsapp_verify_token = "hellodine_verify_token_123"
        restaurant.whatsapp_app_id = "929427992934451"
        restaurant.whatsapp_app_secret = "67a16d5ae79f444c918be1fb7d316ed6"
        
        await db.commit()
        print("Update successful!")

if __name__ == "__main__":
    asyncio.run(update_big_king())
