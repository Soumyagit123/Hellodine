import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.tenancy import TableQRToken

async def check_tokens():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(TableQRToken))
        tokens = result.scalars().all()
        print(f"Total tokens in DB: {len(tokens)}")
        for t in tokens:
            print(f"  Token: {t.token} (Table ID: {t.table_id}, revoked: {t.is_revoked})")

if __name__ == "__main__":
    asyncio.run(check_tokens())
