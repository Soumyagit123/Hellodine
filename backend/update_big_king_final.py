
import asyncio
from sqlalchemy import text
from app.database import engine

async def update_creds():
    rest_id = "8584d86d-b191-4a9c-9b7f-a54f17a7abc7"
    wa_id = "+1 555 153 9633"
    wa_display = "BigKing"
    wa_token = "EAANNT1FcZBDMBQ378GbPG7fY5skKH9rZCrpoAQlgEtX6ZAvnyRgOJbkcOfxGZAOjwqRO1Dq3gCRyBjmAOEhYyReMVMZCBut66g5E9bN7ZA8lKTH2dXpaZCB3vINhWHlctft1jRPK2iQcNySLVUNxpfAYEalZCGjZCgV4KVzv8FPRwDpCS6eT9FzqUKUlFyrMg4ueiU6mUoVGPLi21ucN1mQlFpxGbyzEmB14palKxcywrzmWABB0YZBQDo9IjovSLCEMV5eIb06ZArheMh8lXjF3AEtWo1iuLlN"
    wa_verify = "hellodine_verify_token_123"
    wa_app_id = "929427992934451"
    wa_app_secret = "67a16d5ae79f444c918be1fb7d316ed6"

    async with engine.begin() as conn:
        await conn.execute(text("""
            UPDATE restaurants 
            SET whatsapp_phone_number_id = :wa_id,
                whatsapp_display_number = :wa_display,
                whatsapp_access_token = :wa_token,
                whatsapp_verify_token = :wa_verify,
                whatsapp_app_id = :wa_app_id,
                whatsapp_app_secret = :wa_app_secret
            WHERE id = :rest_id
        """), {
            "wa_id": wa_id,
            "wa_display": wa_display,
            "wa_token": wa_token,
            "wa_verify": wa_verify,
            "wa_app_id": wa_app_id,
            "wa_app_secret": wa_app_secret,
            "rest_id": rest_id
        })
        print(f"Successfully updated credentials for Big King ({rest_id})")

if __name__ == "__main__":
    asyncio.run(update_creds())
