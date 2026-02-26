
import asyncio
from sqlalchemy import text
from app.database import engine

async def list_tables():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';"))
        tables = result.fetchall()
        print("Existing Tables:")
        for t in tables:
            print(f"- {t[0]}")

if __name__ == "__main__":
    asyncio.run(list_tables())
