
import asyncio
from sqlalchemy import text
from app.database import engine

async def find_big_king():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT id, name FROM restaurants WHERE name = 'Big King';"))
        row = result.fetchone()
        if row:
            print(f"FOUND: ID={row[0]}, NAME={row[1]}")
        else:
            print("NOT FOUND. All restaurants:")
            result = await conn.execute(text("SELECT id, name FROM restaurants;"))
            for r in result.fetchall():
                print(f"- {r[1]} (ID: {r[0]})")

if __name__ == "__main__":
    asyncio.run(find_big_king())
