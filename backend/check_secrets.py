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
            print(f"  Phone Number ID: {r.whatsapp_phone_number_id}")
            print(f"  App ID: {r.whatsapp_app_id}")
            print(f"  Access Token: {r.whatsapp_access_token[:10]}...{r.whatsapp_access_token[-10:] if r.whatsapp_access_token else ''}")
            print(f"  Token has whitespace? {r.whatsapp_access_token.strip() != r.whatsapp_access_token if r.whatsapp_access_token else False}")
            print(f"  Token length: {len(r.whatsapp_access_token) if r.whatsapp_access_token else 0}")
            
            from app.config import settings
            print(f"  Matches .env Phone ID? {r.whatsapp_phone_number_id == settings.WA_PHONE_NUMBER_ID}")
            print(f"  Matches .env Secret? {r.whatsapp_app_secret == settings.WA_APP_SECRET}")
            print(f"  Matches .env Token? {r.whatsapp_access_token == settings.WA_ACCESS_TOKEN}")

if __name__ == "__main__":
    asyncio.run(check_secrets())
