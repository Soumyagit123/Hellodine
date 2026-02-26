"""Fix WhatsApp credentials for Big King restaurant in the DB."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import text
from app.database import engine
from app.config import settings


async def fix_credentials():
    phone_number_id = "1004593176074926"
    display_number = "15551539633"
    access_token = settings.WA_ACCESS_TOKEN
    verify_token = settings.WA_WEBHOOK_VERIFY_TOKEN
    app_id = settings.WA_APP_ID
    app_secret = settings.WA_APP_SECRET
    rest_id = "8584d86d-b191-4a9c-9b7f-a54f17a7abc7"

    async with engine.begin() as conn:
        await conn.execute(text("""
            UPDATE restaurants 
            SET whatsapp_phone_number_id = :pid,
                whatsapp_display_number = :display,
                whatsapp_access_token = :token,
                whatsapp_verify_token = :verify,
                whatsapp_app_id = :app_id,
                whatsapp_app_secret = :app_secret
            WHERE id = :rest_id
        """), {
            "pid": phone_number_id,
            "display": display_number,
            "token": access_token,
            "verify": verify_token,
            "app_id": app_id,
            "app_secret": app_secret,
            "rest_id": rest_id,
        })
        print("Updated Big King credentials")

    # Verify
    async with engine.begin() as conn:
        result = await conn.execute(text(
            "SELECT name, whatsapp_phone_number_id, whatsapp_display_number, "
            "LENGTH(whatsapp_access_token) as token_len FROM restaurants WHERE id = :rid"
        ), {"rid": rest_id})
        row = result.fetchone()
        if row:
            print(f"  name: {row[0]}")
            print(f"  phone_number_id: {row[1]}")
            print(f"  display_number: {row[2]}")
            print(f"  token_length: {row[3]}")


if __name__ == "__main__":
    asyncio.run(fix_credentials())
