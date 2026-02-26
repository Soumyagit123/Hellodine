"""Bot nodes — detect_language (lightweight) + intent_router (Gemini)"""
import json
from app.bot.state import BotState
from app.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0,
)

INTENT_PROMPT = """You are an intent classifier for a restaurant WhatsApp ordering chatbot.

Classify the customer message into ONE of these intents:
- QR_SCAN        : message contains HELLODINE_START (QR pairing)
- BROWSE         : customer wants to see menu, categories, items
- ADD_ITEM       : customer wants to add item(s) to cart
- REMOVE_ITEM    : customer wants to remove an item from cart
- UPDATE_QTY     : customer wants to change quantity
- CONFIRM        : customer wants to place/confirm their order
- BILL           : customer wants the bill / check-out / pay
- CART_VIEW      : customer wants to see their current cart
- OTHER          : greetings, thanks, unrelated

Also extract entities:
- item_name (string, optional)  
- quantity (int, optional)
- notes (string, optional — e.g. "less spicy", "no onion")

Return ONLY valid JSON like:
{"intent": "ADD_ITEM", "entities": {"item_name": "paneer tikka", "quantity": 2, "notes": "extra spicy"}}

Customer message: "{message}"
"""


async def detect_language(state: BotState) -> BotState:
    """Lightweight: detect Hindi vs English from Unicode range."""
    text = state.get("message_text", "")
    hindi_chars = sum(1 for c in text if "\u0900" <= c <= "\u097F")
    if hindi_chars > 2:
        state["preferred_language"] = "hi"
    else:
        state["preferred_language"] = state.get("preferred_language", "en")
    return state


async def intent_router(state: BotState) -> BotState:
    """Use Gemini to classify intent + extract entities."""
    # If QR scan already detected, skip
    if state.get("intent") == "QR_SCAN":
        return state

    text = state.get("message_text", "")
    if not text:
        state["intent"] = "OTHER"
        return state

    # Quick rule-based shortcuts (avoid LLM for common patterns)
    lower = text.lower().strip()
    if any(w in lower for w in ["confirm", "place order", "order karo", "हाँ", "yes", "ok"]):
        state["intent"] = "CONFIRM"
        state["entities"] = {}
        return state
    if any(w in lower for w in ["bill", "check", "pay", "payment", "bill please", "bil"]):
        state["intent"] = "BILL"
        state["entities"] = {}
        return state
    if any(w in lower for w in ["cart", "my order", "show cart", "what i ordered", "टोकरी"]):
        state["intent"] = "CART_VIEW"
        state["entities"] = {}
        return state
    if any(w in lower for w in ["menu", "list", "show", "browse", "सूची", "show_menu"]):
        state["intent"] = "BROWSE"
        state["entities"] = {}
        return state

    # Interactive Replies (cat_, item_, or button IDs)
    if lower == "do_confirm":
        state["intent"] = "CONFIRM_PREVIEW"
        return state
    if lower == "confirm_order":
        state["intent"] = "CONFIRM"
        return state
    if lower == "view_cart" or lower == "edit_cart":
        state["intent"] = "CART_VIEW"
        return state
    
    if lower.startswith("cat_"):
        state["intent"] = "BROWSE"
        state["entities"] = {"category_id": lower.replace("cat_", "")}
        return state
    if lower.startswith("item_"):
        state["intent"] = "ADD_ITEM"
        state["entities"] = {"item_id": lower.replace("item_", ""), "quantity": 1}
        return state

    # Veg / Non-Veg Filtering
    if any(w in lower for w in ["veg", "शाकाहारी", "vegetarian"]):
        state["intent"] = "BROWSE"
        state["entities"] = {"is_veg": True}
        return state
    if any(w in lower for w in ["non-veg", "मांसाहारी", "non veg", "chicken", "meat"]):
        state["intent"] = "BROWSE"
        state["entities"] = {"is_veg": False}
        return state

    # LLM classification
    try:
        prompt = INTENT_PROMPT.format(message=text)
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        raw = response.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw)
        state["intent"] = parsed.get("intent", "OTHER")
        state["entities"] = parsed.get("entities", {})
    except Exception:
        state["intent"] = "BROWSE"
        state["entities"] = {}

    return state
