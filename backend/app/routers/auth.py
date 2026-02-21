"""Auth router — /api/auth"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import uuid

from app.database import get_db
from app.models.auth import StaffUser, StaffRole
from app.services.auth_service import verify_password, create_access_token, get_current_staff

router = APIRouter(prefix="/api/auth", tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    name: str
    branch_id: str | None


class StaffOut(BaseModel):
    id: uuid.UUID
    name: str
    phone: str
    role: StaffRole
    branch_id: uuid.UUID | None
    is_active: bool

    model_config = {"from_attributes": True}


@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StaffUser).where(StaffUser.phone == form.username, StaffUser.is_active == True))
    staff = result.scalar_one_or_none()
    if not staff or not verify_password(form.password, staff.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid phone or password")

    token = create_access_token({"sub": str(staff.id), "role": staff.role, "restaurant_id": str(staff.restaurant_id)})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=staff.role,
        name=staff.name,
        branch_id=str(staff.branch_id) if staff.branch_id else None,
    )


@router.get("/me", response_model=StaffOut)
async def me(staff: StaffUser = Depends(get_current_staff)):
    return staff
