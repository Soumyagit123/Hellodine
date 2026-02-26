
import asyncio
from sqlalchemy import text
from app.database import engine

async def describe_restaurants():
    async with engine.connect() as conn:
        print("Describing 'restaurants' table:")
        # For PostgreSQL
        query = text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'restaurants';
        """)
        result = await conn.execute(query)
        for row in result.fetchall():
            print(f"- {row[0]} ({row[1]})")

if __name__ == "__main__":
    asyncio.run(describe_restaurants())
