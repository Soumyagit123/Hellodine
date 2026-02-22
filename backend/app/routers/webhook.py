"""WhatsApp Webhook router — /api/webhook"""
from fastapi import APIRouter, Request, Response, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.bot.graph import compiled_graph
from app.database import AsyncSessionLocal
from app.models.logs import WhatsAppMessageLog, MessageDirection
from app.bot.wa_sender import send_text, send_interactive_buttons, send_interactive_list
from app.models.tenancy import Restaurant
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import uuid

router = APIRouter(prefix="/api/webhook", tags=["webhook"])


@router.get("/{restaurant_id}")
async def verify_webhook(restaurant_id: uuid.UUID, request: Request):
    """Meta webhook verification handshake per restaurant."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
        restaurant = result.scalar_one_or_none()
        if not restaurant:
            raise HTTPException(404, "Restaurant not found")

    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    # Use restaurant-specific verify token
    if mode == "subscribe" and token == restaurant.whatsapp_verify_token:
        return Response(content=challenge, media_type="text/plain")
    
    raise HTTPException(403, "Verification failed")


@router.post("/{restaurant_id}")
async def receive_webhook(restaurant_id: uuid.UUID, request: Request):
    """Inbound WhatsApp messages per restaurant → LangGraph bot."""
    payload = await request.json()

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
        restaurant = result.scalar_one_or_none()
        if not restaurant:
            raise HTTPException(404, "Restaurant not found")
        
        # Check if restaurant has bot tokens configured
        if not restaurant.whatsapp_access_token:
            # We log message but skip bot processing if No Token
            return {"status": "no_token_configured"}

        # Quick dedup + log
        try:
            entry = payload.get("entry", [{}])[0]
            value = entry.get("changes", [{}])[0].get("value", {})
            messages = value.get("messages", [])

            if not messages:
                return {"status": "ok"}

            msg = messages[0]
            wa_message_id = msg.get("id", str(uuid.uuid4()))

            try:
                log = WhatsAppMessageLog(
                    restaurant_id=restaurant.id,
                    wa_message_id=wa_message_id,
                    direction=MessageDirection.INBOUND,
                    message_type=msg.get("type", "text"),
                    raw_payload=payload,
                )
                db.add(log)
                await db.commit()
            except IntegrityError:
                return {"status": "duplicate"}

        except Exception:
            pass

    # Run LangGraph bot (we already have restaurant_id from URL)
    # The ingest_webhook node will still run but we can ensure it uses the URL ID
    initial_state = {
        "raw_message": payload,
        "restaurant_id": str(restaurant_id) # Pre-fill from URL
    }
    state = await compiled_graph.ainvoke(initial_state)

    # Send reply using restaurant credentials
    final = state.get("final_response")
    to = state.get("wa_user_id", "")

    if final and to:
        msg_type = final.get("type", "text")
        # Dynamic credentials
        p_id = restaurant.whatsapp_phone_number_id
        token = restaurant.whatsapp_access_token

        if msg_type == "text":
            await send_text(to, final["body"], p_id, token)
        elif msg_type == "buttons":
            await send_interactive_buttons(to, final["body"], final["buttons"], p_id, token)
        elif msg_type == "list":
            await send_interactive_list(to, final["body"], final.get("button_label", "View"), final["sections"], p_id, token)

    return {"status": "ok"}
