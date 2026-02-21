"""Orders router — /api/orders  (kitchen board + WebSocket)"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.orders import Order, OrderItem, OrderItemModifier, OrderStatus
from app.models.tenancy import Table
from app.services.order_service import create_order_from_cart, CheckoutError
from app.services.ws_manager import manager

router = APIRouter(prefix="/api/orders", tags=["orders"])


class PlaceOrderRequest(BaseModel):
    session_id: uuid.UUID
    parent_order_id: Optional[uuid.UUID] = None


class StatusUpdateRequest(BaseModel):
    status: OrderStatus


@router.post("/place")
async def place_order(data: PlaceOrderRequest, db: AsyncSession = Depends(get_db)):
    try:
        order = await create_order_from_cart(data.session_id, db, data.parent_order_id)
        # Broadcast to kitchen
        table_result = await db.execute(select(Table).where(Table.id == order.table_id))
        table = table_result.scalar_one()
        await manager.broadcast_to_branch(str(order.branch_id), {
            "event": "NEW_ORDER",
            "order_id": str(order.id),
            "order_number": order.order_number,
            "table_number": table.table_number,
            "total": str(order.total),
        })
        return {"order_id": order.id, "order_number": order.order_number, "status": order.status}
    except CheckoutError as e:
        raise HTTPException(400, str(e))


@router.get("")
async def list_orders(
    branch_id: uuid.UUID,
    status: Optional[OrderStatus] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Order).where(Order.branch_id == branch_id)
    if status:
        q = q.where(Order.status == status)
    q = q.options(selectinload(Order.items).selectinload(OrderItem.modifiers)).order_by(Order.created_at.desc())
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{order_id}")
async def get_order(order_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Order).where(Order.id == order_id)
        .options(selectinload(Order.items).selectinload(OrderItem.modifiers))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Order not found")
    return order


@router.patch("/{order_id}/status")
async def update_status(order_id: uuid.UUID, data: StatusUpdateRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Order not found")

    order.status = data.status
    await db.commit()

    # Broadcast status update to kitchen
    await manager.broadcast_to_branch(str(order.branch_id), {
        "event": "ORDER_STATUS_UPDATED",
        "order_id": str(order.id),
        "order_number": order.order_number,
        "status": order.status,
    })
    return {"ok": True, "status": order.status}


@router.websocket("/ws/kitchen/{branch_id}")
async def kitchen_ws(websocket: WebSocket, branch_id: str):
    await manager.connect(websocket, branch_id)
    try:
        while True:
            await websocket.receive_text()  # heartbeat
    except WebSocketDisconnect:
        manager.disconnect(websocket, branch_id)
