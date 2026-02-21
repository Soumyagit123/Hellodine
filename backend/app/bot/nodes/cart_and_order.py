"""Bot nodes — cart_executor + checkout_guard + kitchen_dispatch"""
import uuid
from app.bot.state import BotState
from app.database import AsyncSessionLocal
from app.models.menu import MenuItem
from app.models.cart import Cart, CartItem, CartStatus
from app.models.customers import TableSession
from app.services.cart_service import add_item_to_cart, remove_cart_item, get_or_create_cart
from app.services.order_service import create_order_from_cart, CheckoutError
from app.services.ws_manager import manager
from app.models.tenancy import Table
from sqlalchemy import select


async def cart_executor(state: BotState) -> BotState:
    """Handle ADD_ITEM / REMOVE_ITEM / UPDATE_QTY / CART_VIEW intents."""
    intent = state.get("intent")
    session_id = state.get("session_id")
    branch_id = state.get("branch_id")
    entities = state.get("entities", {})

    if not session_id:
        state["error"] = "no_session"
        return state

    # ── CART_VIEW ────────────────────────────────────────────────
    if intent == "CART_VIEW":
        async with AsyncSessionLocal() as db:
            cart = await get_or_create_cart(uuid.UUID(session_id), db)
            result = await db.execute(select(CartItem).where(CartItem.cart_id == cart.id))
            items = result.scalars().all()
            if not items:
                state["final_response"] = {"type": "text", "body": "🛒 Your cart is empty. Say *show menu* to browse."}
                return state

            lines = []
            for ci in items:
                item_r = await db.execute(select(MenuItem).where(MenuItem.id == ci.menu_item_id))
                mi = item_r.scalar_one()
                lines.append(f"• {mi.name} ×{ci.quantity} — ₹{ci.line_total:.0f}" + (f"\n  📝 {ci.notes}" if ci.notes else ""))

            cart_text = "\n".join(lines)
            state["final_response"] = {
                "type": "text",
                "body": f"🛒 *Your Cart (Table)*\n\n{cart_text}\n\n💰 *Total: ₹{cart.total:.2f}*\n(incl. CGST ₹{cart.cgst_amount:.2f} + SGST ₹{cart.sgst_amount:.2f})\n\nSay *confirm* to place order or keep adding items.",
            }
        return state

    # ── ADD_ITEM ─────────────────────────────────────────────────
    if intent == "ADD_ITEM":
        item_name = entities.get("item_name", "")
        quantity = int(entities.get("quantity") or 1)
        notes = entities.get("notes")

        if not item_name:
            state["final_response"] = {"type": "text", "body": "What would you like to add? Say e.g. *add 2 paneer tikka*."}
            return state

        async with AsyncSessionLocal() as db:
            # Fuzzy match item by name in branch
            items_result = await db.execute(
                select(MenuItem).where(
                    MenuItem.branch_id == uuid.UUID(branch_id),
                    MenuItem.is_available == True,
                )
            )
            all_items = items_result.scalars().all()
            matched = [i for i in all_items if item_name.lower() in i.name.lower()]
            if not matched:
                state["final_response"] = {
                    "type": "text",
                    "body": f"❌ Couldn't find *{item_name}* on the menu. Say *show menu* to browse.",
                }
                return state

            menu_item = matched[0]
            try:
                cart = await add_item_to_cart(
                    session_id=uuid.UUID(session_id),
                    menu_item_id=menu_item.id,
                    quantity=quantity,
                    db=db,
                    notes=notes,
                )
                veg = "🟢" if menu_item.is_veg else "🔴"
                state["final_response"] = {
                    "type": "buttons",
                    "body": (
                        f"✅ Added {veg} *{menu_item.name}* ×{quantity}!\n"
                        + (f"📝 Note: {notes}\n" if notes else "")
                        + f"\n🛒 Cart total: *₹{cart.total:.2f}*\n\nWhat would you like to do?"
                    ),
                    "buttons": [
                        {"id": "view_cart", "title": "View Cart 🛒"},
                        {"id": "show_menu", "title": "Add More 📋"},
                        {"id": "confirm_order", "title": "Place Order ✅"},
                    ],
                }
            except ValueError as e:
                state["final_response"] = {"type": "text", "body": f"❌ {e}"}
        return state

    # ── REMOVE_ITEM ──────────────────────────────────────────────
    if intent == "REMOVE_ITEM":
        item_name = entities.get("item_name", "")
        async with AsyncSessionLocal() as db:
            cart = await get_or_create_cart(uuid.UUID(session_id), db)
            items_result = await db.execute(select(CartItem).where(CartItem.cart_id == cart.id))
            cart_items = items_result.scalars().all()

            target = None
            for ci in cart_items:
                item_r = await db.execute(select(MenuItem).where(MenuItem.id == ci.menu_item_id))
                mi = item_r.scalar_one()
                if item_name.lower() in mi.name.lower():
                    target = ci
                    break

            if not target:
                state["final_response"] = {"type": "text", "body": f"❌ *{item_name}* not found in your cart."}
                return state

            cart = await remove_cart_item(target.id, db)
            state["final_response"] = {
                "type": "text",
                "body": f"✅ Removed *{item_name}* from cart.\n🛒 Cart total: *₹{cart.total:.2f}*",
            }
        return state

    return state


async def checkout_guard_node(state: BotState) -> BotState:
    """Show order summary and ask for CONFIRM button."""
    session_id = state.get("session_id")
    if not session_id:
        state["error"] = "no_session"
        return state

    async with AsyncSessionLocal() as db:
        cart = await get_or_create_cart(uuid.UUID(session_id), db)
        result = await db.execute(select(CartItem).where(CartItem.cart_id == cart.id))
        items = result.scalars().all()

        if not items:
            state["final_response"] = {"type": "text", "body": "🛒 Your cart is empty! Say *show menu* to start ordering."}
            return state

        lines = []
        for ci in items:
            item_r = await db.execute(select(MenuItem).where(MenuItem.id == ci.menu_item_id))
            mi = item_r.scalar_one()
            lines.append(f"• {mi.name} ×{ci.quantity} — ₹{ci.line_total:.0f}")

        summary = "\n".join(lines)
        state["final_response"] = {
            "type": "buttons",
            "body": (
                f"📋 *Order Summary*\n\n{summary}\n\n"
                f"💰 Subtotal: ₹{cart.subtotal:.2f}\n"
                f"📊 GST (CGST+SGST): ₹{cart.cgst_amount + cart.sgst_amount:.2f}\n"
                f"💵 *Total: ₹{cart.total:.2f}*\n\n"
                "Confirm to send to kitchen? 👇"
            ),
            "buttons": [
                {"id": "do_confirm", "title": "✅ Confirm Order"},
                {"id": "edit_cart", "title": "✏️ Edit Cart"},
            ],
        }
        state["intent"] = "CONFIRM_PREVIEW"
    return state


async def kitchen_dispatch(state: BotState) -> BotState:
    """Actually place the order — called when customer taps Confirm."""
    session_id = state.get("session_id")
    if not session_id:
        state["error"] = "no_session"
        return state

    async with AsyncSessionLocal() as db:
        try:
            order = await create_order_from_cart(uuid.UUID(session_id), db)
            # Broadcast realtime to kitchen PWA
            table_result = await db.execute(select(Table).where(Table.id == order.table_id))
            table = table_result.scalar_one()
            await manager.broadcast_to_branch(str(order.branch_id), {
                "event": "NEW_ORDER",
                "order_id": str(order.id),
                "order_number": order.order_number,
                "table_number": table.table_number,
                "total": str(order.total),
            })
            state["final_response"] = {
                "type": "text",
                "body": (
                    f"✅ *Order #{order.order_number} sent to kitchen!*\n\n"
                    f"🍽️ Table: {table.table_number}\n"
                    f"💵 Total: ₹{order.total:.2f}\n\n"
                    "You can add more items anytime. Payment at billing time. 😊"
                ),
            }
        except CheckoutError as e:
            state["final_response"] = {"type": "text", "body": f"⚠️ {e}"}
    return state
