"""Restaurant, Branch, Table & QR token router — /api/admin"""
import uuid, secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.tenancy import Restaurant, Branch, Table, TableQRToken
from app.models.auth import StaffUser, StaffRole
from app.services.auth_service import get_current_staff

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ─── Schemas ────────────────────────────────────────────────────────────────
class RestaurantCreate(BaseModel):
    name: str
    gstin: str | None = None
    fssai_license_number: str | None = None
    whatsapp_phone_number_id: str
    whatsapp_display_number: str
    whatsapp_access_token: str | None = None
    whatsapp_verify_token: str = "hellodine"

class RestaurantUpdate(BaseModel):
    name: str | None = None
    max_branches: int | None = None
    is_active: bool | None = None
    whatsapp_phone_number_id: str | None = None
    whatsapp_display_number: str | None = None
    whatsapp_access_token: str | None = None
    whatsapp_verify_token: str | None = None

class ResetPasswordRequest(BaseModel):
    new_password: str


class BranchCreate(BaseModel):
    restaurant_id: uuid.UUID
    name: str
    address: str
    city: str
    state: str
    pincode: str
    gstin: str | None = None


class TableCreate(BaseModel):
    branch_id: uuid.UUID
    table_number: int


class StaffCreate(BaseModel):
    restaurant_id: uuid.UUID
    branch_id: uuid.UUID | None = None
    role: StaffRole
    name: str
    phone: str
    password: str


class StaffOut(BaseModel):
    id: uuid.UUID
    name: str
    phone: str
    role: StaffRole
    branch_id: uuid.UUID | None
    is_active: bool
    model_config = {"from_attributes": True}


# ─── Restaurants ─────────────────────────────────────────────────────────────
@router.post("/restaurants")
async def create_restaurant(data: RestaurantCreate, db: AsyncSession = Depends(get_db)):
    r = Restaurant(**data.model_dump())
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return r


@router.get("/restaurants")
async def list_restaurants(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Restaurant).order_by(Restaurant.created_at.desc()))
    return result.scalars().all()


@router.get("/restaurants/{restaurant_id}")
async def get_restaurant(restaurant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Restaurant not found")
    return r


@router.patch("/restaurants/{restaurant_id}")
async def update_restaurant(restaurant_id: uuid.UUID, data: RestaurantUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Restaurant not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(r, key, value)

    await db.commit()
    await db.refresh(r)
    return r


@router.post("/restaurants/{restaurant_id}/reset-owner-password")
async def reset_owner_password(restaurant_id: uuid.UUID, data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Allow System Admin to reset the password for a restaurant's owner (Super Admin)."""
    from app.services.auth_service import hash_password
    # Find the Super Admin for this restaurant
    result = await db.execute(select(StaffUser).where(StaffUser.restaurant_id == restaurant_id, StaffUser.role == StaffRole.SUPER_ADMIN))
    owner = result.scalar_one_or_none()
    if not owner:
        raise HTTPException(404, "Owner account not found for this restaurant")
    
    owner.password_hash = hash_password(data.new_password)
    await db.commit()
    return {"ok": True}


# ─── Branches ────────────────────────────────────────────────────────────────
@router.post("/branches")
async def create_branch(data: BranchCreate, db: AsyncSession = Depends(get_db), current_staff: StaffUser = Depends(get_current_staff)):
    if current_staff.role not in [StaffRole.SUPER_ADMIN, StaffRole.SYSTEM_ADMIN]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only owners or system admins can create branches")
        
    # Check branch limit
    rest_result = await db.execute(select(Restaurant).where(Restaurant.id == data.restaurant_id))
    restaurant = rest_result.scalar_one_or_none()
    if not restaurant:
        raise HTTPException(404, "Restaurant not found")

    branch_count = await db.execute(select(func.count(Branch.id)).where(Branch.restaurant_id == data.restaurant_id))
    count = branch_count.scalar_one()

    if count >= restaurant.max_branches:
        raise HTTPException(400, f"Branch limit ({restaurant.max_branches}) reached for this restaurant. Please contact the provider to upgrade.")

    b = Branch(**data.model_dump())
    db.add(b)
    await db.commit()
    await db.refresh(b)
    return b


@router.get("/branches")
async def list_branches(restaurant_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_staff: StaffUser = Depends(get_current_staff)):
    if current_staff.role == StaffRole.BRANCH_ADMIN:
        # A branch admin should only see their own branch in listings
        result = await db.execute(select(Branch).where(Branch.id == current_staff.branch_id))
    else:
        result = await db.execute(select(Branch).where(Branch.restaurant_id == restaurant_id))
    return result.scalars().all()


# ─── Tables ──────────────────────────────────────────────────────────────────
@router.post("/tables")
async def create_table(data: TableCreate, db: AsyncSession = Depends(get_db), current_staff: StaffUser = Depends(get_current_staff)):
    if current_staff.role == StaffRole.BRANCH_ADMIN:
        if str(data.branch_id) != str(current_staff.branch_id):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Branch admins can only create tables for their assigned branch")
    elif current_staff.role != StaffRole.SUPER_ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")

    t = Table(**data.model_dump())
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return t


@router.get("/tables")
async def list_tables(branch_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_staff: StaffUser = Depends(get_current_staff)):
    if current_staff.role == StaffRole.BRANCH_ADMIN:
        if str(branch_id) != str(current_staff.branch_id):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied to this branch's tables")
            
    result = await db.execute(select(Table).where(Table.branch_id == branch_id, Table.is_active == True))
    return result.scalars().all()


@router.post("/tables/{table_id}/qr")
async def generate_qr(table_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Generate a new secure QR token for a table."""
    # Revoke previous tokens
    existing = await db.execute(
        select(TableQRToken).where(TableQRToken.table_id == table_id, TableQRToken.is_revoked == False)
    )
    for tok in existing.scalars().all():
        tok.is_revoked = True

    token_str = secrets.token_urlsafe(32)
    qr = TableQRToken(table_id=table_id, token=token_str)
    db.add(qr)
    await db.commit()
    await db.refresh(qr)

    # Build the pre-filled WhatsApp message payload
    table_result = await db.execute(select(Table).where(Table.id == table_id))
    table = table_result.scalar_one()
    branch_result = await db.execute(select(Branch).where(Branch.id == table.branch_id))
    branch = branch_result.scalar_one()

    wa_message = (
        f"HELLODINE_START\n"
        f"branch={branch.id}\n"
        f"table={table.table_number}\n"
        f"token={token_str}"
    )
    wa_link = f"https://wa.me/?text={wa_message.replace(chr(10), '%0A')}"

    return {"token": token_str, "wa_link": wa_link, "table_number": table.table_number}


# ─── Staff ────────────────────────────────────────────────────────────────────
@router.post("/staff", response_model=StaffOut)
async def create_staff(data: StaffCreate, db: AsyncSession = Depends(get_db), current_staff: StaffUser = Depends(get_current_staff)):
    # Permission check
    if current_staff.role == StaffRole.BRANCH_ADMIN:
        # Branch admin can only create staff for their own branch
        if str(data.branch_id) != str(current_staff.branch_id):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Branch admins can only manage staff for their assigned branch")
        # Branch admin cannot create other Branch Admins or Super Admins
        if data.role in [StaffRole.SUPER_ADMIN, StaffRole.BRANCH_ADMIN]:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Branch admins cannot create other admins")
    elif current_staff.role != StaffRole.SUPER_ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")

    from app.services.auth_service import hash_password
    s = StaffUser(
        restaurant_id=data.restaurant_id,
        branch_id=data.branch_id,
        role=data.role,
        name=data.name,
        phone=data.phone,
        password_hash=hash_password(data.password),
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s


@router.get("/staff", response_model=list[StaffOut])
async def list_staff(restaurant_id: uuid.UUID, branch_id: uuid.UUID | None = None, db: AsyncSession = Depends(get_db), current_staff: StaffUser = Depends(get_current_staff)):
    # Data isolation
    from app.models.tenancy import Branch
    query = select(StaffUser, Branch.name.label("branch_name")).outerjoin(Branch, StaffUser.branch_id == Branch.id).where(StaffUser.restaurant_id == restaurant_id)
    
    if current_staff.role == StaffRole.BRANCH_ADMIN:
        # Force filter by their branch
        query = query.where(StaffUser.branch_id == current_staff.branch_id)
    elif branch_id:
        query = query.where(StaffUser.branch_id == branch_id)
        
    result = await db.execute(query)
    rows = result.all()
    
    staff_list = []
    for staff, branch_name in rows:
        setattr(staff, "branch_name", branch_name)
        staff_list.append(staff)
        
    return staff_list


@router.patch("/staff/{staff_id}/deactivate")
async def deactivate_staff(staff_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StaffUser).where(StaffUser.id == staff_id))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Staff not found")
    s.is_active = False
    await db.commit()
    return {"ok": True}
