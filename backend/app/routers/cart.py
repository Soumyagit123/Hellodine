"""Cart router — /api/cart"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.cart import Cart, CartItem, CartStatus
from app.services.cart_service import add_item_to_cart, remove_cart_item, get_or_create_cart

router = APIRouter(prefix="/api/cart", tags=["cart"])


class AddItemRequest(BaseModel):
    session_id: uuid.UUID
    menu_item_id: uuid.UUID
    quantity: int = 1
    variant_id: Optional[uuid.UUID] = None
    modifier_ids: Optional[list[uuid.UUID]] = None
    notes: Optional[str] = None


class UpdateQuantityRequest(BaseModel):
    quantity: int


@router.post("/add")
async def add_item(data: AddItemRequest, db: AsyncSession = Depends(get_db)):
    try:
        cart = await add_item_to_cart(
            session_id=data.session_id,
            menu_item_id=data.menu_item_id,
            quantity=data.quantity,
            db=db,
            variant_id=data.variant_id,
            modifier_ids=data.modifier_ids,
            notes=data.notes,
        )
        return {"cart_id": cart.id, "total": cart.total, "subtotal": cart.subtotal, "cgst": cart.cgst_amount, "sgst": cart.sgst_amount}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/item/{cart_item_id}")
async def remove_item(cart_item_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        cart = await remove_cart_item(cart_item_id, db)
        return {"ok": True, "total": cart.total}
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.patch("/item/{cart_item_id}/quantity")
async def update_quantity(cart_item_id: uuid.UUID, data: UpdateQuantityRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CartItem).where(CartItem.id == cart_item_id))
    ci = result.scalar_one_or_none()
    if not ci:
        raise HTTPException(404, "Cart item not found")
    if data.quantity <= 0:
        return await remove_cart_item(cart_item_id, db)
    ci.quantity = data.quantity
    cart_result = await db.execute(
        select(Cart).where(Cart.id == ci.cart_id)
        .options(selectinload(Cart.items))
    )
    cart = cart_result.scalar_one()
    from app.services.cart_service import recalculate_cart
    await recalculate_cart(cart, db)
    await db.commit()
    return {"ok": True, "total": cart.total}


@router.get("/{session_id}")
async def get_cart(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Cart).where(Cart.session_id == session_id, Cart.status == CartStatus.OPEN)
        .options(selectinload(Cart.items).selectinload(CartItem.modifiers))
    )
    cart = result.scalar_one_or_none()
    if not cart:
        return {"items": [], "total": 0}
    return cart
