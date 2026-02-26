
import asyncio
from sqlalchemy import text
from app.database import engine

async def check_big_king():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT name, whatsapp_phone_number_id, whatsapp_display_number, whatsapp_app_id, whatsapp_app_secret FROM restaurants WHERE name = 'Big King';"))
        row = result.fetchone()
        if row:
            print(f"Name: {row[0]}")
            print(f"WA ID: {row[1]}")
            print(f"Display: {row[2]}")
            print(f"App ID: {row[3]}")
            print(f"App Secret: {row[4]}")
        else:
            print("Big King not found!")

if __name__ == "__main__":
    asyncio.run(check_big_king())
