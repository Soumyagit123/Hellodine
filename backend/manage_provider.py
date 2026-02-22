import asyncio
import sys
import os
import uuid
sys.path.insert(0, os.path.dirname(__file__))

from app.database import AsyncSessionLocal
from app.models.tenancy import Restaurant
from app.models.auth import StaffUser, StaffRole
from app.services.auth_service import hash_password
from sqlalchemy import select

async def create_provider():
    async with AsyncSessionLocal() as db:
        # 1. Create a "System" Restaurant for the Provider
        rest_result = await db.execute(select(Restaurant).where(Restaurant.name == "HelloDine System"))
        restaurant = rest_result.scalar_one_or_none()
        
        if not restaurant:
            restaurant = Restaurant(
                name="HelloDine System",
                whatsapp_phone_number_id="SYSTEM",
                whatsapp_display_number="SYSTEM"
            )
            db.add(restaurant)
            await db.flush()
            print(f"Created System Restaurant: {restaurant.id}")
        else:
            print(f"Using Existing System Restaurant: {restaurant.id}")

        # 2. Create the System Admin (App Owner)
        phone = "+91 0000000000"
        pwd = "owner123"
        
        staff_result = await db.execute(select(StaffUser).where(StaffUser.phone == phone))
        staff = staff_result.scalar_one_or_none()
        
        if not staff:
            staff = StaffUser(
                restaurant_id=restaurant.id,
                role=StaffRole.SYSTEM_ADMIN,
                name="App Owner",
                phone=phone,
                password_hash=hash_password(pwd)
            )
            db.add(staff)
            await db.commit()
            print(f"\n✅ SUCCESS: System Admin Created!")
            print(f"Phone: {phone}")
            print(f"Password: {pwd}")
        else:
            print(f"\nℹ️ System Admin already exists with phone {phone}")

if __name__ == "__main__":
    asyncio.run(create_provider())
