"""Order service — checkout_guard + order creation + kitchen dispatch."""
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.cart import Cart, CartItem, CartItemModifier, CartStatus
from app.models.orders import Order, OrderItem, OrderItemModifier, OrderStatus
from app.models.menu import MenuItem
from app.models.customers import TableSession, SessionStatus
from app.services.cart_service import compute_cart_hash, recalculate_cart


class CheckoutError(Exception):
    pass


async def checkout_guard(session_id: uuid.UUID, db: AsyncSession) -> tuple[Cart, list[CartItem]]:
    """Validate cart before creating an order. Raises CheckoutError on failure."""

    # 1. Session must be ACTIVE
    sess_result = await db.execute(select(TableSession).where(TableSession.id == session_id))
    session = sess_result.scalar_one_or_none()
    if not session or session.status != SessionStatus.ACTIVE:
        raise CheckoutError("Session is not active")

    # 2. Cart must exist and be open
    cart_result = await db.execute(
        select(Cart).where(Cart.session_id == session_id, Cart.status == CartStatus.OPEN)
        .options(selectinload(Cart.items).selectinload(CartItem.modifiers))
    )
    cart = cart_result.scalar_one_or_none()
    if not cart or not cart.items:
        raise CheckoutError("Cart is empty")

    items = cart.items

    # 3. All items must still be available
    for ci in items:
        item_res = await db.execute(select(MenuItem).where(MenuItem.id == ci.menu_item_id))
        menu_item = item_res.scalar_one_or_none()
        if not menu_item:
            raise CheckoutError(f"Menu item {ci.menu_item_id} no longer exists")
        if not menu_item.is_available:
            raise CheckoutError(f"Item '{menu_item.name}' is no longer available")

    # 4. Idempotency: reject if same hash was used within last 30 seconds
    cart_hash = compute_cart_hash(session_id, items)
    recent_result = await db.execute(
        select(Order).where(
            Order.session_id == session_id,
            Order.cart_hash == cart_hash,
            Order.created_at >= datetime.now(timezone.utc) - timedelta(seconds=30),
        )
    )
    if recent_result.scalar_one_or_none():
        raise CheckoutError("Duplicate order detected — please wait a moment before retrying")

    return cart, items, cart_hash


async def create_order_from_cart(
    session_id: uuid.UUID,
    db: AsyncSession,
    parent_order_id: uuid.UUID | None = None,
) -> Order:
    cart, items, cart_hash = await checkout_guard(session_id, db)

    sess_result = await db.execute(select(TableSession).where(TableSession.id == session_id))
    session = sess_result.scalar_one_or_none()
    if not session:
        raise CheckoutError("Table session lost — please scan QR again")

    # Generate order number
    import time
    order_number = f"ORD-{int(time.time() * 1000) % 10_000_000}"

    order = Order(
        branch_id=session.branch_id,
        table_id=session.table_id,
        session_id=session_id,
        order_number=order_number,
        parent_order_id=parent_order_id,
        cart_hash=cart_hash,
        status=OrderStatus.NEW,
        subtotal=cart.subtotal,
        cgst_amount=cart.cgst_amount,
        sgst_amount=cart.sgst_amount,
        total=cart.total,
    )
    db.add(order)
    await db.flush()

    for ci in items:
        oi = OrderItem(
            order_id=order.id,
            menu_item_id=ci.menu_item_id,
            variant_id=ci.variant_id,
            quantity=ci.quantity,
            unit_price=ci.unit_price,
            notes=ci.notes,
            line_total=ci.line_total,
        )
        # Snapshot HSN code
        item_res = await db.execute(select(MenuItem).where(MenuItem.id == ci.menu_item_id))
        menu_item = item_res.scalar_one_or_none()
        if menu_item:
            oi.hsn_code_snapshot = menu_item.hsn_code
        db.add(oi)
        await db.flush()

        for cim in ci.modifiers:
            oim = OrderItemModifier(
                order_item_id=oi.id,
                modifier_id=cim.modifier_id,
                modifier_name_snapshot=cim.modifier_name_snapshot,
                price_delta_snapshot=cim.price_delta_snapshot,
            )
            db.add(oim)

    # Mark cart as checked out
    cart.status = CartStatus.CHECKED_OUT
    await db.commit()
    await db.refresh(order)
    return order
