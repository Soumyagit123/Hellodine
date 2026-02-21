"""Bot nodes — bill_generator + receipt_sender"""
import uuid
from app.bot.state import BotState
from app.database import AsyncSessionLocal
from app.models.billing import Bill, BillStatus
from app.models.orders import Order, OrderItem, OrderStatus
from app.models.menu import MenuItem
from app.models.customers import TableSession
from app.models.tenancy import Table, Branch
from sqlalchemy import select
import time


async def bill_generator(state: BotState) -> BotState:
    """Aggregate all open orders for the session into a consolidated bill."""
    session_id = state.get("session_id")
    if not session_id:
        state["error"] = "no_session"
        return state

    async with AsyncSessionLocal() as db:
        # Check if unpaid bill already exists
        exist = await db.execute(
            select(Bill).where(Bill.session_id == uuid.UUID(session_id), Bill.status == BillStatus.UNPAID)
        )
        bill = exist.scalar_one_or_none()

        if not bill:
            orders_result = await db.execute(
                select(Order).where(
                    Order.session_id == uuid.UUID(session_id),
                    Order.status.notin_([OrderStatus.CANCELLED]),
                )
            )
            orders = orders_result.scalars().all()
            if not orders:
                state["final_response"] = {"type": "text", "body": "No orders found for this table. Order something first! 😊"}
                return state

            sess_result = await db.execute(select(TableSession).where(TableSession.id == uuid.UUID(session_id)))
            session = sess_result.scalar_one()

            subtotal = sum(o.subtotal for o in orders)
            cgst = sum(o.cgst_amount for o in orders)
            sgst = sum(o.sgst_amount for o in orders)
            total = sum(o.total for o in orders)

            bill = Bill(
                branch_id=session.branch_id,
                table_id=session.table_id,
                session_id=uuid.UUID(session_id),
                bill_number=f"BILL-{int(time.time() * 1000) % 10_000_000}",
                subtotal=subtotal,
                cgst_amount=cgst,
                sgst_amount=sgst,
                total=total,
                status=BillStatus.UNPAID,
            )
            db.add(bill)
            await db.commit()
            await db.refresh(bill)

        # Build bill summary lines from orders
        orders_result = await db.execute(
            select(Order).where(Order.session_id == uuid.UUID(session_id))
        )
        orders = orders_result.scalars().all()
        lines = []
        for order in orders:
            items_r = await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
            for oi in items_r.scalars().all():
                item_r = await db.execute(select(MenuItem).where(MenuItem.id == oi.menu_item_id))
                mi = item_r.scalar_one()
                lines.append(f"• {mi.name} ×{oi.quantity} — ₹{oi.line_total:.0f}")

        items_text = "\n".join(lines) if lines else "No items"

        state["final_response"] = {
            "type": "text",
            "body": (
                f"🧾 *Bill #{bill.bill_number}*\n\n"
                f"{items_text}\n\n"
                f"{'─'*28}\n"
                f"Subtotal : ₹{bill.subtotal:.2f}\n"
                f"CGST      : ₹{bill.cgst_amount:.2f}\n"
                f"SGST      : ₹{bill.sgst_amount:.2f}\n"
                f"{'─'*28}\n"
                f"*Total    : ₹{bill.total:.2f}*\n\n"
                "Please pay at the cashier counter 💳 or ask staff for UPI QR."
            ),
        }
    return state


async def receipt_sender(state: BotState) -> BotState:
    """Send receipt after payment is confirmed (called from cashier marking paid)."""
    # This node is called externally after cashier marks paid.
    # In the bot graph it's a terminal node that just echoes the state.
    return state
