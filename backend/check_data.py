import asyncio
import uuid
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.tenancy import Restaurant, Branch, Table
from app.models.menu import MenuCategory, MenuItem

async def check_data():
    rest_id = uuid.UUID("8584d86d-b191-4a9c-9b7f-a54f17a7abc7")
    async with AsyncSessionLocal() as db:
        # Check branches
        branches = (await db.execute(select(Branch).where(Branch.restaurant_id == rest_id))).scalars().all()
        print(f"Branches for Big King: {len(branches)}")
        for b in branches:
            print(f"  Branch: {b.name} (ID: {b.id})")
            
            # Check categories
            cats = (await db.execute(select(MenuCategory).where(MenuCategory.branch_id == b.id))).scalars().all()
            print(f"    Categories: {len(cats)}")
            for c in cats:
                print(f"      - {c.name} (active: {c.is_active})")
                
            # Check tables
            tables = (await db.execute(select(Table).where(Table.branch_id == b.id))).scalars().all()
            print(f"    Tables: {len(tables)}")
            for t in tables:
                print(f"      - Table {t.table_number} (ID: {t.id})")

if __name__ == "__main__":
    asyncio.run(check_data())
