"""Bot nodes — menu_retrieval + response_formatter"""
import uuid
from app.bot.state import BotState
from app.database import AsyncSessionLocal
from app.models.menu import MenuCategory, MenuItem
from sqlalchemy import select


VEG_EMOJI = {"veg": "🟢", "nonveg": "🔴", "jain": "🌿"}
SPICE_EMOJI = {"mild": "🌶", "medium": "🌶🌶", "hot": "🌶🌶🌶"}


async def menu_retrieval(state: BotState) -> BotState:
    """Fetch menu categories or items and prepare response payload."""
    branch_id = state.get("branch_id")
    entities = state.get("entities", {})
    item_name_hint = (entities.get("item_name") or "").lower()

    async with AsyncSessionLocal() as db:
        # If a specific item hint, search items directly
        if item_name_hint:
            items_result = await db.execute(
                select(MenuItem).where(
                    MenuItem.branch_id == uuid.UUID(branch_id),
                    MenuItem.is_available == True,
                )
            )
            all_items = items_result.scalars().all()
            matched = [i for i in all_items if item_name_hint in i.name.lower()]
            if not matched:
                matched = all_items[:10]  # fallback: show first 10

            rows = []
            for item in matched[:10]:
                veg = VEG_EMOJI["veg"] if item.is_veg else VEG_EMOJI["nonveg"]
                spice = SPICE_EMOJI.get(item.spice_level, "") if item.spice_level else ""
                rows.append({
                    "id": f"item_{item.id}",
                    "title": f"{veg} {item.name[:24]}",
                    "description": f"₹{item.base_price:.0f} {spice}",
                })
            state["final_response"] = {
                "type": "list",
                "body": "Here are the matching items 👇\nTap one to add it to cart:",
                "button_label": "View Items",
                "sections": [{"title": "Menu Items", "rows": rows}],
            }
        else:
            # Show categories
            cats_result = await db.execute(
                select(MenuCategory).where(
                    MenuCategory.branch_id == uuid.UUID(branch_id),
                    MenuCategory.is_active == True,
                ).order_by(MenuCategory.sort_order)
            )
            cats = cats_result.scalars().all()
            rows = [{"id": f"cat_{c.id}", "title": c.name, "description": f"~{c.estimated_prep_minutes} min" if c.estimated_prep_minutes else ""} for c in cats[:10]]
            state["final_response"] = {
                "type": "list",
                "body": "📋 Our Menu Categories — tap to browse:",
                "button_label": "Browse Menu",
                "sections": [{"title": "Categories", "rows": rows}],
            }
    return state


async def response_formatter(state: BotState) -> BotState:
    """Build WA-sendable payload from state.final_response."""
    # final_response is already set by other nodes; this node is a pass-through
    # to allow future enrichment (language, personalisation, etc.)
    lang = state.get("preferred_language", "en")

    if not state.get("final_response"):
        if state.get("error") == "no_session":
            state["final_response"] = {
                "type": "text",
                "body": "👋 Please scan the QR code on your table to start ordering.",
            }
        elif state.get("error") == "invalid_token":
            state["final_response"] = {
                "type": "text",
                "body": "❌ Invalid or expired QR code. Please ask staff for a new one.",
            }
        else:
            state["final_response"] = {
                "type": "text",
                "body": "I didn't understand that. Try: *show menu*, *add [item]*, *confirm*, or *bill please*.",
            }
    return state
